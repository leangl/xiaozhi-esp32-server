import os
import sys
import copy
import json
import re
import uuid
import time
import queue
import asyncio
import threading
import traceback
import subprocess
import websockets
import opuslib_next
import numpy as np

from core.utils.util import (
    extract_json_from_string,
    check_vad_update,
    check_asr_update,
    filter_sensitive_info,
)
from typing import Dict, Any
from collections import deque
from core.utils.modules_initialize import (
    initialize_modules,
    initialize_tts,
    initialize_asr,
)
from core.handle.reportHandle import report, enqueue_tool_report
from core.providers.tts.default import DefaultTTS
from concurrent.futures import ThreadPoolExecutor
from core.utils.dialogue import Message, Dialogue
from core.providers.asr.dto.dto import InterfaceType
from core.handle.textHandle import handleTextMessage
from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.loadplugins import auto_import_modules
from plugins_func.register import Action, ActionResponse, all_function_registry, module_func_map
from core.auth import AuthenticationError
from config.config_loader import get_private_config_from_api
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from config.logger import setup_logging, build_module_string, create_connection_logger
from config.manage_api_client import DeviceNotFoundException, DeviceBindException, generate_and_save_chat_title
from core.utils.prompt_manager import PromptManager
from core.utils.voiceprint_provider import VoiceprintProvider
from core.utils.util import get_system_error_response
from core.utils import textUtils


TAG = __name__

auto_import_modules("plugins_func.functions")


class TTSException(RuntimeError):
    pass

# direct_answer virtual tool definition.
# A routing mechanism, not a real tool: turn the binary tool/no-tool choice into a tool-selection choice to reduce accidental tool calls by small models.
DIRECT_ANSWER_TOOL = {
    "type": "function",
    "function": {
        "name": "direct_answer",
        # Model-facing prompt: reply directly via response when no other tool matches.
        "description": "当用户的请求不匹配其他任何工具时，可用此选项直接回复。将回复内容写在response参数里。",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    # Model-facing prompt: the complete reply to the user.
                    "description": "你回复用户的完整内容",
                },
            },
            "required": ["response"],
        },
    },
}


class ConnectionHandler:
    def __init__(
            self,
            config: Dict[str, Any],
            _vad,
            _asr,
            _llm,
            _memory,
            _intent,
            server=None,
    ):
        self.common_config = config
        self.config = copy.deepcopy(config)
        self.session_id = str(uuid.uuid4())
        self.logger = setup_logging()
        self.server = server  # Keep a reference to the server instance.

        self.need_bind = False  # Whether device binding is required.
        self.bind_completed_event = asyncio.Event()
        self.bind_code = None  # Device binding verification code.
        self.last_bind_prompt_time = 0  # Timestamp of the last binding prompt, in seconds.
        self.bind_prompt_interval = 60  # Binding-prompt interval, in seconds.

        self.read_config_from_api = self.config.get("read_config_from_api", False)

        self.websocket: websockets.ServerConnection | None = None
        self.headers = None
        self.device_id = None
        self.client_ip = None
        self.prompt = None
        self.welcome_msg = None
        self.max_output_size = 0
        self.chat_history_conf = 0
        self.audio_format = "opus"
        self.sample_rate = 24000  # Default sample rate; updated dynamically from the client's hello message.

        # Client state.
        self.client_abort = False
        self.client_is_speaking = False
        self.client_listen_mode = "auto"
        self.client_aec = False  # Whether server-side AEC is enabled.

        # Thread/task state.
        self.loop = None  # Retrieve the running event loop in handle_connection.
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Add the reporting thread pool.
        self.report_queue = queue.Queue()
        self.report_thread = None
        # Adjust ASR/TTS reporting here in the future; both are enabled by default.
        self.report_asr_enable = self.read_config_from_api
        self.report_tts_enable = self.read_config_from_api

        # Component dependencies.
        self.vad = None
        self.asr = None
        self.tts = None
        self._asr = _asr
        self._vad = _vad
        self.llm = _llm
        self.memory = _memory
        self.intent = _intent

        # Manage voiceprint recognition separately for each connection.
        self.voiceprint_provider = None

        # VAD state.
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_window = deque(maxlen=5)
        self.first_activity_time = 0.0  # First activity timestamp, in milliseconds.
        self.last_activity_time = 0.0  # Shared activity timestamp, in milliseconds.
        self.vad_last_voice_time = 0.0  # User's last speech timestamp, in milliseconds.
        self.client_voice_stop = False
        self.last_is_voice = False

        # ASR state.
        # Deployments may share a local ASR instance; do not expose connection-specific state on it.
        # Define ASR-related state here as private connection variables.
        self.asr_audio = []  # PCM frames shared by VAD and ASR.
        self.asr_audio_queue = queue.Queue()
        self.current_speaker = None  # Current speaker.
        self.introduced_speakers = set()  # Speakers already introduced; include their name only on the first turn.
        self.system_introduced_speakers = set()  # Speakers whose identity was already injected into system; do so only on their first turn.

        # LLM state.
        self.dialogue = Dialogue()

        # TTS state.
        self.sentence_id = None
        # Handle TTS responses that return no text.
        self.tts_MessageText = ""

        # IoT state.
        self.iot_descriptors = {}
        self.func_handler = None

        self.cmd_exit = self.config["exit_commands"]

        # Whether to close the connection after chatting.
        self.close_after_chat = False
        self.load_function_plugin = False
        self.intent_type = "nointent"

        self.timeout_seconds = (
                int(self.config.get("close_connection_no_voice_time", 120)) + 60
        )  # Second-stage closure: 60 seconds after the original first-stage timeout.
        self.timeout_task = None

        # {"mcp":true} enables MCP support.
        self.features = None

        # Whether the connection originates from MQTT.
        self.conn_from_mqtt_gateway = False

        # Initialize the prompt manager.
        self.prompt_manager = PromptManager(self.config, self.logger)

        # Initialize call state.
        self.calling = False
        # Whether incoming-call mode is active.
        self.incoming_call = None

    async def handle_connection(self, ws: websockets.ServerConnection):
        try:
            # Get the running event loop (requires an asynchronous context).
            self.loop = asyncio.get_running_loop()

            # Read and validate headers.
            self.headers = dict(ws.request.headers)
            real_ip = self.headers.get("x-real-ip") or self.headers.get(
                "x-forwarded-for"
            )
            if real_ip:
                self.client_ip = real_ip.split(",")[0].strip()
            else:
                self.client_ip = ws.remote_address[0]
            self.logger.bind(tag=TAG).info(
                f"{self.client_ip} conn - Headers: {self.headers}"
            )

            self.device_id = self.headers.get("device-id", None)

            # Authentication passed; continue processing.
            self.websocket = ws

            # Check whether this is an MQTT connection.
            request_path = ws.request.path
            self.conn_from_mqtt_gateway = request_path.endswith("?from=mqtt_gateway")
            if self.conn_from_mqtt_gateway:
                self.logger.bind(tag=TAG).info("Connection source: MQTT gateway")

            # Initialize activity timestamps.
            self.first_activity_time = time.time() * 1000
            self.last_activity_time = time.time() * 1000

            # Start the timeout-check task.
            self.timeout_task = asyncio.create_task(self._check_timeout())

            # Start the AEC cache-cleanup task.
            self._aec_cache_cleanup_task = asyncio.create_task(self._check_aec_cache_expiry())

            self.welcome_msg = self.config["xiaozhi"]
            self.welcome_msg["session_id"] = self.session_id

            # Read the sample rate from configuration.
            self.sample_rate = self.welcome_msg["audio_params"]["sample_rate"]
            self.logger.bind(tag=TAG).info(f"Configured output audio sample rate: {self.sample_rate}")

            # Initialize configuration and components in the background without blocking the main loop.
            asyncio.create_task(self._background_initialize())

            try:
                async for message in self.websocket:
                    await self._route_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.bind(tag=TAG).info("Client disconnected")

        except AuthenticationError as e:
            self.logger.bind(tag=TAG).error(f"Authentication failed: {str(e)}")
            return
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.bind(tag=TAG).error(f"Connection error: {str(e)}-{stack_trace}")
            return
        finally:
            try:
                await self._save_and_close(ws)
            except Exception as final_error:
                self.logger.bind(tag=TAG).error(f"Error during final cleanup: {final_error}")
                # Close the connection even if saving memory fails.
                try:
                    await self.close(ws)
                except Exception as close_error:
                    self.logger.bind(tag=TAG).error(
                        f"Error forcing the connection closed: {close_error}"
                    )

    async def _save_and_close(self, ws):
        """Save memory and close the connection."""
        try:
            # Daemon thread 1: generate the title independently of the memory model.
            # Generate titles only when server-side chat_history reporting is enabled.
            # Otherwise the server cannot resolve the corresponding agent/chat_history from session_id,
            # and reports an agent-not-found error.
            if self.session_id and self.chat_history_conf != 0:
                def generate_title_task():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            generate_and_save_chat_title(self.session_id)
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(f"Title generation failed: {e}")
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                threading.Thread(target=generate_title_task, daemon=True).start()

            # Daemon thread 2: retain the existing memory-save path (memory only, no title).
            if self.memory:
                # Save memory asynchronously using the thread pool.
                def save_memory_task():
                    try:
                        # Create a new event loop to avoid conflicts with the main loop.
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory.save_memory(
                                self.dialogue.dialogue, self.session_id
                            )
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(f"Failed to save memory: {e}")
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                # Start the memory-saving thread without waiting for completion.
                threading.Thread(target=save_memory_task, daemon=True).start()
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to save memory: {e}")
        finally:
            # Close the connection immediately without waiting for memory to be saved.
            try:
                await self.close(ws)
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"Failed to close the connection after saving memory: {close_error}"
                )

    async def _discard_message_with_bind_prompt(self):
        """Discard the message and check whether a binding prompt is needed."""
        current_time = time.time()
        # Check whether a binding prompt is needed.
        if current_time - self.last_bind_prompt_time >= self.bind_prompt_interval:
            self.last_bind_prompt_time = current_time
            # Reuse existing binding-prompt logic.
            from core.handle.receiveAudioHandle import check_bind_device

            asyncio.create_task(check_bind_device(self))

    async def _route_message(self, message):
        """Route an incoming message."""
        # Check whether the actual binding state has been retrieved.
        if not self.bind_completed_event.is_set():
            # Wait until the actual state arrives or the timeout expires.
            try:
                await asyncio.wait_for(self.bind_completed_event.wait(), timeout=1)
            except asyncio.TimeoutError:
                # Discard the message if the state is still unavailable after timeout.
                await self._discard_message_with_bind_prompt()
                return

        # With the actual state available, check whether binding is required.
        if self.need_bind:
            # Binding required: discard the message.
            await self._discard_message_with_bind_prompt()
            return

        # Binding not required: continue handling the message.

        if isinstance(message, str):
            await handleTextMessage(self, message)
        elif isinstance(message, bytes):
            if self.vad is None or self.asr is None:
                return

            # Handle audio packets from the MQTT gateway.
            if self.conn_from_mqtt_gateway and len(message) >= 16:
                handled = await self._process_mqtt_audio_message(message)
                if handled:
                    return

            # Decode PCM at entry to avoid decoding it separately for VAD and ASR.
            pcm_frame = self._decode_opus_packet(message)
            if pcm_frame:
                self.asr_audio_queue.put(pcm_frame)

    async def _process_mqtt_audio_message(self, message):
        """
        Handle MQTT gateway audio: parse its 16-byte header, extract audio and apply AEC before enqueueing.

        Args:
            message: Audio message including its header.

        Returns:
            bool: Whether the message was processed successfully.
        """
        try:
            # Parse timestamp.
            timestamp = int.from_bytes(message[8:12], "big")

            audio_data = message[16:]
            # Decode PCM at entry.
            pcm_frame = self._decode_opus_packet(audio_data)
            if not pcm_frame:
                return True

            # Apply AEC if timestamp>0 and AEC is enabled.
            if timestamp > 0 and self.client_aec:
                pcm_frame = self._apply_aec(timestamp, pcm_frame)

            self.asr_audio_queue.put(pcm_frame)
            return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to parse WebSocket audio packet: {e}")

        # On failure, return False to request further handling.
        return False

    def _apply_aec(self, timestamp: int, pcm_frame: bytes) -> bytes:
        """Apply AEC using cross-correlation delay estimation, Wiener filtering and spectral subtraction."""
        try:
            if not pcm_frame or len(pcm_frame) == 0:
                return pcm_frame

            if not hasattr(self, "aec_audio_cache") or not self.aec_audio_cache:
                return pcm_frame

            mic_audio = np.frombuffer(pcm_frame, dtype=np.int16).astype(np.float32)
            mic_rms = np.sqrt(np.mean(mic_audio ** 2))

            if mic_rms < 100:
                return pcm_frame

            sorted_timestamps = sorted(self.aec_audio_cache.keys())
            if len(sorted_timestamps) < 2:
                return pcm_frame

            # ========== Match reference frames using log power spectra ==========
            n = len(mic_audio)

            # Start from the closest timestamp.
            closest_idx = min(range(len(sorted_timestamps)), key=lambda i: abs(sorted_timestamps[i] - timestamp))

            # Precompute mic_audio's log power spectrum for reuse in the loop, avoiding repeated FFTs.
            mic_window = np.hanning(n)
            mic_fft = np.fft.rfft(mic_audio * mic_window)
            mic_psd = np.abs(mic_fft) ** 2
            mic_log_psd = 10 * np.log10(mic_psd + 1e-8)
            mic_P_xx = np.dot(mic_log_psd, mic_log_psd)

            # Find the best log-power-spectrum match within two frames on either side.
            best_corr = -1
            best_ref_idx = closest_idx
            best_ref_rms = 0.0

            for offset in range(-2, 3):  # T-2, T-1, T, T+1, T+2
                test_idx = closest_idx + offset
                if test_idx < 0 or test_idx >= len(sorted_timestamps):
                    continue
                test_ts = sorted_timestamps[test_idx]
                test_ref = np.frombuffer(self.aec_audio_cache[test_ts], dtype=np.int16).astype(np.float32)
                test_ref_rms = np.sqrt(np.mean(test_ref ** 2))
                if test_ref_rms < 50:
                    continue

                # Log-power-spectrum correlation.
                test_window = np.hanning(len(test_ref))
                test_fft = np.fft.rfft(test_ref * test_window)
                test_psd = np.abs(test_fft) ** 2
                test_log_psd = 10 * np.log10(test_psd + 1e-8)
                P_xy = np.dot(mic_log_psd, test_log_psd)
                P_yy = np.dot(test_log_psd, test_log_psd)
                corr = abs(P_xy) / (np.sqrt(mic_P_xx) * np.sqrt(P_yy) + 1e-8)

                if corr > best_corr:
                    best_corr = corr
                    best_ref_idx = test_idx
                    best_ref_rms = test_ref_rms

            best_ts = sorted_timestamps[best_ref_idx]
            best_ref = np.frombuffer(self.aec_audio_cache[best_ts], dtype=np.int16).astype(np.float32)
            ref_rms = best_ref_rms

            if ref_rms < 50:
                return pcm_frame

            # Align the reference signal by truncating to the same length.
            aligned_ref = best_ref[:n]
            if len(aligned_ref) < n:
                aligned_ref = np.pad(aligned_ref, (0, n - len(aligned_ref)))

            # ========== Frequency-domain AEC using spectral subtraction ==========
            # Acoustic-path phase distortion lowers time-domain correlation and makes P_xy's sign unstable.
            # Frequency-domain magnitudes are phase-independent; log-power-spectrum correlation stays above 0.97.
            # Formula: result_mag = max(|mic_fft| - |ref_fft| * scale * coef, 0).

            mic_mag = np.abs(mic_fft)
            mic_phase = np.angle(mic_fft)
            ref_fft = np.fft.rfft(aligned_ref * np.hanning(n))
            ref_mag = np.abs(ref_fft)

            # Compute the echo ratio scale in the frequency domain.
            scale = np.sum(mic_mag * ref_mag) / (np.dot(ref_mag, ref_mag) + 1e-8)

            # Adaptive coefficient: adjust dynamically using scale and coh.
            # Larger scale (stronger echo) or coh (better match) increases coef.
            raw_coef = 1.0 + scale * 3 + (best_corr - 0.97) * 30
            coef = max(0.5, min(3.0, raw_coef))

            # Spectral subtraction (oversubtraction + half-wave rectification).
            echo_mag = ref_mag * scale * coef
            result_mag = np.maximum(mic_mag - echo_mag * 1.5, mic_mag * 0.1)

            # Reconstruct the signal while preserving phase.
            result_fft = result_mag * np.exp(1j * mic_phase)
            output = np.fft.irfft(result_fft, n)

            # Further suppress high-confidence pure echo so VAD does not detect it.
            if best_corr >= 0.97 and ref_rms > 500:
                output = output * 0.3

            # Postprocessing: amplitude limiting.
            output = np.clip(output, -32768, 32767)

            # Convert to bytes.
            result = output.astype(np.int16).tobytes()

            return result

        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"[AEC] Processing failed: {e}")
            return pcm_frame

    def _decode_opus_packet(self, opus_packet: bytes) -> bytes:
        """
        Decode an Opus packet to PCM data.

        Args:
            opus_packet: Opus-encoded audio data.

        Returns:
            bytes: Decoded PCM data, or None on failure.
        """
        try:
            if not opus_packet or len(opus_packet) == 0:
                return None

            self._init_connection_state(self)
            pcm_frame = self._connection_opus_decoder.decode(opus_packet, 960)
            return pcm_frame
        except Exception as e:
            self.logger.bind(tag=TAG).debug(f"Opus decoding failed: {e}")
            return None

    def _init_connection_state(self, conn):
        """Initialize a dedicated Opus decoder for the connection."""
        if not hasattr(conn, "_connection_opus_decoder"):
            conn._connection_opus_decoder = opuslib_next.Decoder(16000, 1)

    async def handle_restart(self, message):
        """Handle a server restart request."""
        try:

            self.logger.bind(tag=TAG).info("Server restart command received; preparing to restart...")

            # Send the acknowledgement.
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "success",
                        "message": "Server restarting...",
                        "content": {"action": "restart"},
                    }
                )
            )

            # Perform the restart asynchronously.
            def restart_server():
                """Perform the actual restart."""
                time.sleep(1)
                self.logger.bind(tag=TAG).info("Restarting the server...")
                subprocess.Popen(
                    [sys.executable, "app.py"],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    start_new_session=True,
                )
                os._exit(0)

            # Run the restart in a thread to avoid blocking the event loop.
            threading.Thread(target=restart_server, daemon=True).start()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Restart failed: {str(e)}")
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": f"Restart failed: {str(e)}",
                        "content": {"action": "restart"},
                    }
                )
            )

    def _initialize_components(self):
        try:
            if self.tts is None:
                self.tts = self._initialize_tts()
            # Open the speech-synthesis channel.
            asyncio.run_coroutine_threadsafe(
                self.tts.open_audio_channels(self), self.loop
            )
            if self.need_bind:
                self.bind_completed_event.set()
                return
            self.selected_module_str = build_module_string(
                self.config.get("selected_module", {})
            )
            self.logger = create_connection_logger(self.selected_module_str)

            """Initialize components."""
            if self.config.get("prompt") is not None:
                user_prompt = self.config["prompt"]
                # Initialize with the quick prompt.
                prompt = self.prompt_manager.get_quick_prompt(user_prompt)
                self.change_system_prompt(prompt)
                self.logger.bind(tag=TAG).info(
                    f"Quick component initialization: prompt ready {prompt[:50]}..."
                )

            """Initialize local components."""
            if self.vad is None:
                self.vad = self._vad
            if self.asr is None:
                self.asr = self._initialize_asr()

            # Initialize voiceprint recognition.
            self._initialize_voiceprint()
            # Open the speech-recognition channel.
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )

            """Load memory."""
            self._initialize_memory()
            """Load intent recognition."""
            self._initialize_intent()
            """Initialize the reporting thread."""
            self._init_report_threads()
            """Update the system prompt."""
            self._init_prompt_enhancement()
            """Inject tool-call few-shot examples (function_call mode only)."""
            self._inject_tool_call_fewshot()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to instantiate components: {e}")

    def _init_prompt_enhancement(self):

        # Update context information.
        self.prompt_manager.update_context_info(self, self.client_ip)
        enhanced_prompt = self.prompt_manager.build_enhanced_prompt(
            self.config["prompt"],
            self.device_id,
            self.client_ip,
            emoji_enabled=(self.features or {}).get("emoji", True),
        )
        if enhanced_prompt:
            self.change_system_prompt(enhanced_prompt)
            self.logger.bind(tag=TAG).debug("Enhanced system prompt updated")

    def _inject_tool_call_fewshot(self):
        """Inject tool-call few-shot examples into conversation history.
        Place positive examples (tool calls) before the dynamic system context to enable prefix caching.
        Place negative examples (direct answers) after dynamic system context, just before real user messages,
        so the final pattern the model sees before handling a user message is answering without tools.
        """
        if self.intent_type != "function_call":
            return
        if not hasattr(self, "func_handler") or self.func_handler is None:
            return

        tools = self.func_handler.get_functions()
        if not tools:
            return

        tool_names = {t.get("function", {}).get("name") for t in tools}

        # === Few-shot examples (is_temporary): preserve their model-facing language ===
        # Demonstrate direct_answer with a response argument, completing the reply in one call.

        # Example 1: direct_answer (reply in the response argument; no recursion).
        da_tc_id = "fewshot_da_001"
        self.dialogue.put(Message(role="user", content="给我讲个故事吧", is_temporary=True))
        self.dialogue.put(Message(
            role="assistant",
            tool_calls=[{
                "id": da_tc_id,
                "function": {"arguments": '{"response": "好呀，你想听什么类型的呀？童话、冒险还是搞笑的？选一个我给你开讲~"}', "name": "direct_answer"},
                "type": "function", "index": 0,
            }],
            is_temporary=True,
        ))
        self.dialogue.put(Message(
            role="tool", tool_call_id=da_tc_id,
            content="已直接回复", is_temporary=True,
        ))

        # Example 2: a real tool call (handle_exit_intent).
        if "handle_exit_intent" in tool_names:
            tc_id = "fewshot_exit_001"
            self.dialogue.put(Message(role="user", content="拜拜", is_temporary=True))
            self.dialogue.put(Message(
                role="assistant",
                tool_calls=[{
                    "id": tc_id,
                    "function": {"arguments": '{"say_goodbye": "再见，下次再聊~"}', "name": "handle_exit_intent"},
                    "type": "function", "index": 0,
                }],
                is_temporary=True,
            ))
            self.dialogue.put(Message(
                role="tool", tool_call_id=tc_id,
                content="退出意图已处理", is_temporary=True,
            ))
            self.dialogue.put(Message(
                role="assistant", content="再见，下次再聊~", is_temporary=True,
            ))

        self.logger.bind(tag=TAG).debug("Tool-call few-shot examples injected")

    def _init_report_threads(self):
        """Initialize ASR and TTS reporting threads."""
        if not self.read_config_from_api or self.need_bind:
            return
        if self.chat_history_conf == 0:
            return
        if self.report_thread is None or not self.report_thread.is_alive():
            self.report_thread = threading.Thread(
                target=self._report_worker, daemon=True
            )
            self.report_thread.start()
            self.logger.bind(tag=TAG).info("TTS reporting thread started")

    def _initialize_tts(self):
        """Initialize TTS."""
        tts = None
        if not self.need_bind:
            tts = initialize_tts(self.config)

        if tts is None:
            tts = DefaultTTS(self.config, delete_audio_file=True)

        return tts

    def _initialize_asr(self):
        """Initialize ASR."""
        if (
                self._asr is not None
                and hasattr(self._asr, "interface_type")
                and self._asr.interface_type == InterfaceType.LOCAL
        ):
            # Return the shared ASR directly if it is local.
            # A local ASR instance can be shared by multiple connections.
            asr = self._asr
        else:
            # Create a new instance when the shared ASR configuration is remote.
            # Remote ASR has WebSocket connections and receiver threads, requiring one instance per connection.
            asr = initialize_asr(self.config)

        return asr

    def _initialize_voiceprint(self):
        """Initialize voiceprint recognition for this connection."""
        try:
            voiceprint_config = self.config.get("voiceprint", {})
            if voiceprint_config:
                voiceprint_provider = VoiceprintProvider(voiceprint_config)
                if voiceprint_provider is not None and voiceprint_provider.enabled:
                    self.voiceprint_provider = voiceprint_provider
                    self.logger.bind(tag=TAG).info("Voiceprint recognition enabled dynamically on connection")
                else:
                    self.logger.bind(tag=TAG).warning("Voiceprint recognition enabled, but configuration is incomplete")
            else:
                self.logger.bind(tag=TAG).info("Voiceprint recognition disabled")
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"Voiceprint initialization failed: {str(e)}")

    async def _background_initialize(self):
        """Initialize configuration and components in the background without blocking the main loop."""
        try:
            # Fetch connection-specific configuration asynchronously.
            await self._initialize_private_config_async()
            # Initialize components in the thread pool.
            self.executor.submit(self._initialize_components)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Background initialization failed: {e}")

    async def _initialize_private_config_async(self):
        """Fetch connection-specific configuration asynchronously without blocking the main loop."""
        if not self.read_config_from_api:
            self.need_bind = False
            self.bind_completed_event.set()
            return
        try:
            begin_time = time.time()
            private_config = await get_private_config_from_api(
                self.config,
                self.headers.get("device-id"),
                self.headers.get("client-id", self.headers.get("device-id")),
            )
            private_config["delete_audio"] = bool(self.config.get("delete_audio", True))
            private_config["tts_timeout"] = self.config.get("tts_timeout", 15)
            self.logger.bind(tag=TAG).info(
                f"{time.time() - begin_time} seconds; connection-specific configuration fetched asynchronously: {json.dumps(filter_sensitive_info(private_config), ensure_ascii=False)}"
            )
            self.need_bind = False
            self.bind_completed_event.set()
        except DeviceNotFoundException as e:
            self.need_bind = True
            private_config = {}
        except DeviceBindException as e:
            self.need_bind = True
            self.bind_code = e.bind_code
            private_config = {}
        except Exception:
            self.logger.bind(tag=TAG).error("Device configuration unavailable; no shared-provider fallback will be activated")
            raise

        init_llm, init_tts, init_memory, init_intent = (
            False,
            False,
            False,
            False,
        )

        init_vad = check_vad_update(self.common_config, private_config)
        init_asr = check_asr_update(self.common_config, private_config)

        if init_vad:
            self.config["VAD"] = private_config["VAD"]
            self.config["selected_module"]["VAD"] = private_config["selected_module"][
                "VAD"
            ]
        if init_asr:
            self.config["ASR"] = private_config["ASR"]
            self.config["selected_module"]["ASR"] = private_config["selected_module"][
                "ASR"
            ]
        if private_config.get("TTS", None) is not None:
            init_tts = True
            self.config["TTS"] = private_config["TTS"]
            self.config["selected_module"]["TTS"] = private_config["selected_module"][
                "TTS"
            ]
        if private_config.get("LLM", None) is not None:
            init_llm = True
            self.config["LLM"] = private_config["LLM"]
            self.config["selected_module"]["LLM"] = private_config["selected_module"][
                "LLM"
            ]
        if private_config.get("VLLM", None) is not None:
            self.config["VLLM"] = private_config["VLLM"]
            self.config["selected_module"]["VLLM"] = private_config["selected_module"][
                "VLLM"
            ]
        if private_config.get("Memory", None) is not None:
            init_memory = True
            self.config["Memory"] = private_config["Memory"]
            self.config["selected_module"]["Memory"] = private_config[
                "selected_module"
            ]["Memory"]
        if private_config.get("Intent", None) is not None:
            init_intent = True
            self.config["Intent"] = private_config["Intent"]
            model_intent = private_config.get("selected_module", {}).get("Intent", {})
            self.config["selected_module"]["Intent"] = model_intent
            # Load plugin configuration.
            if model_intent != "Intent_nointent":
                plugin_from_server = private_config.get("plugins", {})
                for plugin, config_str in plugin_from_server.items():
                    plugin_from_server[plugin] = json.loads(config_str)
                # Copy module-level plugin configuration to each concrete function name
                # for later per-function lookup of descriptions, news_sources and other settings.
                for module_name, func_names in module_func_map.items():
                    if module_name in plugin_from_server:
                        module_config = plugin_from_server[module_name]
                        for func_name in func_names:
                            if func_name not in plugin_from_server:
                                plugin_from_server[func_name] = module_config
                self.config["plugins"] = plugin_from_server
                # Expand module-level plugin names into concrete function names.
                expanded_functions = []
                for plugin_key in plugin_from_server.keys():
                    if plugin_key in all_function_registry:
                        expanded_functions.append(plugin_key)
                    elif plugin_key in module_func_map:
                        expanded_functions.extend(module_func_map[plugin_key])
                    else:
                        expanded_functions.append(plugin_key)
                self.config["Intent"][self.config["selected_module"]["Intent"]][
                    "functions"
                ] = expanded_functions
        if private_config.get("prompt", None) is not None:
            self.config["prompt"] = private_config["prompt"]
        # Get voiceprint information.
        if private_config.get("voiceprint", None) is not None:
            self.config["voiceprint"] = private_config["voiceprint"]
        if private_config.get("summaryMemory", None) is not None:
            self.config["summaryMemory"] = private_config["summaryMemory"]
        if private_config.get("device_max_output_size", None) is not None:
            self.max_output_size = int(private_config["device_max_output_size"])
        if private_config.get("chat_history_conf", None) is not None:
            self.chat_history_conf = int(private_config["chat_history_conf"])
        if private_config.get("mcp_endpoint", None) is not None:
            self.config["mcp_endpoint"] = private_config["mcp_endpoint"]
        if private_config.get("context_providers", None) is not None:
            self.config["context_providers"] = private_config["context_providers"]

        # Inject replacement words into TTS configuration.
        if private_config.get("correct_words", None) is not None:
            select_tts_module = self.config["selected_module"]["TTS"]
            self.config["TTS"][select_tts_module]["correct_words"] = private_config[
                "correct_words"
            ]

        # Run initialize_modules in the thread pool using run_in_executor to avoid blocking the main loop.
        try:
            modules = await self.loop.run_in_executor(
                None,  # Use the default thread pool.
                initialize_modules,
                self.logger,
                private_config,
                init_vad,
                init_asr,
                init_llm,
                init_tts,
                init_memory,
                init_intent,
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Component initialization failed: {e}")
            modules = {}
        if modules.get("tts", None) is not None:
            self.tts = modules["tts"]
        if modules.get("vad", None) is not None:
            self.vad = modules["vad"]
        if modules.get("asr", None) is not None:
            self.asr = modules["asr"]
        if modules.get("llm", None) is not None:
            self.llm = modules["llm"]
        if modules.get("intent", None) is not None:
            self.intent = modules["intent"]
        if modules.get("memory", None) is not None:
            self.memory = modules["memory"]

    def _initialize_memory(self):
        if self.memory is None:
            return
        """Initialize the memory module."""
        self.memory.init_memory(
            role_id=self.device_id,
            llm=self.llm,
            summary_memory=self.config.get("summaryMemory", None),
            save_to_file=not self.read_config_from_api,
        )

        # Get memory-summary configuration.
        memory_config = self.config["Memory"]
        memory_type = self.config["Memory"][self.config["selected_module"]["Memory"]][
            "type"
        ]
        # Return immediately for nomem or mem_report_only.
        if memory_type == "nomem" or memory_type == "mem_report_only":
            return
        # Use mem_local_short mode.
        elif memory_type == "mem_local_short":
            memory_llm_name = memory_config[self.config["selected_module"]["Memory"]][
                "llm"
            ]
            if memory_llm_name and memory_llm_name in self.config["LLM"]:
                # Create a separate LLM instance if a dedicated model is configured.
                from core.utils import llm as llm_utils

                memory_llm_config = self.config["LLM"][memory_llm_name]
                memory_llm_type = memory_llm_config.get("type", memory_llm_name)
                memory_llm = llm_utils.create_instance(
                    memory_llm_type, memory_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"Created a dedicated LLM for memory summaries: {memory_llm_name}, type: {memory_llm_type}"
                )
                self.memory.set_llm(memory_llm)
            else:
                # Otherwise use the main LLM.
                self.memory.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("Using the main LLM for intent recognition")

    def _initialize_intent(self):
        if self.intent is None:
            return
        self.intent_type = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ]["type"]
        if self.intent_type == "function_call" or self.intent_type == "intent_llm":
            self.load_function_plugin = True
        """Initialize the intent-recognition module."""
        # Get intent-recognition configuration.
        intent_config = self.config["Intent"]
        intent_type = self.config["Intent"][self.config["selected_module"]["Intent"]][
            "type"
        ]

        # Return immediately for nointent.
        if intent_type == "nointent":
            return
        # Use intent_llm mode.
        elif intent_type == "intent_llm":
            intent_llm_name = intent_config[self.config["selected_module"]["Intent"]][
                "llm"
            ]

            if intent_llm_name and intent_llm_name in self.config["LLM"]:
                # Create a separate LLM instance if a dedicated model is configured.
                from core.utils import llm as llm_utils

                intent_llm_config = self.config["LLM"][intent_llm_name]
                intent_llm_type = intent_llm_config.get("type", intent_llm_name)
                intent_llm = llm_utils.create_instance(
                    intent_llm_type, intent_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"Created a dedicated LLM for intent recognition: {intent_llm_name}, type: {intent_llm_type}"
                )
                self.intent.set_llm(intent_llm)
            else:
                # Otherwise use the main LLM.
                self.intent.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("Using the main LLM for intent recognition")

        """Load the unified tool handler."""
        self.func_handler = UnifiedToolHandler(self)

        # Initialize the tool handler asynchronously.
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(self.func_handler._initialize(), self.loop)

    def change_system_prompt(self, prompt):
        self.prompt = prompt
        # Update the system prompt in context.
        self.dialogue.update_system_message(self.prompt)

    def chat(self, query, depth=0):
        # Capture the current task's sentence_id locally so a new task cannot overwrite it.
        current_sentence_id = None

        if query is not None:
            self.logger.bind(tag=TAG).info(f"LLM received user message: {query}")

        # At the top level, create a sentence ID and send FIRST.
        if depth == 0:
            current_sentence_id = str(uuid.uuid4().hex)
            self.sentence_id = current_sentence_id  # Update the shared attribute.
            self.dialogue.put(Message(role="user", content=query))
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=current_sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
        else:
            # Reuse the current sentence_id in recursive calls.
            current_sentence_id = self.sentence_id

        # Set a maximum recursion depth to prevent infinite loops; adjust as needed.
        MAX_DEPTH = 5
        force_final_answer = False  # Whether to force a final answer.

        if depth >= MAX_DEPTH:
            self.logger.bind(tag=TAG).debug(
                f"Maximum tool-call depth reached: {MAX_DEPTH}; forcing an answer using available information"
            )
            force_final_answer = True
            # Add the existing model-language system instruction to answer using available information.
            self.dialogue.put(
                Message(
                    role="user",
                    content="[系统提示] 已达到最大工具调用次数限制，请你基于目前已经获取的所有信息，直接给出最终答案。不要再尝试调用任何工具。",
                )
            )

        # Define intent functions
        functions = None
        # At maximum depth, disable tools and force the LLM to answer directly.
        if (
                self.intent_type == "function_call"
                and hasattr(self, "func_handler")
                and not force_final_answer
        ):
            functions = list(self.func_handler.get_functions())
            # Inject the direct_answer virtual tool only at the first call level.
            # Do not inject it during recursive calls (depth>0), avoiding loops where text responses invoke direct_answer again.
            if functions is not None and depth == 0:
                functions.append(DIRECT_ANSWER_TOOL)

        response_message = []

        try:
            # Use conversation context with memory.
            memory_str = None
            # Query memory only for a nonempty query (a user request).
            if self.memory is not None and query:
                future = asyncio.run_coroutine_threadsafe(
                    self.memory.query_memory(query), self.loop
                )
                memory_str = future.result()

            # Inject identity into system only on a speaker's first appearance; retain it through conversation history afterward.
            # Avoid repeating names in system each turn and encouraging repetitive forms of address.
            speaker_for_system = None
            cs = (self.current_speaker or "").strip()
            if cs and cs != "未知说话人" and cs not in self.system_introduced_speakers:
                self.system_introduced_speakers.add(cs)
                speaker_for_system = cs

            if self.intent_type == "function_call" and functions is not None:
                # Use the streaming interface with function support.
                llm_responses = self.llm.response_with_functions(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {}), speaker_for_system
                    ),
                    functions=functions,
                )
            else:
                llm_responses = self.llm.response(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {}), speaker_for_system
                    ),
                )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM processing error for {query}: {e}")
            return None

        # Handle the streaming response.
        tool_call_flag = False
        # Support multiple parallel tool calls by storing them in a list.
        tool_calls_list = []  # Format: [{"id": "", "name": "", "arguments": ""}].
        content_arguments = ""
        emotion_flag = True
        try:
            for response in llm_responses:
                if self.client_abort:
                    break
                if self.intent_type == "function_call" and functions is not None:
                    content, tools_call = response
                    if "content" in response:
                        content = response["content"]
                        tools_call = None
                    if content is not None and len(content) > 0:
                        content_arguments += content

                    if not tool_call_flag and content_arguments.startswith("<tool_call>"):
                        # print("content_arguments", content_arguments)
                        tool_call_flag = True

                    if tools_call is not None and len(tools_call) > 0:
                        tool_call_flag = True
                        self._merge_tool_calls(tool_calls_list, tools_call)

                    # Extract direct_answer's response argument incrementally and send it to TTS in real time.
                    # Use a safety buffer to prevent JSON closing characters from leaking into TTS.
                    _DA_STREAM_BUFFER = 5
                    for tc in tool_calls_list:
                        if tc["name"] == "direct_answer" and tc.get("arguments"):
                            da_text = self._extract_direct_answer_response(tc["arguments"])
                            sent_len = tc.get("_da_sent", 0)
                            if da_text and len(da_text) > sent_len:
                                safe_end = max(sent_len, len(da_text) - _DA_STREAM_BUFFER)
                                if safe_end > sent_len:
                                    new_part = da_text[sent_len:safe_end]
                                    # Remove JSON closing fragments that may have leaked into delta.
                                    new_part = self._clean_response_garbage(new_part)
                                    if new_part:
                                        tc["_da_sent"] = safe_end
                                        self.tts.tts_text_queue.put(
                                            TTSMessageDTO(
                                                sentence_id=current_sentence_id,
                                                sentence_type=SentenceType.MIDDLE,
                                                content_type=ContentType.TEXT,
                                                content_detail=new_part,
                                            )
                                        )
                else:
                    content = response

                # Extract an emotion emoji from the LLM response once, at the start of each turn.
                if emotion_flag and content is not None and content.strip():
                    if (self.features or {}).get("emoji", True):
                        asyncio.run_coroutine_threadsafe(
                            textUtils.get_emotion(self, content),
                            self.loop,
                        )
                    emotion_flag = False

                if content is not None and len(content) > 0:
                    if not tool_call_flag:
                        response_message.append(content)
                        self.tts.tts_text_queue.put(
                            TTSMessageDTO(
                                sentence_id=current_sentence_id,
                                sentence_type=SentenceType.MIDDLE,
                                content_type=ContentType.TEXT,
                                content_detail=content,
                            )
                        )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM stream processing error: {e}")
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=current_sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail=get_system_error_response(self.config),
                )
            )
            if depth == 0:
                self.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=current_sentence_id,
                        sentence_type=SentenceType.LAST,
                        content_type=ContentType.ACTION,
                    )
                )
            return
        # Handle function calls.
        if tool_call_flag:
            bHasError = False
            # Handle text-based tool-call formatting.
            if len(tool_calls_list) == 0 and content_arguments:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        tool_calls_list.append(
                            {
                                "id": str(uuid.uuid4().hex),
                                "name": content_arguments_json["name"],
                                "arguments": json.dumps(
                                    content_arguments_json["arguments"],
                                    ensure_ascii=False,
                                ),
                            }
                        )
                    except Exception as e:
                        bHasError = True
                        response_message.append(a)
                else:
                    bHasError = True
                    response_message.append(content_arguments)
                if bHasError:
                    self.logger.bind(tag=TAG).error(
                        f"function call error: {content_arguments}"
                    )

            if not bHasError and len(tool_calls_list) > 0:
                # Handle the direct_answer virtual tool.
                direct_answer_calls = [tc for tc in tool_calls_list if tc["name"] == "direct_answer"]
                real_tool_calls = [tc for tc in tool_calls_list if tc["name"] != "direct_answer"]

                if direct_answer_calls:
                    self.logger.bind(tag=TAG).debug(
                        f"Model selected direct_answer; streaming speech completed; saving conversation history"
                    )
                    for tc in direct_answer_calls:
                        da_response = self._extract_direct_answer_response(tc.get("arguments", "{}"))
                        if da_response:
                            # Flush the unsent part of the streaming buffer.
                            sent_len = tc.get("_da_sent", 0)
                            remaining = da_response[sent_len:]
                            if remaining:
                                remaining = self._clean_response_garbage(remaining)
                                if remaining:
                                    self.tts.tts_text_queue.put(
                                        TTSMessageDTO(
                                            sentence_id=current_sentence_id,
                                            sentence_type=SentenceType.MIDDLE,
                                            content_type=ContentType.TEXT,
                                            content_detail=remaining,
                                        )
                                    )
                            # Append to conversation history.
                            da_response = self._clean_response_garbage(da_response)
                            self.tts.store_tts_text(current_sentence_id, da_response)
                            self.dialogue.put(Message(role="assistant", content=da_response))

                    if not real_tool_calls:
                        if depth == 0:
                            self.tts.tts_text_queue.put(
                                TTSMessageDTO(
                                    sentence_id=current_sentence_id,
                                    sentence_type=SentenceType.LAST,
                                    content_type=ContentType.ACTION,
                                )
                            )
                        return

                    tool_calls_list = real_tool_calls

            if not bHasError and len(tool_calls_list) > 0:
                self.logger.bind(tag=TAG).debug(
                    f"Detected {len(tool_calls_list)} tool calls"
                )

                # Text already spoken during LLM streaming.
                streamed_text = ""
                if len(response_message) > 0:
                    streamed_text = "".join(response_message)
                    self.tts.store_tts_text(current_sentence_id, streamed_text)
                    self.dialogue.put(Message(role="assistant", content=streamed_text))
                response_message.clear()

                # Collect Futures for all tool calls.
                futures_with_data = []
                for tool_call_data in tool_calls_list:
                    self.logger.bind(tag=TAG).debug(
                        f"function_name={tool_call_data['name']}, function_id={tool_call_data['id']}, function_arguments={tool_call_data['arguments']}"
                    )

                    # Report tool calls through the shared method.
                    tool_input = json.loads(tool_call_data.get("arguments") or "{}")
                    enqueue_tool_report(self, tool_call_data['name'], tool_input)

                    future = asyncio.run_coroutine_threadsafe(
                        self.func_handler.handle_llm_function_call(
                            self, tool_call_data
                        ),
                        self.loop,
                    )
                    futures_with_data.append((future, tool_call_data, tool_input))

                # Configurable tool-call timeout; default: 30 seconds.
                tool_call_timeout = int(self.config.get("tool_call_timeout", 30))
                # Wait for coroutines to finish (the slowest determines the wait duration).
                tool_results = []

                for future, tool_call_data, tool_input in futures_with_data:
                    try:
                        result = future.result(timeout=tool_call_timeout)
                        tool_results.append((result, tool_call_data))
                        # Report tool-call results through the shared method.
                        enqueue_tool_report(self, tool_call_data['name'], tool_input, str(result.result) if result.result else None, report_tool_call=False)

                    except Exception as e:
                        self.logger.bind(tag=TAG).error(
                            f"Tool-call timeout or exception: {tool_call_data['name']}, error: {e}"
                        )
                        # Return the existing user-language error on timeout to prevent the whole flow from hanging.
                        tool_results.append((
                            ActionResponse(action=Action.ERROR, result="哎呀，网络遇到点问题，请稍后再试下！"),
                            tool_call_data
                        ))
                        # Report tool-call errors.
                        enqueue_tool_report(self, tool_call_data['name'], tool_input, str(e), report_tool_call=False)

                # Handle tool-call results uniformly.
                if tool_results:
                    self._handle_function_result(tool_results, depth=depth, streamed_text=streamed_text)

        # Store conversation content.
        if len(response_message) > 0:
            text_buff = "".join(response_message)
            self.tts.store_tts_text(current_sentence_id, text_buff)
            self.dialogue.put(Message(role="assistant", content=text_buff))

        if depth == 0:
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=current_sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
            # Defer evaluation with a lambda; call get_llm_dialogue() only at DEBUG level.
            self.logger.bind(tag=TAG).debug(
                lambda: json.dumps(
                    self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False
                )
            )

        return True

    def _handle_function_result(self, tool_results, depth, streamed_text=""):
        need_llm_tools = []
        record_tools = []

        for result, tool_call_data in tool_results:
            if result.action in [
                Action.RESPONSE,
                Action.NOTFOUND,
                Action.ERROR,
            ]:
                text = result.response if result.response else result.result
                if streamed_text and text in streamed_text:
                    self.logger.bind(tag=TAG).debug(
                        f"Skipping duplicate TTS for tool {tool_call_data['name']}, already streamed"
                    )
                else:
                    self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
                    self.tts.store_tts_text(self.sentence_id, text)
                self.dialogue.put(Message(role="assistant", content=text))
            elif result.action == Action.REQLLM:
                need_llm_tools.append((result, tool_call_data))
            elif result.action == Action.RECORD:
                record_tools.append((result, tool_call_data))
            else:
                pass

        # Action.RECORD: write the full tool-call chain (assistant(tool_calls) → tool(result) → assistant(response)).
        # The model learns tool-call patterns from history without an additional LLM call.
        if record_tools:
            # Build an assistant message with tool_calls to record which tools the model invoked.
            all_tool_calls = [
                {
                    "id": tool_call_data["id"],
                    "function": {
                        "arguments": (
                            "{}"
                            if tool_call_data["arguments"] == ""
                            else tool_call_data["arguments"]
                        ),
                        "name": tool_call_data["name"],
                    },
                    "type": "function",
                    "index": idx,
                }
                for idx, (_, tool_call_data) in enumerate(record_tools)
            ]
            self.dialogue.put(Message(role="assistant", tool_calls=all_tool_calls))

            # Write each tool's execution result to record what the tool returned.
            for result, tool_call_data in record_tools:
                text = result.result or ""
                self.dialogue.put(
                    Message(
                        role="tool",
                        tool_call_id=(
                            str(uuid.uuid4())
                            if tool_call_data["id"] is None
                            else tool_call_data["id"]
                        ),
                        content=text,
                    )
                )

            # Use fixed text as the final response to complete the three-message sequence, allowing a user message next rather than another tool message.
            response_parts = []
            for result, _ in record_tools:
                resp = result.response or result.result
                if resp:
                    response_parts.append(resp)
            if response_parts:
                self.dialogue.put(Message(role="assistant", content="，".join(response_parts)))

        if need_llm_tools:
            all_tool_calls = [
                {
                    "id": tool_call_data["id"],
                    "function": {
                        "arguments": (
                            "{}"
                            if tool_call_data["arguments"] == ""
                            else tool_call_data["arguments"]
                        ),
                        "name": tool_call_data["name"],
                    },
                    "type": "function",
                    "index": idx,
                }
                for idx, (_, tool_call_data) in enumerate(need_llm_tools)
            ]
            self.dialogue.put(Message(role="assistant", tool_calls=all_tool_calls))

            for result, tool_call_data in need_llm_tools:
                text = result.result
                if text is not None and len(text) > 0:
                    self.dialogue.put(
                        Message(
                            role="tool",
                            tool_call_id=(
                                str(uuid.uuid4())
                                if tool_call_data["id"] is None
                                else tool_call_data["id"]
                            ),
                            content=text,
                        )
                    )

            self.chat(None, depth=depth + 1)

    def _report_worker(self):
        """Chat-history reporting worker thread."""
        while not self.stop_event.is_set():
            try:
                # Read from the queue with a timeout to check the stop event periodically.
                item = self.report_queue.get(timeout=1)
                if item is None:  # Detect the shutdown sentinel.
                    break
                try:
                    # Check thread-pool state.
                    if self.executor is None:
                        continue
                    # Submit the task to the thread pool.
                    self.executor.submit(self._process_report, *item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"Chat-history reporting thread error: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"Chat-history reporting worker error: {e}")

        self.logger.bind(tag=TAG).info("Chat-history reporting thread exited")

    def _process_report(self, type, text, audio_data, report_time):
        """Handle a reporting task."""
        try:
            # Run asynchronous reporting in the event loop.
            asyncio.run(report(self, type, text, audio_data, report_time))
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Report-processing error: {e}")
        finally:
            # Mark the task complete.
            self.report_queue.task_done()

    def clearSpeakStatus(self):
        self.client_is_speaking = False
        self.logger.bind(tag=TAG).debug(f"Clearing server-side speaking state")

    async def close(self, ws=None):
        """Clean up resources."""
        try:
            # Clean up VAD connection resources.
            if (
                    hasattr(self, "vad")
                    and self.vad
                    and hasattr(self.vad, "release_conn_resources")
            ):
                self.vad.release_conn_resources(self)

            # Clean up the Opus decoder.
            if hasattr(self, "_connection_opus_decoder"):
                try:
                    delattr(self, "_connection_opus_decoder")
                except Exception:
                    pass

            # Clear audio buffers.
            if hasattr(self, "audio_buffer"):
                self.audio_buffer.clear()

            # Cancel the timeout task.
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
                try:
                    await self.timeout_task
                except asyncio.CancelledError:
                    pass
                self.timeout_task = None

            # Cancel the AEC cache-cleanup task.
            if hasattr(self, "_aec_cache_cleanup_task") and self._aec_cache_cleanup_task and not self._aec_cache_cleanup_task.done():
                self._aec_cache_cleanup_task.cancel()
                try:
                    await self._aec_cache_cleanup_task
                except asyncio.CancelledError:
                    pass
                self._aec_cache_cleanup_task = None

            # Clear the AEC cache.
            if hasattr(self, "aec_audio_cache"):
                self.aec_audio_cache.clear()
                self.aec_audio_cache_time.clear()

            # Clean up tool-handler resources.
            if hasattr(self, "func_handler") and self.func_handler:
                try:
                    await self.func_handler.cleanup()
                except Exception as cleanup_error:
                    self.logger.bind(tag=TAG).error(
                        f"Error cleaning up tool handler: {cleanup_error}"
                    )

            # Set the stop event.
            if self.stop_event:
                self.stop_event.set()

            # Drain task queues.
            self.clear_queues()

            # Close the WebSocket connection.
            try:
                if ws:
                    # Check the WebSocket state safely and close it.
                    try:
                        if hasattr(ws, "closed") and not ws.closed:
                            await ws.close()
                        elif hasattr(ws, "state") and ws.state.name != "CLOSED":
                            await ws.close()
                        else:
                            # Try closing directly if there is no closed attribute.
                            await ws.close()
                    except Exception:
                        # Ignore errors if closing fails.
                        pass
                elif self.websocket:
                    try:
                        if (
                                hasattr(self.websocket, "closed")
                                and not self.websocket.closed
                        ):
                            await self.websocket.close()
                        elif (
                                hasattr(self.websocket, "state")
                                and self.websocket.state.name != "CLOSED"
                        ):
                            await self.websocket.close()
                        else:
                            # Try closing directly if there is no closed attribute.
                            await self.websocket.close()
                    except Exception:
                        # Ignore errors if closing fails.
                        pass
            except Exception as ws_error:
                self.logger.bind(tag=TAG).error(f"Error closing WebSocket connection: {ws_error}")

            if self.tts:
                await self.tts.close()
            if self.asr:
                await self.asr.close()

            # Finally close the thread pool without blocking.
            if self.executor:
                try:
                    self.executor.shutdown(wait=False)
                except Exception as executor_error:
                    self.logger.bind(tag=TAG).error(
                        f"Error closing thread pool: {executor_error}"
                    )
                self.executor = None
            self.logger.bind(tag=TAG).info("Connection resources released")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error closing connection: {e}")
        finally:
            # Ensure the stop event is set.
            if self.stop_event:
                self.stop_event.set()

    def clear_queues(self):
        """Drain all task queues."""
        if self.tts:
            self.logger.bind(tag=TAG).debug(
                f"Cleanup started: TTS queue size={self.tts.tts_text_queue.qsize()}, audio queue size={self.tts.tts_audio_queue.qsize()}"
            )

            # Drain queues without blocking.
            for q in [
                self.tts.tts_text_queue,
                self.tts.tts_audio_queue,
                self.report_queue,
            ]:
                if not q:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

            # Reset the audio pacing controller (cancel the background task and drain the queue).
            if hasattr(self, "audio_rate_controller") and self.audio_rate_controller:
                self.audio_rate_controller.reset()
                self.logger.bind(tag=TAG).debug("Audio pacing controller reset")

            self.logger.bind(tag=TAG).debug(
                f"Cleanup completed: TTS queue size={self.tts.tts_text_queue.qsize()}, audio queue size={self.tts.tts_audio_queue.qsize()}"
            )

    def reset_audio_states(self):
        """
        Reset all audio-related state (VAD + ASR).
        """
        # Reset VAD states
        self.client_audio_buffer.clear()
        self.client_have_voice = False
        self.client_voice_stop = False
        self.client_voice_window.clear()
        self.last_is_voice = False
        self.vad_last_voice_time = 0.0

        # Clear ASR buffers
        self.asr_audio.clear()

        self.logger.bind(tag=TAG).debug("All audio states reset.")

    def chat_and_close(self, text):
        """Chat with the user and then close the connection"""
        try:
            # Use the existing chat method
            self.chat(text)

            # After chat is complete, close the connection
            self.close_after_chat = True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Chat and close error: {str(e)}")

    async def _check_timeout(self):
        """Check for connection timeout."""
        try:
            while not self.stop_event.is_set():
                last_activity_time = self.last_activity_time
                if self.need_bind:
                    last_activity_time = self.first_activity_time

                # Check for timeout only after the timestamp is initialized.
                if last_activity_time > 0.0:
                    current_time = time.time() * 1000
                    if current_time - last_activity_time > self.timeout_seconds * 1000:
                        if not self.stop_event.is_set():
                            self.logger.bind(tag=TAG).info("Connection timed out; preparing to close")
                            # Set the stop event to prevent duplicate processing.
                            self.stop_event.set()
                            # Wrap closing in try-except so an exception cannot stall processing.
                            try:
                                await self.close(self.websocket)
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).error(
                                    f"Error closing a timed-out connection: {close_error}"
                                )
                        break
                # Check every ten seconds to avoid excessive polling.
                await asyncio.sleep(10)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Timeout-check task error: {e}")
        finally:
            self.logger.bind(tag=TAG).info("Timeout-check task exited")

    async def _check_aec_cache_expiry(self):
        """Periodically remove expired AEC cache entries."""
        try:
            while not self.stop_event.is_set():
                if hasattr(self, "aec_audio_cache") and self.aec_audio_cache:
                    current_time = time.time()
                    expired_keys = [
                        ts for ts, cache_time in list(self.aec_audio_cache_time.items())
                        if current_time - cache_time > 120  # Expire after two minutes.
                    ]
                    for ts in expired_keys:
                        self.aec_audio_cache.pop(ts, None)
                        self.aec_audio_cache_time.pop(ts, None)
                    if expired_keys:
                        self.logger.bind(tag=TAG).debug(f"[AEC] Expired cache entries removed: {len(expired_keys)} entries")
                # Check every 30 seconds.
                await asyncio.sleep(30)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"AEC cache-cleanup task error: {e}")

    @staticmethod
    def _extract_direct_answer_response(arguments_str):
        """Extract response from direct_answer arguments.
        Prefer standard json.loads parsing; fall back to string extraction while streaming.
        """
        if not arguments_str:
            return ""
        # First try standard JSON parsing for complete, well-formed JSON.
        try:
            data = json.loads(arguments_str)
            if isinstance(data, dict) and "response" in data:
                return data["response"]
        except (json.JSONDecodeError, TypeError):
            pass
        # Fallback: streaming JSON may be incomplete, so extract from the string.
        marker = '"response": "'
        idx = arguments_str.find(marker)
        if idx < 0:
            marker = '"response":"'
            idx = arguments_str.find(marker)
        if idx < 0:
            return ""
        start = idx + len(marker)
        raw = arguments_str[start:]
        # Remove trailing JSON closing characters if already complete.
        if raw.endswith('"}'):
            raw = raw[:-2]
        elif raw.endswith('"'):
            raw = raw[:-1]
        # Handle JSON escaping.
        raw = raw.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
        return raw

    @staticmethod
    def _clean_response_garbage(text):
        """Remove JSON closing characters that may have leaked into response.
        The model sometimes emits JSON closing fragments inside response, such as )"}} or '}),
        which are not part of the story and must be removed.
        """
        if not text:
            return text
        # Remove standalone lines of stray JSON closing characters.
        _garbage_chars = frozenset('")\'}）')
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            stripped = line.strip()
            if stripped and len(stripped) <= 8 and all(c in _garbage_chars for c in stripped):
                continue
            cleaned.append(line)
        result = '\n'.join(cleaned)
        # Remove leftover trailing JSON closing characters.
        result = re.sub(r'["\'}\]]+$', '', result.rstrip()).rstrip()
        return result

    def _merge_tool_calls(self, tool_calls_list, tools_call):
        """Merge tool-call lists.

        Args:
            tool_calls_list: Tool calls already collected.
            tools_call: New tool call.
        """
        for tool_call in tools_call:
            tool_index = getattr(tool_call, "index", None)
            if tool_index is None:
                if tool_call.function.name:
                    # A function_name indicates a new tool call.
                    tool_index = len(tool_calls_list)
                else:
                    tool_index = len(tool_calls_list) - 1 if tool_calls_list else 0

            # Ensure the list has enough entries.
            if tool_index >= len(tool_calls_list):
                tool_calls_list.append({"id": "", "name": "", "arguments": ""})

            # Update tool-call information.
            if tool_call.id:
                tool_calls_list[tool_index]["id"] = tool_call.id
            if tool_call.function.name:
                tool_calls_list[tool_index]["name"] = tool_call.function.name
            if tool_call.function.arguments:
                tool_calls_list[tool_index]["arguments"] += tool_call.function.arguments

#!/usr/bin/env python3
"""Bounded real voice-protocol acceptance; run with the owned Python image.

    python tools/service-voice-smoke.py \
      --source-root main/xiaozhi-server \
      --vad-model models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx

Use Docker --network none, no deployment mounts, and only public Python source
plus the reviewed model. This script copies config/core/plugins_func *.py into
a fresh temporary tree, generates its own YAML, and starts the unchanged
WebSocketServer in a child process. It never reads config.yaml, .env or data
from the source tree. No pytest conftest, provider patches, model downloads,
startup fake-provider flags or external inference services are involved.

The HTTP protocol fakes are explicitly test-only: multipart ASR -> fixed text,
OpenAI chat SSE -> fixed response, TTS -> locally synthesized WAVE bytes. This
proves framing/integration, not recognition/synthesis quality, automatic VAD
segmentation, deployment behavior, or independent egress enforcement. Manual
listen mode is intentional; the real Silero ONNX model is still loaded.
Only fixed event labels and counters are reported; payloads and exceptions
are never printed. Runtime configuration/audio/log paths are temporary.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import collections
import contextlib
import copy
import email.parser
import email.policy
import hashlib
import hmac
import io
import json
import logging
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace


MODEL_SHA256 = "2623a2953f6ff3d2c1e61740c6cdb7168133479b267dfef114a4a3cc5bdd788f"
ASR_TEXT = "Synthetic voice smoke turn"
REPLY = "Synthetic response complete."
# The retained TTS queue strips edge punctuation before synthesis/subtitles.
SPOKEN_REPLY = "Synthetic response complete"
FRAME_COUNT = 20
FRAME_SAMPLES = 960  # 60 ms, 16 kHz mono signed PCM16, as decoded by the server.
MAX_BODY = 1024 * 1024


class SmokeFailure(Exception):
    """Only fixed harness event labels may be passed as messages."""


def require(condition, event):
    if not condition:
        raise SmokeFailure(event)


def pcm_fixture(rate, count):
    return b"".join(struct.pack("<h", round(6000 * math.sin(2 * math.pi * 440 * i / rate)))
                    for i in range(count))


def wave_fixture():
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(pcm_fixture(24000, 8640))
    return output.getvalue()


class ProtocolFakes(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, address=("127.0.0.1", 0), *, allow_titles=False):
        super().__init__(address, FakeHandler)
        self.counts = collections.Counter()
        self.lock = threading.Lock()
        self.wav = wave_fixture()
        self.allow_titles = allow_titles

    def count(self, event, amount=1):
        with self.lock:
            self.counts[event] += amount

    def snapshot(self):
        with self.lock:
            return dict(self.counts)

    def handle_error(self, request, client_address):
        self.count("http_handler_error")


class FakeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass  # Never log HTTP paths, headers, credentials, questions or audio.

    def setup(self):
        super().setup()
        self.connection.settimeout(4)

    def reply(self, body, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()
        self.close_connection = True

    def do_GET(self):
        self.server.count("unexpected_http")
        self.send_error(404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            require(0 < length <= MAX_BODY, "invalid_body_size")
            body = self.rfile.read(length)
            require(len(body) == length, "incomplete_body")
            require(self.headers.get("Authorization") == "Bearer local-only", "invalid_synthetic_auth")
            if self.path == "/v1/audio/transcriptions":
                self.asr(body)
            elif self.path == "/v1/chat/completions":
                self.llm(body)
            elif self.path == "/v1/audio/speech":
                self.tts(body)
            else:
                raise SmokeFailure("unexpected_http")
        except Exception as error:
            self.server.count("invalid_http_contract")
            if isinstance(error, SmokeFailure):
                self.server.count(str(error))
            self.close_connection = True
            with contextlib.suppress(Exception):
                self.send_error(400)

    def asr(self, body):
        content_type = self.headers.get("Content-Type", "")
        require(content_type.startswith("multipart/form-data;"), "asr_not_multipart")
        message = email.parser.BytesParser(policy=email.policy.default).parsebytes(
            b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body)
        parts = {part.get_param("name", header="content-disposition"): part.get_payload(decode=True)
                 for part in message.iter_parts()}
        require(parts.get("model") == b"smoke-asr", "asr_model")
        with wave.open(io.BytesIO(parts.get("file", b"")), "rb") as wav:
            require((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 16000), "asr_wave_format")
            samples = wav.getnframes()
            self.server.count("asr_received_pcm_samples", samples)
            require(samples == FRAME_COUNT * FRAME_SAMPLES, "asr_audio_frame_loss")
            pcm = wav.readframes(samples)
            require(any(pcm), "asr_silent_audio")
        self.server.count("asr_requests")
        self.server.count("asr_pcm_samples", samples)
        self.reply(json.dumps({"text": ASR_TEXT}).encode(), "application/json")

    def llm(self, body):
        request = json.loads(body)
        if request.get("stream") is not True and self.server.allow_titles:
            # Candidate-only title/memory requests are separate from voice SSE.
            messages = request.get("messages", [])
            require(request.get("model") == "smoke-llm" and len(messages) == 1
                    and messages[0].get("role") == "user", "llm_title_contract")
            prompt = messages[0].get("content", "")
            require(isinstance(prompt, str) and not request.get("tools"), "llm_auxiliary_prompt_contract")
            if prompt.startswith("Generate a concise Chinese session title"):
                require(ASR_TEXT in prompt or "Synthetic API smoke history" in prompt, "llm_title_prompt_contract")
                self.server.count("llm_title_requests")
                text = "Synthetic title"
            elif prompt.startswith("You are an experienced memory summarizer."):
                require("Synthetic API smoke history" in prompt and "Historical memory:" in prompt,
                        "llm_summary_prompt_contract")
                self.server.count("llm_summary_requests")
                text = "Synthetic memory summary"
            else:
                raise SmokeFailure("llm_auxiliary_prompt_contract")
            self.reply(json.dumps({"id": "smoke-title", "object": "chat.completion", "model": "smoke-llm",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                             "finish_reason": "stop"}]}).encode(), "application/json")
            return
        if request.get("model") != "smoke-llm":
            self.server.count("llm_unexpected_model")
        if request.get("stream") is not True:
            self.server.count("llm_non_stream_request")
        if request.get("model") != "smoke-llm" or request.get("stream") is not True:
            agent = self.headers.get("User-Agent", "")
            origin = "java" if agent.startswith("Java") else "python" if "Python" in agent else "other"
            self.server.count("llm_rejected_client_" + origin)
        require(request.get("model") == "smoke-llm" and request.get("stream") is True, "llm_stream_contract")
        users = [item.get("content") for item in request.get("messages", []) if item.get("role") == "user"]
        require(users == [ASR_TEXT], "llm_transcript_contract")
        require(not request.get("tools"), "unexpected_llm_tools")
        chunks = []
        deltas = [{"role": "assistant", "content": ""}, {"content": "Synthetic response "},
                  {"content": "complete."}, {}]
        for index, delta in enumerate(deltas):
            event = {"id": "smoke", "object": "chat.completion.chunk", "created": 0,
                     "model": "smoke-llm", "choices": [{"index": 0, "delta": delta,
                     "finish_reason": "stop" if index == len(deltas) - 1 else None}]}
            chunks.append(("data: " + json.dumps(event) + "\n\n").encode())
        chunks.append(b"data: [DONE]\n\n")
        self.server.count("llm_requests")
        self.server.count("llm_sse_events", len(chunks))
        self.reply(b"".join(chunks), "text/event-stream")

    def tts(self, body):
        request = json.loads(body)
        require(request.get("model") == "smoke-tts" and request.get("voice") == "alloy", "tts_model_contract")
        require(request.get("response_format") == "wav" and request.get("input", "").strip() == SPOKEN_REPLY,
                "tts_text_contract")
        self.server.count("tts_requests")
        self.server.count("tts_wave_bytes", len(self.server.wav))
        self.reply(self.server.wav, "audio/wav")


def generated_config(http_port, ws_port, model):
    base = f"http://127.0.0.1:{http_port}/v1"
    return {
        "server": {"ip": "127.0.0.1", "port": ws_port, "auth_key": "synthetic-smoke-only",
                   "auth": {"enabled": False}},
        "log": {"log_level": "CRITICAL", "log_format": "{level}", "log_format_file": "{level}",
                "log_dir": "tmp", "log_file": os.devnull, "data_dir": "data"},
        "selected_module": {"VAD": "SileroVAD", "ASR": "OpenAIASR", "LLM": "OpenAILLM",
                            "TTS": "OpenAITTS", "Memory": "nomem", "Intent": "nointent"},
        "VAD": {"SileroVAD": {"type": "silero", "model_path": str(model)}},
        "ASR": {"OpenAIASR": {"type": "openai", "base_url": base + "/audio/transcriptions",
                               "model_name": "smoke-asr", "output_dir": "tmp/asr"}},
        "LLM": {"OpenAILLM": {"type": "openai", "base_url": base, "model_name": "smoke-llm", "timeout": 4}},
        "TTS": {"OpenAITTS": {"type": "openai", "api_url": base + "/audio/speech",
                               "model": "smoke-tts", "voice": "alloy", "format": "wav", "output_dir": "tmp/tts"}},
        "Memory": {"nomem": {"type": "nomem"}}, "Intent": {"nointent": {"type": "nointent"}},
        "xiaozhi": {"type": "hello", "version": 1, "transport": "websocket",
                    "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}},
        "prompt": "Reply with one short synthetic sentence.", "prompt_template": "smoke-prompt.txt",
        "exit_commands": [], "wakeup_words": [], "delete_audio": True, "read_config_from_api": False,
        "enable_wakeup_words_response_cache": False, "enable_greeting": False,
        "enable_stop_tts_notify": False, "enable_websocket_ping": True,
        "end_prompt": {"enable": False}, "tts_timeout": 4, "close_connection_no_voice_time": 120,
        "mcp_endpoint": "", "context_providers": [], "plugins": {}, "voiceprint": {},
    }


def clean_environment(home):
    # Do not inherit API keys, proxy settings, Python hooks, .env or user config.
    return {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(home),
            "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
            "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}


def copy_source(source, destination):
    for directory in ("config", "core", "plugins_func"):
        files = sorted((source / directory).rglob("*.py"))
        require(bool(files), "source_directory_missing")
        for file in files:
            require(not file.is_symlink(), "source_symlink_rejected")
            relative = file.relative_to(source)
            require(not any(part in {"data", ".env", "__pycache__"} for part in relative.parts), "source_path_rejected")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)


def read_status(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def worker(status_file):
    """Load real generated config and unmodified providers in an isolated cwd."""
    sys.path.insert(0, os.getcwd())
    state = collections.Counter()
    lock = threading.RLock()

    def event(name, amount=1):
        with lock:
            state[name] += amount
            pending = status_file.with_suffix(".pending")
            pending.write_text(json.dumps(dict(state)))
            pending.replace(status_file)

    try:
        event("load_config_started")
        from config.config_loader import load_config
        config = asyncio.run(load_config())
        # Initialize logging outside an event loop, as the actual entry point does.
        from config.logger import setup_logging
        logger = setup_logging(config)
        logger.remove()
        logging.disable(logging.CRITICAL)

        def observe_init(message):
            # Observe only known lifecycle labels, never retain message content.
            value = message.record["message"]
            if value == "Enhanced system prompt updated":
                event("connection_ready")
            elif value.startswith("Failed to instantiate components:"):
                event("component_initialization_failed")

        logger.add(observe_init, level="DEBUG", format="{message}", diagnose=False, backtrace=False)
        event("import_server_started")
        from core.websocket_server import WebSocketServer
        from config.provider_profile import ProviderProfileError, validate_config
        from config.service_policy import ServicePolicyError, validate_endpoint
        from core.providers.tools.unified_tool_manager import ToolManager
        from plugins_func.unavailable import REMOVED_TOOLS

        async def run():
            # Side-effect-free rejection paths, distinct from the positive voice path.
            for capability in ("asr", "llm", "tts", "context", "tool", "mcp", "memory", "voiceprint"):
                try:
                    validate_endpoint("https://unreviewed.invalid/fixture", capability)
                except ServicePolicyError:
                    event("unapproved_endpoint_rejected")
                else:
                    raise SmokeFailure("unapproved_endpoint_accepted")
            removed = copy.deepcopy(config)
            removed["ASR"]["OpenAIASR"]["type"] = "fun_local"
            try:
                validate_config(removed, require_ready=True)
            except ProviderProfileError:
                event("removed_provider_rejected")
            else:
                raise SmokeFailure("removed_provider_accepted")
            manager = ToolManager(SimpleNamespace())
            for name in sorted(REMOVED_TOOLS):
                require(not manager.has_tool(name), "stale_tool_advertised")
                result = await manager.execute_tool(name, {"query": "synthetic"})
                require(result.result == "service_unavailable", "stale_tool_executed")
                event("stale_tool_rejected")
            event("construct_server_started")
            server = WebSocketServer(config)
            event("real_server_initialized")
            await server.start()

        asyncio.run(run())
    except Exception as error:
        event("worker_failed")
        if isinstance(error, SmokeFailure):
            event(str(error))
        # Class only: never expose exception text/tracebacks or captured payloads.
        if isinstance(error, ImportError):
            event("import_failed")
            missing = getattr(error, "name", None)
            if isinstance(missing, str) and all(c.isalnum() or c in "._" for c in missing):
                event("missing_import_" + missing)
        return 1
    return 0


async def voice_turn(port, process, status_file, counts, device_id="synthetic-smoke-device"):
    import opuslib_next
    import websockets

    websocket = None
    headers = {"Device-Id": device_id, "Client-Id": "synthetic-smoke-client"}
    if status_file is None:
        # Only the explicitly synthetic managed candidate uses this known key.
        # No deployment configuration, real key or authentication bypass is read.
        timestamp = int(time.time())
        signed = f"synthetic-smoke-client|{device_id}|{timestamp}".encode()
        signature = base64.urlsafe_b64encode(hmac.new(b"a" * 64, signed, hashlib.sha256).digest()).decode().rstrip("=")
        headers["Authorization"] = f"Bearer {signature}.{timestamp}"
    while websocket is None:
        require(process is None or process.poll() is None, "worker_exited_before_connect")
        try:
            websocket = await websockets.connect(
                f"ws://127.0.0.1:{port}/xiaozhi/v1/",
                additional_headers=headers,
                open_timeout=1, close_timeout=1, ping_interval=None, max_size=MAX_BODY)
        except (OSError, TimeoutError):
            await asyncio.sleep(0.05)
    try:
        await websocket.send(json.dumps({"type": "hello", "version": 1, "transport": "websocket",
            "features": {"mcp": False, "aec": False, "emoji": False},
            "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}}))
        hello = json.loads(await websocket.recv())
        require(hello.get("type") == "hello" and bool(hello.get("session_id")), "invalid_hello")
        require(hello.get("audio_params") == {"format": "opus", "sample_rate": 16000,
                "channels": 1, "frame_duration": 60}, "hello_audio_format")
        session = hello["session_id"]
        counts["hello"] += 1
        # A remote candidate has no harness-internal status channel. A short
        # settling period is only client pacing; all audio/response assertions
        # below still have to pass through the real managed server.
        if status_file is None:
            await asyncio.sleep(1)
        while status_file is not None and not read_status(status_file).get("connection_ready"):
            status = read_status(status_file)
            require(not status.get("component_initialization_failed"), "component_initialization_failed")
            require(process.poll() is None, "worker_exited_during_init")
            await asyncio.sleep(0.025)
        await websocket.send(json.dumps({"type": "listen", "state": "start", "mode": "manual"}))
        counts["listen_start"] += 1
        encoder = opuslib_next.Encoder(16000, 1, opuslib_next.APPLICATION_AUDIO)
        decoder = opuslib_next.Decoder(16000, 1)
        pcm = pcm_fixture(16000, FRAME_COUNT * FRAME_SAMPLES)
        for index in range(FRAME_COUNT):
            frame = pcm[index * FRAME_SAMPLES * 2:(index + 1) * FRAME_SAMPLES * 2]
            await websocket.send(encoder.encode(frame, FRAME_SAMPLES))
            counts["incoming_opus_packets"] += 1
            # Actual 60 ms capture cadence gives the real ASR queue time to drain.
            await asyncio.sleep(0.06)
        # Protocol round-trip barrier plus one scheduling turn before listen stop.
        await websocket.send(json.dumps({"type": "ping"}))
        pong = json.loads(await websocket.recv())
        require(pong.get("type") == "pong", "audio_barrier_failed")
        await asyncio.sleep(0.1)
        await websocket.send(json.dumps({"type": "listen", "state": "stop"}))
        counts["listen_stop"] += 1
        phase = "stt"
        text = []
        while True:
            message = await websocket.recv()
            if isinstance(message, bytes):
                require(phase == "audio", "audio_before_tts_text")
                decoded = decoder.decode(message, FRAME_SAMPLES)
                require(len(decoded) == FRAME_SAMPLES * 2, "invalid_outgoing_opus")
                counts["outgoing_opus_packets"] += 1
                counts["outgoing_pcm_samples"] += len(decoded) // 2
                if any(decoded):
                    counts["nonzero_audio_packets"] += 1
                continue
            event = json.loads(message)
            kind = event.get("type")
            require(event.get("session_id") == session, "session_mismatch")
            if kind == "stt":
                require(phase == "stt" and event.get("text") == ASR_TEXT, "stt_text_mismatch")
                counts["stt"] += 1
                phase = "start"
            elif kind == "tts":
                state = event.get("state")
                if state == "start":
                    require(phase == "start", "tts_start_order")
                    counts["tts_start"] += 1
                    phase = "sentence"
                elif state == "sentence_start":
                    require(phase in {"sentence", "audio"}, "tts_text_order")
                    text.append(event.get("text", ""))
                    counts["tts_text"] += 1
                    phase = "audio"
                elif state == "stop":
                    require(phase == "audio" and counts["outgoing_opus_packets"] > 0, "tts_stop_order")
                    require("".join(text).strip() == SPOKEN_REPLY, "tts_display_text_mismatch")
                    require(counts["nonzero_audio_packets"] > 0, "outgoing_silent_audio")
                    counts["tts_stop"] += 1
                    break
                else:
                    raise SmokeFailure("unexpected_tts_state")
            elif kind == "llm":
                counts["llm_status"] += 1
            else:
                raise SmokeFailure("unexpected_ws_event")
    finally:
        await websocket.close()


def run(args):
    import yaml

    source = args.source_root.resolve()
    model = (source / args.vad_model).resolve()
    require(model.is_file(), "reviewed_model_missing")
    require(hashlib.sha256(model.read_bytes()).hexdigest() == MODEL_SHA256, "reviewed_model_hash_mismatch")
    counts = collections.Counter()
    summary = {"events": counts, "http": {}, "worker": {}, "egress_proof": False}
    process = None
    with tempfile.TemporaryDirectory(prefix="xiaozhi-voice-smoke-") as temporary:
        root = Path(temporary)
        status_file = root / "status.json"
        destination = root / "server"
        destination.mkdir()
        copy_source(source, destination)
        reviewed_model = destination / "reviewed-silero.onnx"
        shutil.copyfile(model, reviewed_model)
        (destination / "data").mkdir()
        (destination / "data/.config.yaml").write_text("{}\n")
        (destination / "smoke-prompt.txt").write_text("{{ base_prompt }}\n")
        with ProtocolFakes() as http:
            http_thread = threading.Thread(target=http.serve_forever, daemon=True)
            http_thread.start()
            # Acquire an ephemeral loopback port; a subsequent bind failure is fatal.
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                ws_port = listener.getsockname()[1]
            config = generated_config(http.server_port, ws_port, reviewed_model)
            (destination / "config.yaml").write_text(yaml.safe_dump(config, allow_unicode=True))
            try:
                process = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", str(status_file)],
                    cwd=destination, env=clean_environment(root), stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, start_new_session=True)
                asyncio.run(asyncio.wait_for(voice_turn(ws_port, process, status_file, counts), args.timeout))
                snapshot = http.snapshot()
                for key in ("asr_requests", "llm_requests", "tts_requests"):
                    require(snapshot.get(key) == 1, "http_request_count_mismatch")
                require(not any(snapshot.get(key) for key in ("invalid_http_contract", "http_handler_error", "unexpected_http")),
                        "http_contract_failed")
                counts["voice_turn_complete"] += 1
            except Exception as error:
                summary["failure"] = str(error) if isinstance(error, SmokeFailure) else "bounded_runtime_failure"
            finally:
                if process is not None:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        with contextlib.suppress(ProcessLookupError):
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=2)
                summary["worker"] = read_status(status_file)
                summary["http"] = http.snapshot()
                http.shutdown()
                http_thread.join(timeout=2)
    summary["result"] = "fail" if "failure" in summary else "pass"
    print(json.dumps(summary, sort_keys=True))
    return int(summary["result"] != "pass")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1] / "main/xiaozhi-server")
    parser.add_argument("--vad-model", type=Path)
    parser.add_argument("--timeout", type=int, choices=range(10, 121), default=45, metavar="10..120")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--serve-fakes", action="store_true", help="Test-only loopback protocol fakes on port 19200")
    parser.add_argument("--candidate-port", type=int, help="Test a candidate on literal loopback (18000 or 8000 only)")
    parser.add_argument("--device-id", help="Synthetic candidate device MAC; no real device identities")
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    if args.serve_fakes:
        server = ProtocolFakes(("127.0.0.1", 19200), allow_titles=True)
        stopped = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stopped.set())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(json.dumps({"fixture": "local-protocol-fakes", "port": 19200, "ready": True}), flush=True)
        try:
            stopped.wait()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            print(json.dumps({"fixture": "local-protocol-fakes", "counts": server.snapshot()}), flush=True)
        return 0
    if args.candidate_port is not None:
        import re
        if args.candidate_port not in {8000, 18000} or not args.device_id or not re.fullmatch(r"02:00:00:00:00:0[12]", args.device_id):
            parser.error("Candidate port/device must be the explicitly supported synthetic fixture")
        counts = collections.Counter()
        try:
            asyncio.run(asyncio.wait_for(voice_turn(args.candidate_port, None, None, counts, args.device_id), args.timeout))
            print(json.dumps({"result": "pass", "scope": "managed-candidate-websocket", "counts": dict(counts), "egress_proof": False}))
            return 0
        except Exception as error:
            print(json.dumps({"result": "fail", "failure": str(error) if isinstance(error, SmokeFailure) else "candidate_turn_failed",
                              "counts": dict(counts), "egress_proof": False}))
            return 1
    if args.vad_model is None:
        parser.error("--vad-model must explicitly name the reviewed local ONNX fixture")
    try:
        return run(args)
    except Exception as error:
        print(json.dumps({"result": "fail", "failure": str(error) if isinstance(error, SmokeFailure)
                          else "harness_setup_failed", "egress_proof": False}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

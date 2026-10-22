import time
import uuid
import asyncio
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

from core.utils.dialogue import Message
from core.providers.asr.dto.dto import InterfaceType
from core.handle.receiveAudioHandle import startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.utils.util import remove_punctuation_and_length
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType


TAG = __name__

class ListenTextMessageHandler(TextMessageHandler):
    """Listen message handler."""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LISTEN

    async def handle(self, conn: "ConnectionHandler", msg_json: Dict[str, Any]) -> None:
        if "mode" in msg_json:
            conn.client_listen_mode = msg_json["mode"]
            conn.logger.bind(tag=TAG).debug(
                f"Client listening mode: {conn.client_listen_mode}"
            )
        if msg_json["state"] == "start":
            # The device switches from playback to recording; clear audio states and buffers.
            conn.reset_audio_states()
        elif msg_json["state"] == "stop":
            # Ignore stop if ASR has not been initialized.
            if conn.asr is None:
                return

            conn.client_voice_stop = True
            if conn.asr.interface_type == InterfaceType.STREAM:
                # Send a stop request in streaming mode.
                asyncio.create_task(conn.asr._send_stop_request())
            else:
                # Non-streaming mode: trigger ASR directly.
                if len(conn.asr_audio) > 0:
                    asr_audio_task = conn.asr_audio.copy()
                    conn.reset_audio_states()

                    if len(asr_audio_task) > 0:
                        await conn.asr.handle_voice_stop(conn, asr_audio_task)
        elif msg_json["state"] == "detect":
            conn.client_have_voice = False
            conn.reset_audio_states()
            if "text" in msg_json:
                conn.last_activity_time = time.time() * 1000
                original_text = msg_json["text"]  # Preserve the original text.
                filtered_len, filtered_text = remove_punctuation_and_length(
                    original_text
                )

                # Check for the [device_call] command.
                if original_text.startswith("[device_call]"):
                    # Extract the text after the tag.
                    call_text = original_text[len("[device_call]"):].strip()
                    conn.logger.bind(tag=TAG).info(f"Received device-call command: {call_text}")

                    # Mark this as incoming-call mode.
                    conn.incoming_call = True

                    # Prepare a new conversation.
                    conn.sentence_id = uuid.uuid4().hex

                    await send_stt_message(conn, call_text)

                    # Wait at most three seconds for TTS initialization.
                    start_time = time.time()
                    while time.time() - start_time < 3:
                        if conn.tts:
                            break
                        await asyncio.sleep(0.1)

                    if conn.tts:
                        conn.tts.store_tts_text(conn.sentence_id, call_text)
                        conn.tts.tts_text_queue.put(TTSMessageDTO(sentence_id=conn.sentence_id, sentence_type=SentenceType.FIRST, content_type=ContentType.ACTION))
                        conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=call_text)
                        conn.tts.tts_text_queue.put(TTSMessageDTO(sentence_id=conn.sentence_id, sentence_type=SentenceType.LAST, content_type=ContentType.ACTION))

                    # Add to conversation history so the model understands the context.
                    conn.dialogue.put(Message(role="assistant", content=call_text))
                    return

                # Check whether this is a wake word.
                is_wakeup_words = filtered_text in conn.config.get("wakeup_words")
                # Check whether wake-word greetings are enabled.
                enable_greeting = conn.config.get("enable_greeting", True)

                if is_wakeup_words and not enable_greeting:
                    # Do not reply to a wake word when greetings are disabled.
                    await send_stt_message(conn, original_text)
                    await send_tts_message(conn, "stop", None)
                    conn.client_is_speaking = False
                elif is_wakeup_words:
                    conn.just_woken_up = True
                    # Report text only using ASR reporting without audio.
                    # Preserve the Chinese greeting as spoken/user-language content.
                    enqueue_asr_report(conn, "嘿，你好呀", [])
                    await startToChat(conn, "嘿，你好呀")
                else:
                    conn.just_woken_up = True
                    # Report text only using ASR reporting without audio.
                    enqueue_asr_report(conn, original_text, [])
                    # Otherwise ask the LLM to respond to the text.
                    await startToChat(conn, original_text)

"""
TTS reporting is integrated into ConnectionHandler.

Reporting features:
1. Each connection owns its reporting queue and worker thread.
2. The reporting thread's lifetime follows the connection.
3. Submit reports using ConnectionHandler.enqueue_tts_report.

See core/connection.py for the implementation.
"""

import time
import json
import opuslib_next
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

from config.manage_api_client import report as manage_report

TAG = __name__


async def report(conn: "ConnectionHandler", chat_type, text, audio_data, report_time):
    """Report chat history.

    Args:
        conn: Connection object.
        chat_type: Report type: 1=user (ASR/PCM), 2=agent (TTS/Opus), 3=tool call.
        text: Synthesized text.
        audio_data: Audio data (PCM for chat_type=1; Opus for chat_type=2).
        report_time: Report timestamp.
    """
    try:
        if audio_data:

            if chat_type == 1:
                wav_data = pcm_to_wav(conn, audio_data)
            elif chat_type == 2:
                wav_data = opus_to_wav(conn, audio_data)
            else:
                wav_data = None
        else:
            wav_data = None
        # Submit the report asynchronously.
        await manage_report(
            mac_address=conn.device_id,
            session_id=conn.session_id,
            chat_type=chat_type,
            content=text,
            audio=wav_data,
            report_time=report_time,
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Chat-history reporting failed: {e}")


def pcm_to_wav(conn: "ConnectionHandler", pcm_data):
    """Convert PCM data to WAV bytes.

    Args:
        conn: Connection object.
        pcm_data: PCM audio data (a list or bytes).

    Returns:
        bytes: Audio data in WAV format.
    """
    try:
        # Handle PCM data supplied as a list or bytes.
        if isinstance(pcm_data, list):
            pcm_data_bytes = b"".join(pcm_data)
        else:
            pcm_data_bytes = pcm_data

        if not pcm_data_bytes:
            raise ValueError("No valid PCM data")

        # Create the WAV header.
        num_samples = len(pcm_data_bytes) // 2  # 16-bit samples

        # WAV header.
        wav_header = bytearray()
        wav_header.extend(b"RIFF")  # ChunkID
        wav_header.extend((36 + len(pcm_data_bytes)).to_bytes(4, "little"))  # ChunkSize
        wav_header.extend(b"WAVE")  # Format
        wav_header.extend(b"fmt ")  # Subchunk1ID
        wav_header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
        wav_header.extend((1).to_bytes(2, "little"))  # AudioFormat (PCM)
        wav_header.extend((1).to_bytes(2, "little"))  # NumChannels
        wav_header.extend((16000).to_bytes(4, "little"))  # SampleRate
        wav_header.extend((32000).to_bytes(4, "little"))  # ByteRate
        wav_header.extend((2).to_bytes(2, "little"))  # BlockAlign
        wav_header.extend((16).to_bytes(2, "little"))  # BitsPerSample
        wav_header.extend(b"data")  # Subchunk2ID
        wav_header.extend(len(pcm_data_bytes).to_bytes(4, "little"))  # Subchunk2Size

        # Return the complete WAV data.
        return bytes(wav_header) + pcm_data_bytes
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"PCM-to-WAV conversion failed: {e}", exc_info=True)
        raise


def opus_to_wav(conn: "ConnectionHandler", opus_data):
    """Convert Opus data to WAV bytes.

    Args:
        conn: Connection object.
        opus_data: Opus audio data (a list or bytes).

    Returns:
        bytes: Audio data in WAV format.
    """
    decoder = None
    try:
        decoder = opuslib_next.Decoder(16000, 1)
        pcm_data = []

        if isinstance(opus_data, list):
            for opus_packet in opus_data:
                try:
                    pcm_frame = decoder.decode(opus_packet, 960)
                    pcm_data.append(pcm_frame)
                except opuslib_next.OpusError as e:
                    conn.logger.bind(tag=TAG).error(f"Opus decoding error: {e}", exc_info=True)
        elif isinstance(opus_data, bytes):
            pcm_frame = decoder.decode(opus_data, 960)
            pcm_data.append(pcm_frame)

        if not pcm_data:
            raise ValueError("No valid audio data")

        pcm_data_bytes = b"".join(pcm_data)

        wav_header = bytearray()
        wav_header.extend(b"RIFF")
        wav_header.extend((36 + len(pcm_data_bytes)).to_bytes(4, "little"))
        wav_header.extend(b"WAVE")
        wav_header.extend(b"fmt ")
        wav_header.extend((16).to_bytes(4, "little"))
        wav_header.extend((1).to_bytes(2, "little"))
        wav_header.extend((1).to_bytes(2, "little"))
        wav_header.extend((16000).to_bytes(4, "little"))
        wav_header.extend((32000).to_bytes(4, "little"))
        wav_header.extend((2).to_bytes(2, "little"))
        wav_header.extend((16).to_bytes(2, "little"))
        wav_header.extend(b"data")
        wav_header.extend(len(pcm_data_bytes).to_bytes(4, "little"))

        return bytes(wav_header) + pcm_data_bytes
    finally:
        if decoder is not None:
            try:
                del decoder
            except Exception as e:
                conn.logger.bind(tag=TAG).debug(f"Error releasing decoder resources: {e}")


def enqueue_tts_report(conn: "ConnectionHandler", text, opus_data):
    """Enqueue TTS data for reporting.

    Args:
        conn: Connection object.
        text: Synthesized text.
        opus_data: Opus audio data.
    """
    if not conn.read_config_from_api or conn.need_bind or not conn.report_tts_enable:
        return
    if conn.chat_history_conf == 0:
        return
    try:
        # Use the connection's queue, passing text and binary data rather than file paths.
        if conn.chat_history_conf == 2:
            conn.report_queue.put((2, text, opus_data, int(time.time() * 1000)))
            conn.logger.bind(tag=TAG).debug(
                f"TTS data queued for reporting: {conn.device_id}, audio size: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((2, text, None, int(time.time() * 1000)))
            conn.logger.bind(tag=TAG).debug(
                f"TTS data queued for reporting: {conn.device_id}, audio not included"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Failed to enqueue TTS report: {text}, {e}")


def enqueue_tool_report(conn: "ConnectionHandler", tool_name: str, tool_input: dict, tool_result: str = None, report_tool_call: bool = True):
    """Enqueue tool-call data for reporting.

    Args:
        conn: Connection object.
        tool_name: Tool name.
        tool_input: Tool input arguments.
        tool_result: Optional tool execution result.
        report_tool_call: Whether to report the call itself (default: True); use False to report only results.
    """
    if not conn.read_config_from_api or conn.need_bind:
        return
    if conn.chat_history_conf == 0:
        return

    try:
        timestamp = int(time.time() * 1000)

        # Build the tool-call content.
        if report_tool_call:
            tool_text = json.dumps(
                [
                    {
                        "type": "tool",
                        "text": f"{tool_name}({json.dumps(tool_input, ensure_ascii=False)})",
                    }
                ]
            )
            conn.report_queue.put((3, tool_text, None, timestamp))

        # Build the tool-result content.
        if tool_result:
            result_display = f'{{"result":"{str(tool_result)}"}}'
            result_content = json.dumps([{"type": "tool_result", "text": result_display}], ensure_ascii=False)
            conn.report_queue.put((3, result_content, None, timestamp + 1))
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Failed to enqueue tool report: {e}")


def enqueue_asr_report(conn: "ConnectionHandler", text, opus_data):
    """Enqueue ASR data for reporting.

    Args:
        conn: Connection object.
        text: Synthesized text.
        opus_data: Opus audio data.
    """
    if not conn.read_config_from_api or conn.need_bind or not conn.report_asr_enable:
        return
    if conn.chat_history_conf == 0:
        return
    try:
        # Use the connection's queue, passing text and binary data rather than file paths.
        if conn.chat_history_conf == 2:
            conn.report_queue.put((1, text, opus_data, int(time.time() * 1000)))
            conn.logger.bind(tag=TAG).debug(
                f"ASR data queued for reporting: {conn.device_id}, audio size: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((1, text, None, int(time.time() * 1000)))
            conn.logger.bind(tag=TAG).debug(
                f"ASR data queued for reporting: {conn.device_id}, audio not included"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).debug(f"Failed to enqueue ASR report: {text}, {e}")

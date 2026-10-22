import time
import json
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.utils.util import audio_to_data
from core.handle.abortHandle import handleAbortMessage
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.sendAudioHandle import send_stt_message, SentenceType
from core.providers.vad.device import DeviceAudioFrame, DeviceVadLimitError

TAG = __name__


async def handleAudioMessage(conn: "ConnectionHandler", pcm_frame):
    if isinstance(pcm_frame, DeviceAudioFrame):
        if (not conn.vad.is_listening(conn)
                or pcm_frame.turn_id != getattr(conn, "_device_vad_turn_id", None)):
            return  # An aborted turn's in-flight worker cannot enter the next turn.
        pcm_frame = pcm_frame.pcm
    # Check whether the current segment contains speech.
    try:
        have_voice = conn.vad.is_vad(conn, pcm_frame)
    except DeviceVadLimitError:
        conn.reset_audio_states()
        conn.logger.bind(tag=TAG).warning("Device VAD turn limit reached; discarding audio and closing")
        await conn.close()
        return
    if getattr(conn.vad, "device_controlled", False) is True and not have_voice:
        # Never buffer/transcribe late packets or unsolicited microphone audio.
        return
    # Briefly ignore VAD when the device has just woken up.
    if hasattr(conn, "just_woken_up") and conn.just_woken_up:
        have_voice = False
        # Restore VAD after a brief delay.
        if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
            conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
        return
    # Server-side AEC requires real-time interruption.
    if conn.client_aec and have_voice:
        if conn.client_is_speaking and conn.client_listen_mode != "manual":
            await handleAbortMessage(conn)
    # Detect prolonged device inactivity to trigger the goodbye message.
    await no_voice_close_connect(conn, have_voice)
    # Receive audio.
    await conn.asr.receive_audio(conn, pcm_frame, have_voice)


async def resume_vad_detection(conn: "ConnectionHandler"):
    # Restore VAD after two seconds.
    await asyncio.sleep(2)
    conn.just_woken_up = False


async def startToChat(conn: "ConnectionHandler", text):
    # Check for JSON input containing speaker information.
    speaker_name = None
    actual_text = text

    try:
        # Try parsing the input as JSON.
        if text.strip().startswith("{") and text.strip().endswith("}"):
            data = json.loads(text)
            if "speaker" in data and "content" in data:
                speaker_name = data["speaker"]
                actual_content = data["content"]
                conn.logger.bind(tag=TAG).info(f"Parsed speaker information: {speaker_name}")

                # Retain {"speaker":...} JSON only on the speaker's first appearance so the model addresses them once.
                # Use plain text on later turns to avoid encouraging repeated forms of address.
                if speaker_name not in conn.introduced_speakers:
                    conn.introduced_speakers.add(speaker_name)
                    actual_text = text
                else:
                    actual_text = actual_content
            elif "content" in data:
                # FunASR and similar providers return {"content","language","emotion"}; send only recognized content to the LLM,
                # otherwise the entire JSON object enters conversation history.
                actual_text = data["content"]
    except (json.JSONDecodeError, KeyError):
        # Keep using the original text if parsing fails.
        pass

    # Save speaker information on the connection object.
    if speaker_name:
        conn.current_speaker = speaker_name
    else:
        conn.current_speaker = None

    if conn.need_bind:
        await check_bind_device(conn)
        return

    # Check whether today's output character count exceeds the configured limit.
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return

    # Do not interrupt playback in manual mode.
    if conn.client_is_speaking and conn.client_listen_mode != "manual":
        await handleAbortMessage(conn)

    # Analyze intent first, using the actual text content.
    intent_handled = await handle_user_intent(conn, actual_text)

    if intent_handled:
        # Do not continue chatting if the intent has already been handled.
        return

    # If the intent was not handled, continue normal chat using the actual text content.
    await send_stt_message(conn, actual_text)

    # Prepare a new conversation.
    conn.client_abort = False

    conn.executor.submit(conn.chat, actual_text)


async def no_voice_close_connect(conn: "ConnectionHandler", have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # Check timeouts only after the timestamp has been initialized.
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info("Ending conversation without a closing message")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "请你以```时间过得真快```未来头，用富有感情、依依不舍的话来结束这场对话吧。！"
            await startToChat(conn, prompt)


async def max_out_size(conn: "ConnectionHandler"):
    # Play the output-limit notification in its existing user-facing language.
    conn.client_abort = False
    text = "不好意思，我现在有点事情要忙，明天这个时候我们再聊，约好了哦！明天不见不散，拜拜！"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets = await audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn: "ConnectionHandler"):
    if conn.bind_code:
        # Ensure bind_code contains six digits.
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(f"Invalid binding-code format: {conn.bind_code}")
            text = "绑定码格式错误，请检查配置。"
            await send_stt_message(conn, text)
            return

        text = f"请登录控制面板，输入{conn.bind_code}，绑定设备。"
        await send_stt_message(conn, text)

        # Play the notification sound.
        music_path = "config/assets/bind_code.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # Play the digits one by one.
        for i in range(6):  # Play exactly six digits.
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets = await audio_to_data(num_path)
                conn.tts.tts_audio_queue.put((SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Failed to play digit audio: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        # Play the unbound-device notification in its existing user-facing language.
        conn.client_abort = False
        text = f"没有找到该设备的版本信息，请正确配置 OTA地址，然后重新编译固件。"
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets = await audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))

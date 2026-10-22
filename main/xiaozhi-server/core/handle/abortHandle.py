import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
TAG = __name__


async def handleAbortMessage(conn: "ConnectionHandler"):
    conn.logger.bind(tag=TAG).info("Abort message received")
    # Set the abort state to interrupt LLM and TTS tasks automatically.
    conn.close_after_chat = False
    conn.client_abort = True
    conn.clear_queues()
    if getattr(getattr(conn, "vad", None), "device_controlled", False) is True:
        conn.vad.stop_listening(conn)
        conn.reset_audio_states()
    # Interrupt the client's speaking state.
    await conn.websocket.send(
        json.dumps({"type": "tts", "state": "stop", "session_id": conn.session_id})
    )
    conn.clearSpeakStatus()
    conn.logger.bind(tag=TAG).info("Abort message received-end")

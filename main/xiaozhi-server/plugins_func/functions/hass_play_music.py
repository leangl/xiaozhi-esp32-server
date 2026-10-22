import httpx
from config.service_policy import async_httpx_client
from config.logger import setup_logging
from plugins_func.functions.hass_init import initialize_hass_handler
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

hass_play_music_function_desc = {
    "type": "function",
    "function": {
        "name": "hass_play_music",
        "description": "Use when the user wants music or an audiobook; play the audio on the room's media_player",
        "parameters": {
            "type": "object",
            "properties": {
                "media_content_id": {
                    "type": "string",
                    "description": "Music/audiobook album, song title or performer; use random when unspecified",
                },
                "entity_id": {
                    "type": "string",
                    "description": "Speaker's Home Assistant entity_id, starting with media_player",
                },
            },
            "required": ["media_content_id", "entity_id"],
        },
    },
}


@register_function(
    "hass_play_music", hass_play_music_function_desc, ToolType.SYSTEM_CTL
)
async def hass_play_music(conn: "ConnectionHandler", entity_id="", media_content_id="random"):
    # Preserve the Chinese playback acknowledgements and spoken failure reply.
    try:
        result = await handle_hass_play_music(conn, entity_id, media_content_id)
        return ActionResponse(
            action=Action.RECORD, result="指令已接收", response=result
        )
    except Exception as e:
        logger.bind(tag=TAG).error("Home Assistant playback unavailable")
        return ActionResponse(
            action=Action.RESPONSE, result="service_unavailable", response="播放音乐时出错了"
        )


async def handle_hass_play_music(
    conn: "ConnectionHandler", entity_id, media_content_id
):
    # These Chinese result phrases are spoken to the user; retain their formatting.
    ha_config = initialize_hass_handler(conn)
    api_key = ha_config.get("api_key")
    base_url = ha_config.get("base_url")
    url = f"{base_url}/api/services/music_assistant/play_media"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"entity_id": entity_id, "media_id": media_content_id}

    async with async_httpx_client("tool", timeout=httpx.Timeout(10.0, connect=3.0)) as client:
        response = await client.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return f"正在播放{media_content_id}的音乐"
    else:
        return f"音乐播放失败，错误码: {response.status_code}"

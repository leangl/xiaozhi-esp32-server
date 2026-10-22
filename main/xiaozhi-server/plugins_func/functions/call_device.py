"""Device-to-device calling tool."""
import httpx
from config.service_policy import async_httpx_client, validate_endpoint, ServicePolicyError
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

call_device_function_desc = {
    "type": "function",
    "function": {
        "name": "call_device",
        "description": (
            "Establish a voice call between devices. "
            "Call this tool for the following intents:\n"
            "1. Outgoing call: for Chinese requests such as 呼叫XX/打电话给XX/连线XX/打给XX/帮我呼叫XX "
            "(call/connect to XX), set nickname to XX. "
            "Examples: 呼叫张三 -> nickname=张三; 帮我连线小陈 -> nickname=小陈.\n"
            "2. Answering: immediately after the system asks 您收到来自XX的来电，是否接听？ "
            "(incoming call from XX; answer?), accept Chinese replies such as 接听/接通/同意接听/同意连线/同意对话 "
            "(answer/connect/agree), and use XX from that prompt as nickname.\n"
            "If the reply neither clearly accepts nor clearly rejects the call, do not call call_device; ask for clarification once."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nickname": {"type": "string", "description": "Target device's saved alias, for example 小陈 or 小翁 (Chinese personal-name aliases)"},
            },
            "required": ["nickname"],
        },
    },
}


async def _request_api(url: str, params: dict, headers: dict):
    validate_endpoint(url, "tool")
    async with async_httpx_client("tool", timeout=httpx.Timeout(10.0, connect=3.0)) as client:
        return await client.get(url, params=params, headers=headers)


def _failed_reply(msg: str) -> ActionResponse:
    return ActionResponse(action=Action.RESPONSE, response=msg)


def _is_answering(conn: "ConnectionHandler") -> bool:
    """Check answering mode: conn.incoming_call is not None."""
    return hasattr(conn, 'incoming_call') and conn.incoming_call is not None


@register_function("call_device", call_device_function_desc, ToolType.SYSTEM_CTL)
async def call_device(conn: "ConnectionHandler", nickname: str):
    # Keep the Chinese spoken call/error replies and nickname interpolation unchanged.
    caller_mac = conn.headers.get("device-id")
    if not caller_mac:
        return _failed_reply("无法获取本机MAC地址")

    api_config = conn.config.get("manager-api", {})
    api_url = api_config.get("url")
    api_secret = api_config.get("secret")
    if not api_url or not api_secret:
        logger.bind(tag=TAG).error("manager-api configuration is missing")
        return _failed_reply("配置错误，请稍后再试")

    headers = {"Authorization": f"Bearer {api_secret}"}

    # Distinguish outgoing calls from incoming-call answers.
    is_answer = _is_answering(conn)
    params = {"callerMac": caller_mac, "nickname": nickname}
    if is_answer:
        params["answer"] = "true"

    # Look up the address book and initiate the call.
    try:
        resp = await _request_api(
            f"{api_url}/device/address-book/call",
            params=params,
            headers=headers,
        )
        result = resp.json()
    except (httpx.HTTPError, ServicePolicyError):
        logger.bind(tag=TAG).error("Call service unavailable; review manager-api configuration")
        return _failed_reply("呼叫失败，请稍后再试")

    if result.get("code") != 0:
        return _failed_reply(result.get("msg", "呼叫失败"))

    data = result.get("data", {})
    if data.get("status") == "error":
        return _failed_reply(data.get("message"))

    if is_answer:
        return ActionResponse(action=Action.NONE, response="已成功接听")
    else:
        conn.calling = True
        return ActionResponse(action=Action.NONE, response=f"正在呼叫{nickname}，请等待对方接听")

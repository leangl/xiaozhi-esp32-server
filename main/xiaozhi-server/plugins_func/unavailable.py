"""Compatibility outcomes for retired optional integrations; no outbound code."""
from plugins_func.register import Action, ActionResponse

REMOVED_TOOLS = frozenset({
    "get_weather", "get_news", "get_news_from_newsnow", "get_news_from_chinanews", "web_search",
})
UNAVAILABLE_MESSAGE = "This optional tool is unavailable. An approved replacement has not been configured."


def unavailable_tool():
    return ActionResponse(Action.ERROR, result="service_unavailable", response=UNAVAILABLE_MESSAGE)

"""Reviewed outbound origins for retained compatible AI adapters.

This is operator-owned code, not an administrator/API supplied allow-all flag.
An additional cloud or self-hosted origin needs a documented review and tests.
This boundary is not a replacement for deployment-level egress enforcement.
"""
import ipaddress
from urllib.parse import parse_qsl, urlsplit


class ServicePolicyError(ValueError):
    """Safe to display: never includes supplied URLs, keys or payloads."""


# Host ownership/role evidence is recorded in the service-removal progress doc.
# Exact host matching prevents suffix tricks and OpenAI-compatible vendor aliases.
_CLOUD_ROLES = {
    "api.openai.com": frozenset({"asr", "llm", "vllm", "tts"}),
    "generativelanguage.googleapis.com": frozenset({"llm", "vllm"}),
}
_ROLES = frozenset({"asr", "llm", "vllm", "tts", "context", "tool", "mcp", "memory", "voiceprint"})


def validate_endpoint(url, capability):
    """Reject before credentials/data are sent; only loopback may use plain HTTP."""
    if capability not in _ROLES:
        raise ServicePolicyError("Unknown service capability")
    if not isinstance(url, str) or not url or any(ord(c) <= 32 for c in url) or "\\" in url:
        raise ServicePolicyError("An explicit approved service endpoint is required")
    try:
        parsed = urlsplit(url)
        if parsed.username is not None or parsed.password is not None or parsed.fragment:
            raise ValueError()
        if capability in {"asr", "llm", "vllm", "tts"} and any(
            key.lower() in {"api_key", "apikey", "key", "token", "access_token", "secret", "signature"}
            for key, _ in parse_qsl(parsed.query)
        ):
            raise ValueError()
        host = parsed.hostname
        if not host or "%" in host:
            raise ValueError()
        host = host.removesuffix(".").encode("idna").decode("ascii").lower()
        port = parsed.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError()
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host == "localhost"
        scheme = parsed.scheme.lower()
    except (ValueError, UnicodeError):
        raise ServicePolicyError("Invalid service endpoint; credentials must not be in its authority") from None
    if loopback:
        schemes = {"http", "https", "ws", "wss"} if capability == "mcp" else {"http", "https"}
        if scheme in schemes:
            return url
    elif scheme == "https" and port in (None, 443) and capability in _CLOUD_ROLES.get(host, ()):
        return url
    raise ServicePolicyError("Service destination is not approved for this capability; select a reviewed endpoint")


def httpx_client(capability, **kwargs):
    """Validate every SDK request; no environment proxy, netrc or redirect fallback."""
    import httpx

    if kwargs.get("verify") is False or kwargs.get("proxy") is not None:
        raise ServicePolicyError("Service clients require TLS verification and direct reviewed routes")

    def check(request):
        validate_endpoint(str(request.url), capability)

    return httpx.Client(**kwargs, trust_env=False, follow_redirects=False,
                        event_hooks={"request": [check]})


def async_httpx_client(capability, **kwargs):
    """Guard async context/tool calls, including SDK-created secondary requests."""
    import httpx

    if kwargs.get("verify") is False or kwargs.get("proxy") is not None:
        raise ServicePolicyError("Service clients require TLS verification and direct reviewed routes")

    async def check(request):
        validate_endpoint(str(request.url), capability)

    async def check_response(response):
        if 300 <= response.status_code < 400:
            await response.aclose()
            raise ServicePolicyError("Service redirected; configure a reviewed final endpoint explicitly")

    return httpx.AsyncClient(**kwargs, trust_env=False, follow_redirects=False,
                             event_hooks={"request": [check], "response": [check_response]})


def mcp_httpx_client(headers=None, timeout=None, auth=None):
    """MCP SDK factory: override its redirect-enabled default client."""
    return async_httpx_client("mcp", headers=headers, timeout=timeout or 30, auth=auth)


def mcp_websocket(url):
    """WebSockets 14.2 connects directly; forbid its automatic redirects."""
    from websockets.asyncio.client import connect

    validate_endpoint(url, "mcp")

    class DirectConnection(connect):
        def process_redirect(self, exc):
            return ServicePolicyError("MCP connection failed or redirected; review its endpoint")

    return DirectConnection(url)


def post(url, capability, **kwargs):
    """Guard retained requests-based ASR/TTS; never follow an HTTP redirect."""
    import requests

    validate_endpoint(url, capability)
    if kwargs.get("proxies"):
        raise ServicePolicyError("Service clients require direct reviewed routes")
    kwargs["allow_redirects"] = False
    kwargs["verify"] = True
    kwargs.setdefault("timeout", 30)
    with requests.Session() as session:
        session.trust_env = False
        response = session.post(url, **kwargs)
    if 300 <= response.status_code < 400:
        raise ServicePolicyError("Service redirected; configure a reviewed final endpoint explicitly")
    return response

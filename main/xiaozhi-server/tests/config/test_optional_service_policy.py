"""Optional services must reject before I/O and never advertise retired tools."""
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from config.service_policy import (
    ServicePolicyError, async_httpx_client, mcp_httpx_client, mcp_websocket,
)
from core.utils.context_provider import ContextDataProvider
from plugins_func.unavailable import REMOVED_TOOLS, UNAVAILABLE_MESSAGE


@pytest.fixture(autouse=True)
def explicit_test_clients_only(monkeypatch):
    from httpx._client import Client, AsyncClient
    monkeypatch.setattr(httpx, "Client", Client)
    monkeypatch.setattr(httpx, "AsyncClient", AsyncClient)


@pytest.mark.asyncio
async def test_async_client_rejects_unknown_destination_before_transport(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://secret@unreviewed.example:8080")
    requests = []
    async with async_httpx_client("tool", transport=httpx.MockTransport(
        lambda request: requests.append(request) or httpx.Response(200)
    )) as client:
        with pytest.raises(ServicePolicyError):
            await client.post("https://metaso.cn/api/v1/search?token=private-secret",
                              headers={"Authorization": "private-secret"}, json={"question": "fixture"})
    assert not requests


@pytest.mark.asyncio
async def test_async_client_rejects_redirect_without_following():
    requests = []
    def response(request):
        requests.append(str(request.url))
        return httpx.Response(307, headers={"Location": "https://unknown.example/?token=private-secret"})
    async with async_httpx_client("context", transport=httpx.MockTransport(response)) as client:
        with pytest.raises(ServicePolicyError) as error:
            await client.get("http://127.0.0.1:8001/context")
    assert requests == ["http://127.0.0.1:8001/context"]
    assert "private-secret" not in str(error.value)


def test_rejected_context_does_not_construct_client_or_log_url(monkeypatch):
    logger = Mock()
    logger.bind.return_value = logger
    no_client = Mock(side_effect=AssertionError("No context I/O"))
    monkeypatch.setattr("core.utils.context_provider.httpx_client", no_client)
    provider = ContextDataProvider({"context_providers": [{
        "url": "https://unknown.example/context?token=private-secret",
        "headers": {"Authorization": "private-secret"},
    }]}, logger)
    assert provider.fetch_all("synthetic-device") == ""
    no_client.assert_not_called()
    assert "private-secret" not in str(logger.mock_calls)
    assert "unknown.example" not in str(logger.mock_calls)


def test_mcp_default_factory_disables_redirects_and_environment():
    client = mcp_httpx_client(headers={"Authorization": "fixture"})
    assert client.trust_env is False
    assert client.follow_redirects is False


@pytest.mark.parametrize("config", [
    {"command": "npx", "args": ["-y", "unreviewed-package"]},
    {"url": "https://unknown.example/mcp?token=private-secret"},
    {"url": "http://localhost:8001/mcp", "env": {"TOKEN": "private-secret"}},
])
def test_mcp_rejects_subprocess_and_unknown_service_before_worker(config):
    from core.providers.tools.server_mcp.mcp_client import ServerMCPClient
    with pytest.raises(ServicePolicyError) as error:
        ServerMCPClient(config)
    assert "private-secret" not in str(error.value)


def test_mcp_websocket_rejects_destination_and_all_redirects():
    with pytest.raises(ServicePolicyError):
        mcp_websocket("wss://unreviewed.example/mcp?token=private-secret")
    connection = mcp_websocket("ws://localhost:8001/mcp?token=fixture")
    error = connection.process_redirect(RuntimeError("private-secret"))
    assert isinstance(error, ServicePolicyError)
    assert "private-secret" not in str(error)


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(REMOVED_TOOLS))
async def test_stale_tool_request_unavailable_even_without_advertisement(name, monkeypatch):
    from core.providers.tools.unified_tool_manager import ToolManager
    monkeypatch.setattr("core.providers.tools.unified_tool_manager.setup_logging", lambda: Mock())
    manager = ToolManager(SimpleNamespace())
    assert name not in manager.get_all_tools()
    result = await manager.execute_tool(name, {"query": "fixture"})
    assert result.result == "service_unavailable"
    assert result.response == UNAVAILABLE_MESSAGE


def test_supported_plugins_exclude_removed_schemas_and_keep_local_tools():
    from plugins_func.loadplugins import auto_import_modules
    from plugins_func.register import all_function_registry
    auto_import_modules("plugins_func.functions")
    assert not (REMOVED_TOOLS & all_function_registry.keys())
    assert {"get_lunar", "handle_exit_intent", "call_device"} <= all_function_registry.keys()


def test_voiceprint_unknown_endpoint_rejected_before_health_request(monkeypatch):
    from core.utils.voiceprint_provider import VoiceprintProvider
    transport = Mock(side_effect=AssertionError("No voiceprint I/O"))
    monkeypatch.setattr("core.utils.voiceprint_provider.httpx_client", transport)
    with pytest.raises(ServicePolicyError) as failure:
        VoiceprintProvider({"url": "https://unknown.example/voiceprint?key=private-secret",
                            "speakers": ["fixture,Fixture,Synthetic speaker"]})
    assert "private-secret" not in str(failure.value)
    transport.assert_not_called()


def test_failed_runtime_update_keeps_prior_configuration_and_instances(monkeypatch):
    from core.websocket_server import WebSocketServer
    from unittest.mock import AsyncMock
    import asyncio
    server = object.__new__(WebSocketServer)
    old = {"selected_module": {}}
    server.config = old
    server.config_lock = asyncio.Lock()
    server.logger = Mock()
    previous = object()
    server._vad = previous
    server._asr = previous
    monkeypatch.setattr("core.websocket_server.get_config_from_api_async", AsyncMock(
        return_value={"selected_module": {}}))
    monkeypatch.setattr("core.websocket_server.check_vad_update", lambda *args: True)
    monkeypatch.setattr("core.websocket_server.check_asr_update", lambda *args: True)
    monkeypatch.setattr("core.websocket_server.initialize_modules", Mock(
        side_effect=ServicePolicyError("Synthetic invalid configuration")))
    assert asyncio.run(server.update_config()) is False
    assert server.config is old
    assert server._vad is previous and server._asr is previous

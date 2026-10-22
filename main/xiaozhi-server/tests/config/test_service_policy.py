"""No live providers: endpoint policy and request-before-send regression checks."""
from unittest.mock import Mock

import httpx
import pytest

from config.service_policy import ServicePolicyError, httpx_client, post, validate_endpoint


@pytest.fixture(autouse=True)
def real_client_with_only_explicit_mock_transports(monkeypatch):
    # Root conftest replaces httpx.Client with a no-I/O shim. These two transport
    # tests need the real request hooks, but supply MockTransport for every call.
    from httpx._client import Client
    monkeypatch.setattr(httpx, "Client", Client)


@pytest.mark.parametrize("url,role", [
    ("https://api.openai.com/v1", "llm"),
    ("https://API.OPENAI.COM.:443/v1/audio/transcriptions", "asr"),
    ("https://generativelanguage.googleapis.com/v1beta/openai", "vllm"),
    ("http://localhost:8880/v1/audio/speech", "tts"),
    ("http://127.0.0.1:8080/v1", "llm"),
    ("https://[::1]:8080/context", "context"),
    ("ws://localhost:8080/mcp", "mcp"),
])
def test_reviewed_origin_and_role(url, role):
    assert validate_endpoint(url, role) == url


@pytest.mark.parametrize("url", [
    None, "", "https://api.deepseek.com/v1", "https://open.bigmodel.cn/api/paas/v4",
    "https://api.openai.com.evil.example/v1", "https://api.openai.com@evil.example/v1",
    "https://user:private-secret@api.openai.com/v1", "https://unknown.example/v1",
    "http://api.openai.com/v1", "https://api.openai.com:444/v1", "https://api.openai.com/#private-secret",
    "https://api.openai.com\\@evil.example/v1", "https://api.openai.com\n.evil.example/v1",
    "file:///private/data", "ftp://localhost/data", "http://127.1:8080/v1",
    "http://169.254.169.254/latest/meta-data", "https://api.openai.com:0/v1",
    "https://api.openai.com:99999/v1", "https://[broken", "https://api%2eopenai.com/v1",
    "https://api.openai.com/v1?api_key=private-secret",
])
def test_removed_unknown_or_malformed_destination_is_rejected_and_redacted(url):
    with pytest.raises(ServicePolicyError) as failure:
        validate_endpoint(url, "llm")
    assert "private-secret" not in str(failure.value)
    assert str(url) not in str(failure.value) if url else True


def test_approved_operator_is_not_approved_for_every_capability():
    with pytest.raises(ServicePolicyError):
        validate_endpoint("https://api.openai.com/context", "context")
    with pytest.raises(ServicePolicyError):
        validate_endpoint("https://generativelanguage.googleapis.com/tts", "tts")


def test_httpx_rejects_before_transport_even_with_a_configured_environment_proxy(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://private-secret@unknown.example:8080")
    calls = []
    transport = httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200))
    with httpx_client("llm", transport=transport) as client:
        with pytest.raises(ServicePolicyError):
            client.post("https://api.deepseek.com/v1/chat/completions", headers={"Authorization": "secret"})
    assert not calls


def test_httpx_does_not_follow_a_redirect_to_an_unreviewed_destination():
    calls = []
    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(307, headers={"Location": "https://unknown.example/receive"})
    with httpx_client("llm", transport=httpx.MockTransport(respond)) as client:
        response = client.post("https://api.openai.com/v1/chat/completions", content=b"fixture")
    assert response.status_code == 307
    assert calls == ["https://api.openai.com/v1/chat/completions"]


def test_requests_rejects_before_constructing_a_session(monkeypatch):
    import requests
    factory = Mock(side_effect=AssertionError("No session for unapproved endpoint"))
    monkeypatch.setattr(requests, "Session", factory)
    with pytest.raises(ServicePolicyError):
        post("https://api.deepseek.com/v1", "asr", headers={"Authorization": "secret"})
    factory.assert_not_called()


def test_requests_disables_proxies_and_redirects(monkeypatch):
    import requests
    session = Mock()
    session.post.return_value = Mock(status_code=307)
    context = Mock()
    context.__enter__ = Mock(return_value=session)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(requests, "Session", Mock(return_value=context))
    with pytest.raises(ServicePolicyError, match="redirected"):
        post("http://localhost:8880/v1/audio/speech", "tts", json={"input": "fixture"})
    assert session.trust_env is False
    assert session.post.call_args.kwargs["allow_redirects"] is False
    assert session.post.call_args.kwargs["verify"] is True


@pytest.mark.parametrize("module,class_name,endpoint_key,extra", [
    ("core.providers.asr.openai", "ASRProvider", "base_url", {"delete_audio_file": True}),
    ("core.providers.tts.openai", "TTSProvider", "api_url", {"delete_audio_file": True}),
    ("core.providers.llm.openai.openai", "LLMProvider", "base_url", {}),
    ("core.providers.vllm.openai", "VLLMProvider", "base_url", {}),
    ("core.providers.llm.ollama.ollama", "LLMProvider", "base_url", {}),
])
def test_compatible_adapter_rejects_retired_destination_before_initialization(module, class_name, endpoint_key, extra):
    import importlib
    provider = getattr(importlib.import_module(module), class_name)
    with pytest.raises(ServicePolicyError):
        provider({endpoint_key: "https://api.deepseek.com/v1", "api_key": "synthetic-secret"}, **extra)

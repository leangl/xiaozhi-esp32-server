"""Offline provider-profile proof: synthetic configuration/audio, no live keys."""
import asyncio
import copy
import importlib
import io
import json
import socket
import subprocess
import sys
import types
import wave
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
import yaml

from config.provider_profile import (
    ProviderProfileError, SUPPORTED_PROVIDERS, readiness_issues,
    validate_config, validate_provider_config, validate_provider_type,
)
from config.service_policy import ServicePolicyError


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Provider unit test attempted network access")
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def provider_config(module):
    config = {"type": "openai", "model_name": "fixture-model", "api_key": ""}
    if module == "TTS":
        config.update(api_url="http://127.0.0.1:9999/v1/audio/speech", model="fixture-voice", voice="alloy", format="wav")
    else:
        config["base_url"] = "http://127.0.0.1:9999/v1"
    return config


def full_config(tmp_path):
    model = tmp_path / "reviewed-fixture.onnx"
    model.write_bytes(b"not-an-inference-model")
    config = {"selected_module": {}, "server": {}}
    for module in ("ASR", "LLM", "TTS", "VLLM"):
        config[module] = {"fixture": provider_config(module)}
        config["selected_module"][module] = "fixture"
    for module, kind in (("VAD", "silero"), ("Memory", "nomem"), ("Intent", "nointent")):
        config[module] = {"fixture": {"type": kind}}
        config["selected_module"][module] = "fixture"
    config["VAD"]["fixture"]["model_path"] = str(model)
    return config


@pytest.mark.parametrize("module,kind", [
    (module, kind) for module, kinds in SUPPORTED_PROVIDERS.items() for kind in kinds
])
def test_supported_types(module, kind):
    assert validate_provider_type(module, kind) == kind


@pytest.mark.parametrize("module,kind", [
    ("ASR", "fun_local"), ("ASR", "sherpa_onnx_local"), ("ASR", "vosk"),
    ("LLM", "AliBL"), ("LLM", "gemini"), ("LLM", "coze"),
    ("VLLM", "../openai"), ("TTS", "edge"), ("TTS", "custom"),
    ("Memory", "mem0ai"), ("Memory", "powermem"), ("Intent", "removed"),
    ("VAD", "torch.hub"), ("ASR", {"secret": "never-display"}),
])
def test_removed_types_fail_before_import(module, kind, monkeypatch):
    factory = importlib.import_module(f"core.utils.{module.lower()}")
    importer = Mock(side_effect=AssertionError("Provider imported before validation"))
    monkeypatch.setattr(factory.importlib, "import_module", importer)
    with pytest.raises(ServicePolicyError) as error:
        factory.create_instance(kind, {})
    assert "unavailable" in str(error.value)
    assert "never-display" not in str(error.value)
    importer.assert_not_called()


@pytest.mark.parametrize("module", ["ASR", "LLM", "TTS", "VLLM"])
@pytest.mark.parametrize("url", [
    "https://api.deepseek.com/v1", "https://example.org/v1",
    "https://user:secret-value@api.openai.com/v1", "https://api.openai.com.evil.invalid/v1",
])
def test_rejected_endpoints_are_redacted(module, url):
    config = provider_config(module)
    config["api_url" if module == "TTS" else "base_url"] = url
    config["api_key"] = "secret-value"
    with pytest.raises(ProviderProfileError) as error:
        validate_provider_config(module, config, require_ready=True)
    assert url not in str(error.value)
    assert "secret-value" not in str(error.value)


@pytest.mark.parametrize("module", ["ASR", "LLM", "TTS", "VLLM"])
def test_readiness_requires_explicit_cloud_credentials(module, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "never-use-an-environment-key")
    config = provider_config(module)
    config["api_url" if module == "TTS" else "base_url"] = "https://api.openai.com/v1"
    validate_provider_config(module, config)
    with pytest.raises(ProviderProfileError, match="api_key is not ready"):
        validate_provider_config(module, config, require_ready=True)


def test_default_profile_is_safe_but_explicitly_unready():
    config = yaml.safe_load((Path(__file__).parents[1] / "config.yaml").read_text())
    validate_config(config)
    issues = readiness_issues(config)
    assert any("ASR.model_name" in issue for issue in issues)
    assert any("TTS.model" in issue for issue in issues)
    assert any("VAD.model_path" in issue for issue in issues)
    assert config["plugins"] == {}
    assert config["selected_module"]["Memory"] == "nomem"
    assert config["selected_module"]["Intent"] == "nointent"


def test_active_and_auxiliary_references_validated_without_mutation(tmp_path):
    config = full_config(tmp_path)
    # Retired, unselected records are inert and preserved, not migrated/deleted.
    config["Memory"]["retired"] = {"type": "mem0ai", "api_key": "inert-secret"}
    before = copy.deepcopy(config)
    assert validate_config(config, require_ready=True) is config
    assert config == before
    config["selected_module"]["Memory"] = "retired"
    with pytest.raises(ProviderProfileError, match="Memory provider is unavailable"):
        validate_config(config)
    config["selected_module"]["Memory"] = "fixture"
    config["Memory"]["fixture"] = {"type": "mem_local_short", "llm": "retired-llm"}
    config["LLM"]["retired-llm"] = {"type": "coze", "api_key": "inert-secret"}
    with pytest.raises(ProviderProfileError, match="LLM provider is unavailable"):
        validate_config(config)


def test_silero_missing_file_is_clear_without_model_sdk_import(tmp_path, monkeypatch):
    factory = importlib.import_module("core.utils.vad")
    importer = Mock(side_effect=AssertionError("No model/runtime import allowed"))
    monkeypatch.setattr(factory.importlib, "import_module", importer)
    with pytest.raises(ProviderProfileError, match="Automatic model downloads are disabled"):
        factory.create_instance("silero", {"model_path": str(tmp_path / "secret-path" / "absent.onnx")})
    importer.assert_not_called()


def test_ollama_has_no_implicit_endpoint_or_cloud_alias():
    for url in (None, "https://api.openai.com/v1"):
        config = {"type": "ollama", "model_name": "fixture", "base_url": url}
        with pytest.raises(ProviderProfileError):
            validate_provider_config("LLM", config, require_ready=True)


@pytest.mark.parametrize("kind", ["nomem", "mem_report_only"])
def test_inert_memory_requires_no_sdk_or_store(kind):
    factory = importlib.import_module("core.utils.memory")
    provider = factory.create_instance(kind, {"type": kind}, "inert-history")
    assert asyncio.run(provider.query_memory("fixture")) == ""
    assert asyncio.run(provider.save_memory([], "session")) is None


def test_asr_synthetic_pcm_preserves_wav_contract(tmp_path, monkeypatch):
    adapter = importlib.import_module("core.providers.asr.openai")
    config = provider_config("ASR")
    config["output_dir"] = str(tmp_path)
    provider = adapter.ASRProvider(config, delete_audio_file=True)
    pcm = b"\x00\x01" * 1600
    seen = []
    def fake_post(url, capability, **kwargs):
        assert capability == "asr"
        assert kwargs["data"] == {"model": "fixture-model"}
        with wave.open(io.BytesIO(kwargs["files"]["file"].read()), "rb") as wav:
            assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 16000)
            assert wav.readframes(wav.getnframes()) == pcm
        seen.append(url)
        return types.SimpleNamespace(status_code=200, json=lambda: {"text": "Synthetic transcript"})
    monkeypatch.setattr(adapter, "post", fake_post)
    transcript, _ = asyncio.run(provider.speech_to_text_wrapper([pcm], "fixture-session"))
    assert transcript == "Synthetic transcript"
    assert len(seen) == 1
    assert list(tmp_path.glob("*.wav")) == []


def test_tts_deterministic_wav_and_voice_contract(tmp_path, monkeypatch):
    adapter = importlib.import_module("core.providers.tts.openai")
    config = provider_config("TTS")
    config.update(output_dir=str(tmp_path), private_voice="fixture-private", speed=1.25)
    provider = adapter.TTSProvider(config, delete_audio_file=True)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\0\0" * 1440)
    audio = buffer.getvalue()
    def fake_post(url, capability, **kwargs):
        assert capability == "tts"
        assert kwargs["json"] == {"model": "fixture-voice", "input": "fixture text", "voice": "fixture-private", "response_format": "wav", "speed": 1.25}
        return types.SimpleNamespace(status_code=200, content=audio)
    monkeypatch.setattr(adapter, "post", fake_post)
    assert asyncio.run(provider.text_to_speak("fixture text", None)) == audio
    output = tmp_path / "fixture.wav"
    asyncio.run(provider.text_to_speak("fixture text", str(output)))
    assert output.read_bytes() == audio


def test_llm_and_vision_use_compatible_http_contract(monkeypatch):
    import config.service_policy as policy
    # Legacy conftest globally replaces the public Client; use the real class
    # with an in-memory transport for this contract test, never a socket.
    from httpx._client import Client
    monkeypatch.setattr(httpx, "Client", Client)
    original = policy.httpx_client
    seen = []
    def fake(request):
        payload = json.loads(request.content)
        seen.append(payload)
        assert request.url.host == "127.0.0.1"
        if payload.get("stream"):
            data = 'data: {"id":"fixture","choices":[{"index":0,"delta":{"content":"Fixture reply"}}]}\n\ndata: [DONE]\n\n'
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=data)
        return httpx.Response(200, json={"id": "fixture", "choices": [{"index": 0, "message": {"role": "assistant", "content": "Fixture vision"}, "finish_reason": "stop"}]})
    def client(capability, **kwargs):
        return original(capability, transport=httpx.MockTransport(fake), **kwargs)
    llm = importlib.import_module("core.providers.llm.openai.openai")
    vision = importlib.import_module("core.providers.vllm.openai")
    monkeypatch.setattr(llm, "httpx_client", client)
    monkeypatch.setattr(vision, "httpx_client", client)
    language = llm.LLMProvider(provider_config("LLM"))
    visual = vision.VLLMProvider(provider_config("VLLM"))
    try:
        assert list(language.response("fixture", [{"role": "user", "content": "hello"}])) == ["Fixture reply"]
        assert visual.response("describe", "ZmFrZQ==") == "Fixture vision"
        assert seen[1]["messages"][0]["content"][1]["image_url"]["url"] == "data:image/jpeg;base64,ZmFrZQ=="
    finally:
        language.client.close()
        visual.client.close()


def test_api_config_rejects_removed_selection_before_activation(tmp_path, monkeypatch):
    import config.config_loader as loader
    config = full_config(tmp_path)
    config["selected_module"]["ASR"] = "retired"
    config["ASR"]["retired"] = {"type": "fun_local", "api_key": "never-display"}
    async def response(*args):
        return copy.deepcopy(config)
    monkeypatch.setattr(loader, "init_service", lambda _: None)
    monkeypatch.setattr(loader, "get_server_config", response)
    with pytest.raises(ProviderProfileError) as error:
        asyncio.run(loader.get_config_from_api_async({"manager-api": {"url": "http://localhost", "secret": "fixture"}}))
    assert "never-display" not in str(error.value)


def test_device_api_cannot_replace_active_endpoint_via_partial_config(tmp_path, monkeypatch):
    import config.config_loader as loader
    config = full_config(tmp_path)
    async def models(*args):
        return {"LLM": {"fixture": {"base_url": "https://unknown.invalid/secret"}}}
    async def corrections(*args):
        return {}
    monkeypatch.setattr(loader, "get_agent_models", models)
    monkeypatch.setattr(loader, "get_correct_words", corrections)
    with pytest.raises(ProviderProfileError):
        asyncio.run(loader.get_private_config_from_api(config, "fixture-device", "fixture-client"))
    assert config["LLM"]["fixture"]["base_url"] == "http://127.0.0.1:9999/v1"


def test_managed_global_config_preserves_vad_asr_only_contract(tmp_path, monkeypatch):
    import config.config_loader as loader
    config = full_config(tmp_path)
    for kind in ("LLM", "TTS", "VLLM", "Memory", "Intent"):
        del config["selected_module"][kind]
        del config[kind]
    async def response():
        return copy.deepcopy(config)
    monkeypatch.setattr(loader, "init_service", lambda _: None)
    monkeypatch.setattr(loader, "get_server_config", response)
    managed = asyncio.run(loader.get_config_from_api_async({"manager-api": {"url": "http://localhost", "secret": "fixture"}}))
    assert managed["read_config_from_api"] is True
    assert set(managed["selected_module"]) == {"VAD", "ASR"}
    assert readiness_issues(managed, partial=True) == []
    assert "LLM" not in managed and "TTS" not in managed


def test_managed_auxiliary_slots_preserve_the_existing_wire_contract(tmp_path):
    config = full_config(tmp_path)
    config["SLM"] = {"auxiliary": provider_config("LLM")}
    config["RAG"] = {"retrieval": {"type": "ragflow", "base_url": "http://127.0.0.1:9998"}}
    config["selected_module"].update(SLM="auxiliary", RAG="retrieval")
    original = copy.deepcopy(config)
    assert validate_config(config, require_ready=True) is config
    assert readiness_issues(config) == []
    assert config == original


@pytest.mark.parametrize("module,settings", [
    ("SLM", {"type": "AliBL", "base_url": "http://127.0.0.1:9999"}),
    ("SLM", {"type": "openai", "base_url": "https://api.deepseek.com/v1", "api_key": "private-secret"}),
    ("RAG", {"type": "ragflow", "base_url": "https://unknown.example/?key=private-secret"}),
    ("RAG", {"type": "removed", "base_url": "http://127.0.0.1:9998"}),
])
def test_managed_auxiliary_slots_cannot_bypass_provider_policy(tmp_path, module, settings):
    config = full_config(tmp_path)
    config[module] = {"auxiliary": settings}
    config["selected_module"][module] = "auxiliary"
    original = copy.deepcopy(config)
    with pytest.raises(ProviderProfileError) as error:
        validate_config(config)
    assert "private-secret" not in str(error.value)
    assert "unknown.example" not in str(error.value)
    assert config == original


def test_device_api_error_never_falls_back_to_defaults(tmp_path, monkeypatch):
    import config.config_loader as loader
    config = full_config(tmp_path)
    async def models(*args):
        raise RuntimeError("sensitive-upstream-error")
    async def corrections(*args):
        return {}
    monkeypatch.setattr(loader, "get_agent_models", models)
    monkeypatch.setattr(loader, "get_correct_words", corrections)
    with pytest.raises(ProviderProfileError) as error:
        asyncio.run(loader.get_private_config_from_api(config, "fixture-device", "fixture-client"))
    assert "sensitive-upstream-error" not in str(error.value)
    assert "configuration is unavailable" in str(error.value)


def test_managed_device_partial_config_remains_partial_during_initialization(tmp_path, monkeypatch):
    import config.config_loader as loader
    startup = importlib.import_module("core.utils.modules_initialize")
    config = full_config(tmp_path)
    config["read_config_from_api"] = True
    private = copy.deepcopy(config)
    private.pop("read_config_from_api")
    for module in ("ASR", "VAD"):
        del private["selected_module"][module]
        del private[module]
    original = copy.deepcopy(private)
    async def models(*args):
        return private
    async def corrections(*args):
        return {}
    monkeypatch.setattr(loader, "get_agent_models", models)
    monkeypatch.setattr(loader, "get_correct_words", corrections)
    received = asyncio.run(loader.get_private_config_from_api(config, "fixture-device", "fixture-client"))
    assert received["read_config_from_api"] is True
    assert private == original
    assert "ASR" not in received["selected_module"] and "VAD" not in received["selected_module"]
    tts_instance, llm_instance = object(), object()
    monkeypatch.setattr(startup.tts, "create_instance", Mock(return_value=tts_instance))
    monkeypatch.setattr(startup.llm, "create_instance", Mock(return_value=llm_instance))
    for module in ("asr", "vad"):
        monkeypatch.setattr(getattr(startup, module), "create_instance", Mock(
            side_effect=AssertionError("Unchanged global provider must not be recreated")))
    modules = startup.initialize_modules(Mock(), received, init_tts=True, init_llm=True)
    assert modules == {"tts": tts_instance, "llm": llm_instance}


def test_startup_readiness_fails_before_constructing_any_provider(tmp_path, monkeypatch):
    startup = importlib.import_module("core.utils.modules_initialize")
    config = full_config(tmp_path)
    config["ASR"]["fixture"]["model_name"] = ""
    constructors = []
    for kind in ("asr", "tts", "llm", "vad", "intent", "memory"):
        constructor = Mock(side_effect=AssertionError("Unready startup constructed a provider"))
        monkeypatch.setattr(getattr(startup, kind), "create_instance", constructor)
        constructors.append(constructor)
    with pytest.raises(ProviderProfileError, match="ASR.model_name is not ready"):
        startup.initialize_modules(Mock(), config, True, True, True, True, True, True)
    for constructor in constructors:
        constructor.assert_not_called()


def test_startup_retained_modules_need_no_sensevoice_or_hub(tmp_path, monkeypatch):
    startup = importlib.import_module("core.utils.modules_initialize")
    silero = importlib.import_module("core.providers.vad.silero")
    llm = importlib.import_module("core.providers.llm.openai.openai")
    from httpx._client import Client
    monkeypatch.setattr(httpx, "Client", Client)
    import config.service_policy as policy
    monkeypatch.setattr(llm, "httpx_client", lambda role, **kw: policy.httpx_client(role, transport=httpx.MockTransport(lambda _: pytest.fail("Startup sent an AI request")), **kw))
    session = Mock()
    monkeypatch.setattr(silero.onnxruntime, "InferenceSession", session)
    config = full_config(tmp_path)
    for kind in ("ASR", "TTS"):
        config[kind]["fixture"]["output_dir"] = str(tmp_path / "audio")
    assert not (tmp_path / "models/SenseVoiceSmall").exists()
    modules = startup.initialize_modules(Mock(), config, True, True, True, True, True, True)
    try:
        assert set(modules) == {"asr", "tts", "llm", "vad", "memory", "intent"}
        assert modules["asr"].requires_file()
        assert session.call_args.args[0] == config["VAD"]["fixture"]["model_path"]
        assert session.call_args.kwargs["providers"] == ["CPUExecutionProvider"]
    finally:
        modules["llm"].client.close()


def test_yaml_parse_errors_are_redacted_and_empty_override_is_supported(tmp_path):
    import config.config_loader as loader
    path = tmp_path / "fixture.yaml"
    path.write_text("")
    assert loader.read_config(path) == {}
    path.write_text("api_key: [secret-never-display")
    with pytest.raises(ProviderProfileError) as error:
        loader.read_config(path)
    assert "secret-never-display" not in str(error.value)


def test_yaml_activation_rejects_before_cache_and_directory_side_effects(tmp_path, monkeypatch):
    # Conftest replaces the public load_config; load a private copy of the real
    # source so the production YAML/cache entry point is actually exercised.
    import config.config_loader as loader
    spec = importlib.util.spec_from_file_location("_profile_loader_test", loader.__file__)
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    config = full_config(tmp_path)
    config["ASR"]["fixture"]["type"] = "fun_local"
    monkeypatch.setattr(fresh, "read_config", lambda _: copy.deepcopy(config))
    directories = Mock()
    monkeypatch.setattr(fresh, "ensure_directories", directories)
    from core.utils.cache.manager import cache_manager
    monkeypatch.setattr(cache_manager, "get", lambda *args: None)
    cached = Mock()
    monkeypatch.setattr(cache_manager, "set", cached)
    with pytest.raises(ProviderProfileError, match="ASR provider is unavailable"):
        asyncio.run(fresh.load_config())
    cached.assert_not_called()
    directories.assert_not_called()


def test_distributed_adapter_and_dependency_inventory(tmp_path):
    root = Path(__file__).parents[1]
    removed = ("funasr", "modelscope", "dashscope", "baidu-aip", "cozepy", "mem0ai", "powermem", "edge_tts", "google-generativeai", "sherpa_onnx", "vosk", "mcp-proxy")
    requirements = (root / "requirements.txt").read_text().lower()
    for package in removed:
        assert package not in requirements
    expected = {
        "asr": {"base", "openai", "utils"}, "tts": {"base", "openai", "default"},
        "vllm": {"base", "openai"}, "vad": {"base", "silero", "device"},
    }
    for directory, names in expected.items():
        assert {p.stem for p in (root / "core/providers" / directory).glob("*.py")} == names
    # A clean process avoids conftest's eager fake SDK insertion. Import all
    # retained adapters with removed imports forbidden, without loading config.
    script = '''
import importlib, sys, types, socket
from loguru import logger
removed = {"funasr", "modelscope", "dashscope", "cozepy", "mem0", "powermem", "edge_tts", "sherpa_onnx", "vosk", "torch", "torchaudio"}
class BlockRemoved:
    def find_spec(self, fullname, *args):
        if fullname.split(".")[0] in removed:
            raise AssertionError("Removed SDK import attempted")
sys.meta_path.insert(0, BlockRemoved())
def no_network(*args, **kwargs):
    raise AssertionError("Network attempted during retained imports")
socket.socket.connect = no_network
socket.getaddrinfo = no_network
logging = types.ModuleType("config.logger")
logging.setup_logging = lambda *args, **kwargs: logger
sys.modules["config.logger"] = logging
for kind in ("asr", "llm", "tts", "vad", "vllm", "memory", "intent"):
    importlib.import_module("core.utils." + kind)
for module in ("asr.openai", "llm.openai.openai", "llm.ollama.ollama", "tts.openai", "vllm.openai", "vad.silero", "vad.device", "memory.nomem.nomem", "memory.mem_report_only.mem_report_only", "memory.mem_local_short.mem_local_short", "intent.nointent.nointent", "intent.intent_llm.intent_llm", "intent.function_call.function_call"):
    importlib.import_module("core.providers." + module)
assert not removed.intersection(sys.modules)
'''
    import os
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path,
                            env={**os.environ, "PYTHONPATH": str(root)},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr

"""Supported AI implementations and redacted, side-effect-free readiness checks.

Only selected providers (and their explicit reasoning LLMs) are activated. Legacy
unselected records may remain inert; nothing here rewrites credentials or data.
"""
from collections.abc import Mapping
import ipaddress
from pathlib import Path
from urllib.parse import urlsplit

from config.service_policy import ServicePolicyError, validate_endpoint


SUPPORTED_PROVIDERS = {
    "ASR": frozenset({"openai"}),
    "LLM": frozenset({"openai", "ollama"}),
    "VLLM": frozenset({"openai"}),
    "TTS": frozenset({"openai"}),
    "VAD": frozenset({"silero", "device"}),
    "Memory": frozenset({"nomem", "mem_local_short", "mem_report_only"}),
    "Intent": frozenset({"nointent", "intent_llm", "function_call"}),
}

# Manager's existing wire contract also carries auxiliary slots. These are
# validated metadata, not new Python provider factories or automatic services.
CONFIG_ONLY_PROVIDERS = {
    "SLM": SUPPORTED_PROVIDERS["LLM"],
    "RAG": frozenset({"ragflow"}),
}


class ProviderProfileError(ServicePolicyError):
    """Safe to display: supplied names, URLs, credentials and paths are omitted."""


def validate_provider_type(module, provider_type):
    choices_by_module = {**SUPPORTED_PROVIDERS, **CONFIG_ONLY_PROVIDERS}
    if module not in choices_by_module:
        raise ProviderProfileError("Unknown AI capability")
    if not isinstance(provider_type, str) or provider_type not in choices_by_module[module]:
        choices = ", ".join(sorted(choices_by_module[module]))
        raise ProviderProfileError(
            f"{module} provider is unavailable; explicitly select a supported type: {choices}. "
            "Existing data and credentials are not migrated."
        )
    return provider_type


def _configured(value):
    return (isinstance(value, str) and bool(value.strip())
            and value.strip().lower() not in {"none", "null"}
            and not value.strip().startswith("你的")
            and "placeholder" not in value.lower())


def vad_model_path(config):
    """An operator-provisioned file only; never consult a hub or downloader."""
    explicit = config.get("model_path")
    if explicit is not None:
        return Path(explicit) if _configured(explicit) else None
    directory = config.get("model_dir")
    return (Path(directory) / "src/silero_vad/data/silero_vad.onnx"
            if _configured(directory) else None)


def device_vad_max_audio_duration_ms(config):
    """Bound manual turns; accept integer strings from the model editor."""
    value = config.get("max_audio_duration_ms", 60000)
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ProviderProfileError("Device VAD max_audio_duration_ms must be an integer from 1000 to 300000")
    if isinstance(value, str) and (not value.isascii() or not value.isdecimal()):
        raise ProviderProfileError("Device VAD max_audio_duration_ms must be an integer from 1000 to 300000")
    try:
        duration = int(value)
    except (ValueError, OverflowError):
        raise ProviderProfileError("Device VAD max_audio_duration_ms must be an integer from 1000 to 300000") from None
    if not 1000 <= duration <= 300000:
        raise ProviderProfileError("Device VAD max_audio_duration_ms must be an integer from 1000 to 300000")
    return duration


def validate_provider_config(module, config, provider_type=None, *, require_ready=False):
    if not isinstance(config, Mapping):
        raise ProviderProfileError("AI provider settings must be a mapping")
    kind = validate_provider_type(module, provider_type or config.get("type"))
    if "type" in config and config["type"] != kind:
        raise ProviderProfileError(f"{module} provider type does not match the explicitly selected implementation")
    # SLM is an auxiliary LLM selection in the management API, with precisely
    # the same recipient/readiness constraints as the primary LLM.
    if module == "SLM":
        return validate_provider_config("LLM", config, kind, require_ready=require_ready)
    if module == "RAG":
        try:
            validate_endpoint(config.get("base_url"), "tool")
        except ServicePolicyError:
            raise ProviderProfileError("RAG.base_url must be an explicit approved endpoint") from None
        if any(config.get(key) for key in ("proxy", "proxies", "http_proxy", "https_proxy")):
            raise ProviderProfileError("RAG proxy overrides are unavailable")
    elif module in {"ASR", "LLM", "VLLM", "TTS"}:
        field = "api_url" if module == "TTS" else "base_url"
        endpoint = config.get(field, config.get("url") if module in {"LLM", "VLLM"} else None)
        try:
            validate_endpoint(endpoint, module.lower())
        except ServicePolicyError:
            raise ProviderProfileError(
                f"{module}.{field} must be an explicit approved endpoint; "
                "removed or unknown destinations are unavailable."
            ) from None
        if any(config.get(key) for key in ("proxy", "proxies", "http_proxy", "https_proxy")):
            raise ProviderProfileError(f"{module} proxy overrides are unavailable")
        # The Ollama implementation is a self-hosted seam, never a cloud alias.
        host = urlsplit(endpoint).hostname.removesuffix(".").encode("idna").decode("ascii").lower()
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host == "localhost"
        if kind == "ollama" and not loopback:
            raise ProviderProfileError("LLM ollama requires an explicit loopback endpoint")
        if require_ready:
            key = config.get("api_key")
            if key is not None and key != "" and not _configured(key):
                raise ProviderProfileError(f"{module}.api_key is not ready; configure credentials server-side")
            model_field = "model" if module == "TTS" else "model_name"
            if not _configured(config.get(model_field)):
                raise ProviderProfileError(f"{module}.{model_field} is not ready; explicitly configure a model")
            # Loopback OpenAI-compatible servers need no external account. Their
            # SDK-only token is supplied locally by the adapter, never persisted.
            if not loopback and not _configured(config.get("api_key")):
                raise ProviderProfileError(f"{module}.api_key is not ready; configure credentials server-side")
    elif module == "VAD" and kind == "device":
        device_vad_max_audio_duration_ms(config)
    elif module == "VAD" and require_ready:
        path = vad_model_path(config)
        try:
            exists = path is not None and path.is_file()
        except (OSError, ValueError):
            exists = False
        if not exists:
            raise ProviderProfileError(
                "VAD.model_path is not ready; provision a reviewed local Silero ONNX file. "
                "Automatic model downloads are disabled."
            )
    return config


def validate_config(config, *, require_ready=False, partial=False):
    """Validate active selections before cache writes, imports or initialization.

    A device API response may omit unchanged capabilities; validate its explicit
    selections without inventing replacements. Full configuration must select
    ASR/LLM/TTS/VAD. Optional VLLM, memory and intent can be absent.
    """
    if not isinstance(config, Mapping):
        raise ProviderProfileError("AI configuration must be a mapping")
    selected = config.get("selected_module", {})
    if not isinstance(selected, Mapping):
        raise ProviderProfileError("selected_module must be a mapping")
    if not partial and any(not selected.get(module) for module in ("ASR", "LLM", "TTS", "VAD")):
        raise ProviderProfileError("ASR, LLM, TTS and VAD must be explicitly selected")
    for module in selected:
        if module not in SUPPORTED_PROVIDERS and module not in CONFIG_ONLY_PROVIDERS:
            raise ProviderProfileError("Unknown selected AI capability")
        name = selected[module]
        providers = config.get(module, {})
        if not isinstance(name, str) or not name or not isinstance(providers, Mapping):
            raise ProviderProfileError(f"{module} selection is unavailable; explicitly configure a supported provider")
        provider = providers.get(name)
        if not isinstance(provider, Mapping):
            raise ProviderProfileError(f"{module} selection has no provider settings")
        validate_provider_config(module, provider, provider.get("type", name), require_ready=require_ready)
        if module in {"Memory", "Intent"} and provider.get("llm"):
            llms = config.get("LLM", {})
            llm_name = provider["llm"]
            reasoning = llms.get(llm_name) if isinstance(llms, Mapping) and isinstance(llm_name, str) else None
            if not isinstance(reasoning, Mapping):
                raise ProviderProfileError(f"{module}.llm reference is unavailable; explicitly select a supported LLM")
            validate_provider_config("LLM", reasoning, reasoning.get("type", llm_name), require_ready=require_ready)
    return config


def readiness_issues(config, *, partial=False):
    """Collect redacted diagnostics without reading credentials from elsewhere."""
    try:
        validate_config(config, partial=partial)
    except ProviderProfileError as error:
        return [str(error)]
    issues = []
    for module, name in config["selected_module"].items():
        provider = config[module][name]
        try:
            validate_provider_config(module, provider, provider.get("type", name), require_ready=True)
        except ProviderProfileError as error:
            issues.append(str(error))
        if module in {"Memory", "Intent"} and provider.get("llm"):
            reasoning = config["LLM"][provider["llm"]]
            try:
                validate_provider_config("LLM", reasoning, reasoning.get("type", provider["llm"]), require_ready=True)
            except ProviderProfileError as error:
                issues.append(str(error))
    return issues

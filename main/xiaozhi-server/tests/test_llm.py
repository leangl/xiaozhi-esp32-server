"""LLM integration tests.

Mock mode (default): construct real providers from data/.config.yaml;
network calls use conftest shims without making requests.
Live mode (RUN_LIVE_API_TESTS=1): call the real LLM provider, following
performance_tester_llm.py's ThreadPoolExecutor with a ten-second timeout.

Interface contract (core/providers/llm/base.py):
    response(session_id, dialogue) -> Iterator[str], a synchronous streaming generator
    response_no_stream(system_prompt, user_content) -> str

Special handling:
- CozeLLM uses bot_id / user_id rather than api_key.
- Ollama requires model_name and an available local service.
- Placeholder detection retains the legacy Chinese prefix plus "placeholder" / "xxx" / "sk-xxx".
- A synchronous LLM generator cannot use asyncio.wait_for directly; use a thread pool.
"""
from __future__ import annotations

import concurrent.futures
import sys
from pathlib import Path

import pytest

from tests.conftest import (
    CONFIG,
    LIVE_API_TESTS,
    get_provider_config,
    get_provider_type,
    get_selected_provider_name,
    has_real_key,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _build_provider():
    name = get_selected_provider_name("LLM")
    if not name:
        pytest.skip("selected_module.LLM is not set")
    cfg = get_provider_config("LLM", name)
    if not cfg:
        pytest.skip(f"LLM provider '{name}' configuration is missing")

    # Skip placeholder credentials in every mode. Real requests need real keys; in mock mode,
    # continuing without real keys may still fail in real SDK network stacks (openai/edge_tts).
    if name == "CozeLLM":
        if any(x in cfg.get("bot_id", "") for x in ["你的"]) or any(
            x in cfg.get("user_id", "") for x in ["你的"]
        ):
            pytest.skip("LLM 'CozeLLM' bot_id/user_id not configured")
    elif name == "Ollama":
        if not cfg.get("model_name"):
            pytest.skip("LLM 'Ollama' model_name not configured")
    elif not has_real_key(cfg, "api_key"):
        if LIVE_API_TESTS:
            pytest.skip(f"LLM '{name}' api_key not configured")
        else:
            pytest.skip(
                f"LLM '{name}' api_key is a placeholder (mock mode makes no real requests)."
                "For real requests: export RUN_LIVE_API_TESTS=1, supply real keys, then rerun."
            )

    ptype = get_provider_type("LLM", name)
    if not ptype:
        pytest.skip(f"LLM '{name}' type field is missing")
    from core.utils.llm import create_instance

    return create_instance(ptype, cfg)


def _collect_with_timeout(provider, session_id: str, dialogue, timeout: float = 10.0):
    """Call synchronous response() in a thread pool with a ten-second timeout."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: list(provider.response(session_id, dialogue)))
        return future.result(timeout=timeout)


def test_llm_response_streams_non_empty() -> None:
    """response(session_id, dialogue) should yield a nonempty token stream."""
    provider = _build_provider()
    dialogue = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "用一句话说 hi"},
    ]
    chunks = _collect_with_timeout(provider, "test-session", dialogue, timeout=10.0)

    full = "".join(chunks).strip()
    assert isinstance(full, str), f"Joined LLM chunks should be str, got {type(full).__name__}"
    assert full, f"LLM returned an empty response (provider={type(provider).__name__})"


def test_llm_response_no_stream_returns_string() -> None:
    """response_no_stream should return a nonempty string."""
    provider = _build_provider()
    text = provider.response_no_stream("你是助手", "介绍一下北京").strip()

    assert isinstance(text, str), f"response_no_stream should return str, got {type(text).__name__}"
    assert text, "response_no_stream returned an empty string"


def test_llm_dialogue_min_length_one_user() -> None:
    """A dialogue containing a single user message should work."""
    provider = _build_provider()
    dialogue = [{"role": "user", "content": "ping"}]
    chunks = _collect_with_timeout(provider, "s1", dialogue, timeout=10.0)

    assert "".join(chunks).strip(), "A single user message should produce content"

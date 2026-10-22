"""Memory integration tests.

Mock mode (default): construct real providers from data/.config.yaml; external
SDK calls (mem0ai / powermem clients) use shims without real requests.
Live mode (RUN_LIVE_API_TESTS=1): call the real Memory provider.

Interface contract (core/providers/memory/base.py):
    async save_memory(msgs, session_id=None) -> str
    async query_memory(query: str) -> str

Default: selected_module.Memory = nomem (memory disabled; runs locally).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from tests.conftest import (
    get_provider_config,
    get_provider_type,
    get_selected_provider_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _build_provider():
    name = get_selected_provider_name("Memory")
    if not name:
        pytest.skip("selected_module.Memory is not set")
    cfg = get_provider_config("Memory", name)
    if not cfg:
        pytest.skip(f"Memory provider '{name}' configuration is missing")
    ptype = get_provider_type("Memory", name)
    if not ptype:
        pytest.skip(f"Memory '{name}' type field is missing")
    from core.utils.memory import create_instance

    return create_instance(ptype, cfg, None)


def test_memory_provider_constructs_from_config() -> None:
    """Configuration should instantiate a MemoryProviderBase subclass."""
    provider = _build_provider()
    from core.providers.memory.base import MemoryProviderBase

    assert isinstance(provider, MemoryProviderBase), (
        f"Incorrect Memory provider type:{type(provider).__name__}"
    )


def test_memory_provider_exposes_save_and_query() -> None:
    """The provider must implement save_memory / query_memory."""
    provider = _build_provider()
    assert hasattr(provider, "save_memory"), (
        f"{type(provider).__name__} is missing save_memory"
    )
    assert hasattr(provider, "query_memory"), (
        f"{type(provider).__name__} is missing query_memory"
    )


def test_memory_save_and_query_roundtrip() -> None:
    """Querying after saving should not raise; nomem may return None/an empty string."""
    provider = _build_provider()
    msgs = [{"role": "user", "content": "test message"}]

    async def run():
        mid = await provider.save_memory(msgs, "test-session")
        result = await provider.query_memory("test")
        return mid, result

    mid, result = asyncio.run(run())
    # Memory-disabled implementations such as nomem may return None; real memory services should return a string ID.
    assert mid is None or isinstance(mid, str), (
        f"save_memory should return str or None, got {type(mid).__name__}"
    )
    assert isinstance(result, str), "query_memory should return str"

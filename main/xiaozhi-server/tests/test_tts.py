"""TTS (speech synthesis) integration tests.

Mock mode (default): construct real TTS providers from data/.config.yaml.
All external HTTP/SDK calls use conftest shims without real requests.
Live mode (RUN_LIVE_API_TESTS=1): call the real TTS provider.

Interface contract (core/providers/tts/base.py):
    text_to_speak(text, output_file) -> async; write synthesized audio to output_file.

Notes:
- The first three construction tests do not depend on cloud services; the fourth,
  test_tts_text_to_speak_writes_nonempty_file, makes real HTTP calls in live mode.
- Mock mode: the fourth test requires only that the file exists (shims create empty files);
  it does not require size > 0. Live mode enforces size > 0.
"""
from __future__ import annotations

import asyncio
import os
import sys
import threading
from contextlib import nullcontext
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.conftest import (
    LIVE_API_TESTS,
    get_provider_config,
    get_provider_type,
    get_selected_provider_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _build_provider():
    from core.utils.tts import create_instance
    if not LIVE_API_TESTS:
        return create_instance("openai", {"type": "openai", "api_url": "http://127.0.0.1:9100/v1/audio/speech",
            "model": "synthetic-tts", "api_key": "local-only", "voice": "alloy", "format": "wav",
            "output_dir": "tmp/test-tts"}, True)
    name = get_selected_provider_name("TTS")
    if not name:
        pytest.skip("selected_module.TTS is not set")
    cfg = get_provider_config("TTS", name)
    if not cfg:
        pytest.skip(f"TTS provider '{name}' configuration is missing")
    ptype = get_provider_type("TTS", name)
    if not ptype:
        pytest.skip(f"TTS '{name}' type field is missing")
    return create_instance(ptype, cfg, True)


def test_tts_provider_constructs_from_config() -> None:
    """Configuration should instantiate a TTSProviderBase subclass."""
    provider = _build_provider()
    from core.providers.tts.base import TTSProviderBase

    assert isinstance(provider, TTSProviderBase), (
        f"Incorrect TTS provider type:{type(provider).__name__}"
    )


def test_tts_provider_exposes_to_tts() -> None:
    """The provider must implement to_tts or to_tts_stream."""
    provider = _build_provider()
    has_sync = hasattr(provider, "to_tts") and callable(provider.to_tts)
    has_stream = hasattr(provider, "to_tts_stream") and callable(
        provider.to_tts_stream
    )
    assert has_sync or has_stream, (
        f"{type(provider).__name__} is missing to_tts / to_tts_stream"
    )


def test_tts_provider_has_output_dir() -> None:
    """The provider should have output_file to specify the synthesis output path."""
    provider = _build_provider()
    assert hasattr(provider, "output_file"), (
        f"{type(provider).__name__} is missing output_file"
    )
    assert isinstance(provider.output_file, str)
    assert provider.output_file, "output_file should not be empty"


def test_tts_text_to_speak_writes_file() -> None:
    """Mock mode: assert that the file exists. Live mode: assert size > 0.

    Following performance_tester_tts.py:
    - mock conn（sample_rate/audio_format/stop_event/client_abort/headers）
      and opus_encoder (a SimpleNamespace stand-in is sufficient).
    - Get the output path using generate_filename().
    - text_to_speak() calls the cloud service asynchronously and writes a file.
    - Ten-second timeout.
    - Delete the test file afterward to avoid accumulating files in tmp/.
    """
    provider = _build_provider()

    # Following performance_tester_tts.py: some providers access self.conn.sample_rate and similar fields.
    if not hasattr(provider, "conn") or provider.conn is None:
        provider.conn = SimpleNamespace(
            sample_rate=16000,
            audio_format="pcm",
            stop_event=threading.Event(),
            client_abort=False,
            headers={},
        )
    if not hasattr(provider, "opus_encoder") or provider.opus_encoder is None:
        provider.opus_encoder = SimpleNamespace()

    out_file = provider.generate_filename()
    if not LIVE_API_TESTS:
        Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    try:
        async def run():
            await asyncio.wait_for(
                provider.text_to_speak("测试一下", out_file),
                timeout=10.0,
            )

        transport = (nullcontext() if LIVE_API_TESTS else patch("core.providers.tts.openai.post",
            return_value=SimpleNamespace(status_code=200, content=b"synthetic-audio")))
        with transport:
            asyncio.run(run())

        assert os.path.exists(out_file), f"Output file does not exist:{out_file}"
        if LIVE_API_TESTS:
            assert os.path.getsize(out_file) > 0, f"Output file is empty:{out_file}"
    finally:
        if os.path.exists(out_file):
            try:
                os.remove(out_file)
            except OSError:
                pass

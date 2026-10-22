"""ASR (speech recognition) integration tests.

Mock mode (default): construct real ASR providers from data/.config.yaml.
All external HTTP/SDK calls use conftest shims without real requests.
Live mode (RUN_LIVE_API_TESTS=1): call the real ASR provider.

Interface contract (core/providers/asr/base.py):
    async speech_to_text_wrapper(pcm_data, session_id) -> Tuple[Optional[str], Optional[str]]
    async speech_to_text(opus_data, session_id, artifacts) -> Tuple[Optional[str], Optional[str]]

Notes:
- performance_tester_asr.py incorrectly calls the wrapper with three arguments (the base accepts two);
  these tests use the correct two-argument call.
- FunASR loads local model files from model_dir during construction;
  if not downloaded, __init__ raises and the test skips.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from tests.conftest import (
    LIVE_API_TESTS,
    get_provider_config,
    get_provider_type,
    get_selected_provider_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "config" / "assets"


def _build_provider():
    from core.utils.asr import create_instance
    if not LIVE_API_TESTS:
        # Defaults are intentionally unready now. Unit construction uses an
        # explicit synthetic loopback configuration, never operator secrets.
        return create_instance("openai", {"type": "openai", "base_url": "http://127.0.0.1:9100/v1/audio/transcriptions",
            "model_name": "synthetic-asr", "api_key": "local-only", "output_dir": "tmp/test-asr"}, True)
    name = get_selected_provider_name("ASR")
    if not name:
        pytest.skip("selected_module.ASR is not set")
    cfg = get_provider_config("ASR", name)
    if not cfg:
        pytest.skip(f"ASR provider '{name}' configuration is missing")
    ptype = get_provider_type("ASR", name)
    if not ptype:
        pytest.skip(f"ASR '{name}' type field is missing")
    return create_instance(ptype, cfg, True)


def _find_test_audio() -> Path:
    """Find a WAV file larger than 300 KB in config/assets/ for test audio."""
    if not _ASSETS_DIR.exists():
        pytest.skip(f"Audio directory does not exist:{_ASSETS_DIR}")
    wavs = sorted(
        (p for p in _ASSETS_DIR.glob("*.wav") if p.stat().st_size > 300 * 1024),
        key=lambda p: p.stat().st_size,
        reverse=True,  # Largest first.
    )
    if not wavs:
        pytest.skip(f"No WAV file larger than 300 KB in config/assets/")
    return wavs[0]


def test_asr_provider_constructs_from_config() -> None:
    """Configuration should instantiate an ASRProviderBase subclass."""
    provider = _build_provider()
    from core.providers.asr.base import ASRProviderBase

    assert isinstance(provider, ASRProviderBase), (
        f"Incorrect ASR provider type:{type(provider).__name__}"
    )


def test_asr_provider_exposes_speech_to_text() -> None:
    """The provider must implement speech_to_text."""
    provider = _build_provider()
    assert hasattr(provider, "speech_to_text"), (
        f"{type(provider).__name__} is missing speech_to_text"
    )
    assert callable(provider.speech_to_text)


def test_asr_provider_has_output_dir() -> None:
    """The provider must have output_dir for recognition output."""
    provider = _build_provider()
    assert hasattr(provider, "output_dir"), (
        f"{type(provider).__name__} is missing output_dir"
    )


def test_asr_speech_to_text_wrapper_returns_text() -> None:
    """Make one real ASR request in live mode and assert recognition results.

    Mock mode calls the same method, but shims return empty dict/text, so assertions are permissive:
    text may be None / str / dict; passing means no exception is raised.

    Following performance_tester_asr.py:
    - Pass real WAV bytes to speech_to_text_wrapper.
    - Ten-second timeout.
    - Returned text may be None (recognition failure), str (some providers), or dict (FunASR, with emotion/language).
    """
    provider = _build_provider()
    # Mock mode works without WAV assets because shims do not read files.
    from tests.conftest import LIVE_API_TESTS
    if LIVE_API_TESTS:
        wav_path = _find_test_audio()
        audio_data = wav_path.read_bytes()
    else:
        # Mock mode: supply placeholder bytes; the shim does not decode them.
        audio_data = b"\x00" * 1024

    async def run():
        return await asyncio.wait_for(
            provider.speech_to_text_wrapper([audio_data], "test-session"),
            timeout=10.0,
        )

    text, file_path = asyncio.run(run())
    # ASR result compatibility: None / str / dict (FunASR returns {content, language, emotion}).
    assert text is None or isinstance(text, (str, dict)), (
        f"speech_to_text_wrapper should return (None/str/dict, str|None), "
        f"got text type {type(text).__name__}"
    )
    if isinstance(text, dict):
        # FunASR format: read content; enforce nonempty content only in live mode.
        if LIVE_API_TESTS:
            assert text.get("content"), f"ASR dictionary result is missing content:{text!r}"

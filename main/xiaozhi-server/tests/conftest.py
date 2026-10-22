"""Pytest configuration — must run BEFORE any test imports project modules.

Adds the xiaozhi-server directory to sys.path so the existing implicit
relative imports (`from core.utils.textUtils import ...`) resolve.

External-API mock toggle (default: mocked)
-------------------------------------------
The dep-upgrade orchestrator and CI run this test suite *without* any
real API credentials. By default the tests construct the actual provider
objects from ``data/.config.yaml`` but route every network call through
a recording shim, so no traffic leaves the host.

Set ``RUN_LIVE_API_TESTS=1`` to opt in to real network calls. In that
mode the 5-module readiness check runs in strict form (any missing key
→ ``sys.exit(3)``), the mock shims are uninstalled, and tests hit the
real providers.

Configuration loading
---------------------
Always uses the file-merge path (``config.yaml`` + ``data/.config.yaml``).
``manager-api`` is intentionally NOT contacted — pytest must work in a
single-module deployment.
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import yaml

# Windows consoles may default to GBK, which cannot print all emoji/Chinese; force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# opuslib_next stub: allow imports; actual audio calls fail and must be handled by tests.
# ---------------------------------------------------------------------------
try:
    import opuslib_next  # noqa: F401
except Exception:
    _stub = types.ModuleType("opuslib_next")
    _stub.Encoder = type("Encoder", (), {"__init__": lambda *a, **kw: None})
    _stub.Decoder = type("Decoder", (), {"__init__": lambda *a, **kw: None})
    _stub.APPLICATION_AUDIO = 0
    _stub.OpusError = type("OpusError", (Exception,), {})
    _stub.constants = types.SimpleNamespace()
    sys.modules["opuslib_next"] = _stub
    for sub in ("api", "exceptions"):
        sys.modules[f"opuslib_next.{sub}"] = types.ModuleType(f"opuslib_next.{sub}")


# ---------------------------------------------------------------------------
# Configuration loading: always merge files.
# ---------------------------------------------------------------------------
# Precedence:
#   1. File specified by PYTEST_CONFIG_FILE (recommended: isolates test configuration).
#   2. data/.config.yaml (production / server-only deployment configuration).
_DEFAULT_CUSTOM = _PROJECT_ROOT / "data" / ".config.yaml"
_CUSTOM_CONFIG = Path(os.environ["PYTEST_CONFIG_FILE"]) if os.environ.get(
    "PYTEST_CONFIG_FILE"
) else _DEFAULT_CUSTOM


def _load_via_file_merge() -> dict:
    """Merge config.yaml and data/.config.yaml, matching production server-only deployments."""
    from config.config_loader import merge_configs

    config: dict = {}
    default_path = _PROJECT_ROOT / "config.yaml"
    if default_path.exists():
        config = yaml.safe_load(default_path.read_text(encoding="utf-8")) or {}

    if _CUSTOM_CONFIG.exists():
        custom = yaml.safe_load(_CUSTOM_CONFIG.read_text(encoding="utf-8")) or {}
        config = merge_configs(config, custom)

    return config


# Detect all-module deployments and fail fast in every mode to avoid remote API calls.
# These deployments make load_config fetch from manager-api, which pytest must not trigger.
if _CUSTOM_CONFIG.exists():
    _raw_custom = yaml.safe_load(_CUSTOM_CONFIG.read_text(encoding="utf-8")) or {}
    _api_cfg = _raw_custom.get("manager-api", {})
    _has_url = bool(_api_cfg.get("url"))
    # Compatibility: keep the Chinese placeholder test used by existing configuration.
    _has_secret = bool(_api_cfg.get("secret")) and "你" not in str(
        _api_cfg.get("secret", "")
    )
    if _has_url and _has_secret:
        print(
            "\n[conftest] ============================================================\n"
            "[conftest] FAIL: all-module deployment detected (manager-api.url + secret configured).\n"
            "[conftest]       pytest does not support all-module deployments.\n"
            "[conftest] Reason: manager-api server.secret is an anonymous token,\n"
            "[conftest]       without sys:role:superAdmin permission;\n"
            "[conftest]       it cannot access LLM/TTS/Memory configJson (including api_key).\n"
            "[conftest] To switch to a server-only deployment:\n"
            "[conftest]   1) In manager-web, open Parameter Management → Model Configuration;\n"
            "[conftest]      copy the LLM/TTS/Memory configJson values\n"
            "[conftest]   2) Write them to data/.config.yaml (same structure as config.yaml)\n"
            "[conftest]   3) Remove the entire manager-api block from data/.config.yaml\n"
            "[conftest]   4) Run pytest again\n"
            "[conftest] ============================================================",
            flush=True,
        )
        sys.exit(2)


# Always use file merging for server-only tests.
CONFIG: dict = _load_via_file_merge()


# ---------------------------------------------------------------------------
# Replace runtime configuration entry points (load_config/get_server_config) with
# the CONFIG already built above. This prevents config.config_loader.load_config
# from rereading data/.config.yaml (which defaults to an all-module deployment)
# during tests and triggering remote manager-api calls.
# ---------------------------------------------------------------------------
async def _load_config_patched(*_args, **_kwargs):
    return CONFIG


async def _get_server_config_patched(*_args, **_kwargs):
    return None


def _init_service_noop(_config):
    """Prevent init_service from constructing ManageApiClient."""
    return None


import config.config_loader as _cl  # noqa: E402
import config.manage_api_client as _mac  # noqa: E402
_cl.load_config = _load_config_patched
_mac.init_service = _init_service_noop
_mac.get_server_config = _get_server_config_patched
# Clear any ManageApiClient singleton that other code may already have created.
_mac.ManageApiClient._instance = None
_mac.ManageApiClient._closed = True


# ---------------------------------------------------------------------------
# Configuration access helpers used by tests.
# ---------------------------------------------------------------------------
def get_provider_config(module: str, provider_name: str | None = None) -> dict:
    """Return the configuration dictionary for a provider.

    - provider_name=None: use selected_module[module].
    - Otherwise use the explicitly named provider.
    Return {} when unconfigured.
    """
    if provider_name is None:
        provider_name = CONFIG.get("selected_module", {}).get(module)
    if not provider_name:
        return {}
    return CONFIG.get(module, {}).get(provider_name, {}) or {}


def get_selected_provider_name(module: str) -> str | None:
    return CONFIG.get("selected_module", {}).get(module)


def get_provider_type(module: str, provider_name: str | None = None) -> str | None:
    """Return the type name required by create_instance (possibly not the section name).

    Follow core/utils/modules_initialize.py: fall back to the section name when type is absent.
    """
    cfg = get_provider_config(module, provider_name)
    if not cfg:
        return None
    return cfg.get("type") or (provider_name or get_selected_provider_name(module))


def has_real_key(config: dict, *keys: str) -> bool:
    """Return True if any candidate field contains a non-placeholder credential.

    Placeholders are empty values, the legacy Chinese prefix, values containing
    "placeholder", or the literal "none". Preserve the prefix match below for compatibility.
    """
    if not config:
        return False
    for key in keys:
        val = config.get(key)
        if val is None:
            continue
        s = str(val).strip().lower()
        if not s or s == "none":
            continue
        if s.startswith("你的") or "placeholder" in s:
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# Default mock mode intercepts third-party HTTP/SDK calls so tests need no real credentials.
# ---------------------------------------------------------------------------
LIVE_API_TESTS: bool = os.environ.get("RUN_LIVE_API_TESTS") == "1"

# Third-party SDKs: live mode retains real imports without modification.
# Mock mode inserts these names into sys.modules with exception/client stand-ins.
_MOCKED_MODULES: tuple[str, ...] = (
    # openai/httpx/requests are usually installed in the conda environment.
    # Shimming entire modules breaks resolution of openai.types/httpx.AsyncClient;
    # shim only missing packages (__getattr__ still follows real import paths).
    "anthropic",
    "dashscope",
    "tencentcloud",
    "xunfei",
    "vosk",
    "edge_tts",
    "elevenlabs",
    "mem0",
    "mem0ai",
    "freezegun",
)

# Always shim these packages, even if installed: local model imports can fail
# (funasr imports torch; torch DLL paths can be too long), or GPU dependencies are too heavy for mocks.
_FORCE_SHIM_MODULES: tuple[str, ...] = (
    "funasr",
    "torch",
    "torchaudio",
    "modelscope",
)


def _try_import_real(name: str) -> bool:
    """Check whether a real package is available using find_spec without importing it.

    __import__ triggers package-level side effects (such as funasr importing torch).
    Instead, check directly whether the package exists on sys.path / in site-packages.
    """
    import importlib.util

    spec = importlib.util.find_spec(name)
    return spec is not None


class _RecordingShim:
    """A no-op stand-in for any object reachable through a shimmed module.

    Acts as both a callable and an attribute container: every attribute
    access returns a callable that records the call and yields another
    shim. Used as a base class for fake exception classes so
    ``except httpx.ConnectError`` blocks evaluate correctly.
    """

    _calls: list = []

    def __init__(self, *_args, **_kwargs):
        pass

    def __getattr__(self, attr):
        def _record(*args, **kwargs):
            type(self)._calls.append((attr, args, kwargs))
            return _RecordingShim()

        return _record

    def __call__(self, *args, **kwargs):
        type(self)._calls.append(("__call__", args, kwargs))
        return _RecordingShim()


class _ShimModule(types.ModuleType):
    """PEP 562 module — any attribute access returns a recording shim."""

    def __getattr__(self, attr):
        if attr in ("__path__", "__loader__", "__spec__"):
            raise AttributeError(attr)
        # Cache so identity stays stable across accesses.
        value = _RecordingShim()
        setattr(self, attr, value)
        return value


def _install_mock_layer() -> None:
    """Insert PEP 562 shims for every third-party SDK in :data:`_MOCKED_MODULES`.

    Exception classes (e.g. ``httpx.ConnectError``) become ``_RecordingShim``
    subclasses — so ``except`` blocks match and ``isinstance`` checks pass.
    Common callable symbols (``Client`` / ``OpenAI`` / ``AutoModel``) are
    pre-bound to the shim type so ``Client(...)`` constructions succeed.

    If a real package is already importable (e.g. openai installed in conda),
    we leave it alone — shimming would break submodule resolution like
    ``openai.types``.
    """
    for name in list(_MOCKED_MODULES) + list(_FORCE_SHIM_MODULES):
        if name in sys.modules and isinstance(sys.modules[name], _ShimModule):
            continue
        if name not in _FORCE_SHIM_MODULES and _try_import_real(name):
            # Real package is available — use it. We'll patch network I/O
            # at the request layer in mock mode (see below).
            continue
        shim = _ShimModule(name)
        shim.OpenAI = _RecordingShim
        shim.AsyncOpenAI = _RecordingShim
        shim.Client = _RecordingShim
        shim.AsyncClient = _RecordingShim
        shim.AutoModel = _RecordingShim
        shim.completions = _RecordingShim()
        shim.chat = _RecordingShim()
        shim.exceptions = _ShimModule(f"{name}.exceptions")
        sys.modules[name] = shim
        sys.modules[f"{name}.exceptions"] = shim.exceptions

    # Short-circuit asyncio.sleep so retry loops do not slow tests down.
    import asyncio

    async def _fast_sleep(_seconds):
        return None

    asyncio.sleep = _fast_sleep  # type: ignore[assignment]

    # Network mock: if real httpx is loaded, replace its clients with stand-ins
    # whose send immediately raises ConnectError, exercising _should_retry/raise
    # without real requests. Do not install this layer in live mode.
    if not LIVE_API_TESTS:
        try:
            import httpx as _httpx  # noqa: F401

            class _FakeAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass

                async def send(self, *args, **kwargs):
                    raise _httpx.ConnectError("MOCK: connect refused")

                async def aclose(self):
                    return None

            class _FakeClient:
                def __init__(self, *args, **kwargs):
                    pass

                def send(self, *args, **kwargs):
                    raise _httpx.ConnectError("MOCK: connect refused")

                def close(self):
                    return None

            _httpx.AsyncClient = _FakeAsyncClient  # type: ignore[misc]
            _httpx.Client = _FakeClient  # type: ignore[misc]
        except ImportError:
            pass


if not LIVE_API_TESTS:
    _install_mock_layer()


# ---------------------------------------------------------------------------
# Live-mode startup checks: server-only deployment detection ran earlier during loading.
# ---------------------------------------------------------------------------
if LIVE_API_TESTS:
    print("[conftest] OK: server-only deployment (merged file configuration)")


_REQUIRED_MODULES = ("ASR", "LLM", "TTS", "Memory", "VAD")
_SECRET_FIELDS = (
    "api_key", "token", "access_token", "authorization",
    "secret_key", "access_key", "app_id", "app_secret",
    "bot_id", "user_id",
)


def _check_modules_ready() -> None:
    """Require all five core modules in live mode; only warn in mock mode."""
    problems: list[str] = []
    selected = CONFIG.get("selected_module") or {}
    for module in _REQUIRED_MODULES:
        provider_name = selected.get(module)
        if not provider_name:
            problems.append(f"{module} is missing from selected_module (no provider selected)")
            continue
        cfg = CONFIG.get(module, {}).get(provider_name)
        if not cfg:
            problems.append(
                f"{module}.{provider_name} configuration is missing (provider absent from CFG)"
            )
            continue
        secret_keys_present = [k for k in _SECRET_FIELDS if k in cfg]
        if secret_keys_present and not any(
            has_real_key(cfg, k) for k in secret_keys_present
        ):
            problems.append(
                f"{module}.{provider_name} secret fields "
                f"{secret_keys_present} are all placeholders (no real credentials supplied)"
            )
    if not problems:
        return
    if LIVE_API_TESTS:
        msg = (
            "\n[conftest] ============================================================\n"
            "[conftest] FAIL: pytest requires all five core modules to be configured.\n"
            "[conftest] Missing/not-ready items:\n"
            + "\n".join(f"[conftest]   - {p}" for p in problems)
            + "\n[conftest] Configure all five modules in data/.config.yaml "
            "(ASR/LLM/TTS/Memory/VAD) before running pytest.\n"
            "[conftest] ============================================================"
        )
        print(msg, file=sys.stderr, flush=True)
        sys.exit(3)
    print(
        "[conftest] NOTE: default mock mode; these modules are incomplete, but pytest can run:\n  - "
        + "\n  - ".join(problems)
        + "\n[conftest] For real requests: export RUN_LIVE_API_TESTS=1, complete configuration, then rerun.",
        flush=True,
    )


_check_modules_ready()


# ---------------------------------------------------------------------------
# Explicitly identify mock mode to the user.
# ---------------------------------------------------------------------------
if not LIVE_API_TESTS:
    print(
        "[conftest] MOCK mode (default): third-party HTTP/SDK shims installed; no real requests.\n"
        "[conftest] For real requests: export RUN_LIVE_API_TESTS=1 pytest tests/ -v",
        flush=True,
    )


import pytest  # noqa: E402  (after conftest hooks so pytest is initialised)


def pytest_collection_modifyitems(config, items):
    """Collection hook for live_api tests; live mode uses the startup readiness checks."""
    if LIVE_API_TESTS:
        return
    # Do not force skips in mock mode: tests should run using shims.
    return

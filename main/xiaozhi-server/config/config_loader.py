import os
import asyncio
import yaml
from collections.abc import Mapping
from config.provider_profile import ProviderProfileError, validate_config
from config.manage_api_client import (
    init_service,
    get_server_config,
    get_agent_models,
    get_correct_words,
    DeviceNotFoundException,
    DeviceBindException,
)


def get_project_dir():
    """Return the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"


def read_config(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError:
        raise ProviderProfileError("Configuration YAML could not be parsed; check its structure without sharing secrets") from None
    if config is None:
        return {}
    if not isinstance(config, Mapping):
        raise ProviderProfileError("Configuration YAML must contain a mapping")
    return config


async def load_config():
    """Load the configuration files."""
    from core.utils.cache.manager import cache_manager, CacheType

    # Check the cache.
    cached_config = cache_manager.get(CacheType.CONFIG, "main_config")
    if cached_config is not None:
        return validate_config(cached_config, partial=isinstance(cached_config, Mapping) and bool(cached_config.get("read_config_from_api")))

    default_config_path = get_project_dir() + "config.yaml"
    custom_config_path = get_project_dir() + "data/.config.yaml"

    # Load the default configuration.
    default_config = read_config(default_config_path)
    custom_config = read_config(custom_config_path)

    if custom_config.get("manager-api", {}).get("url"):
        config = await get_config_from_api_async(custom_config)
    else:
        # Merge the configurations.
        config = merge_configs(default_config, custom_config)
    # Reject active legacy/unknown providers before filesystem or cache effects.
    validate_config(config, partial=bool(config.get("read_config_from_api")))
    # Initialize directories.
    ensure_directories(config)

    # Cache the configuration.
    cache_manager.set(CacheType.CONFIG, "main_config", config)
    return config


async def get_config_from_api_async(config):
    """Fetch configuration from the Java API asynchronously."""
    # Initialize the API client.
    init_service(config)

    # Fetch server configuration.
    config_data = await get_server_config()
    if config_data is None:
        raise Exception("Failed to fetch server config from API")
    # The management server's global contract contains only VAD/ASR. Device
    # LLM/TTS selections are delivered later, never filled from local defaults.
    validate_config(config_data, partial=True)

    config_data["read_config_from_api"] = True
    config_data["manager-api"] = {
        "url": config["manager-api"].get("url", ""),
        "secret": config["manager-api"].get("secret", ""),
    }
    auth_enabled = config_data.get("server", {}).get("auth", {}).get("enabled", False)
    # Local server settings take precedence.
    if config.get("server"):
        config_data["server"] = {
            "ip": config["server"].get("ip", ""),
            "port": config["server"].get("port", ""),
            "http_port": config["server"].get("http_port", ""),
            "vision_explain": config["server"].get("vision_explain", ""),
            "auth_key": config["server"].get("auth_key", ""),
        }
    config_data["server"]["auth"] = {"enabled": auth_enabled}
    # Use the local prompt_template if the server does not provide one.
    if not config_data.get("prompt_template"):
        config_data["prompt_template"] = config.get("prompt_template")
    return validate_config(config_data, partial=True)


async def get_private_config_from_api(config, device_id, client_id):
    """Fetch device-specific configuration from the Java API."""
    results = await asyncio.gather(
        get_agent_models(device_id, client_id, config["selected_module"]),
        get_correct_words(device_id),
        return_exceptions=True,
    )
    agent_result = results[0]
    correct_words = results[1] if not isinstance(results[1], Exception) else None

    # Propagate application-level exceptions.
    if isinstance(agent_result, DeviceNotFoundException):
        raise agent_result
    if isinstance(agent_result, DeviceBindException):
        raise agent_result

    if isinstance(agent_result, Exception):
        raise ProviderProfileError(
            "Device AI configuration is unavailable; review its supported provider selections in manager-api"
        ) from None
    # The device response intentionally omits unchanged global VAD/ASR slots.
    # Preserve its managed/partial origin when component initialization runs
    # later; do not reinterpret it as a standalone full YAML configuration.
    private_config = dict(agent_result) if isinstance(agent_result, Mapping) else agent_result
    validate_config(private_config, partial=True)
    private_config["read_config_from_api"] = True
    if correct_words:
        private_config["correct_words"] = correct_words
    # Validate both explicit selections and their merged active configuration.
    validate_config(merge_configs(config, private_config), partial=bool(config.get("read_config_from_api")))
    return private_config


def ensure_directories(config):
    """Ensure that all configured directories exist."""
    dirs_to_create = set()
    project_dir = get_project_dir()  # Get the project root directory.
    # Log directory.
    log_dir = config.get("log", {}).get("log_dir", "tmp")
    dirs_to_create.add(os.path.join(project_dir, log_dir))

    # Only selected output paths are active; legacy records remain inert.
    for module in ["ASR", "TTS"]:
        selected_provider = config.get("selected_module", {}).get(module)
        provider_config = config.get(module, {}).get(selected_provider, {})
        output_dir = provider_config.get("output_dir")
        if output_dir:
            full_model_dir = os.path.join(project_dir, output_dir)
            dirs_to_create.add(full_model_dir)

    # Create all directories, retaining the existing data-directory behavior.
    for dir_path in dirs_to_create:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except PermissionError:
            print(f"Warning: cannot create directory {dir_path}; check write permissions")


def merge_configs(default_config, custom_config):
    """
    Recursively merge configurations; custom_config takes precedence.

    Args:
        default_config: Default configuration.
        custom_config: User-defined configuration.

    Returns:
        The merged configuration.
    """
    if not isinstance(default_config, Mapping) or not isinstance(
        custom_config, Mapping
    ):
        return custom_config

    merged = dict(default_config)

    for key, value in custom_config.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged

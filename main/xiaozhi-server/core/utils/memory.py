"""Factory for explicitly supported Memory implementations only."""
import importlib

from config.provider_profile import validate_provider_config, validate_provider_type


def create_instance(class_name, *args, **kwargs):
    validate_provider_type("Memory", class_name)
    config = args[0] if args else kwargs.get("config")
    validate_provider_config("Memory", config, class_name, require_ready=True)
    provider = importlib.import_module(
        f"core.providers.memory.{class_name}.{class_name}"
    )
    return provider.MemoryProvider(*args, **kwargs)

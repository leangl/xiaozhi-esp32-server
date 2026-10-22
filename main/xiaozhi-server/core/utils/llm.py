"""Factory for explicitly supported LLM implementations only."""
import importlib

from config.provider_profile import validate_provider_config, validate_provider_type


def create_instance(class_name, *args, **kwargs):
    validate_provider_type("LLM", class_name)
    config = args[0] if args else kwargs.get("config")
    validate_provider_config("LLM", config, class_name, require_ready=True)
    provider = importlib.import_module(
        f"core.providers.llm.{class_name}.{class_name}"
    )
    return provider.LLMProvider(*args, **kwargs)

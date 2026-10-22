from config.logger import setup_logging
from core.utils.util import check_model_key
from config.service_policy import validate_endpoint

TAG = __name__
logger = setup_logging()


def append_devices_to_prompt(conn):
    if conn.intent_type == "function_call":
        funcs = conn.config["Intent"][conn.config["selected_module"]["Intent"]].get(
            "functions", []
        )

        # Read plugin configuration with a default for missing entries.
        plugins_config = conn.config.get("plugins", {})
        config_source = (
            "home_assistant"
            if plugins_config.get("home_assistant")
            else "hass_state"
        )

        if "hass_get_state" in funcs or "hass_set_state" in funcs:
            prompt = "\nBelow is the list of smart-home devices (location, device name, entity_id) that Home Assistant can control.\n"
            deviceStr = plugins_config.get(config_source, {}).get("devices", "")
            conn.prompt += prompt + deviceStr + "\n"
            # Update the system prompt.
            conn.dialogue.update_system_message(conn.prompt)


def initialize_hass_handler(conn):
    ha_config = {}
    if not conn.load_function_plugin:
        return ha_config

    # Read plugin configuration with a default for missing entries.
    plugins_config = conn.config.get("plugins", {})
    # Select the configuration source.
    config_source = (
        "home_assistant" if plugins_config.get("home_assistant") else "hass_state"
    )
    if not plugins_config.get(config_source):
        return ha_config

    # Read the selected configuration.
    plugin_config = plugins_config[config_source]
    ha_config["base_url"] = plugin_config.get("base_url")
    validate_endpoint(ha_config["base_url"], "tool")
    ha_config["api_key"] = plugin_config.get("api_key")

    # Validate the API key using the shared check.
    model_key_msg = check_model_key("home_assistant", ha_config.get("api_key"))
    if model_key_msg:
        logger.bind(tag=TAG).error(model_key_msg)

    return ha_config

import os
import asyncio
from config.config_loader import read_config, get_project_dir, load_config


default_config_file = "config.yaml"
config_file_valid = False


def check_config_file():
    global config_file_valid
    if config_file_valid:
        return
    """
    Perform a lightweight check and explain how the configuration files are used.
    """
    custom_config_file = get_project_dir() + "data/." + default_config_file
    if not os.path.exists(custom_config_file):
        raise FileNotFoundError(
            "Cannot find data/.config.yaml; follow the setup guide and check that it exists"
        )

    # Check whether configuration is loaded from the API.
    config = asyncio.run(load_config())
    if config.get("read_config_from_api", False):
        print("Loading configuration from the API")
        old_config_origin = read_config(custom_config_file)
        if old_config_origin.get("selected_module") is not None:
            error_msg = "Your configuration appears to mix management-console and local settings:\n"
            error_msg += "\nRecommended steps:\n"
            error_msg += "1. Copy config_from_api.yaml from the project root into data and rename it .config.yaml\n"
            error_msg += "2. Follow the guide to configure the API address and secret\n"
            raise ValueError(error_msg)
    config_file_valid = True

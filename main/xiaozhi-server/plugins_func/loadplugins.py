import importlib
from config.logger import setup_logging

TAG = __name__

logger = setup_logging()

# Deliberate supported surface. Merely dropping a Python file into the directory
# must not import a downloader, SDK or new remote service at process startup.
SUPPORTED_MODULES = (
    "get_time", "handle_exit_intent", "call_device", "change_role", "play_music",
    "hass_state", "hass_play_music", "search_from_ragflow",
)

def auto_import_modules(package_name):
    """
    Import all modules in the specified package.

    Args:
        package_name (str): Package name, for example 'functions'.
    """
    if package_name != "plugins_func.functions":
        raise ValueError("Only the reviewed plugin package can be loaded")
    for module_name in SUPPORTED_MODULES:
        # Import the module.
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)
        #logger.bind(tag=TAG).info(f"Module '{full_module_name}' loaded")

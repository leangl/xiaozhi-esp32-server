from config.logger import setup_logging
from enum import Enum

TAG = __name__

logger = setup_logging()


class ToolType(Enum):
    NONE = (1, "Take no further action after calling the tool")
    WAIT = (2, "Call the tool and wait for its return value")
    CHANGE_SYS_PROMPT = (3, "Change the system prompt to switch persona or role")
    SYSTEM_CTL = (
        4,
        "System control changes conversation flow, such as exiting or playing music; requires conn",
    )
    IOT_CTL = (5, "IoT device control; requires conn")
    MCP_CLIENT = (6, "MCP client")

    def __init__(self, code, message):
        self.code = code
        self.message = message


class Action(Enum):
    ERROR = (-1, "Error")
    NOTFOUND = (0, "Function not found")
    NONE = (1, "Take no action")
    RESPONSE = (2, "Reply directly")
    REQLLM = (3, "Ask the LLM for a response after the function call")
    RECORD = (4, "Record the tool call in conversation history without calling the LLM")

    def __init__(self, code, message):
        self.code = code
        self.message = message


class ActionResponse:
    def __init__(self, action: Action, result=None, response=None):
        self.action = action  # Action type.
        self.result = result  # Result of the action.
        self.response = response  # Content for a direct reply.


class FunctionItem:
    def __init__(self, name, description, func, type):
        self.name = name
        self.description = description
        self.func = func
        self.type = type


class DeviceTypeRegistry:
    """Manage IoT device types and their functions."""

    def __init__(self):
        self.type_functions = {}  # type_signature -> {func_name: FunctionItem}

    def generate_device_type_id(self, descriptor):
        """Generate a type ID from the device capability descriptor."""
        properties = sorted(descriptor["properties"].keys())
        methods = sorted(descriptor["methods"].keys())
        # Identify the device type by its name, properties and methods.
        type_signature = (
            f"{descriptor['name']}:{','.join(properties)}:{','.join(methods)}"
        )
        return type_signature

    def get_device_functions(self, type_id):
        """Get all functions for a device type."""
        return self.type_functions.get(type_id, {})

    def register_device_type(self, type_id, functions):
        """Register a device type and its functions."""
        if type_id not in self.type_functions:
            self.type_functions[type_id] = functions


# Initialize the function registry.
all_function_registry = {}
# Map module names to function names to expand module-level plugin configuration.
module_func_map = {}


def register_function(name, desc, type=None):
    """Decorate a function to add it to the function registry."""

    def decorator(func):
        all_function_registry[name] = FunctionItem(name, desc, func, type)
        # Record module-to-function mappings for module-level plugin expansion.
        module_name = func.__module__.split(".")[-1]
        module_func_map.setdefault(module_name, []).append(name)
        logger.bind(tag=TAG).debug(f"Function '{name}' loaded and available for registration")
        return func

    return decorator


def register_device_function(name, desc, type=None):
    """Decorate a device-level function for registry integration."""

    def decorator(func):
        logger.bind(tag=TAG).debug(f"Device function '{name}' loaded")
        return func

    return decorator


class FunctionRegistry:
    def __init__(self):
        self.function_registry = {}
        self.logger = setup_logging()

    def register_function(self, name, func_item=None):
        # Register the supplied function item directly.
        if func_item:
            self.function_registry[name] = func_item
            self.logger.bind(tag=TAG).debug(f"Function '{name}' registered directly")
            return func_item

        # Otherwise, look it up in all_function_registry.
        func = all_function_registry.get(name)
        if not func:
            self.logger.bind(tag=TAG).error(f"Function '{name}' not found")
            return None
        self.function_registry[name] = func
        self.logger.bind(tag=TAG).debug(f"Function '{name}' registered")
        return func

    def unregister_function(self, name):
        # Check that the function exists before unregistering it.
        if name not in self.function_registry:
            self.logger.bind(tag=TAG).error(f"Function '{name}' not found")
            return False
        self.function_registry.pop(name, None)
        self.logger.bind(tag=TAG).info(f"Function '{name}' unregistered")
        return True

    def get_function(self, name):
        return self.function_registry.get(name)

    def get_all_functions(self):
        return self.function_registry

    def get_all_function_desc(self):
        return [func.description for _, func in self.function_registry.items()]

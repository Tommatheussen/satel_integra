import importlib
import pkgutil
from pathlib import Path


def discover_handlers():
    """
    Automatically discover and import all handler modules.
    This causes their @registry.register_handler decorators to execute.
    """
    handlers_path = Path(__file__).parent

    for module_info in pkgutil.iter_modules([str(handlers_path)]):
        if module_info.name == "registry":
            # Skip the registry module itself
            continue

        module_name = f"{__package__}.{module_info.name}"
        importlib.import_module(module_name)


# Import the registry so it's easily accessible
from .registry import registry  # noqa: E402, F401

discover_handlers()

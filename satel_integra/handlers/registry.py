from collections.abc import Callable
import logging

from satel_integra.commands import SatelBaseCommand

_logger = logging.getLogger(__name__)


class CommandHandlerRegistry:
    """Central registry for command handlers."""

    _handlers: dict[SatelBaseCommand, Callable] = {}

    def register_handler(self, command_name: SatelBaseCommand):
        """Decorator to register a command handler."""

        def decorator(func: Callable) -> Callable:
            if command_name in self._handlers:
                _logger.warning(
                    "Handler for command '%s' already registered, overwriting",
                    command_name,
                )
            self._handlers[command_name] = func
            _logger.debug("Registered handler for command: %s", command_name)
            return func

        return decorator

    def get_handler(self, command_name: SatelBaseCommand) -> Callable | None:
        """Retrieve a handler for a given command."""
        return self._handlers.get(command_name)

    def has_handler(self, command_name: SatelBaseCommand) -> bool:
        """Check if a handler exists for a command."""
        return command_name in self._handlers

    @property
    def registered_commands(self):
        """Return list of all registered command names."""
        return list(self._handlers.keys())


# Create the global registry instance
registry = CommandHandlerRegistry()

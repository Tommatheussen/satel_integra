"""Message handler registry"""

from collections.abc import Callable
from satel_integra.commands import SatelBaseCommand

MESSAGE_HANDLERS: dict[SatelBaseCommand, Callable] = {}


def register_handler(msg_type: SatelBaseCommand):
    def decorator(func):
        MESSAGE_HANDLERS[msg_type] = func
        return func

    return decorator

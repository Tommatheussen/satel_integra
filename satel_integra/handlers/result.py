"""Result message handlers"""

from __future__ import annotations

import logging
from enum import IntEnum, unique
from typing import TYPE_CHECKING

from satel_integra.commands import SatelReadCommand
from satel_integra.handlers import registry

if TYPE_CHECKING:
    from satel_integra.messages import SatelReadMessage
    from satel_integra.satel_integra import AsyncSatel

_LOGGER = logging.getLogger(__name__)


@unique
class ResultStatus(IntEnum):
    """Write commands supported by Satel Integra protocol."""

    OK = 0x00
    COMMAND_ACCEPTED = 0xFF

    def __str__(self) -> str:
        """Format command string as CMD [HEX]"""
        return f"{self.name} [0x{self.value:02X}]"


@registry.register_handler(SatelReadCommand.RESULT)
def command_result(controller: AsyncSatel, msg: SatelReadMessage):
    """Handle result messages."""
    result_status = ResultStatus(msg.msg_data[0])

    _LOGGER.debug("Command result: %s", result_status)

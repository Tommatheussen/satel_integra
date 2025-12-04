"""Output message handlers"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from satel_integra.commands import SatelReadCommand
from satel_integra.handlers import registry

if TYPE_CHECKING:
    from satel_integra.messages import SatelReadMessage
    from satel_integra.satel_integra import AsyncSatel

_LOGGER = logging.getLogger(__name__)


@registry.register_handler(SatelReadCommand.OUTPUTS_STATE)
def outputs_state(controller: AsyncSatel, msg: SatelReadMessage):
    """Handle output state change messages."""
    status: dict[int, int] = {}

    output_states = msg.get_active_bits(32)
    controller.violated_outputs = output_states

    _LOGGER.debug("Output states: %s", output_states)

    for output in controller._monitored_outputs:
        status[output] = 1 if output in output_states else 0

    _LOGGER.debug("Returning status: %s", status)

    if controller._output_changed_callback:
        controller._output_changed_callback(status)

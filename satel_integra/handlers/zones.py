from __future__ import annotations
from satel_integra.commands import SatelReadCommand
from satel_integra.handlers import registry
from satel_integra.messages import SatelReadMessage

from typing import TYPE_CHECKING


import logging

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from satel_integra.satel_integra import AsyncSatel
    from satel_integra.messages import SatelReadMessage


@registry.register_handler(SatelReadCommand.ZONES_VIOLATED)
def zones_violated(controller: AsyncSatel, msg: SatelReadMessage):
    """Handle zone violation messages."""
    status: dict[int, int] = {}

    violated_zones = msg.get_active_bits(32)
    controller.violated_zones = violated_zones

    _LOGGER.debug("Violated zones: %s", violated_zones)

    for zone in controller._monitored_zones:
        status[zone] = 1 if zone in violated_zones else 0

    _LOGGER.debug("Returning status: %s", status)

    if controller._zone_changed_callback:
        controller._zone_changed_callback(status)

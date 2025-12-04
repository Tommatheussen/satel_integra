"""Partition message handlers"""

import logging
from typing import TYPE_CHECKING
from satel_integra.handlers import registry
from satel_integra.commands import SatelReadCommand
from satel_integra.state import alarm_state_from_command

_LOGGER = logging.getLogger(__name__)


if TYPE_CHECKING:
    from satel_integra.satel_integra import AsyncSatel
    from satel_integra.messages import SatelReadMessage


@registry.register_handler(SatelReadCommand.PARTITIONS_ARMED_SUPPRESSED)
@registry.register_handler(SatelReadCommand.PARTITIONS_ARMED_MODE0)
@registry.register_handler(SatelReadCommand.PARTITIONS_ARMED_MODE2)
@registry.register_handler(SatelReadCommand.PARTITIONS_ARMED_MODE3)
@registry.register_handler(SatelReadCommand.PARTITIONS_ENTRY_TIME)
@registry.register_handler(SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_OVER_10)
@registry.register_handler(SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_UNDER_10)
@registry.register_handler(SatelReadCommand.PARTITIONS_ALARM)
@registry.register_handler(SatelReadCommand.PARTITIONS_FIRE_ALARM)
@registry.register_handler(SatelReadCommand.PARTITIONS_ARMED_MODE1)
def partitions_armed_state(controller: AsyncSatel, msg: SatelReadMessage):
    mode = alarm_state_from_command(msg.cmd)

    if mode is None:
        _LOGGER.warning("Could not map command to state: %s", msg)
        return

    partitions = msg.get_active_bits(4)

    _LOGGER.debug("Update: list of partitions in mode %s: %s", mode, partitions)

    controller.partition_states[mode] = partitions

    if controller._alarm_status_callback:
        controller._alarm_status_callback()

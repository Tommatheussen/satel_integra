"""Possible alarm states"""

from __future__ import annotations
from enum import Enum, unique

from satel_integra.commands import SatelReadCommand


@unique
class AlarmState(Enum):
    """Represents status of the alarm."""

    ARMED_MODE0 = 0
    ARMED_MODE1 = 1
    ARMED_MODE2 = 2
    ARMED_MODE3 = 3
    ARMED_SUPPRESSED = 4
    ENTRY_TIME = 5
    EXIT_COUNTDOWN_OVER_10 = 6
    EXIT_COUNTDOWN_UNDER_10 = 7
    TRIGGERED = 8
    TRIGGERED_FIRE = 9
    DISARMED = 10


COMMAND_TO_STATE: dict[SatelReadCommand, AlarmState] = {
    SatelReadCommand.PARTITIONS_ARMED_SUPPRESSED: AlarmState.ARMED_SUPPRESSED,
    SatelReadCommand.PARTITIONS_ARMED_MODE0: AlarmState.ARMED_MODE0,
    SatelReadCommand.PARTITIONS_ARMED_MODE2: AlarmState.ARMED_MODE2,
    SatelReadCommand.PARTITIONS_ARMED_MODE3: AlarmState.ARMED_MODE3,
    SatelReadCommand.PARTITIONS_ENTRY_TIME: AlarmState.ENTRY_TIME,
    SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_OVER_10: AlarmState.EXIT_COUNTDOWN_OVER_10,
    SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_UNDER_10: AlarmState.EXIT_COUNTDOWN_UNDER_10,
    SatelReadCommand.PARTITIONS_ALARM: AlarmState.TRIGGERED,
    SatelReadCommand.PARTITIONS_FIRE_ALARM: AlarmState.TRIGGERED_FIRE,
    SatelReadCommand.PARTITIONS_ARMED_MODE1: AlarmState.ARMED_MODE1,
}


def alarm_state_from_command(cmd: SatelReadCommand) -> AlarmState | None:
    return COMMAND_TO_STATE.get(cmd)

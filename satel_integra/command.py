"""Commands and responses for Satel Integra protocol."""

from enum import IntEnum, unique


@unique
class SatelResultCode(IntEnum):
    """Result codes returned in the RESULT command."""

    OK = 0x00
    USER_CODE_NOT_FOUND = 0x01
    NO_ACCESS = 0x02
    USER_NOT_EXIST = 0x03
    USER_ALREADY_EXIST = 0x04
    WRONG_CODE_OR_CODE_ALREADY_EXIST = 0x05
    TELEPHONE_CODE_ALREADY_EXIST = 0x06
    CHANGED_CODE_IS_THE_SAME = 0x07
    OTHER_ERROR = 0x08
    CANNOT_ARM_BUT_CAN_USE_FORCE_ARM = 0x11
    CANNOT_ARM = 0x12
    # OTHER_ERRORS = 0x80  # and up to 0x8F, TODO: define all?
    COMMAND_ACCEPTED = 0xFF


@unique
class SatelBaseCommand(IntEnum):
    """Base class for all Satel commands."""

    def to_bytearray(self) -> bytearray:
        """Return command as single-byte bytearray."""
        return bytearray(self.value.to_bytes(1, "little"))

    def __str__(self) -> str:
        return self.name


@unique
class SatelReadCommand(SatelBaseCommand):
    """Read commands supported by Satel Integra protocol."""

    ZONES_VIOLATED = 0x00
    PARTITIONS_ARMED_SUPPRESSED = 0x09
    PARTITIONS_ARMED_MODE0 = 0x0A
    PARTITIONS_ARMED_MODE2 = 0x0B
    PARTITIONS_ARMED_MODE3 = 0x0C
    PARTITIONS_ENTRY_TIME = 0x0E
    PARTITIONS_EXIT_COUNTDOWN_OVER_10 = 0x0F
    PARTITIONS_EXIT_COUNTDOWN_UNDER_10 = 0x10
    PARTITIONS_ALARM = 0x13
    PARTITIONS_FIRE_ALARM = 0x14
    OUTPUTS_STATE = 0x17
    PARTITIONS_ARMED_MODE1 = 0x2A
    RESULT = 0xEF


@unique
class SatelWriteCommand(SatelBaseCommand):
    """Write commands supported by Satel Integra protocol."""

    START_MONITORING = 0x7F
    PARTITIONS_ARM_MODE_0 = 0x80
    PARTITIONS_ARM_MODE_1 = 0x81
    PARTITIONS_ARM_MODE_2 = 0x82
    PARTITIONS_ARM_MODE_3 = 0x83
    PARTITIONS_DISARM = 0x84
    PARTITIONS_CLEAR_ALARM = 0x85
    OUTPUTS_ON = 0x88
    OUTPUTS_OFF = 0x89

    # RTC_AND_STATUS = 0x1A
    # DEVICE_INFO = 0xEE
    # DOORS_OPENED = 0x18
    # ZONES_BYPASSED = 0x06
    # INTEGRA_VERSION = 0x7E
    # ZONE_TEMP = 0x7D

    # CMD_ARM_MODE_1 = (0x81, True)
    # CMD_ARM_MODE_2 = (0x82, True)
    # CMD_ARM_MODE_3 = (0x83, True)
    # CMD_ZONE_BYPASS = (0x86, True)
    # CMD_OPEN_DOOR = (0x8A, True)
    # CMD_READ_ZONE_TEMP = (0x7D,)
    # CMD_DEVICE_INFO = (0xEE,)

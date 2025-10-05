"""Message classes for communication with Satel Integra panel."""

import logging

from satel_integra.command import SatelBaseCommand, SatelReadCommand, SatelWriteCommand
from satel_integra.utils import checksum, decode_bitmask_le, encode_bitmask_le

_LOGGER = logging.getLogger(__name__)


class SatelBaseMessage:
    """Base class shared by read/write message types."""

    def __init__(self, cmd: SatelBaseCommand, msg_data: bytearray) -> None:
        self.cmd = cmd
        self.msg_data = msg_data

    def __str__(self) -> str:
        return f"SatelMessage({self.cmd}, {self.msg_data.hex()})"


class SatelWriteMessage(SatelBaseMessage):
    """Message used to send commands to the panel."""

    def __init__(
        self,
        cmd: SatelWriteCommand,
        code: str | None = None,
        partitions: list[int] | None = None,
        outputs: list[int] | None = None,
        raw_data: bytearray | None = None,
    ) -> None:
        if raw_data is not None:
            msg_data = raw_data
        else:
            msg_data = bytearray()
            if code:
                msg_data += bytearray.fromhex(code.ljust(16, "F"))
            if partitions:
                msg_data += encode_bitmask_le(partitions, 4)
            if outputs:
                msg_data += encode_bitmask_le(outputs, 32)

        super().__init__(cmd, msg_data)

    def encode_frame(self) -> bytearray:
        """Construct full message frame for sending to panel."""
        data = self.cmd.to_bytearray() + self.msg_data
        csum = checksum(data)
        data.append(csum >> 8)
        data.append(csum & 0xFF)
        data = data.replace(b"\xfe", b"\xfe\xf0")
        return bytearray.fromhex("FEFE") + data + bytearray.fromhex("FE0D")


class SatelReadMessage(SatelBaseMessage):
    """Message representing data received from the panel."""

    @staticmethod
    def decode_frame(
        resp: bytes,
    ) -> (
        "SatelReadMessage | None"
    ):  # TODO: Verify this type, no sure if we should return None??
        """Verify checksum and strip header/footer of received frame."""
        if resp[0:2] != b"\xfe\xfe":
            _LOGGER.error("Bad header: %s", resp.hex())
            raise ValueError("Invalid frame header")
        if resp[-2:] != b"\xfe\x0d":
            _LOGGER.error("Bad footer: %s", resp.hex())
            raise ValueError("Invalid frame footer")

        output = resp[2:-2].replace(b"\xfe\xf0", b"\xfe")
        calc_sum = checksum(output[:-2])
        received_sum = (output[-2] << 8) | output[-1]

        if received_sum != calc_sum:
            msg = f"Checksum mismatch: got {received_sum}, expected {calc_sum}"
            raise ValueError(msg)

        cmd_byte, data = output[0], output[1:-2]
        try:
            cmd = SatelReadCommand(cmd_byte)
            return SatelReadMessage(cmd, bytearray(data))
        except ValueError:
            _LOGGER.warning("Unknown command byte: %s", hex(cmd_byte))
            return None

    def get_active_bits(self, expected_length: int) -> list[int]:
        """Convenience wrapper around decode_bitmask_le() for this message."""
        return decode_bitmask_le(self.msg_data, expected_length)

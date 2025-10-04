import logging
from satel_integra.command import SatelBaseCommand, SatelWriteCommand
from .utils import bitmask_bytes_le, checksum

from binascii import hexlify

_LOGGER = logging.getLogger(__name__)


class SatelBaseMessage:
    """Base class shared by read/write message types."""

    def __init__(self, cmd: SatelBaseCommand, msg_data: bytearray):
        self.cmd = cmd
        self.msg_data = msg_data

    def __str__(self):
        return f"SatelMessage({self.cmd}, {hexlify(self.msg_data)})"

    def encode_frame(self) -> bytearray:
        """Construct full message frame for sending to panel."""
        data = self.cmd.to_bytearray() + self.msg_data
        csum = checksum(data)
        data.append(csum >> 8)
        data.append(csum & 0xFF)
        data = data.replace(b"\xfe", b"\xfe\xf0")
        return bytearray.fromhex("FEFE") + data + bytearray.fromhex("FE0D")

    @staticmethod
    def decode_frame(resp: bytes):
        """Verify checksum and strip header/footer of received frame."""
        if resp[0:2] != b"\xfe\xfe":
            _LOGGER.error("Bad header: %s", hexlify(resp))
            raise ValueError("Invalid frame header")
        if resp[-2:] != b"\xfe\x0d":
            _LOGGER.error("Bad footer: %s", hexlify(resp))
            raise ValueError("Invalid frame footer")

        output = resp[2:-2].replace(b"\xfe\xf0", b"\xfe")
        calc_sum = checksum(output[:-2])
        received_sum = (output[-2] << 8) | output[-1]

        if received_sum != calc_sum:
            raise ValueError(
                f"Checksum mismatch: got {received_sum}, expected {calc_sum}"
            )

        cmd_byte, data = output[0], output[1:-2]
        try:
            cmd = SatelBaseCommand.from_value(cmd_byte)
            return SatelBaseMessage(cmd, bytearray(data))
        except ValueError:
            _LOGGER.warning("Unknown command byte: %s", hex(cmd_byte))
            return None


class SatelWriteMessage(SatelBaseMessage):
    """Message used to send commands to the panel."""

    def __init__(
        self,
        cmd: SatelWriteCommand,
        code: str | None = None,
        partitions: list[int] | None = None,
        outputs: list[int] | None = None,
        raw_data: bytearray | None = None,
    ):
        if raw_data is not None:
            msg_data = raw_data
        else:
            msg_data = bytearray()
            if code:
                msg_data += bytearray.fromhex(code.ljust(16, "F"))
            if partitions:
                msg_data += bitmask_bytes_le(partitions, 4)
            if outputs:
                msg_data += bitmask_bytes_le(outputs, 32)

        super().__init__(cmd, msg_data)


class SatelReadMessage(SatelBaseMessage):
    """Message representing data received from the panel."""

    # No extra logic needed yet — but ready for custom parsing/decoding later.
    pass

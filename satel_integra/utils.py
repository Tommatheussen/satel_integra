"""Utility functions."""


def checksum(command: bytes | bytearray) -> int:
    """Calculate 16-bit checksum for given command."""
    crc = 0x147A
    for b in command:
        # rotate (crc 1 bit left)
        crc = ((crc << 1) & 0xFFFF) | (crc & 0x8000) >> 15
        crc = crc ^ 0xFFFF
        crc = (crc + (crc >> 8) + b) & 0xFFFF
    return crc


def bitmask_bytes_le(positions: list[int], length: int) -> bytes:
    """Convert a list of bit positions to a fixed-length little-endian byte array.

    Used for partitions, zones, outputs, expanders, etc.
    """
    ret_val = 0
    for pos in positions:
        if pos < 1 or pos > length * 8:
            msg = f"Position {pos} out of bounds for length {length}"
            raise IndexError(msg)
        ret_val |= 1 << (pos - 1)
    return ret_val.to_bytes(length, "little")


def value_bytes(value: int, length: int) -> bytes:
    """Convert an integer (or numeric value) to a fixed-length byte array.

    Endianness can be specified ('big' or 'little').
    Used for user codes, time, numeric fields, etc.
    """
    return value.to_bytes(length, "big")

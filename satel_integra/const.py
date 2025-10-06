"""Constants for Satel Integra integration."""

FRAME_START = bytes([0xFE, 0xFE])
FRAME_END = bytes([0xFE, 0x0D])

FRAME_RESTRICTED_BYTES = bytes([0xFE])
FRAME_RESTRICTED_REPLACEMENT = bytes([0xFE, 0xF0])

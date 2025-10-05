from satel_integra.utils import checksum, decode_bitmask_le, encode_bitmask_le


def test_checksum_known_value() -> None:
    """Test checksum calculation against known value from manual."""
    data = bytearray([0xFE, 0xFE, 0xE0, 0x12, 0x34, 0xFF, 0xFF, 0x8A, 0x9B, 0xFE, 0x0D])

    c = checksum(data[2:-4])  # exclude headers, footers and checksum itself
    assert c == 0x8A9B  # replace with expected known checksum


def test_bitmask_bytes_encoding() -> None:
    """Test encode_bitmask_le function."""
    partitions = [1, 2, 29]
    result = encode_bitmask_le(partitions, 4)

    assert isinstance(result, bytes)
    assert result == bytearray([0x03, 0x00, 0x00, 0x10])


def test_bitmask_bytes_decoding() -> None:
    """Test bitmask_bytes_le function."""
    data = bytearray(
        [
            0x04,
            0x20,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x80,
        ]
    )

    result = decode_bitmask_le(data, 16)

    assert isinstance(result, list)
    assert result == [3, 14, 128]

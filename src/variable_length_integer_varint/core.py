"""Core varint encoding and decoding functions.

This module implements the protobuf-style base-128 varint scheme.
Each byte stores 7 bits of the integer, with the most significant bit
set on every byte except the last.  Integers are encoded in
least-significant group first order, which matches how a human would
append bits when writing them out in base 128.
"""

from __future__ import annotations

from typing import List

_MAX_64_BIT = (1 << 64) - 1


def encode(value: int) -> bytes:
    """Encode a non-negative integer as a protobuf-style varint.

    Args:
        value: A non-negative integer no larger than 2**64 - 1.

    Returns:
        The varint encoding as a bytes object.

    Raises:
        ValueError: If ``value`` is negative or exceeds the 64-bit
            unsigned integer range.

    The upper bound is enforced because protobuf varints are defined
    for 64-bit unsigned integers; allowing arbitrary precision would
    create encodings that many decoders cannot consume.
    """
    if not isinstance(value, int):
        raise TypeError("value must be an int")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value > _MAX_64_BIT:
        raise ValueError("value exceeds 64-bit unsigned integer range")

    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            break
    return bytes(out)


def decode(data: bytes) -> int:
    """Decode a complete varint from a bytes object.

    Args:
        data: A bytes object containing exactly one varint.  No extra
            trailing bytes are permitted.

    Returns:
        The decoded integer.

    Raises:
        ValueError: If ``data`` is empty, contains an incomplete
            varint, uses more than 10 bytes, or overflows 64 bits.

    This function is intentionally strict: it is meant for cases where
    the caller has already sliced out the encoded varint.  For reading
    from a longer byte stream, use :func:`decode_stream`.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes-like")

    value, offset = decode_stream(data, 0)
    if offset != len(data):
        raise ValueError("trailing bytes after varint")
    return value


def decode_stream(data: bytes | bytearray, offset: int = 0) -> tuple[int, int]:
    """Decode a varint from a byte stream at a given offset.

    Args:
        data: A bytes-like object containing at least one varint
            starting at ``offset``.
        offset: The starting position within ``data``.

    Returns:
        A tuple ``(value, next_offset)`` where ``next_offset`` is the
        index of the first byte after the decoded varint.

    Raises:
        ValueError: If ``offset`` is outside ``data``, the stream ends
            in the middle of a varint, the varint uses more than 10
            bytes, or the decoded value overflows 64 bits.

    Protobuf varints are limited to 10 bytes because 10 * 7 bits ==
    70 bits, which is enough to hold 64 bits plus the termination
    bit.  Allowing longer encodings would make the decoder accept
    non-canonical or malicious input.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes-like")
    if not isinstance(offset, int):
        raise TypeError("offset must be an int")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if offset > len(data):
        raise ValueError("offset is outside data")

    value = 0
    shift = 0
    position = offset

    for _ in range(10):
        if position >= len(data):
            raise ValueError("incomplete varint")

        byte = data[position]
        position += 1

        # The lower 7 bits are payload; the top bit is the continuation flag.
        value |= (byte & 0x7F) << shift

        if not (byte & 0x80):
            # Final byte of this varint.
            if value > _MAX_64_BIT:
                raise ValueError("varint overflows 64-bit unsigned integer")
            return value, position

        shift += 7

    raise ValueError("varint is too long; maximum is 10 bytes")

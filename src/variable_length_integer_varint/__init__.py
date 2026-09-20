"""Variable-length integer encoding (protobuf-style varint)."""

from .core import decode, decode_stream, encode

__all__ = ["encode", "decode", "decode_stream"]

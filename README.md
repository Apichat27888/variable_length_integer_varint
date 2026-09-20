# variable-length-integer-varint

Encodes and decodes non-negative integers using protobuf-style base-128 varint format.

```python
from variable_length_integer_varint import encode, decode, decode_stream

encoded = encode(300)          # b'\xac\x02'
decoded = decode(encoded)      # 300

# Read from a larger byte stream:
data = b'\x08\x96\x01\x12\x07testing'
value, next_offset = decode_stream(data, 0)
# value == 150, next_offset == 3
```

## Why this library exists

Protocols such as Protocol Buffers use variable-length integer encoding to
store integers compactly: small values occupy one byte, while larger values
use up to ten.  The trade-off is that decoding is slightly more complex than
reading a fixed-width integer, and encodings are not self-delimiting without
knowing the expected length.  This library implements the canonical base-128
varint format with strict bounds checking so that callers do not have to
re-implement the wire format each time.

## Edge cases

The encoder and decoder reject integers that fall outside the 64-bit unsigned
range.  This mirrors the protobuf wire format, which has no representation for
integers larger than `2**64 - 1`.  The decoder also refuses to accept more than
ten bytes for a single varint, because ten bytes is the longest valid encoding
for a 64-bit value.

`decode` expects a bytes object containing exactly one varint and will raise
`ValueError` if trailing bytes are present.  Use `decode_stream` when reading
from a buffer that contains additional data after the varint.

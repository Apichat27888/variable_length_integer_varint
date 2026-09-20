import unittest

from variable_length_integer_varint import decode, decode_stream, encode


class TestEncode(unittest.TestCase):
    def test_zero_encodes_to_single_zero_byte(self):
        self.assertEqual(encode(0), b"\x00")

    def test_small_values_under_128_use_one_byte(self):
        self.assertEqual(encode(1), b"\x01")
        self.assertEqual(encode(127), b"\x7f")

    def test_128_requires_two_bytes(self):
        self.assertEqual(encode(128), b"\x80\x01")

    def test_300_is_standard_example(self):
        self.assertEqual(encode(300), b"\xac\x02")

    def test_max_64_bit_value_uses_ten_bytes(self):
        max_value = (1 << 64) - 1
        self.assertEqual(encode(max_value), b"\xff" * 9 + b"\x01")

    def test_rejects_negative_integers(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_rejects_values_above_64_bits(self):
        with self.assertRaises(ValueError):
            encode(1 << 64)

    def test_rejects_non_integer_types(self):
        with self.assertRaises(TypeError):
            encode("123")


class TestDecode(unittest.TestCase):
    def test_zero_decodes(self):
        self.assertEqual(decode(b"\x00"), 0)

    def test_single_byte(self):
        self.assertEqual(decode(b"\x01"), 1)
        self.assertEqual(decode(b"\x7f"), 127)

    def test_two_bytes(self):
        self.assertEqual(decode(b"\x80\x01"), 128)

    def test_standard_example(self):
        self.assertEqual(decode(b"\xac\x02"), 300)

    def test_max_64_bit_value(self):
        max_value = (1 << 64) - 1
        self.assertEqual(decode(b"\xff" * 9 + b"\x01"), max_value)

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            decode(b"")

    def test_rejects_incomplete_varint(self):
        with self.assertRaises(ValueError):
            decode(b"\x80")

    def test_rejects_trailing_bytes(self):
        with self.assertRaises(ValueError):
            decode(b"\x01\x02")

    def test_rejects_overflowing_64_bit_value(self):
        # 10 bytes with the final byte carrying extra high bits beyond 64.
        with self.assertRaises(ValueError):
            decode(b"\xff" * 9 + b"\x02")

    def test_rejects_non_bytes_input(self):
        with self.assertRaises(TypeError):
            decode("\x01")


class TestDecodeStream(unittest.TestCase):
    def test_decodes_from_start_of_stream(self):
        value, next_offset = decode_stream(b"\xac\x02\x05", 0)
        self.assertEqual(value, 300)
        self.assertEqual(next_offset, 2)

    def test_decodes_from_nonzero_offset(self):
        data = b"\xff\xac\x02\x05"
        value, next_offset = decode_stream(data, 1)
        self.assertEqual(value, 300)
        self.assertEqual(next_offset, 3)

    def test_accepts_bytearray(self):
        data = bytearray(b"\x80\x01")
        value, next_offset = decode_stream(data, 0)
        self.assertEqual(value, 128)
        self.assertEqual(next_offset, 2)

    def test_zero_from_stream(self):
        value, next_offset = decode_stream(b"\x00", 0)
        self.assertEqual(value, 0)
        self.assertEqual(next_offset, 1)

    def test_rejects_negative_offset(self):
        with self.assertRaises(ValueError):
            decode_stream(b"\x00", -1)

    def test_rejects_offset_beyond_data(self):
        with self.assertRaises(ValueError):
            decode_stream(b"\x00", 2)

    def test_rejects_incomplete_varint_at_end(self):
        with self.assertRaises(ValueError):
            decode_stream(b"\x80", 0)

    def test_rejects_more_than_ten_bytes(self):
        with self.assertRaises(ValueError):
            decode_stream(b"\x80" * 10 + b"\x01", 0)


if __name__ == "__main__":
    unittest.main()

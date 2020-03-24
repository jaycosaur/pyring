import unittest
import typing
from pyring import RingBuffer, Empty, SequenceOverwritten, SequenceNotFound, RingFactory


class CustomSumFactory(RingFactory):
    value: typing.List[int] = []

    def get(self):
        return sum(self.value)

    def set(self, values):
        self.value = values


class TestRingBuffer(unittest.TestCase):
    def test_can_create_with_default_args(self):
        ring_buffer = RingBuffer()
        self.assertIsInstance(ring_buffer, RingBuffer)

    def test_accepts_valid_sizes(self):
        with self.assertRaises(AttributeError):
            RingBuffer(size=5)
        self.assertIsInstance(RingBuffer(size=4), RingBuffer)

    def test_cannot_read_ahead_of_cursor(self):
        ring_buffer = RingBuffer(size=4)

        with self.assertRaises(Empty):
            ring_buffer.get_latest()

        with self.assertRaises(SequenceNotFound):
            ring_buffer.get(0)

        ring_buffer.put(0)
        with self.assertRaises(SequenceNotFound):
            ring_buffer.get(1)

        for i in range(4):
            ring_buffer.put(i)

        with self.assertRaises(SequenceNotFound):
            ring_buffer.get(5)

    def test_cannot_read_when_overwritten(self):
        ring_buffer = RingBuffer(size=4)

        # overwrite zeroth element
        for i in range(5):
            ring_buffer.put(i)

        with self.assertRaises(SequenceOverwritten):
            ring_buffer.get(0)

    def test_can_read_and_write_with_default_factory(self):
        ring_buffer = RingBuffer(size=4)
        for i in range(10):
            ring_buffer.put(i ** 2)
            sequence, res = ring_buffer.get(i)
            self.assertEqual(res, i ** 2)
            self.assertEqual(sequence, i)

    def test_can_read_and_write_with_custom_factory(self):
        sum_buffer = RingBuffer(size=4, factory=CustomSumFactory)

        for i in range(10):
            sum_buffer.put([i, i, i])
            sequence, res = sum_buffer.get(i)
            self.assertEqual(res, i * 3)
            self.assertEqual(sequence, i)

    def test_flush(self):
        ring_buffer = RingBuffer()

        for i in range(100):
            ring_buffer.put(i)

        self.assertEqual(ring_buffer.get_latest(), (99, 99))

        ring_buffer.flush()

        with self.assertRaises(Empty):
            ring_buffer.get_latest()


if __name__ == "__main__":
    unittest.main()

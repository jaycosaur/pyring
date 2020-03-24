import unittest
import typing
from pyring import (
    BlockingRingBuffer,
    BlockingLockedRingBuffer,
    SequenceNotFound,
    ReadCursorBlock,
)


def construct_test_case(ring_buffer: BlockingRingBuffer):
    class TestBlockingRingBuffer(unittest.TestCase):
        def setUp(self):
            self.ring_buffer = ring_buffer

        def test_can_create_with_default_args(self):
            ring_buffer = self.ring_buffer()
            self.assertIsInstance(ring_buffer, self.ring_buffer)

        def test_accepts_valid_sizes(self):
            with self.assertRaises(AttributeError):
                self.ring_buffer(size=5)
            self.assertIsInstance(self.ring_buffer(size=4), self.ring_buffer)

        def test_get_methods_are_forbidden(self):
            ring_buffer = self.ring_buffer()
            with self.assertRaises(AttributeError):
                ring_buffer.get(0)
            with self.assertRaises(AttributeError):
                ring_buffer.get_latest()

        def test_cannot_read_ahead_of_cursor(self):
            ring_buffer = self.ring_buffer(size=4)

            ring_buffer.put(0)
            ring_buffer.next()

            with self.assertRaises(SequenceNotFound):
                ring_buffer.next()

            self.assertEqual(ring_buffer._read_cursor, 1)

        def test_cannot_write_over_read_cursor(self):
            ring_buffer = self.ring_buffer(size=4)

            for i in range(4):
                ring_buffer.put(i)

            with self.assertRaises(ReadCursorBlock):
                ring_buffer.put(4)

        def test_sync_read_and_write_with_default_factory(self):
            ring_buffer = self.ring_buffer(size=4)
            for i in range(10):
                ring_buffer.put(i ** 2)
                sequence, res = ring_buffer.next()
                self.assertEqual(res, i ** 2)
                self.assertEqual(sequence, i)

    return TestBlockingRingBuffer


class TestBlockingRingBuffer(construct_test_case(BlockingRingBuffer)):
    pass


class TestBlockingLockedRingBuffer(construct_test_case(BlockingLockedRingBuffer)):
    pass


if __name__ == "__main__":
    unittest.main()

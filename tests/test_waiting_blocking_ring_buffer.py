import unittest
import typing
import threading
import time
from pyring import (
    WaitingBlockingRingBuffer,
    SequenceNotFound,
    ReadCursorBlock,
)


class TestWaitingBlockingRingBuffer(unittest.TestCase):
    def setUp(self):
        self.ring_buffer = WaitingBlockingRingBuffer

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
            ring_buffer.next(timeout=1)

        self.assertEqual(ring_buffer._read_cursor, 1)

    def test_cannot_write_over_read_cursor(self):
        ring_buffer = self.ring_buffer(size=4)

        for i in range(4):
            ring_buffer.put(i)
        with self.assertRaises(ReadCursorBlock):
            ring_buffer.put(4, timeout=1)

    def test_slow_consumer(self):
        ring_buffer = self.ring_buffer(size=2)

        final_val = None

        def worker(r_b: WaitingBlockingRingBuffer):
            nonlocal final_val
            for _ in range(4):
                time.sleep(0.25)
                _, val = r_b.next()
                final_val = val

        thread = threading.Thread(target=worker, args=(ring_buffer,))
        thread.start()

        for i in range(4):
            ring_buffer.put(i)

        thread.join()
        self.assertEqual(final_val, 3)

    def test_slow_producer(self):
        ring_buffer = self.ring_buffer(size=2)

        def worker(r_b: WaitingBlockingRingBuffer):
            for i in range(4):
                r_b.put(i, timeout=1)
                time.sleep(0.25)

        thread = threading.Thread(target=worker, args=(ring_buffer,))
        thread.start()

        final_val = None
        for _ in range(4):
            _, val = ring_buffer.next(timeout=1)
            final_val = val
        thread.join()
        self.assertEqual(final_val, 3)

    def test_sync_read_and_write_with_default_factory(self):
        ring_buffer = self.ring_buffer(size=4)
        for i in range(10):
            ring_buffer.put(i ** 2)
            sequence, res = ring_buffer.next()
            self.assertEqual(res, i ** 2)
            self.assertEqual(sequence, i)


if __name__ == "__main__":
    unittest.main()

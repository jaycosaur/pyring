import unittest
import typing
import threading
import time
from pyring import (
    SingleProducerDisruptor,
    DisruptorSubscriber,
    SequenceNotFound,
    ReadCursorBlock,
)


class TestSingleProducerDisruptor(unittest.TestCase):
    def setUp(self):
        self.disruptor = SingleProducerDisruptor

    def test_can_create_with_default_args(self):
        disruptor = self.disruptor()
        self.assertIsInstance(disruptor, self.disruptor)

    def test_accepts_valid_sizes(self):
        with self.assertRaises(AttributeError):
            self.disruptor(size=5)
        self.assertIsInstance(self.disruptor(size=4), self.disruptor)

    def test_methods_are_forbidden(self):
        disruptor = self.disruptor()
        with self.assertRaises(AttributeError):
            disruptor.get(0)
        with self.assertRaises(AttributeError):
            disruptor.get_latest()
        with self.assertRaises(AttributeError):
            disruptor.next()

    def test_single_sub_cannot_read_ahead_of_cursor(self):
        disruptor = self.disruptor(size=4)
        subscriber = disruptor.subscribe()

        disruptor.put(0)
        subscriber.next()

        with self.assertRaises(SequenceNotFound):
            subscriber.next(timeout=0.05)

        self.assertEqual(subscriber._read_cursor, 1)

    def test_no_sub_can_overwrite_ring(self):
        disruptor = self.disruptor(size=4)
        for i in range(10):
            disruptor.put(i)
        self.assertEqual(disruptor._get_cursor_position(), 10)

    def test_single_sub_cannot_write_over_read_cursor(self):
        disruptor = self.disruptor(size=4)
        subsriber = disruptor.subscribe()

        for i in range(4):
            disruptor.put(i)
        with self.assertRaises(ReadCursorBlock):
            disruptor.put(4, timeout=1)

    def test_slow_consumer(self):
        disruptor = self.disruptor(size=2)
        subscriber = disruptor.subscribe()

        final_val = None

        def worker(subscriber: DisruptorSubscriber):
            nonlocal final_val
            for _ in range(4):
                time.sleep(0.25)
                _, val = subscriber.next()
                final_val = val

        thread = threading.Thread(target=worker, args=(subscriber,))
        thread.start()

        for i in range(4):
            disruptor.put(i, timeout=0.1)

        thread.join()
        self.assertEqual(final_val, 3)

    # def test_slow_producer(self):
    #     ring_buffer = self.ring_buffer(size=2)

    #     def worker(r_b: WaitingBlockingRingBuffer):
    #         for i in range(4):
    #             r_b.put(i, timeout=1)
    #             time.sleep(0.25)

    #     thread = threading.Thread(target=worker, args=(ring_buffer,))
    #     thread.start()

    #     final_val = None
    #     for _ in range(4):
    #         _, val = ring_buffer.next(timeout=1)
    #         final_val = val
    #     thread.join()
    #     self.assertEqual(final_val, 3)

    def test_sync_read_and_write_with_default_factory(self):
        disruptor = self.disruptor(size=4)
        subscriber = disruptor.subscribe()
        for i in range(10):
            disruptor.put(i ** 2, timeout=0.01)
            sequence, res = subscriber.next(timeout=0.01)
            self.assertEqual(res, i ** 2)
            self.assertEqual(sequence, i)


if __name__ == "__main__":
    unittest.main()

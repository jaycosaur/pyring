import unittest
import typing
import threading
import time
import random

from pyring import (
    SingleProducerDisruptor,
    DisruptorSubscriber,
    SequenceNotFound,
    ReadCursorBlock,
)


class TestSingleProducerDisruptor(unittest.TestCase):
    def setUp(self):
        pass

    def test_can_create_with_default_args(self):
        disruptor = SingleProducerDisruptor()
        self.assertIsInstance(disruptor, SingleProducerDisruptor)

    def test_accepts_valid_sizes(self):
        with self.assertRaises(AttributeError):
            SingleProducerDisruptor(size=5)
        self.assertIsInstance(SingleProducerDisruptor(size=4), SingleProducerDisruptor)

    def test_methods_are_forbidden(self):
        disruptor = SingleProducerDisruptor()
        with self.assertRaises(AttributeError):
            disruptor.get(0)
        with self.assertRaises(AttributeError):
            disruptor.get_latest()
        with self.assertRaises(AttributeError):
            disruptor.next()

    def test_single_sub_cannot_read_ahead_of_cursor(self):
        disruptor = SingleProducerDisruptor(size=4)
        subscriber = disruptor.subscribe()

        disruptor.put(0)
        subscriber.next()

        with self.assertRaises(SequenceNotFound):
            subscriber.next(timeout=0.05)

        self.assertEqual(subscriber._read_cursor, 1)

    def test_no_sub_can_overwrite_ring(self):
        disruptor = SingleProducerDisruptor(size=4)
        for i in range(10):
            disruptor.put(i)
        self.assertEqual(disruptor._get_cursor_position(), 10)

    def test_single_sub_cannot_write_over_read_cursor(self):
        disruptor = SingleProducerDisruptor(size=4)
        _subsriber = disruptor.subscribe()

        for i in range(4):
            disruptor.put(i)
        with self.assertRaises(ReadCursorBlock):
            disruptor.put(4, timeout=1)

    def test_unregister_unblocks_producer(self):
        disruptor = SingleProducerDisruptor(size=4)
        subscriber = disruptor.subscribe()

        subscriber.unregister()

        for i in range(5):
            disruptor.put(i, timeout=0.05)

    def test_unregister_single_sub_doesnt_unblock_producer(self):
        disruptor = SingleProducerDisruptor(size=4)
        subscriber = disruptor.subscribe()
        _subscriber_block = disruptor.subscribe()

        subscriber.unregister()

        with self.assertRaises(ReadCursorBlock):
            for i in range(5):
                disruptor.put(i, timeout=0.05)

    def test_sync_read_and_write_with_default_factory(self):
        disruptor = SingleProducerDisruptor(size=2)
        subscriber = disruptor.subscribe()
        for i in range(100):
            disruptor.put(i ** 2, timeout=0.01)
            sequence, res = subscriber.next(timeout=0.01)
            self.assertEqual(res, i ** 2)
            self.assertEqual(sequence, i)

    def test_slow_multi_consumer(self):
        disruptor = SingleProducerDisruptor(
            size=4
        )  # this test doesn't pass when size = 2

        number_of_subs = 4

        subscribers = [disruptor.subscribe() for _ in range(number_of_subs)]

        self.assertEqual(len(disruptor._subscribers), number_of_subs)

        final_values = [None for _ in range(number_of_subs)]

        def worker(idx: int, subscriber: DisruptorSubscriber):
            delay = random.random() / 100
            final_value = None
            for _ in range(4):
                time.sleep(delay)
                _, val = subscriber.next(timeout=0.25)
                final_value = val

            nonlocal final_values
            final_values[idx] = final_value

        threads = [
            threading.Thread(target=worker, args=(idx, subscriber))
            for idx, subscriber in enumerate(subscribers)
        ]

        for thread in threads:
            thread.start()

        for i in range(4):
            disruptor.put(i, timeout=0.25)

        for thread in threads:
            thread.join()

        for idx, thread in enumerate(threads):
            self.assertEqual(final_values[idx], 3)

    def test_slow_producer(self):
        disruptor = SingleProducerDisruptor(size=2)

        def worker(disruptor: SingleProducerDisruptor):
            for i in range(4):
                disruptor.put(i, timeout=1)
                time.sleep(0.25)

        subscriber = disruptor.subscribe()

        thread = threading.Thread(target=worker, args=(disruptor,))
        thread.start()

        final_val = None
        for _ in range(4):
            _, val = subscriber.next(timeout=1)
            final_val = val
        thread.join()
        self.assertEqual(final_val, 3)


if __name__ == "__main__":
    unittest.main()

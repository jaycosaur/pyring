import unittest
import typing
from pyring import (
    RingBuffer,
    LockedRingBuffer,
    Empty,
    SequenceOverwritten,
    SequenceNotFound,
    RingFactory,
)


class CustomSumFactory(RingFactory):
    value: typing.List[int] = []

    def get(self):
        return sum(self.value)

    def set(self, values):
        self.value = values


def construct_test_case(ring_class: RingBuffer):
    class GenericTestRingBuffer(unittest.TestCase):
        def setUp(self):
            self.ring_buffer = ring_class

        def test_can_create_with_default_args(self):
            ring_buffer = self.ring_buffer()
            self.assertIsInstance(ring_buffer, self.ring_buffer)

        def test_accepts_valid_sizes(self):
            with self.assertRaises(AttributeError):
                self.ring_buffer(size=5)
            self.assertIsInstance(self.ring_buffer(size=4), self.ring_buffer)

        def test_cannot_read_ahead_of_cursor(self):
            ring_buffer = self.ring_buffer(size=4)

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
            ring_buffer = self.ring_buffer(size=4)

            # overwrite zeroth element
            for i in range(5):
                ring_buffer.put(i)

            with self.assertRaises(SequenceOverwritten):
                ring_buffer.get(0)

        def test_can_read_and_write_with_default_factory(self):
            ring_buffer = self.ring_buffer(size=4)
            for i in range(10):
                ring_buffer.put(i ** 2)
                sequence, res = ring_buffer.get(i)
                self.assertEqual(res, i ** 2)
                self.assertEqual(sequence, i)

        def test_can_read_and_write_with_custom_factory(self):
            sum_buffer = self.ring_buffer(size=4, factory=CustomSumFactory)

            for i in range(10):
                sum_buffer.put([i, i, i])
                sequence, res = sum_buffer.get(i)
                self.assertEqual(res, i * 3)
                self.assertEqual(sequence, i)

        def test_flush(self):
            ring_buffer = self.ring_buffer()
            print("here1")
            for i in range(100):
                ring_buffer.put(i)

            print("here2")

            self.assertEqual(ring_buffer.get_latest(), (99, 99))

            print("here3")
            ring_buffer.flush()

            print("here4")

            with self.assertRaises(Empty):
                ring_buffer.get_latest()

    return GenericTestRingBuffer


class TestRingBuffer(construct_test_case(RingBuffer)):
    pass


class TestLockedRingBuffer(construct_test_case(LockedRingBuffer)):
    pass


if __name__ == "__main__":
    unittest.main()

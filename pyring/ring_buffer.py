import typing
from threading import Lock
from abc import abstractmethod, ABC
from .ring_factory import RingFactory, SimpleFactory
from .exceptions import SequenceNotFound, Empty, SequenceOverwritten, ReadCursorBlock


class RingBufferInternal:
    def __init__(
        self, size: int = 16, factory: typing.Type[RingFactory] = SimpleFactory,
    ):
        if not size % 2 == 0:
            raise AttributeError("size must be a factor of 2 for efficient arithmetic.")

        self.ring_size: int = size
        self.factory = factory

        self._cursor_position: int = 0  # position of next write
        self.__ring: typing.List[RingFactory] = [factory() for _ in range(size)]

    def _put(self, value) -> int:
        cursor_position = self._cursor_position
        ring_index = self._cursor_position % self.ring_size

        self._cursor_position += 1

        self.__ring[ring_index].set(value)

        return cursor_position

    def _get(self, idx: int) -> typing.Tuple[int, typing.Any]:
        if idx >= self._cursor_position:
            raise SequenceNotFound()

        if idx < self._cursor_position - self.ring_size:
            raise SequenceOverwritten()

        return (idx, self.__ring[idx % self.ring_size].get())

    def _get_latest(self) -> typing.Tuple[int, typing.Any]:
        if self._cursor_position <= 0:
            raise Empty()

        idx = self._cursor_position - 1

        return self._get(idx)

    def _flush(self) -> None:
        self.__ring = [self.factory() for _ in range(self.ring_size)]
        self._cursor_position = 0


class RandomAccessRingBufferMethods(ABC):
    @abstractmethod
    def put(self, value: typing.Any):
        ...

    @abstractmethod
    def get(self, sequence: int):
        ...

    @abstractmethod
    def get_latest(self):
        ...

    @abstractmethod
    def flush(self):
        ...


class SequencedRingBufferMethods(ABC):
    @abstractmethod
    def put(self, value: typing.Any):
        ...

    @abstractmethod
    def next(self):
        ...

    @abstractmethod
    def flush(self):
        ...


class RingBuffer(RingBufferInternal, RandomAccessRingBufferMethods):
    def __init__(
        self, size: int = 16, factory: typing.Type[RingFactory] = SimpleFactory,
    ):
        super().__init__(size=size, factory=factory)

    def put(self, value):
        return super()._put(value)

    def get(self, sequence: int):
        return super()._get(sequence)

    def get_latest(self):
        return super()._get_latest()

    def flush(self):
        return super()._flush()


class LockedRingBuffer(RingBuffer, RandomAccessRingBufferMethods):
    def __init__(
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        lock: Lock = Lock(),
    ):
        super().__init__(size=size, factory=factory)
        self.__lock = lock

    def put(self, value) -> int:
        with self.__lock:
            return super().put(value)

    def get(self, idx: int) -> typing.Tuple[int, typing.Any]:
        with self.__lock:
            return super().get(idx)

    def get_latest(self) -> typing.Tuple[int, typing.Any]:
        with self.__lock:
            return super().get_latest()

    def flush(self) -> None:
        with self.__lock:
            return super().flush()


class BlockingRingBuffer(RingBufferInternal, SequencedRingBufferMethods):
    _read_cursor = 0

    def __init__(
        self, size: int = 16, factory: typing.Type[RingFactory] = SimpleFactory,
    ):
        super().__init__(size=size, factory=factory)

    def put(self, value):
        if (self._cursor_position - self._read_cursor) == self.ring_size:
            raise ReadCursorBlock()
        return super()._put(value)

    def next(self):
        res = super()._get(self._read_cursor)
        self._read_cursor += 1
        return res

    def flush(self):
        super()._flush()
        self._read_cursor = 0


class BlockingLockedRingBuffer(BlockingRingBuffer, SequencedRingBufferMethods):
    def __init__(
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        lock: Lock = Lock(),
    ):
        super().__init__(size=size, factory=factory)
        self.__lock = lock

    def put(self, value):
        with self.__lock:
            return super().put(value)

    def next(self):
        with self.__lock:
            return super().next()

    def flush(self):
        with self.__lock:
            return super().flush()

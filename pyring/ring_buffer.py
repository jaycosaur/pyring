import typing
from threading import Lock, Event, RLock
from multiprocessing import Value, Lock as MpLock
from abc import abstractmethod, ABC
from .ring_factory import RingFactory, SimpleFactory
from .exceptions import SequenceNotFound, Empty, SequenceOverwritten, ReadCursorBlock

T = typing.TypeVar("T", bound=typing.Callable[..., typing.Any])


def run_with_lock(func: T) -> T:
    def with_lock(
        ring_buffer: "RingBufferInternal", *args: typing.Any, **kwargs: typing.Any
    ) -> T:
        if ring_buffer._lock is None:
            return func(ring_buffer, *args, **kwargs)
        with ring_buffer._lock:
            return func(ring_buffer, *args, **kwargs)

    return typing.cast(T, with_lock)


LockLike = typing.Union[Lock, RLock]


class RingBufferInternal:
    def __init__(
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        cursor_position_value: typing.Union[Value, int] = 0,
        lock: typing.Optional[LockLike] = None,
    ):
        if not size % 2 == 0:
            raise AttributeError("size must be a factor of 2 for efficient arithmetic.")

        self.ring_size: int = size
        self.factory = factory

        self.__cursor_position = cursor_position_value  # position of next write
        self.__ring: typing.List[RingFactory] = [factory() for _ in range(size)]
        self._lock = lock

    def _get_cursor_position(self):
        if isinstance(self.__cursor_position, int):
            return self.__cursor_position
        else:
            return self.__cursor_position.value

    def _set_cursor_position(self, value: int):
        if isinstance(self.__cursor_position, int):
            self.__cursor_position = value
        else:
            self.__cursor_position.value = value

    @run_with_lock
    def _put(self, value) -> int:
        cursor_position = self._get_cursor_position()
        ring_index = cursor_position % self.ring_size

        self._set_cursor_position(cursor_position + 1)

        self.__ring[ring_index].set(value)

        return cursor_position

    @run_with_lock
    def _get(self, idx: int) -> typing.Tuple[int, typing.Any]:
        cursor_position = self._get_cursor_position()
        if idx >= cursor_position:
            raise SequenceNotFound()

        if idx < cursor_position - self.ring_size:
            raise SequenceOverwritten()

        return (idx, self.__ring[idx % self.ring_size].get())

    @run_with_lock
    def _get_latest(self) -> typing.Tuple[int, typing.Any]:
        cursor_position = self._get_cursor_position()
        if cursor_position <= 0:
            raise Empty()

        idx = cursor_position - 1

        return self._get(idx)

    @run_with_lock
    def _flush(self) -> None:
        self.__ring = [self.factory() for _ in range(self.ring_size)]
        self._set_cursor_position(0)


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
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        cursor_position_value: typing.Union[Value, int] = 0,
        lock: typing.Optional[LockLike] = None,
    ):
        super().__init__(
            size=size,
            factory=factory,
            cursor_position_value=cursor_position_value,
            lock=lock,
        )

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
        lock: RLock = RLock(),
        cursor_position_value: typing.Union[Value, int] = 0,
    ):
        super().__init__(
            size=size,
            factory=factory,
            cursor_position_value=cursor_position_value,
            lock=lock,
        )
        self.__lock = lock


class BlockingRingBuffer(RingBufferInternal, SequencedRingBufferMethods):
    _read_cursor = 0

    def __init__(
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        cursor_position_value: typing.Union[Value, int] = 0,
        lock: typing.Optional[LockLike] = None,
    ):
        super().__init__(
            size=size,
            factory=factory,
            cursor_position_value=cursor_position_value,
            lock=lock,
        )

    def put(self, value):
        if (self._get_cursor_position() - self._read_cursor) == self.ring_size:
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
        lock: LockLike = RLock(),
        cursor_position_value: typing.Union[Value, int] = 0,
    ):
        super().__init__(
            size=size,
            factory=factory,
            cursor_position_value=cursor_position_value,
            lock=lock,
        )
        self.__lock = lock


class WaitingBlockingRingBuffer(RingBufferInternal, SequencedRingBufferMethods):
    _read_cursor = 0
    _read_cursor_barrier = Event()
    _write_cursor_barrier = Event()

    def __init__(
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        cursor_position_value: typing.Union[Value, int] = 0,
    ):
        super().__init__(
            size=size, factory=factory, cursor_position_value=cursor_position_value
        )

    def put(self, value, timeout: int = None):
        if not self._read_cursor_barrier.is_set():
            self._read_cursor_barrier.set()
        if (self._get_cursor_position() - self._read_cursor) == self.ring_size:
            self._write_cursor_barrier.clear()
            success = self._write_cursor_barrier.wait(timeout=timeout)
            if not success:
                raise ReadCursorBlock()
        return super()._put(value)

    def next(self, timeout: int = None):
        try:
            res = super()._get(self._read_cursor)
        except SequenceNotFound:
            self._read_cursor_barrier.clear()
            success = self._read_cursor_barrier.wait(timeout=timeout)
            if not success:
                raise SequenceNotFound()

        res = super()._get(self._read_cursor)
        # release the write barrier
        if not self._write_cursor_barrier.is_set():
            self._write_cursor_barrier.set()
        self._read_cursor += 1
        return res

    def flush(self):
        super()._flush()
        self._read_cursor = 0

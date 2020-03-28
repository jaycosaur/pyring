from abc import ABC, abstractmethod
import typing
from threading import Lock, Event, RLock
from multiprocessing import Value, Lock as MpLock
from .exceptions import SequenceNotFound, ReadCursorBlock
from .ring_buffer import SimpleFactory, RingBufferInternal, RingFactory


class DisruptorMethods(ABC):
    @abstractmethod
    def put(self, value: typing.Any):
        ...

    @abstractmethod
    def subscribe(self, start_at_latest: bool) -> "DisruptorSubscriber":
        ...


class DisruptorSubscriber:
    def __init__(self, ring_buffer: "SingleProducerDisruptor", read_cursor: int = 0):
        self._read_cursor = read_cursor
        self.__ring_buffer = ring_buffer
        self._read_cursor_barrier = Event()
        self._write_cursor_barrier = Event()

    def next(self, timeout: typing.Optional[float] = None):
        try:
            res = self.__ring_buffer._get(self._read_cursor)
        except SequenceNotFound:
            self._read_cursor_barrier.clear()
            success = self._read_cursor_barrier.wait(timeout=timeout)
            if not success:
                raise SequenceNotFound()

        res = self.__ring_buffer._get(self._read_cursor)

        # release the write barrier
        if not self._write_cursor_barrier.is_set():
            self._write_cursor_barrier.set()

        self._read_cursor += 1
        return res

    def unregister(self) -> None:
        self.__ring_buffer._unregister_subscriber(self)
        if not self._write_cursor_barrier.is_set():
            self._write_cursor_barrier.set()


# this really needs locks
class SingleProducerDisruptor(RingBufferInternal, DisruptorMethods):
    def __init__(
        self,
        size: int = 16,
        factory: typing.Type[RingFactory] = SimpleFactory,
        cursor_position_value: typing.Union[Value, int] = 0,
    ):
        super().__init__(
            size=size, factory=factory, cursor_position_value=cursor_position_value
        )
        self._subscribers: typing.List[DisruptorSubscriber] = []

    def subscribe(self, start_at_latest: bool = False) -> DisruptorSubscriber:
        if start_at_latest:
            subscriber = DisruptorSubscriber(
                ring_buffer=self, read_cursor=self._get_latest()[0]
            )
        else:
            subscriber = DisruptorSubscriber(ring_buffer=self,)
        self._subscribers.append(subscriber)
        return subscriber

    def _unregister_subscriber(self, subscriber_to_remove: DisruptorSubscriber):
        subscriber_index = None
        for sid, subscriber in enumerate(self._subscribers):
            if subscriber is subscriber_to_remove:
                subscriber_index = sid
                break

        if subscriber_index is not None:
            self._subscribers.pop(subscriber_index)

    def put(self, value, timeout: float = None):
        for subscriber in self._subscribers:
            if (
                self._get_cursor_position() - subscriber._read_cursor
            ) == self.ring_size:
                subscriber._write_cursor_barrier.clear()
                success = subscriber._write_cursor_barrier.wait(timeout=timeout)
                if not success:
                    raise ReadCursorBlock()

        result = super()._put(value)

        for subscriber in self._subscribers:
            if (
                subscriber._read_cursor == result
                and not subscriber._read_cursor_barrier.is_set()
            ):
                subscriber._read_cursor_barrier.set()

        return result

import typing
from .ring_factory import RingFactory, SimpleFactory
from .exceptions import SequenceNotFound, Empty, SequenceOverwritten


class RingBuffer:
    def __init__(
        self, size: int = 16, factory: typing.Type[RingFactory] = SimpleFactory
    ):
        if not size % 2 == 0:
            raise AttributeError("size must be a factor of 2 for efficient arithmetic.")

        self.ring_size: int = size
        self.factory = factory

        self.__ring: typing.List[RingFactory] = [factory() for _ in range(size)]
        self.__cursor_position: int = 0  # position of next write

    def put(self, value) -> int:
        cursor_position = self.__cursor_position
        ring_index = self.__cursor_position % self.ring_size

        self.__cursor_position += 1

        self.__ring[ring_index].set(value)

        return cursor_position

    def get(self, idx: int) -> typing.Tuple[int, typing.Any]:
        if idx >= self.__cursor_position:
            raise SequenceNotFound()

        if idx < self.__cursor_position - self.ring_size:
            raise SequenceOverwritten()

        return (idx, self.__ring[idx % self.ring_size].get())

    def get_latest(self) -> typing.Tuple[int, typing.Any]:
        if self.__cursor_position <= 0:
            raise Empty()

        idx = self.__cursor_position - 1

        return (idx, self.__ring[idx % self.ring_size].get())

    def flush(self) -> None:
        self.__ring = [self.factory() for _ in range(self.ring_size)]
        self.__cursor_position = 0

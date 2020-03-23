from abc import ABC, abstractmethod
import typing


class RingFactory(ABC):
    @abstractmethod
    def set(self, value):
        ...

    @abstractmethod
    def get(self):
        ...


class SimpleFactory(RingFactory):
    def __init__(self):
        self.value = None

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class RingBuffer:
    def __init__(
        self, size: int = 16, factory: typing.Type[RingFactory] = SimpleFactory
    ):
        if size % 2 != 0:
            raise AttributeError("size must be a factor of 2 for efficient arithmetic.")

        self.ring_size: int = size
        self.factory = factory

        self.__ring: typing.List[RingFactory] = [factory() for _ in range(size)]
        self.__cursor_position: int = 0

    def put(self, value) -> int:
        cursor_position = self.__cursor_position
        ring_index = self.__cursor_position % self.ring_size

        self.__cursor_position += 1

        self.__ring[ring_index].set(value)

        return cursor_position

    def get(self, idx: int) -> typing.Tuple[int, typing.Any]:
        if idx >= self.__cursor_position:
            raise Exception("has not occured yet")

        if idx < self.__cursor_position - self.ring_size:
            raise Exception("item has already been overwritten")

        return (idx, self.__ring[idx % self.ring_size].get())

    def get_latest(self) -> typing.Tuple[int, typing.Any]:
        if self.__cursor_position <= 0:
            raise Exception("no elements have been added yet!")

        idx = self.__cursor_position - 1

        return (idx, self.__ring[idx % self.ring_size].get())

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

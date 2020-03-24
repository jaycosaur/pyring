"""pyring - A ring buffer implemented in pure python.
  @jaycosaur / https://github.com/jaycosaur/pyring
"""

name = "pyring"

from .ring_factory import RingFactory, SimpleFactory
from .ring_buffer import RingBuffer
from .exceptions import SequenceNotFound, Empty, SequenceOverwritten

__version__ = "0.0.2"

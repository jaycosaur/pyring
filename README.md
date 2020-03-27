# PyRing

<p align="left">
  <img src="https://github.com/jaycosaur/pyring/workflows/Build%20and%20Test/badge.svg">
</p>

A pure python implementation of a ring buffer with optional factory for alternate memory allocation. Variants included are Blocking (with a read cursor) and Locked (all manipulations are secured with a lock) ring buffers.

<p align="center">
  <img width="200" height="200" src="https://github.com/jaycosaur/pyring/blob/master/img/pyring.png">
</p>

You may not call it a ring buffer, they also go by other names like circular buffer, circular queue or cyclic buffer.

## Installation

`python3 -m pip install pyring`

## Usage

Included are several variations of a ring buffer:

1. `RingBuffer` - The most basic, non-blocking ring, supports optional RLocks as constructor argument.
2. `LockedRingBuffer` - The same as `RingBuffer` but secured by a lock (handy for multithread / multiproc)
3. `BlockingRingBuffer` - Extension of `RingBuffer` with a read method `next()` which increments a read cursor and the writer cannot advance past the read cursor
4. `BlockingLockedRingBuffer` - The same as `BlockingRingBuffer` but secured by a lock (handy for multithread / multiproc)
5. `WaitingBlockingRingBuffer` - The same as `BlockingRingBuffer` but calls to next and put block and wait (with optional timeout arg)

### Basic usage with default size and factory

```python
import pyring

# create ring buffer
ring_buffer = pyring.RingBuffer()

# add to ring
ring_buffer.put("Something new!")

# get latest from ring
sequence, value = ring_buffer.get_latest()
print(sequence, value) # 0 Something new!
```

### Custom ring size

```python
import pyring

ring_buffer = pyring.RingBuffer(size=128) # size must be a power of 2
```

### Custom factory

```python
import pyring

# custom factory that takes lists of ints and returns the sum
# must declare the get and set methods
class CustomSumFactory(pyring.RingFactory):
    value: typing.List[int] = []

    def get(self):
        return sum(self.value)

    def set(self, values):
        self.value = values

ring_buffer = pyring.RingBuffer(factory=CustomSumFactory)

ring_buffer.put([1,2,3,4,5])

sequence, value = ring_buffer.get_latest()

print(sequence, value) # 0 15
```

### Multiprocess C-Types Example

The below is a demonstration of using a RingBuffer across multiple processes, this requires firstly a LockedRingBuffer (with a multiproc lock), in addition to a custom cursor_position_value to increment sequence counts across processes.

This is more a demonstration on how flexible this ring buffer implementation can be rather than where you should use it, the below approach would most likely (with caveats on datasize) be better handled with threads reading off the ring buffer and passing messages via queues to worker processes.

```python
import multiprocessing as mp
import time
from pyring import LockedRingBuffer, RingFactory

# using r lock due to the reuse for the cursor_position_value
mp_lock = mp.RLock()

# note if using the same lock it must be recursive lock otherwise you will get deadlocks
cursor_position_value = mp.Value("i", 0, lock=mp_lock)

# using multiproc compatible c-types.
class MultiprocFactory(RingFactory):
    def __init__(self):
        self.value = mp.Value("i")

    def set(self, v: int):
        self.value.value = v

    def get(self):
        return self.value.value


ring_buffer = LockedRingBuffer(
    factory=MultiprocFactory, lock=mp_lock, cursor_position_value=cursor_position_value
)


def worker_routine(worker_ring_buffer: LockedRingBuffer):
    for i in range(10):
        worker_ring_buffer.put(i)


proc = mp.Process(target=worker_routine, args=(ring_buffer,))
proc.start()
time.sleep(0.01)

for i in range(10):
    sequence, value = ring_buffer.get(i)
    print(sequence, value)

proc.join()
```

## Examples of Usage

COMING SOON

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

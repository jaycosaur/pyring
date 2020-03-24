# PyRing

![](https://github.com/jaycosaur/pyring/workflows/Build%20and%20Test/badge.svg)
A pure python implementation of a non-blocking ring buffer with optional factory for alternate memory allocation.

<p align="center">
  <img width="200" height="200" src="https://github.com/jaycosaur/pyring/blob/master/img/pyring.png">
</p>

You may not call it a ring buffer, they also go by other names like circular buffer, circular queue or cyclic buffer.

## Installation

`python3 -m pip install pyring`

## Usage

Basic usage with default size and factory

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

Custom size

```python
import pyring

ring_buffer = pyring.RingBuffer(size=128) # size must be a power of 2
```

Custom factory

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

## Examples of Usage

COMING SOON

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

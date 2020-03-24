import multiprocessing
import pyring


def worker(ring_buffer: pyring.RingBuffer):
    for i in range(10):
        print(ring_buffer.get(i))


class EventFactory(pyring.RingFactory):
    def __init__(self):
        self.value = multiprocessing.Value("d")
        self.lock = multiprocessing.Lock()

    def get(self):
        with self.lock:
            return self.value.value

    def set(self, value):
        with self.lock:
            self.value.value = value


def main():
    ring_buffer = pyring.RingBuffer(factory=EventFactory)
    for i in range(10):
        ring_buffer.put(i)

    proc = multiprocessing.Process(target=worker, args=(ring_buffer,))
    proc.start()
    proc.join()


if __name__ == "__main__":
    main()

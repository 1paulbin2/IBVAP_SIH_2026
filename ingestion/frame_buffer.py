from collections import deque


class FrameBuffer:

    def __init__(self, max_size=10):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)

    def add(self, frame):
        self.buffer.append(frame)

    def get(self):
        if len(self.buffer) == 0:
            return None

        return self.buffer.popleft()

    def size(self):
        return len(self.buffer)

    def clear(self):
        self.buffer.clear()


if __name__ == "__main__":
    buffer = FrameBuffer(max_size=3)

    buffer.add("Frame 1")
    buffer.add("Frame 2")
    buffer.add("Frame 3")

    print("Buffer size:", buffer.size())

    print("Getting:", buffer.get())
    print("Getting:", buffer.get())

    print("Buffer size:", buffer.size())

    buffer.clear()

    print("Buffer size after clear:", buffer.size())
from frame_buffer import FrameBuffer


def test_buffer_add_and_get():
    buffer = FrameBuffer(max_size=3)

    buffer.add("Frame 1")
    buffer.add("Frame 2")

    assert buffer.size() == 2
    assert buffer.get() == "Frame 1"
    assert buffer.get() == "Frame 2"


def test_buffer_max_size():
    buffer = FrameBuffer(max_size=3)

    buffer.add("Frame 1")
    buffer.add("Frame 2")
    buffer.add("Frame 3")
    buffer.add("Frame 4")

    assert buffer.size() == 3
    assert buffer.get() == "Frame 2"


def test_buffer_clear():
    buffer = FrameBuffer(max_size=3)

    buffer.add("Frame 1")
    buffer.add("Frame 2")

    buffer.clear()

    assert buffer.size() == 0


if __name__ == "__main__":
    test_buffer_add_and_get()
    test_buffer_max_size()
    test_buffer_clear()

    print("All FrameBuffer tests passed!")
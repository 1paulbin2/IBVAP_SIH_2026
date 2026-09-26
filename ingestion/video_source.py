import cv2


class VideoSource:

    def __init__(self, source):
        self.source = source
        self.source_type = self.detect_source_type(source)
        self.cap = None

    def detect_source_type(self, source):
        if isinstance(source, str) and source.startswith("rtsp://"):
            return "rtsp"

        return "file"

    def connect(self):
        self.cap = cv2.VideoCapture(self.source)

        if self.cap.isOpened():
            print(f"Video source connected: {self.source}")
            return True

        print(f"ERROR: Could not connect to source: {self.source}")
        return False

    def reconnect(self, max_attempts=3, delay_seconds=2):
        # Reconnect is only for RTSP cameras
        if self.source_type != "rtsp":
            print("Reconnect skipped: source is not RTSP.")
            return False

        # Close the old connection first
        self.release()

        for attempt in range(1, max_attempts + 1):
            print(
                f"Reconnect attempt {attempt}/{max_attempts} "
                f"to: {self.source}"
            )

            if self.connect():
                print("RTSP reconnect successful!")
                return True

            if attempt < max_attempts:
                import time
                time.sleep(delay_seconds)

        print("RTSP reconnect failed after all attempts.")
        return False

    def is_opened(self):
        if self.cap is None:
            return False

        return self.cap.isOpened()

    def read(self):
        if self.cap is None:
            return False, None

        ret, frame = self.cap.read()

        if not ret:
            print(
                f"WARNING: Failed to read frame from source: "
                f"{self.source}"
            )

        return ret, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def get_source(self):
        return self.source

    def get_source_type(self):
        return self.source_type


if __name__ == "__main__":
    # Fake RTSP source for testing reconnect behavior
    test_source = "rtsp://example.com/test"

    video = VideoSource(test_source)

    print(f"Source: {video.get_source()}")
    print(f"Source type: {video.get_source_type()}")

    video.reconnect(max_attempts=3, delay_seconds=1)

    video.release()
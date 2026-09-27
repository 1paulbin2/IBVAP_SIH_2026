from video_source import VideoSource


def test_file_source_detection():
    video = VideoSource("../videos/test_videos.mp4")

    assert video.get_source() == "../videos/test_videos.mp4"
    assert video.get_source_type() == "file"


def test_rtsp_source_detection():
    video = VideoSource("rtsp://example.com/test")

    assert video.get_source() == "rtsp://example.com/test"
    assert video.get_source_type() == "rtsp"


def test_file_connection():
    video = VideoSource("../videos/test_videos.mp4")

    assert video.connect()
    assert video.is_opened()

    video.release()


if __name__ == "__main__":
    test_file_source_detection()
    test_rtsp_source_detection()
    test_file_connection()

    print("All VideoSource tests passed!")
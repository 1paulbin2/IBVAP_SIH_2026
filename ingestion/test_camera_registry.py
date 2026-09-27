from camera_registry import CameraRegistry


def test_add_and_get_camera():
    registry = CameraRegistry()

    registry.add_camera(
        "CAM_001",
        "../videos/test_videos.mp4"
    )

    camera = registry.get_camera("CAM_001")

    assert camera is not None
    assert camera["source"] == "../videos/test_videos.mp4"
    assert camera["status"] == "disconnected"


def test_update_camera_status():
    registry = CameraRegistry()

    registry.add_camera(
        "CAM_001",
        "../videos/test_videos.mp4"
    )

    registry.update_status("CAM_001", "connected")

    assert registry.get_status("CAM_001") == "connected"


def test_remove_camera():
    registry = CameraRegistry()

    registry.add_camera(
        "CAM_001",
        "../videos/test_videos.mp4"
    )

    registry.remove_camera("CAM_001")

    assert registry.get_camera("CAM_001") is None


if __name__ == "__main__":
    test_add_and_get_camera()
    test_update_camera_status()
    test_remove_camera()

    print("All CameraRegistry tests passed!")
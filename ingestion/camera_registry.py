class CameraRegistry:

    def __init__(self):
        self.cameras = {}

    def add_camera(self, camera_id, source):
        self.cameras[camera_id] = {
            "source": source,
            "status": "disconnected"
        }

    def get_camera(self, camera_id):
        return self.cameras.get(camera_id)

    def remove_camera(self, camera_id):
        if camera_id in self.cameras:
            del self.cameras[camera_id]

    def get_all_cameras(self):
        return self.cameras

    def update_status(self, camera_id, status):
        if camera_id in self.cameras:
            self.cameras[camera_id]["status"] = status

    def get_status(self, camera_id):
        camera = self.cameras.get(camera_id)

        if camera:
            return camera["status"]

        return None


if __name__ == "__main__":
    registry = CameraRegistry()

    registry.add_camera(
        "CAM_001",
        "../videos/test_videos.mp4"
    )

    registry.add_camera(
        "CAM_002",
        "RTSP_SOURCE_PLACEHOLDER"
    )

    print("All cameras:")
    print(registry.get_all_cameras())

    print("\nCAM_001:")
    print(registry.get_camera("CAM_001"))

    registry.update_status("CAM_001", "connected")

    print("\nCAM_001 status:")
    print(registry.get_status("CAM_001"))
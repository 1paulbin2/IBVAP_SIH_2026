import cv2
from datetime import datetime

from frame_packet import FramePacket
from video_source import VideoSource
from frame_sampler import FrameSampler
from camera_registry import CameraRegistry
from frame_buffer import FrameBuffer


# Create camera registry
registry = CameraRegistry()

# Register our test camera
registry.add_camera(
    "CAM_001",
    "../videos/test_videos.mp4"
)

# Select camera
camera_id = "CAM_001"

# Get camera information
camera = registry.get_camera(camera_id)

if camera is None:
    print("ERROR: Camera not found.")
    exit()

# Get source path
video_path = camera["source"]

# Create video source
video = VideoSource(video_path)

# Connect to video source
if not video.connect():
    registry.update_status(camera_id, "disconnected")
    print("ERROR: Could not connect to video.")
    exit()

# Camera connected successfully
registry.update_status(camera_id, "connected")

print("Video opened successfully!")
print(f"Camera status: {registry.get_status(camera_id)}")

# Create frame buffer
buffer = FrameBuffer(max_size=10)

# Process every 5th frame
sampler = FrameSampler(sample_every=5)

frame_count = 0


while True:

    # Read frame from video source
    ret, frame = video.read()

    if not ret:
        registry.update_status(camera_id, "ended")
        print("VideoSource could not provide a frame.")
        break

    frame_count += 1

    print(f"Received frame: {frame_count}")

    # Add frame to buffer
    buffer.add(frame)

    # Process every 5th frame
    if sampler.should_process(frame_count):

        buffered_frame = buffer.get()

        if buffered_frame is not None:
            packet = FramePacket(
                camera_id=camera_id,
                timestamp=datetime.now(),
                frame=buffered_frame,
                sequence_number=frame_count,
                source_status=registry.get_status(camera_id)
            )

            print(
                f"FramePacket created for frame: "
                f"{frame_count}"
            )

    # Display the current frame
    cv2.imshow("IBVAP Test Video", frame)

    # Press Q to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


print(f"Total frames received: {frame_count}")
print(f"Final camera status: {registry.get_status(camera_id)}")
print(f"Remaining frames in buffer: {buffer.size()}")

video.release()
cv2.destroyAllWindows()
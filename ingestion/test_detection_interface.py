from datetime import datetime

from frame_packet import FramePacket


def create_test_packet():
    packet = FramePacket(
        camera_id="CAM_001",
        timestamp=datetime.now(),
        frame="test_frame",
        sequence_number=1,
        source_status="connected"
    )

    return packet


if __name__ == "__main__":
    packet = create_test_packet()

    print("Detection interface test")
    print("------------------------")
    print("Camera ID:", packet.camera_id)
    print("Timestamp:", packet.timestamp)
    print("Frame:", packet.frame)
    print("Sequence number:", packet.sequence_number)
    print("Source status:", packet.source_status)
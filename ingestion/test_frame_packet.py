from frame_packet import FramePacket
from datetime import datetime


def test_frame_packet_creation():
    packet = FramePacket(
        camera_id="CAM_001",
        timestamp=datetime.now(),
        frame="test_frame",
        sequence_number=1,
        source_status="connected"
    )

    assert packet.camera_id == "CAM_001"
    assert packet.frame == "test_frame"
    assert packet.sequence_number == 1
    assert packet.source_status == "connected"


if __name__ == "__main__":
    test_frame_packet_creation()
    print("All FramePacket tests passed!")
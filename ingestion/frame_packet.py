from dataclasses import dataclass
from datetime import datetime


@dataclass
class FramePacket:
    camera_id: str
    timestamp: datetime
    frame: object
    sequence_number: int
    source_status: str


if __name__ == "__main__":
    packet = FramePacket(
        camera_id="CAM_001",
        timestamp=datetime.now(),
        frame=None,
        sequence_number=1,
        source_status="connected"
    )

    print(packet)
from backend.app.models.base import Base
from backend.app.models.camera import Camera
from backend.app.models.detection import Detection
from backend.app.models.tracking import Track
from backend.app.models.anpr import ANPRRecord
from backend.app.models.event import Event
from backend.app.models.alert import Alert

__all__ = [
    "Base",
    "Camera",
    "Detection",
    "Track",
    "ANPRRecord",
    "Event",
    "Alert"
]

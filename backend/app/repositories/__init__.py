from backend.app.repositories.camera_repository import CameraRepository
from backend.app.repositories.detection_repository import DetectionRepository
from backend.app.repositories.track_repository import TrackRepository
from backend.app.repositories.anpr_repository import ANPRRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.alert_repository import AlertRepository

__all__ = [
    "CameraRepository",
    "DetectionRepository",
    "TrackRepository",
    "ANPRRepository",
    "EventRepository",
    "AlertRepository"
]

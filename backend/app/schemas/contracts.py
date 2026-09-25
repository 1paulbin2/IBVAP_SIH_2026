from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class FrameSchema(BaseModel):
    camera_id: str
    timestamp: str
    frame_reference: str
    sequence_number: Optional[int] = None

class DetectionSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    camera_id: str
    timestamp: str
    class_name: str = Field(..., alias="class")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    model_version: Optional[str] = None

class TrackingSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    camera_id: str
    track_id: str
    class_name: str = Field(..., alias="class")
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    timestamp: str
    tracking_metadata: Optional[Dict[str, Any]] = None

class ANPRSchema(BaseModel):
    track_id: Optional[str] = None
    vehicle_reference: Optional[str] = None
    plate_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_reference: Optional[str] = None

class EventTypeEnum(str, Enum):
    VIRTUAL_FENCE = "virtual_fence"
    NIGHT_MOVEMENT = "night_movement"
    DWELL_PRESENCE = "dwell_presence"
    SUSPICIOUS_RULE = "suspicious_rule"

class EventSchema(BaseModel):
    event_id: str
    camera_id: str
    timestamp: str
    event_type: str
    object_track: str
    zone_rule: str
    evidence_reference: str

class AlertPriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatusEnum(str, Enum):
    UNREAD = "UNREAD"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class AlertSchema(BaseModel):
    event_id: str
    priority: AlertPriorityEnum
    timestamp: str
    status: AlertStatusEnum
    message: str
    reference: Optional[str] = None

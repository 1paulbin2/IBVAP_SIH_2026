from pydantic import BaseModel
from datetime import datetime


class SecurityEvent(BaseModel):
    event_id: str
    camera_id: str
    event_type: str
    confidence: float
    timestamp: datetime
    location: str
    description: str = ""
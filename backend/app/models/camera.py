from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.detection import Detection
    from backend.app.models.tracking import Track
    from backend.app.models.event import Event

class Camera(Base):
    __tablename__ = "cameras"

    camera_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    stream_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    detections: Mapped[List["Detection"]] = relationship("Detection", back_populates="camera")
    tracks: Mapped[List["Track"]] = relationship("Track", back_populates="camera")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="camera")

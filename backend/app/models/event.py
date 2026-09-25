from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.camera import Camera
    from backend.app.models.alert import Alert

class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.camera_id", ondelete="RESTRICT"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_track: Mapped[str] = mapped_column(String(128), nullable=False)
    zone_rule: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="events")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="event")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('virtual_fence', 'night_movement', 'dwell_presence', 'suspicious_rule')",
            name="check_event_type_valid"
        ),
        Index("idx_events_camera_ts", "camera_id", timestamp.desc()),
        Index("idx_events_type_ts", "event_type", timestamp.desc()),
        Index("idx_events_object_track", "object_track"),
    )

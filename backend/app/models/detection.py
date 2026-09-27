from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any
from sqlalchemy import String, Float, DateTime, BigInteger, ForeignKey, Index, CheckConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.camera import Camera

class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.camera_id", ondelete="RESTRICT"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    class_name: Mapped[str] = mapped_column("class", String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[Any] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="detections")

    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="check_detection_confidence_range"),
        Index("idx_detections_camera_ts", "camera_id", timestamp.desc()),
    )

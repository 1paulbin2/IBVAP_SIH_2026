from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any
from sqlalchemy import String, DateTime, BigInteger, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.camera import Camera

class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.camera_id", ondelete="RESTRICT"), nullable=False)
    track_id: Mapped[str] = mapped_column(String(128), nullable=False)
    class_name: Mapped[str] = mapped_column("class", String(64), nullable=False)
    bbox: Mapped[Any] = mapped_column(JSONB, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tracking_metadata: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="tracks")

    __table_args__ = (
        Index("idx_tracks_camera_track", "camera_id", "track_id"),
        Index("idx_tracks_timestamp", timestamp.desc()),
    )

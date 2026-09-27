from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, BigInteger, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base

class ANPRRecord(Base):
    __tablename__ = "anpr_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    track_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    vehicle_reference: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    plate_text: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="check_anpr_confidence_range"),
        Index("idx_anpr_plate_text", "plate_text"),
        Index("idx_anpr_track_id", "track_id"),
    )

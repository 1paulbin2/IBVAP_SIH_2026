from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, BigInteger, ForeignKey, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.event import Event

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(128), ForeignKey("events.event_id", ondelete="RESTRICT"), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="UNREAD", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="alerts")

    __table_args__ = (
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="check_alert_priority_valid"
        ),
        CheckConstraint(
            "status IN ('UNREAD', 'ACKNOWLEDGED', 'RESOLVED')",
            name="check_alert_status_valid"
        ),
        Index("idx_alerts_status_priority_ts", "status", "priority", timestamp.desc()),
        Index("idx_alerts_event_id", "event_id"),
    )

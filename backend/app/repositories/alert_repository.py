from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.alert import Alert

class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        event_id: str,
        priority: str,
        timestamp: datetime,
        message: str,
        status: str = "UNREAD",
        reference: Optional[str] = None
    ) -> Alert:
        alert = Alert(
            event_id=event_id,
            priority=priority,
            timestamp=timestamp,
            status=status,
            message=message,
            reference=reference
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_by_id(self, alert_id: int) -> Optional[Alert]:
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        event_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Alert]:
        stmt = select(Alert)
        if status is not None:
            stmt = stmt.where(Alert.status == status)
        if priority is not None:
            stmt = stmt.where(Alert.priority == priority)
        if event_id is not None:
            stmt = stmt.where(Alert.event_id == event_id)
        stmt = stmt.order_by(Alert.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, alert_id: int, status: str) -> Optional[Alert]:
        stmt = (
            update(Alert)
            .where(Alert.id == alert_id)
            .values(status=status)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_id(alert_id)

    async def query_recent(
        self,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Sequence[Alert]:
        stmt = select(Alert)
        if status is not None:
            stmt = stmt.where(Alert.status == status)
        stmt = stmt.order_by(Alert.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

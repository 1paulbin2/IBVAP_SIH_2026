from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.models.alert import Alert
from backend.app.services.exceptions import EntityNotFoundError

class AlertService:
    def __init__(self, session: AsyncSession):
        self.alert_repo = AlertRepository(session)
        self.event_repo = EventRepository(session)

    async def create_alert_from_event(
        self,
        event_id: str,
        priority: str,
        timestamp: datetime,
        message: str,
        status: str = "UNREAD",
        reference: Optional[str] = None
    ) -> Alert:
        # Validate that referenced event exists
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            raise EntityNotFoundError(f"Cannot create alert: referenced Event '{event_id}' does not exist.")

        return await self.alert_repo.create(
            event_id=event_id,
            priority=priority,
            timestamp=timestamp,
            message=message,
            status=status,
            reference=reference
        )

    async def get_alert(self, alert_id: int) -> Alert:
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise EntityNotFoundError(f"Alert with ID '{alert_id}' not found.")
        return alert

    async def list_alerts(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        event_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Alert]:
        return await self.alert_repo.list_alerts(
            status=status,
            priority=priority,
            event_id=event_id,
            limit=limit,
            offset=offset
        )

    async def update_alert_status(self, alert_id: int, status: str) -> Alert:
        # Verify alert exists
        await self.get_alert(alert_id)
        updated = await self.alert_repo.update_status(alert_id=alert_id, status=status)
        return updated

    async def get_recent_alerts(
        self,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Sequence[Alert]:
        return await self.alert_repo.query_recent(limit=limit, status=status)

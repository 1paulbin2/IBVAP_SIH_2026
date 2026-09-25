from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.event import Event

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        event_id: str,
        camera_id: str,
        timestamp: datetime,
        event_type: str,
        object_track: str,
        zone_rule: str,
        evidence_reference: str
    ) -> Event:
        event = Event(
            event_id=event_id,
            camera_id=camera_id,
            timestamp=timestamp,
            event_type=event_type,
            object_track=object_track,
            zone_rule=zone_rule,
            evidence_reference=evidence_reference
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_id(self, event_id: str) -> Optional[Event]:
        stmt = select(Event).where(Event.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def query_events(
        self,
        camera_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Event]:
        stmt = select(Event)
        if camera_id is not None:
            stmt = stmt.where(Event.camera_id == camera_id)
        if event_type is not None:
            stmt = stmt.where(Event.event_type == event_type)
        if start_time is not None:
            stmt = stmt.where(Event.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Event.timestamp <= end_time)
        stmt = stmt.order_by(Event.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

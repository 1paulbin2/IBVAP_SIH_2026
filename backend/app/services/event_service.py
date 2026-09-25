from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.event_repository import EventRepository
from backend.app.models.event import Event
from backend.app.services.exceptions import EntityNotFoundError, EntityAlreadyExistsError

class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EventRepository(session)

    async def record_event(
        self,
        event_id: str,
        camera_id: str,
        timestamp: datetime,
        event_type: str,
        object_track: str,
        zone_rule: str,
        evidence_reference: str
    ) -> Event:
        existing = await self.repo.get_by_id(event_id)
        if existing:
            raise EntityAlreadyExistsError(f"Event with ID '{event_id}' already exists.")

        from backend.app.services.camera_service import CameraService
        camera_service = CameraService(self.session)
        await camera_service.get_or_create_camera(camera_id)
        return await self.repo.create(
            event_id=event_id,
            camera_id=camera_id,
            timestamp=timestamp,
            event_type=event_type,
            object_track=object_track,
            zone_rule=zone_rule,
            evidence_reference=evidence_reference
        )

    async def get_event(self, event_id: str) -> Event:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise EntityNotFoundError(f"Event with ID '{event_id}' not found.")
        return event

    async def query_events(
        self,
        camera_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Event]:
        return await self.repo.query_events(
            camera_id=camera_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

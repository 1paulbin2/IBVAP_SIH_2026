from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.anpr_repository import ANPRRepository
from backend.app.models.anpr import ANPRRecord

class ANPRService:
    def __init__(self, session: AsyncSession):
        self.repo = ANPRRepository(session)

    async def ingest_anpr_record(
        self,
        plate_text: str,
        confidence: float,
        track_id: Optional[str] = None,
        vehicle_reference: Optional[str] = None,
        evidence_reference: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> ANPRRecord:
        return await self.repo.create(
            plate_text=plate_text,
            confidence=confidence,
            track_id=track_id,
            vehicle_reference=vehicle_reference,
            evidence_reference=evidence_reference,
            timestamp=timestamp
        )

    async def search_by_plate(self, plate_text: str, limit: int = 50) -> Sequence[ANPRRecord]:
        return await self.repo.query_by_plate_text(plate_text=plate_text, limit=limit)

    async def search_by_track(self, track_id: str) -> Sequence[ANPRRecord]:
        return await self.repo.query_by_track_id(track_id=track_id)

    async def search_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[ANPRRecord]:
        return await self.repo.query_by_time_range(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

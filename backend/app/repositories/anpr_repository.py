from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.anpr import ANPRRecord

class ANPRRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        plate_text: str,
        confidence: float,
        track_id: Optional[str] = None,
        vehicle_reference: Optional[str] = None,
        evidence_reference: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> ANPRRecord:
        kwargs = {
            "plate_text": plate_text,
            "confidence": confidence,
            "track_id": track_id,
            "vehicle_reference": vehicle_reference,
            "evidence_reference": evidence_reference
        }
        if timestamp is not None:
            kwargs["timestamp"] = timestamp

        record = ANPRRecord(**kwargs)
        self.session.add(record)
        await self.session.flush()
        return record

    async def query_by_plate_text(
        self,
        plate_text: str,
        limit: int = 50
    ) -> Sequence[ANPRRecord]:
        stmt = (
            select(ANPRRecord)
            .where(ANPRRecord.plate_text == plate_text)
            .order_by(ANPRRecord.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def query_by_track_id(
        self,
        track_id: str
    ) -> Sequence[ANPRRecord]:
        stmt = (
            select(ANPRRecord)
            .where(ANPRRecord.track_id == track_id)
            .order_by(ANPRRecord.timestamp.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def query_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[ANPRRecord]:
        stmt = (
            select(ANPRRecord)
            .where(ANPRRecord.timestamp >= start_time)
            .where(ANPRRecord.timestamp <= end_time)
            .order_by(ANPRRecord.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

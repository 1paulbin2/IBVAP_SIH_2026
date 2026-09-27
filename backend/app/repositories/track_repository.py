from typing import Sequence, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.tracking import Track

class TrackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        camera_id: str,
        track_id: str,
        class_name: str,
        bbox: Union[Dict[str, Any], list],
        timestamp: datetime,
        tracking_metadata: Optional[Dict[str, Any]] = None
    ) -> Track:
        track = Track(
            camera_id=camera_id,
            track_id=track_id,
            class_name=class_name,
            bbox=bbox,
            timestamp=timestamp,
            tracking_metadata=tracking_metadata
        )
        self.session.add(track)
        await self.session.flush()
        return track

    async def query_tracks(
        self,
        camera_id: Optional[str] = None,
        track_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Track]:
        stmt = select(Track)
        if camera_id is not None:
            stmt = stmt.where(Track.camera_id == camera_id)
        if track_id is not None:
            stmt = stmt.where(Track.track_id == track_id)
        if start_time is not None:
            stmt = stmt.where(Track.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Track.timestamp <= end_time)
        stmt = stmt.order_by(Track.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

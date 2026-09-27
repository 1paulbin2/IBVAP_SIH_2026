from typing import Sequence, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.detection import Detection

class DetectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        camera_id: str,
        timestamp: datetime,
        class_name: str,
        confidence: float,
        bbox: Union[Dict[str, Any], list],
        model_version: Optional[str] = None
    ) -> Detection:
        detection = Detection(
            camera_id=camera_id,
            timestamp=timestamp,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox,
            model_version=model_version
        )
        self.session.add(detection)
        await self.session.flush()
        return detection

    async def query_by_camera_and_time(
        self,
        camera_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Detection]:
        stmt = select(Detection).where(Detection.camera_id == camera_id)
        if start_time is not None:
            stmt = stmt.where(Detection.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Detection.timestamp <= end_time)
        stmt = stmt.order_by(Detection.timestamp.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def query_recent(
        self,
        limit: int = 50,
        camera_id: Optional[str] = None
    ) -> Sequence[Detection]:
        stmt = select(Detection)
        if camera_id is not None:
            stmt = stmt.where(Detection.camera_id == camera_id)
        stmt = stmt.order_by(Detection.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

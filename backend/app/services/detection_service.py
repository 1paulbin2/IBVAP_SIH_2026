from typing import Sequence, Optional, Union, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.detection_repository import DetectionRepository
from backend.app.models.detection import Detection

class DetectionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DetectionRepository(session)

    async def ingest_detection(
        self,
        camera_id: str,
        timestamp: datetime,
        class_name: str,
        confidence: float,
        bbox: Union[Dict[str, Any], list],
        model_version: Optional[str] = None
    ) -> Detection:
        from backend.app.services.camera_service import CameraService
        camera_service = CameraService(self.session)
        await camera_service.get_or_create_camera(camera_id)

        return await self.repo.create(
            camera_id=camera_id,
            timestamp=timestamp,
            class_name=class_name,
            confidence=confidence,
            bbox=bbox,
            model_version=model_version
        )

    async def query_detections(
        self,
        camera_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Detection]:
        return await self.repo.query_by_camera_and_time(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

    async def get_recent_detections(
        self,
        limit: int = 50,
        camera_id: Optional[str] = None
    ) -> Sequence[Detection]:
        return await self.repo.query_recent(limit=limit, camera_id=camera_id)

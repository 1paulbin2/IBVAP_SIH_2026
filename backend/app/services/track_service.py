from typing import Sequence, Optional, Union, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.track_repository import TrackRepository
from backend.app.models.tracking import Track

class TrackService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TrackRepository(session)

    async def ingest_track(
        self,
        camera_id: str,
        track_id: str,
        class_name: str,
        bbox: Union[Dict[str, Any], list],
        timestamp: datetime,
        tracking_metadata: Optional[Dict[str, Any]] = None
    ) -> Track:
        from backend.app.services.camera_service import CameraService
        camera_service = CameraService(self.session)
        await camera_service.get_or_create_camera(camera_id)

        return await self.repo.create(
            camera_id=camera_id,
            track_id=track_id,
            class_name=class_name,
            bbox=bbox,
            timestamp=timestamp,
            tracking_metadata=tracking_metadata
        )

    async def query_tracks(
        self,
        camera_id: Optional[str] = None,
        track_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Track]:
        return await self.repo.query_tracks(
            camera_id=camera_id,
            track_id=track_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

from typing import Sequence, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.camera import Camera

class CameraRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        camera_id: str,
        name: str,
        location: Optional[str] = None,
        stream_url: Optional[str] = None,
        is_active: bool = True
    ) -> Camera:
        camera = Camera(
            camera_id=camera_id,
            name=name,
            location=location,
            stream_url=stream_url,
            is_active=is_active
        )
        self.session.add(camera)
        await self.session.flush()
        return camera

    async def get_by_id(self, camera_id: str) -> Optional[Camera]:
        stmt = select(Camera).where(Camera.camera_id == camera_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        is_active_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Camera]:
        stmt = select(Camera)
        if is_active_only:
            stmt = stmt.where(Camera.is_active.is_(True))
        stmt = stmt.order_by(Camera.camera_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_active_status(self, camera_id: str, is_active: bool) -> Optional[Camera]:
        stmt = (
            update(Camera)
            .where(Camera.camera_id == camera_id)
            .values(is_active=is_active)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_id(camera_id)

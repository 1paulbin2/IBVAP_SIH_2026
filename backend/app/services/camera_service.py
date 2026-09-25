from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.camera_repository import CameraRepository
from backend.app.models.camera import Camera
from backend.app.services.exceptions import EntityNotFoundError, EntityAlreadyExistsError

class CameraService:
    def __init__(self, session: AsyncSession):
        self.repo = CameraRepository(session)

    async def register_camera(
        self,
        camera_id: str,
        name: str,
        location: Optional[str] = None,
        stream_url: Optional[str] = None,
        is_active: bool = True
    ) -> Camera:
        existing = await self.repo.get_by_id(camera_id)
        if existing:
            raise EntityAlreadyExistsError(f"Camera with ID '{camera_id}' already exists.")
        return await self.repo.create(
            camera_id=camera_id,
            name=name,
            location=location,
            stream_url=stream_url,
            is_active=is_active
        )

    async def get_or_create_camera(
        self,
        camera_id: str,
        name: Optional[str] = None,
        location: Optional[str] = None
    ) -> Camera:
        camera = await self.repo.get_by_id(camera_id)
        if not camera:
            camera_name = name or f"Auto-created {camera_id}"
            camera = await self.repo.create(
                camera_id=camera_id,
                name=camera_name,
                location=location,
                is_active=True
            )
        return camera

    async def get_camera(self, camera_id: str) -> Camera:
        camera = await self.repo.get_by_id(camera_id)
        if not camera:
            raise EntityNotFoundError(f"Camera with ID '{camera_id}' not found.")
        return camera

    async def list_cameras(
        self,
        is_active_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Camera]:
        return await self.repo.list_all(is_active_only=is_active_only, limit=limit, offset=offset)

    async def set_camera_active_status(self, camera_id: str, is_active: bool) -> Camera:
        # Check existence first
        await self.get_camera(camera_id)
        updated = await self.repo.update_active_status(camera_id=camera_id, is_active=is_active)
        return updated

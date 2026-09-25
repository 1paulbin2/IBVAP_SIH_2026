import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories import (
    CameraRepository,
    DetectionRepository,
    TrackRepository,
    ANPRRepository,
    EventRepository,
    AlertRepository
)
from backend.app.models import Camera, Detection, Track, ANPRRecord, Event, Alert


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
async def test_camera_repository_create_and_update(mock_session):
    repo = CameraRepository(mock_session)
    cam = await repo.create(
        camera_id="cam_001",
        name="Main Gate Camera",
        location="North Gate",
        stream_url="rtsp://stream.local/live"
    )
    assert cam.camera_id == "cam_001"
    assert cam.is_active is True
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_detection_repository_create(mock_session):
    repo = DetectionRepository(mock_session)
    now = datetime.now(timezone.utc)
    det = await repo.create(
        camera_id="cam_001",
        timestamp=now,
        class_name="person",
        confidence=0.95,
        bbox=[10, 20, 100, 200],
        model_version="v1.0"
    )
    assert det.camera_id == "cam_001"
    assert det.class_name == "person"
    assert det.confidence == 0.95
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_track_repository_create(mock_session):
    repo = TrackRepository(mock_session)
    now = datetime.now(timezone.utc)
    trk = await repo.create(
        camera_id="cam_001",
        track_id="trk_123",
        class_name="vehicle",
        bbox=[5, 5, 50, 50],
        timestamp=now,
        tracking_metadata={"speed": 30}
    )
    assert trk.track_id == "trk_123"
    assert trk.class_name == "vehicle"
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_anpr_repository_create(mock_session):
    repo = ANPRRepository(mock_session)
    now = datetime.now(timezone.utc)
    rec = await repo.create(
        plate_text="DL01AB1234",
        confidence=0.99,
        track_id="trk_123",
        timestamp=now
    )
    assert rec.plate_text == "DL01AB1234"
    assert rec.confidence == 0.99
    assert rec.track_id == "trk_123"
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_event_repository_create(mock_session):
    repo = EventRepository(mock_session)
    now = datetime.now(timezone.utc)
    evt = await repo.create(
        event_id="evt_001",
        camera_id="cam_001",
        timestamp=now,
        event_type="virtual_fence",
        object_track="trk_123",
        zone_rule="zone_alpha",
        evidence_reference="http://evidence.local/evt_001.mp4"
    )
    assert evt.event_id == "evt_001"
    assert evt.event_type == "virtual_fence"
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_alert_repository_create(mock_session):
    repo = AlertRepository(mock_session)
    now = datetime.now(timezone.utc)
    alt = await repo.create(
        event_id="evt_001",
        priority="HIGH",
        timestamp=now,
        message="Fence breach detected"
    )
    assert alt.event_id == "evt_001"
    assert alt.priority == "HIGH"
    assert alt.status == "UNREAD"
    mock_session.add.assert_called_once()

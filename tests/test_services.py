import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from backend.app.services import (
    CameraService,
    DetectionService,
    TrackService,
    ANPRService,
    EventService,
    AlertService,
    EntityNotFoundError,
    EntityAlreadyExistsError,
)
from backend.app.models import Camera, Detection, Track, ANPRRecord, Event, Alert


@pytest.fixture
def mock_session():
    return AsyncMock()


# --- CameraService Tests ---

@pytest.mark.asyncio
async def test_camera_service_register_success(mock_session):
    service = CameraService(mock_session)
    with patch.object(service.repo, "get_by_id", new_callable=AsyncMock, return_value=None), \
         patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create:
        
        mock_create.return_value = Camera(camera_id="cam_001", name="Gate 1")
        result = await service.register_camera("cam_001", "Gate 1")
        assert result.camera_id == "cam_001"
        mock_create.assert_called_once_with(
            camera_id="cam_001",
            name="Gate 1",
            location=None,
            stream_url=None,
            is_active=True
        )


@pytest.mark.asyncio
async def test_camera_service_register_duplicate_raises(mock_session):
    service = CameraService(mock_session)
    with patch.object(service.repo, "get_by_id", new_callable=AsyncMock, return_value=Camera(camera_id="cam_001", name="Gate 1")):
        with pytest.raises(EntityAlreadyExistsError):
            await service.register_camera("cam_001", "Gate 1")


@pytest.mark.asyncio
async def test_camera_service_get_not_found(mock_session):
    service = CameraService(mock_session)
    with patch.object(service.repo, "get_by_id", new_callable=AsyncMock, return_value=None):
        with pytest.raises(EntityNotFoundError):
            await service.get_camera("cam_missing")


# --- DetectionService Tests ---

@pytest.mark.asyncio
async def test_detection_service_ingest(mock_session):
    service = DetectionService(mock_session)
    now = datetime.now(timezone.utc)
    with patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = Detection(camera_id="cam_001", class_name="person")
        det = await service.ingest_detection("cam_001", now, "person", 0.9, [0, 0, 10, 10])
        assert det.camera_id == "cam_001"
        mock_create.assert_called_once()


# --- TrackService Tests ---

@pytest.mark.asyncio
async def test_track_service_ingest(mock_session):
    service = TrackService(mock_session)
    now = datetime.now(timezone.utc)
    with patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = Track(track_id="trk_1", class_name="vehicle")
        trk = await service.ingest_track("cam_001", "trk_1", "vehicle", [0, 0, 10, 10], now)
        assert trk.track_id == "trk_1"
        mock_create.assert_called_once()


# --- ANPRService Tests ---

@pytest.mark.asyncio
async def test_anpr_service_ingest_and_search(mock_session):
    service = ANPRService(mock_session)
    with patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create, \
         patch.object(service.repo, "query_by_plate_text", new_callable=AsyncMock) as mock_query:
        
        mock_create.return_value = ANPRRecord(plate_text="KA01AB1234", confidence=0.98)
        mock_query.return_value = [ANPRRecord(plate_text="KA01AB1234", confidence=0.98)]

        res = await service.ingest_anpr_record("KA01AB1234", 0.98)
        assert res.plate_text == "KA01AB1234"

        search_res = await service.search_by_plate("KA01AB1234")
        assert len(search_res) == 1


# --- EventService Tests ---

@pytest.mark.asyncio
async def test_event_service_record_and_get(mock_session):
    service = EventService(mock_session)
    now = datetime.now(timezone.utc)
    with patch.object(service.repo, "get_by_id", new_callable=AsyncMock, return_value=None), \
         patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create:
        
        mock_create.return_value = Event(event_id="evt_01", event_type="virtual_fence")
        evt = await service.record_event("evt_01", "cam_01", now, "virtual_fence", "trk_1", "zone_a", "ref")
        assert evt.event_id == "evt_01"


# --- AlertService Tests ---

@pytest.mark.asyncio
async def test_alert_service_create_from_event_valid(mock_session):
    service = AlertService(mock_session)
    now = datetime.now(timezone.utc)
    with patch.object(service.event_repo, "get_by_id", new_callable=AsyncMock, return_value=Event(event_id="evt_01")), \
         patch.object(service.alert_repo, "create", new_callable=AsyncMock) as mock_create:
        
        mock_create.return_value = Alert(event_id="evt_01", priority="HIGH", message="Warning")
        alt = await service.create_alert_from_event("evt_01", "HIGH", now, "Warning")
        assert alt.event_id == "evt_01"


@pytest.mark.asyncio
async def test_alert_service_create_from_missing_event_raises(mock_session):
    service = AlertService(mock_session)
    now = datetime.now(timezone.utc)
    with patch.object(service.event_repo, "get_by_id", new_callable=AsyncMock, return_value=None):
        with pytest.raises(EntityNotFoundError):
            await service.create_alert_from_event("evt_missing", "HIGH", now, "Warning")

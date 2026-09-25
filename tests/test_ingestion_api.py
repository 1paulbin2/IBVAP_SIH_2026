import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.services.mock_feed_service import MockFeedService
from backend.app.services.exceptions import EntityNotFoundError, EntityAlreadyExistsError

# Override get_db dependency for unit testing FastAPI endpoints without live DB
async def override_get_db():
    mock_session = AsyncMock()
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ingest_frame_endpoint():
    sample = MockFeedService.get_frames()[0]
    response = client.post("/api/v1/ingest/frame", json=sample)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "Frame ingested"


@patch("backend.app.api.v1.endpoints.ingestion.DetectionService")
def test_ingest_detection_endpoint_success(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_det = MagicMock()
    mock_det.id = 1
    mock_det.camera_id = "CAM_BORDER_01"
    mock_det.class_name = "human"
    mock_det.confidence = 0.94
    mock_det.bbox = [120.5, 200.0, 45.0, 110.0]
    mock_det.model_version = "v1.2.0"
    mock_service.ingest_detection.return_value = mock_det

    sample = MockFeedService.get_detections()[0]
    response = client.post("/api/v1/ingest/detection", json=sample)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["class"] == "human"


@patch("backend.app.api.v1.endpoints.ingestion.TrackService")
def test_ingest_tracking_endpoint_success(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_trk = MagicMock()
    mock_trk.id = 1
    mock_trk.camera_id = "CAM_BORDER_01"
    mock_trk.track_id = "TRK_88492"
    mock_trk.class_name = "human"
    mock_trk.bbox = [122.0, 202.0, 45.0, 110.0]
    mock_trk.tracking_metadata = {"velocity_x": 0.5}
    mock_service.ingest_track.return_value = mock_trk

    sample = MockFeedService.get_tracks()[0]
    response = client.post("/api/v1/ingest/tracking", json=sample)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["class"] == "human"


@patch("backend.app.api.v1.endpoints.ingestion.ANPRService")
def test_ingest_anpr_endpoint_success(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_anpr = MagicMock()
    mock_anpr.id = 1
    mock_anpr.track_id = "TRK_99120"
    mock_anpr.vehicle_reference = "/ref/veh.jpg"
    mock_anpr.plate_text = "JK02AB1234"
    mock_anpr.confidence = 0.98
    mock_anpr.evidence_reference = "/ref/plate.jpg"
    mock_service.ingest_anpr_record.return_value = mock_anpr

    sample = MockFeedService.get_anpr_records()[0]
    response = client.post("/api/v1/ingest/anpr", json=sample)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["plate_text"] == "JK02AB1234"


@patch("backend.app.api.v1.endpoints.ingestion.EventService")
def test_ingest_event_endpoint_success(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_evt = MagicMock()
    mock_evt.event_id = "EVT_10092"
    mock_evt.camera_id = "CAM_BORDER_01"
    mock_evt.event_type = "virtual_fence"
    mock_evt.object_track = "TRK_88492"
    mock_evt.zone_rule = "ZONE_NORTH_PERIMETER"
    mock_evt.evidence_reference = "/ref/evt.mp4"
    mock_service.record_event.return_value = mock_evt

    sample = MockFeedService.get_events()[0]
    response = client.post("/api/v1/ingest/event", json=sample)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["event_id"] == "EVT_10092"


@patch("backend.app.api.v1.endpoints.ingestion.AlertService")
def test_ingest_alert_endpoint_success(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_alt = MagicMock()
    mock_alt.id = 1
    mock_alt.event_id = "EVT_10092"
    mock_alt.priority = "HIGH"
    mock_alt.status = "UNREAD"
    mock_alt.message = "Fence breach"
    mock_alt.reference = "/ref/evt.mp4"
    mock_service.create_alert_from_event.return_value = mock_alt

    sample = MockFeedService.get_alerts()[0]
    response = client.post("/api/v1/ingest/alert", json=sample)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["event_id"] == "EVT_10092"


@patch("backend.app.api.v1.endpoints.ingestion.AlertService")
def test_ingest_alert_event_not_found_returns_404(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_service.create_alert_from_event.side_effect = EntityNotFoundError("Referenced event missing")

    sample = MockFeedService.get_alerts()[0]
    response = client.post("/api/v1/ingest/alert", json=sample)
    assert response.status_code == 404
    assert "Referenced event missing" in response.json()["detail"]


@patch("backend.app.api.v1.endpoints.ingestion.EventService")
def test_ingest_event_duplicate_returns_409(mock_service_cls):
    mock_service = AsyncMock()
    mock_service_cls.return_value = mock_service
    mock_service.record_event.side_effect = EntityAlreadyExistsError("Event EVT_10092 already exists")

    sample = MockFeedService.get_events()[0]
    response = client.post("/api/v1/ingest/event", json=sample)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_ingest_detection_validation_error():
    invalid_sample = {
        "camera_id": "CAM_BORDER_01",
        "timestamp": "2026-09-24T21:00:01Z",
        "class": "human",
        "confidence": 1.5,  # Invalid confidence > 1.0
        "bbox": [0, 0, 10, 10]
    }
    response = client.post("/api/v1/ingest/detection", json=invalid_sample)
    assert response.status_code == 422

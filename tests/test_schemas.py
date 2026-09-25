import json
from pathlib import Path
import jsonschema
from backend.app.schemas.contracts import (
    FrameSchema,
    DetectionSchema,
    TrackingSchema,
    ANPRSchema,
    EventSchema,
    AlertSchema
)

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "shared" / "schemas"
MOCK_DIR = BASE_DIR / "mock_data"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_canonical_frame_schema():
    schema = load_json(SCHEMAS_DIR / "frame_schema.json")
    mock = load_json(MOCK_DIR / "sample_frames.json")[0]
    jsonschema.validate(instance=mock, schema=schema)
    parsed = FrameSchema(**mock)
    assert parsed.camera_id == "CAM_BORDER_01"

def test_canonical_detection_schema():
    schema = load_json(SCHEMAS_DIR / "detection_schema.json")
    mock = load_json(MOCK_DIR / "sample_detections.json")[0]
    jsonschema.validate(instance=mock, schema=schema)
    parsed = DetectionSchema(**mock)
    assert parsed.class_name == "human"

def test_canonical_tracking_schema():
    schema = load_json(SCHEMAS_DIR / "tracking_schema.json")
    mock = load_json(MOCK_DIR / "sample_tracks.json")[0]
    jsonschema.validate(instance=mock, schema=schema)
    parsed = TrackingSchema(**mock)
    assert parsed.track_id == "TRK_88492"

def test_canonical_anpr_schema():
    schema = load_json(SCHEMAS_DIR / "anpr_schema.json")
    mock = load_json(MOCK_DIR / "sample_anpr.json")[0]
    jsonschema.validate(instance=mock, schema=schema)
    parsed = ANPRSchema(**mock)
    assert parsed.plate_text == "JK02AB1234"

def test_canonical_event_schema():
    schema = load_json(SCHEMAS_DIR / "event_schema.json")
    mock = load_json(MOCK_DIR / "sample_events.json")[0]
    jsonschema.validate(instance=mock, schema=schema)
    parsed = EventSchema(**mock)
    assert parsed.event_type == "virtual_fence"

def test_canonical_alert_schema():
    schema = load_json(SCHEMAS_DIR / "alert_schema.json")
    mock = load_json(MOCK_DIR / "sample_alerts.json")[0]
    jsonschema.validate(instance=mock, schema=schema)
    parsed = AlertSchema(**mock)
    assert parsed.priority.value == "HIGH"

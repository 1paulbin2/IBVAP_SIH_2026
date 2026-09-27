"""
Unit tests for shared data contracts, canonical JSON schemas,
detection, tracking, and ANPR outputs.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import jsonschema
from pydantic import ValidationError

from schemas.detection import BoundingBox, DetectionRecord, FrameDetections
from schemas.tracking import (
    TrackedObject,
    TrackState,
    TrajectoryPoint,
    TrackingBatch,
)
from schemas.anpr import (
    PlateRecord,
    PlateStandard,
    PlateValidationStatus,
    EvidenceReference,
)
from schemas.pipeline_output import PipelineFrameResult

from backend.app.schemas.contracts import (
    FrameSchema,
    DetectionSchema,
    TrackingSchema,
    ANPRSchema,
    EventSchema,
    AlertSchema,
)


# ---------------------------------------------------------------------------
# Person 2/3 detection, tracking, and ANPR model tests
# ---------------------------------------------------------------------------

def test_bounding_box_valid():
    box = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=120.0)
    assert box.width == 100.0
    assert box.height == 100.0
    assert box.area == 10000.0
    assert box.aspect_ratio == 1.0
    assert box.center == (60.0, 70.0)


def test_bounding_box_invalid_dimensions():
    with pytest.raises(ValidationError):
        BoundingBox(x1=50.0, y1=20.0, x2=40.0, y2=100.0)

    with pytest.raises(ValidationError):
        BoundingBox(x1=10.0, y1=100.0, x2=50.0, y2=80.0)


def test_bounding_box_iou_and_contains():
    box1 = BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
    box2 = BoundingBox(x1=5.0, y1=0.0, x2=15.0, y2=10.0)

    assert abs(box1.iou(box2) - (1.0 / 3.0)) < 1e-4

    inner_box = BoundingBox(x1=2.0, y1=2.0, x2=8.0, y2=8.0)
    assert box1.contains(inner_box)
    assert not inner_box.contains(box1)


def test_frame_detections_filtering(sample_bbox):
    car_det = DetectionRecord(
        detection_id="c1",
        class_name="car",
        confidence=0.9,
        bounding_box=sample_bbox,
    )
    plate_det = DetectionRecord(
        detection_id="p1",
        class_name="license_plate",
        confidence=0.85,
        bounding_box=sample_bbox,
    )

    fd = FrameDetections(
        camera_id="cam1",
        frame_sequence_number=1,
        detections=[car_det, plate_det],
    )

    assert len(fd.vehicle_detections) == 1
    assert fd.vehicle_detections[0].detection_id == "c1"
    assert len(fd.plate_detections) == 1
    assert fd.plate_detections[0].detection_id == "p1"


def test_tracked_object_schema(sample_bbox):
    tp1 = TrajectoryPoint(
        frame_sequence_number=1,
        timestamp=datetime.now(timezone.utc),
        center_x=175.0,
        center_y=225.0,
        bounding_box=sample_bbox,
    )
    tp2 = TrajectoryPoint(
        frame_sequence_number=2,
        timestamp=datetime.now(timezone.utc),
        center_x=195.0,
        center_y=235.0,
        bounding_box=sample_bbox,
    )

    track = TrackedObject(
        track_id=1,
        object_class="car",
        bounding_box=sample_bbox,
        confidence=0.91,
        state=TrackState.CONFIRMED,
        trajectory=[tp1, tp2],
    )

    assert track.track_id == 1
    assert track.is_confirmed
    assert track.trajectory_length == 2
    assert abs(track.total_distance_traveled() - (500 ** 0.5)) < 1e-3


def test_plate_record_schema(sample_bbox):
    ev = EvidenceReference(
        evidence_id="ev_001",
        camera_id="cam1",
        frame_sequence_number=10,
        timestamp=datetime.now(timezone.utc),
        vehicle_track_id=1,
        plate_bounding_box=sample_bbox,
    )

    pr = PlateRecord(
        plate_text="DL01AB1234",
        raw_text="DL01AB1234",
        plate_confidence=0.95,
        vehicle_track_id=1,
        evidence_reference=ev,
        is_valid_format=True,
        validation_status=PlateValidationStatus.VALID,
        standard=PlateStandard.STANDARD_PRIVATE,
        state_code="DL",
        district_code="01",
        series="AB",
        registration_number="1234",
    )

    assert pr.is_readable
    assert pr.state_code == "DL"
    assert pr.evidence_reference.evidence_id == "ev_001"


def test_pipeline_frame_result():
    res = PipelineFrameResult(
        camera_id="cam_main",
        frame_sequence_number=5,
        tracked_objects=[],
        plate_records=[],
        metrics={"tracking_ms": 1.2, "anpr_ms": 3.4},
    )

    assert res.camera_id == "cam_main"
    assert res.metrics["tracking_ms"] == 1.2


# ---------------------------------------------------------------------------
# Backend canonical JSON schema + contract tests
# ---------------------------------------------------------------------------

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

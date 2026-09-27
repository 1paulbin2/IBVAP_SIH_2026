"""
Unit tests for data contracts and schemas (Person 2 detection interface and Person 3 tracking/ANPR outputs).
"""

from datetime import datetime, timezone
import numpy as np
import pytest
from pydantic import ValidationError

from schemas.detection import BoundingBox, DetectionRecord, FrameDetections
from schemas.tracking import TrackedObject, TrackState, TrajectoryPoint, TrackingBatch
from schemas.anpr import PlateRecord, PlateStandard, PlateValidationStatus, EvidenceReference
from schemas.pipeline_output import PipelineFrameResult


def test_bounding_box_valid():
    box = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=120.0)
    assert box.width == 100.0
    assert box.height == 100.0
    assert box.area == 10000.0
    assert box.aspect_ratio == 1.0
    assert box.center == (60.0, 70.0)


def test_bounding_box_invalid_dimensions():
    with pytest.raises(ValidationError):
        # x2 <= x1 is invalid
        BoundingBox(x1=50.0, y1=20.0, x2=40.0, y2=100.0)

    with pytest.raises(ValidationError):
        # y2 <= y1 is invalid
        BoundingBox(x1=10.0, y1=100.0, x2=50.0, y2=80.0)


def test_bounding_box_iou_and_contains():
    box1 = BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
    box2 = BoundingBox(x1=5.0, y1=0.0, x2=15.0, y2=10.0)
    # Intersection is [5, 0, 10, 10] -> area 50
    # Union is 100 + 100 - 50 = 150
    # IoU = 50 / 150 = 1/3
    assert abs(box1.iou(box2) - (1.0 / 3.0)) < 1e-4

    inner_box = BoundingBox(x1=2.0, y1=2.0, x2=8.0, y2=8.0)
    assert box1.contains(inner_box)
    assert not inner_box.contains(box1)


def test_frame_detections_filtering(sample_bbox):
    car_det = DetectionRecord(
        detection_id="c1", class_name="car", confidence=0.9, bounding_box=sample_bbox
    )
    plate_det = DetectionRecord(
        detection_id="p1", class_name="license_plate", confidence=0.85, bounding_box=sample_bbox
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
    # Distance between (175, 225) and (195, 235) = sqrt(20^2 + 10^2) = sqrt(500) ~= 22.36
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

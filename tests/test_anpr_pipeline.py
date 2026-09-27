"""
Integration tests for the unified ANPR Pipeline and downstream contract adherence.
Fulfills Definition of DONE:
- Outputs follow shared schemas.
- Tracker & ANPR accept both real and mock detections.
- ANPR pipeline handles expected plate examples and documents limitations.
"""

from datetime import datetime, timezone
import os
import cv2
import numpy as np
import pytest

from schemas.detection import BoundingBox, DetectionRecord, FrameDetections
from schemas.tracking import TrackState
from schemas.anpr import PlateValidationStatus
from schemas.pipeline_output import PipelineFrameResult
from tracking.byte_tracker import ByteTracker
from anpr.pipeline import ANPRPipeline
from anpr.ocr_engine import MockOCREngine
from test_data.generate_test_assets import create_synthetic_plate_image


def test_pipeline_with_mock_detections():
    """Verify ANPR pipeline handles mock detections without raw image arrays."""
    tracker = ByteTracker(min_hits=1)
    pipeline = ANPRPipeline()

    car_box = BoundingBox(x1=100.0, y1=100.0, x2=400.0, y2=400.0)
    plate_box = BoundingBox(x1=200.0, y1=300.0, x2=320.0, y2=350.0)

    car_det = DetectionRecord(
        detection_id="d_car",
        class_name="car",
        confidence=0.92,
        bounding_box=car_box,
    )
    plate_det = DetectionRecord(
        detection_id="d_plate",
        class_name="license_plate",
        confidence=0.89,
        bounding_box=plate_box,
        metadata={"mock_plate_text": "MH12DE1433"},
    )

    fd = FrameDetections(
        camera_id="cam_mock_01",
        frame_sequence_number=1,
        detections=[car_det, plate_det],
        frame=None,  # No raw frame pixels
    )

    # 1. Tracking
    tracks = tracker.update(fd)
    assert len(tracks) == 1
    car_track = tracks[0]

    # 2. ANPR
    plates = pipeline.process(
        frame=None,
        frame_sequence_number=1,
        timestamp=fd.timestamp,
        camera_id=fd.camera_id,
        tracks=tracks,
        detections=fd.detections,
    )

    assert len(plates) == 1
    plate = plates[0]
    assert plate.plate_text == "MH12DE1433"
    assert plate.is_valid_format is True
    assert plate.vehicle_track_id == car_track.track_id
    assert plate.evidence_reference is not None
    assert plate.evidence_reference.vehicle_track_id == car_track.track_id
    # Track should be enriched with consensus plate
    assert car_track.associated_plate_text == "MH12DE1433"


def test_pipeline_with_real_frame_and_synthetic_vehicle():
    """Verify ANPR pipeline on a synthetic frame with embedded plate."""
    mock_ocr = MockOCREngine()
    mock_ocr.set_default_response("DL01AB1234", 0.96)

    tracker = ByteTracker(min_hits=1)
    pipeline = ANPRPipeline(ocr_engine=mock_ocr)

    # Build synthetic frame
    frame = np.full((600, 800, 3), 120, dtype=np.uint8)
    plate_crop = create_synthetic_plate_image("DL01AB1234", width=140, height=45)
    # Paste plate onto frame at [350:395, 250:390]
    frame[350:395, 250:390] = plate_crop

    car_box = BoundingBox(x1=200.0, y1=200.0, x2=550.0, y2=500.0)
    plate_box = BoundingBox(x1=250.0, y1=350.0, x2=390.0, y2=395.0)

    car_det = DetectionRecord(detection_id="c1", class_name="car", confidence=0.95, bounding_box=car_box)
    plate_det = DetectionRecord(detection_id="p1", class_name="license_plate", confidence=0.90, bounding_box=plate_box)

    fd = FrameDetections(
        camera_id="cam_vis_01",
        frame_sequence_number=1,
        detections=[car_det, plate_det],
        frame=frame,
    )

    tracks = tracker.update(fd)
    plates = pipeline.process(
        frame=frame,
        frame_sequence_number=1,
        timestamp=fd.timestamp,
        camera_id=fd.camera_id,
        tracks=tracks,
        detections=fd.detections,
    )

    assert len(plates) >= 1
    found_plate = plates[0]
    assert found_plate.plate_text == "DL01AB1234"
    assert found_plate.is_valid_format is True
    assert found_plate.vehicle_track_id == tracks[0].track_id


def test_pipeline_unreadable_plate_documents_limitations():
    """Verify that unreadable or garbage plates are rejected and document limitations."""
    mock_ocr = MockOCREngine()
    mock_ocr.set_default_response("UNKNOWN_NOISE", 0.3)

    pipeline = ANPRPipeline(ocr_engine=mock_ocr)
    frame = np.full((400, 400, 3), 80, dtype=np.uint8)

    plate_det = DetectionRecord(
        detection_id="p1",
        class_name="license_plate",
        confidence=0.5,
        bounding_box=BoundingBox(x1=50.0, y1=50.0, x2=150.0, y2=100.0),
    )

    plates = pipeline.process(
        frame=frame,
        frame_sequence_number=1,
        timestamp=datetime.now(timezone.utc),
        camera_id="cam_test",
        tracks=[],
        detections=[plate_det],
    )

    assert len(plates) >= 1
    rejected = plates[0]
    assert rejected.is_valid_format is False
    assert rejected.validation_status in (PlateValidationStatus.INVALID_SYNTAX, PlateValidationStatus.UNREADABLE)
    assert len(rejected.limitations) > 0
    assert any("syntax" in lim.lower() or "contrast" in lim.lower() or "blurry" in lim.lower() for lim in rejected.limitations)

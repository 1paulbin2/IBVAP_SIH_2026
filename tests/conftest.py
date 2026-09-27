"""
Shared Pytest fixtures for Person 3 test suite.
"""

from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from typing import Dict, List
import cv2
import numpy as np
import pytest

from schemas.detection import BoundingBox, DetectionRecord, FrameDetections
from test_data.generate_test_assets import create_synthetic_plate_image


@pytest.fixture
def sample_bbox() -> BoundingBox:
    return BoundingBox(x1=100.0, y1=150.0, x2=250.0, y2=300.0)


@pytest.fixture
def sample_detection(sample_bbox) -> DetectionRecord:
    return DetectionRecord(
        detection_id="det_001",
        camera_id="cam_test_01",
        frame_sequence_number=1,
        timestamp=datetime.now(timezone.utc),
        class_name="car",
        confidence=0.92,
        bounding_box=sample_bbox,
    )


@pytest.fixture
def synthetic_plate_image() -> np.ndarray:
    return create_synthetic_plate_image("DL01AB1234", width=240, height=60)


@pytest.fixture
def blurry_plate_image() -> np.ndarray:
    return create_synthetic_plate_image("DL01AB1234", width=240, height=60, blur=True)


@pytest.fixture
def low_contrast_plate_image() -> np.ndarray:
    return create_synthetic_plate_image("DL01AB1234", width=240, height=60, low_contrast=True)


@pytest.fixture
def sample_plates_test_set() -> List[Dict]:
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(curr_dir, "..", "test_data", "sample_plates.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["sample_plates"]


@pytest.fixture
def mock_scenarios() -> Dict:
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(curr_dir, "..", "test_data", "mock_detections.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

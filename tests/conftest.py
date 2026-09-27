"""Shared test configuration and fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import cv2
import numpy as np
import pytest

from schemas.detection import BoundingBox, DetectionRecord
from test_data.generate_test_assets import create_synthetic_plate_image


# Backend async-test configuration
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark an async test")


# Person 3 tracking/ANPR fixtures
@pytest.fixture
def sample_bbox() -> BoundingBox:
    return BoundingBox(
        x1=100.0,
        y1=150.0,
        x2=250.0,
        y2=300.0,
    )


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
    return create_synthetic_plate_image(
        "DL01AB1234",
        width=240,
        height=60,
    )


@pytest.fixture
def blurry_plate_image() -> np.ndarray:
    return create_synthetic_plate_image(
        "DL01AB1234",
        width=240,
        height=60,
        blur=True,
    )


@pytest.fixture
def low_contrast_plate_image() -> np.ndarray:
    return create_synthetic_plate_image(
        "DL01AB1234",
        width=240,
        height=60,
        low_contrast=True,
    )


@pytest.fixture
def sample_plates_test_set():
    path = (
        Path(__file__).resolve().parents[1]
        / "test_data"
        / "sample_plates.json"
    )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["sample_plates"]


@pytest.fixture
def mock_scenarios():
    path = (
        Path(__file__).resolve().parents[1]
        / "test_data"
        / "mock_detections.json"
    )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
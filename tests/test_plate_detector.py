"""
Unit tests for PlateDetector (Person 2 detection mapping and morphological fallback).
"""

import cv2
import numpy as np
import pytest

from schemas.detection import BoundingBox, DetectionRecord
from anpr.plate_detector import PlateDetector
from test_data.generate_test_assets import create_synthetic_plate_image


def test_plate_detector_uses_person2_plate_detection():
    detector = PlateDetector()
    frame = np.full((400, 600, 3), 120, dtype=np.uint8)

    plate_box = BoundingBox(x1=200.0, y1=250.0, x2=320.0, y2=290.0)
    p_det = DetectionRecord(
        detection_id="p1", class_name="license_plate", confidence=0.91, bounding_box=plate_box
    )
    v_det = DetectionRecord(
        detection_id="v1", class_name="car", confidence=0.95, bounding_box=BoundingBox(x1=100.0, y1=100.0, x2=500.0, y2=350.0)
    )

    candidates = detector.extract_from_frame(
        frame=frame, vehicle_detections=[v_det], plate_detections=[p_det]
    )

    assert len(candidates) >= 1
    best = candidates[0]
    assert best.detection_source == "person2_detector"
    assert best.crop.shape[0] == 40
    assert best.crop.shape[1] == 120


def test_plate_detector_morphological_fallback():
    detector = PlateDetector()
    # Create vehicle image and embed synthetic plate in lower half
    v_img = np.full((200, 300, 3), 50, dtype=np.uint8)
    plate = create_synthetic_plate_image("DL01AB1234", width=120, height=35)
    # Paste plate onto vehicle at (x=90, y=140)
    v_img[140:175, 90:210] = plate

    # Frame containing the vehicle
    frame = np.full((600, 800, 3), 100, dtype=np.uint8)
    frame[100:300, 100:400] = v_img

    v_box = BoundingBox(x1=100.0, y1=100.0, x2=400.0, y2=300.0)
    v_det = DetectionRecord(detection_id="v1", class_name="car", confidence=0.9, bounding_box=v_box)

    candidates = detector.extract_from_frame(
        frame=frame, vehicle_detections=[v_det], plate_detections=[]
    )

    assert len(candidates) >= 1
    assert any(c.detection_source == "morphological_fallback" for c in candidates)

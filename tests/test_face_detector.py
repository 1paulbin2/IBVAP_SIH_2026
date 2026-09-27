import numpy as np
import pytest
from src.detectors.face_detector import FaceDetector
from src.api.detection_interface import DetectionResult

def test_face_detector_initialization():
    detector = FaceDetector()
    assert detector.detector is not None

def test_face_detector_inference_empty_frame():
    detector = FaceDetector()
    
    # Create a dummy frame (black image)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    detections = detector.detect(dummy_frame)
    
    # Ensure it returns a list and doesn't crash on an empty frame
    assert isinstance(detections, list)
    
    for det in detections:
        assert isinstance(det, DetectionResult)
        assert det.class_name == "face"
        assert det.class_id == 1000
        assert 0.0 <= det.confidence <= 1.0

import numpy as np
from src.detectors.yolo_detector import YOLOObjectDetector
from src.core.config import DetectionConfig
from src.api.detection_interface import DetectionResult

def test_yolo_detector_initialization():
    detector = YOLOObjectDetector()
    assert detector.model is not None

def test_yolo_detector_inference():
    detector = YOLOObjectDetector()
    
    # Create a dummy frame (black image)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    detections = detector.detect(dummy_frame)
    
    # Ensure it returns a list
    assert isinstance(detections, list)
    
    # Since it's a black image, there should be 0 detections, 
    # but the execution flow shouldn't crash.
    # If there happen to be false positives, we check the type.
    for det in detections:
        assert isinstance(det, DetectionResult)
        assert det.class_name in ["person", "car", "motorcycle", "bus", "truck"]
        assert 0.0 <= det.confidence <= 1.0

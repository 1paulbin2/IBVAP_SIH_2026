import pytest
from src.api.detection_interface import BoundingBox, DetectionResult

def test_valid_bounding_box():
    bbox = BoundingBox(x_min=10, y_min=20, x_max=100, y_max=200)
    assert bbox.x_min == 10
    assert bbox.y_min == 20
    assert bbox.x_max == 100
    assert bbox.y_max == 200

def test_invalid_bounding_box_coordinates():
    # x_max < x_min
    with pytest.raises(ValueError, match="Invalid bounding box"):
        BoundingBox(x_min=100, y_min=20, x_max=10, y_max=200)
        
    # y_max < y_min
    with pytest.raises(ValueError, match="Invalid bounding box"):
        BoundingBox(x_min=10, y_min=200, x_max=100, y_max=20)

def test_valid_detection_result():
    bbox = BoundingBox(10, 10, 50, 50)
    det = DetectionResult(
        class_name="person", 
        class_id=0, 
        confidence=0.85, 
        bbox=bbox,
        timestamp=1630000000.0,
        camera_id="cam_01"
    )
    assert det.class_name == "person"
    assert det.confidence == 0.85
    assert det.camera_id == "cam_01"

def test_invalid_confidence_high():
    bbox = BoundingBox(10, 10, 50, 50)
    with pytest.raises(ValueError, match="Confidence score must be between"):
        DetectionResult(class_name="car", class_id=2, confidence=1.5, bbox=bbox)

def test_invalid_confidence_low():
    bbox = BoundingBox(10, 10, 50, 50)
    with pytest.raises(ValueError, match="Confidence score must be between"):
        DetectionResult(class_name="car", class_id=2, confidence=-0.1, bbox=bbox)

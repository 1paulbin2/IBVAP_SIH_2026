import os
import cv2
import numpy as np
from typing import List

from src.detectors.base_detector import BaseDetector
from src.api.detection_interface import DetectionResult, BoundingBox
from src.core.config import DetectionConfig

class FaceDetector(BaseDetector):
    """
    Detects visible human faces using OpenCV's YuNet (a lightweight CNN-based detector).
    """
    def __init__(self, config: DetectionConfig = None):
        self.config = config or DetectionConfig()
        
        # We use OpenCV's modern YuNet face detector which is lightweight and fast on CPU
        model_path = os.getenv("IBVAP_FACE_MODEL_PATH", "models/face_detection_yunet_2023mar.onnx")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Face detection model not found at {model_path}. Please download YuNet ONNX.")
            
        # YuNet requires input size at initialization. Set a dummy default, updated dynamically per frame.
        self.detector = cv2.FaceDetectorYN.create(
            model=model_path,
            config="",
            input_size=(320, 320),
            score_threshold=self.config.conf_threshold,
            nms_threshold=self.config.nms_threshold,
            top_k=5000
        )
        self.current_input_size = (320, 320)
        
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        height, width, _ = frame.shape
        input_size = (width, height)
        
        # YuNet requires the explicit input size to match the frame size
        if self.current_input_size != input_size:
            self.detector.setInputSize(input_size)
            self.current_input_size = input_size
            
        # Guard against None or invalid frames
        if frame is None or frame.size == 0:
            return []
        retval, faces = self.detector.detect(frame)
        
        detections = []
        if faces is not None:
            for face in faces:
                # Format: [x, y, w, h, x_re, y_re, x_le, y_le, ... , confidence]
                x, y, w, h = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                confidence = float(face[-1])
                
                # Constrain coordinates to image bounds
                x_min = max(0, x)
                y_min = max(0, y)
                x_max = min(width, x + w)
                y_max = min(height, y + h)
                
                # Filter out invalid bounding boxes
                if x_max <= x_min or y_max <= y_min:
                    continue
                    
                bbox = BoundingBox(x_min, y_min, x_max, y_max)
                detections.append(DetectionResult(
                    class_name="face",
                    class_id=1000, # Kept completely distinct from COCO classes (0-79)
                    confidence=confidence,
                    bbox=bbox
                ))
                
        return detections

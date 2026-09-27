import os
from typing import List
import numpy as np
from ultralytics import YOLO

from src.detectors.base_detector import BaseDetector
from src.api.detection_interface import DetectionResult, BoundingBox
from src.core.config import DetectionConfig

# COCO class IDs that the module is responsible for
TARGET_CLASSES = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

class YOLOObjectDetector(BaseDetector):
    def __init__(self, config: DetectionConfig = None):
        self.config = config or DetectionConfig()
        
        model_path = self.config.model_path
        if not os.path.exists(model_path):
            # Fallback to downloading a tiny YOLOv8 model if the specific path is missing
            print(f"Warning: Model not found at {model_path}. Defaulting to 'yolov8n.pt' for development.")
            model_path = "yolov8n.pt"
            
        self.model = YOLO(model_path)
        
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Runs YOLO object detection on the provided frame.
        Applies thresholds and filters only TARGET_CLASSES.
        """
        # YOLOv8 inference
        results = self.model(
            frame, 
            device=self.config.device, 
            conf=self.config.conf_threshold,
            iou=self.config.nms_threshold,
            imgsz=self.config.input_size,
            classes=list(TARGET_CLASSES.keys()),
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Extract coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                
                # Double-check class mapping (in case Ultralytics class filtering failed)
                if cls_id in TARGET_CLASSES:
                    bbox = BoundingBox(
                        x_min=int(x1),
                        y_min=int(y1),
                        x_max=int(x2),
                        y_max=int(y2)
                    )
                    detections.append(DetectionResult(
                        class_name=TARGET_CLASSES[cls_id],
                        class_id=cls_id,
                        confidence=conf,
                        bbox=bbox
                    ))
                    
        return detections

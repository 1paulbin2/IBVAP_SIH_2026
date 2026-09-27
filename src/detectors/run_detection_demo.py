import urllib.request
import os
import cv2
import time
from src.detectors.yolo_detector import YOLOObjectDetector
from src.core.config import DetectionConfig

def run_demo():
    print("Initializing detector...")
    config = DetectionConfig()
    detector = YOLOObjectDetector(config=config)
    
    image_path = "data/sample_images/bus.jpg"
    output_path = "data/sample_images/bus_detected.jpg"
    
    # Download a sample image if it doesn't exist
    if not os.path.exists(image_path):
        print("Downloading sample image...")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        url = "https://ultralytics.com/images/bus.jpg"
        urllib.request.urlretrieve(url, image_path)
        
    print(f"Loading image from {image_path}...")
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not read image.")
        return
        
    print("Running detection...")
    start_time = time.perf_counter()
    detections = detector.detect(frame)
    end_time = time.perf_counter()
    
    inference_time = end_time - start_time
    fps = 1.0 / inference_time if inference_time > 0 else 0
    
    print(f"Detected {len(detections)} objects.")
    print(f"Inference Time: {inference_time:.4f} seconds ({fps:.2f} FPS) on {config.device}")
    
    # Draw detections
    for det in detections:
        box = det.bbox
        cv2.rectangle(frame, (box.x_min, box.y_min), (box.x_max, box.y_max), (0, 255, 0), 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(frame, label, (box.x_min, box.y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    cv2.imwrite(output_path, frame)
    print(f"Annotated image saved to {output_path}")

if __name__ == "__main__":
    run_demo()

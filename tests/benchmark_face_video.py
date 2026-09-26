import os
import cv2
import time
import glob
import platform
import numpy as np
from src.detectors.face_detector import FaceDetector
from src.core.config import DetectionConfig

def run_benchmark():
    video_dir = "data/sample_videos"
    os.makedirs(video_dir, exist_ok=True)
    video_files = glob.glob(os.path.join(video_dir, "*.mp4")) + glob.glob(os.path.join(video_dir, "*.avi"))
    
    real_videos = [v for v in video_files if "synthetic" not in v and "annotated" not in v]
    
    if not real_videos:
        print("No real sample video found for face detection in data/sample_videos/.")
        print("Please provide a video containing human faces to accurately test the face detector.")
        test_video_path = os.path.join(video_dir, "synthetic_test.mp4")
        if not os.path.exists(test_video_path):
            print("Synthetic video not found. Generating a blank one just to verify execution flow...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(test_video_path, fourcc, 30, (640, 480))
            for _ in range(30):
                out.write(np.zeros((480, 640, 3), dtype=np.uint8))
            out.release()
    else:
        test_video_path = real_videos[0]
        
    output_video_path = os.path.join(video_dir, "annotated_face_" + os.path.basename(test_video_path))
    
    print("--- Environment ---")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    
    config = DetectionConfig()
    print(f"Confidence Threshold: {config.conf_threshold}")
    
    print("\n--- Model Loading ---")
    start_load = time.perf_counter()
    detector = FaceDetector(config=config)
    load_time = time.perf_counter() - start_load
    print(f"Model loaded in {load_time:.4f} seconds (not included in FPS calculation)")
    
    cap = cv2.VideoCapture(test_video_path)
    if not cap.isOpened():
        print(f"Error opening video {test_video_path}")
        return
        
    v_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    v_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    v_fps    = cap.get(cv2.CAP_PROP_FPS)
    v_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"\n--- Video Properties ---")
    print(f"Resolution: {v_width}x{v_height}")
    print(f"Video FPS: {v_fps}")
    print(f"Total Frames: {v_total_frames}")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, v_fps if v_fps > 0 else 30.0, (v_width, v_height))
    
    warmup_frames = min(5, v_total_frames)
    print(f"\n--- Warm-up ({warmup_frames} frames) ---")
    frames_warmed = 0
    start_warmup = time.perf_counter()
    while frames_warmed < warmup_frames:
        ret, frame = cap.read()
        if not ret:
            break
        _ = detector.detect(frame)
        out.write(frame)
        frames_warmed += 1
    warmup_time = time.perf_counter() - start_warmup
    print(f"Warm-up completed in {warmup_time:.4f} seconds")
    
    print("\n--- Benchmark (Continuous Inference) ---")
    processed_frames = 0
    total_inference_time = 0.0
    total_detections = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_start = time.perf_counter()
        detections = detector.detect(frame)
        frame_end = time.perf_counter()
        
        total_inference_time += (frame_end - frame_start)
        processed_frames += 1
        total_detections += len(detections)
        
        for det in detections:
            box = det.bbox
            cv2.rectangle(frame, (box.x_min, box.y_min), (box.x_max, box.y_max), (255, 0, 0), 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(frame, label, (box.x_min, box.y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
        out.write(frame)
        
    cap.release()
    out.release()
    
    avg_processing_time = (total_inference_time / processed_frames) if processed_frames > 0 else 0
    avg_fps = (1.0 / avg_processing_time) if avg_processing_time > 0 else 0
    
    print("\n--- Final Results ---")
    print(f"Total Processed Frames: {processed_frames}")
    print(f"Total Face Detections Found: {total_detections}")
    print(f"Average Frame Processing Time: {avg_processing_time*1000:.2f} ms")
    print(f"Measured Continuous FPS: {avg_fps:.2f} FPS")
    print(f"Annotated output saved to {output_video_path}")
    print("\nNOTE: This is a qualitative/functional validation rather than an accuracy evaluation.")

if __name__ == "__main__":
    run_benchmark()

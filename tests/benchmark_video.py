import os
import cv2
import time
import glob
import platform
import torch
import numpy as np
from src.detectors.yolo_detector import YOLOObjectDetector
from src.core.config import DetectionConfig

def generate_synthetic_video(output_path, resolution=(640, 480), fps=30, frames=100):
    print(f"Generating a small synthetic video at {output_path} for testing purposes...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)
    for i in range(frames):
        # Create a simple grey frame with a moving black square
        frame = np.ones((resolution[1], resolution[0], 3), dtype=np.uint8) * 128
        # Moving box
        x = min(i * 5, resolution[0] - 50)
        y = min(i * 3, resolution[1] - 50)
        cv2.rectangle(frame, (x, y), (x+50, y+50), (0, 0, 0), -1)
        out.write(frame)
    out.release()
    print("Synthetic video generated.")

def run_benchmark():
    video_dir = "data/sample_videos"
    os.makedirs(video_dir, exist_ok=True)
    video_files = glob.glob(os.path.join(video_dir, "*.mp4")) + glob.glob(os.path.join(video_dir, "*.avi"))
    
    test_video_path = None
    # Filter out any existing synthetic or annotated videos if a real one exists
    real_videos = [v for v in video_files if "synthetic" not in v and "annotated" not in v]
    
    if not real_videos:
        print("No real sample video found in data/sample_videos/.")
        test_video_path = os.path.join(video_dir, "synthetic_test.mp4")
        if not os.path.exists(test_video_path):
            generate_synthetic_video(test_video_path)
    else:
        test_video_path = real_videos[0]
        
    output_video_path = os.path.join(video_dir, "annotated_" + os.path.basename(test_video_path))
    
    # 1. Hardware/Environment
    print("--- Environment ---")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    print(f"PyTorch Version: {torch.__version__}")
    
    device_avail = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Available Hardware Device: {device_avail}")
    
    config = DetectionConfig()
    print(f"Configured Device for Inference: {config.device}")
    print(f"Confidence Threshold: {config.conf_threshold}")
    
    # 2. Model Loading
    print("\n--- Model Loading ---")
    start_load = time.perf_counter()
    detector = YOLOObjectDetector(config=config)
    load_time = time.perf_counter() - start_load
    print(f"Model loaded in {load_time:.4f} seconds (not included in FPS calculation)")
    
    # 3. Video Properties
    cap = cv2.VideoCapture(test_video_path)
    if not cap.isOpened():
        print(f"Error opening video stream or file {test_video_path}")
        return
        
    v_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    v_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    v_fps    = cap.get(cv2.CAP_PROP_FPS)
    v_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"\n--- Video Properties ---")
    print(f"Resolution: {v_width}x{v_height}")
    print(f"Video FPS (metadata): {v_fps}")
    print(f"Total Frames: {v_total_frames}")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, v_fps if v_fps > 0 else 30.0, (v_width, v_height))
    
    # 4. Warm-up
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
    print(f"Warm-up completed in {warmup_time:.4f} seconds (not included in FPS calculation)")
    
    # 5. Continuous Inference
    print("\n--- Benchmark (Continuous Inference) ---")
    processed_frames = 0
    total_inference_time = 0.0
    total_detections = 0
    class_counts = {}
    
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
        
        # Annotate and count
        for det in detections:
            box = det.bbox
            cv2.rectangle(frame, (box.x_min, box.y_min), (box.x_max, box.y_max), (0, 0, 255), 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(frame, label, (box.x_min, box.y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Count by class
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
            
        out.write(frame)
        
    cap.release()
    out.release()
    
    avg_processing_time = (total_inference_time / processed_frames) if processed_frames > 0 else 0
    avg_fps = (1.0 / avg_processing_time) if avg_processing_time > 0 else 0
    
    print("\n--- Final Results ---")
    print(f"Total Processed Frames: {processed_frames}")
    print(f"Total Detections Found: {total_detections}")
    print("Detections by Class:")
    for cls_name, count in class_counts.items():
        print(f"  - {cls_name}: {count}")
    print(f"Average Frame Processing Time: {avg_processing_time*1000:.2f} ms")
    print(f"Measured Continuous FPS: {avg_fps:.2f} FPS")
    print(f"Annotated output saved to {output_video_path}")
    print("\nWARNING: This measured FPS does not represent actual deployment performance on dedicated border CCTV hardware.")
    print("NOTE: This is a qualitative/functional validation rather than an accuracy evaluation.")

if __name__ == "__main__":
    run_benchmark()

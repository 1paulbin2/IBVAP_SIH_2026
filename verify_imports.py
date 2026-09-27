import sys
print(f"Python Version: {sys.version}")

try:
    import cv2
    print(f"OpenCV Version: {cv2.__version__}")
except ImportError as e:
    print(f"Failed to import cv2: {e}")

try:
    import torch
    print(f"PyTorch Version: {torch.__version__}")
except ImportError as e:
    print(f"Failed to import torch: {e}")

try:
    import ultralytics
    print(f"Ultralytics YOLO Version: {ultralytics.__version__}")
except ImportError as e:
    print(f"Failed to import ultralytics: {e}")

print("Import verification complete.")

# IBVAP - Module 2: AI Detection

This module is responsible for the AI-based video analytics in the Intelligent Border Video Analytics Platform (IBVAP).

## Features
- Human/person detection
- Vehicle detection and classification
- Face detection
- Detection confidence scores and bounding boxes
- Video-based detection processing

## Architecture
The module exposes a clean interface (`src.api.detection_interface`) for consumption by other components like Object Tracking and ANPR.

### The `BaseDetector` Interface
All detectors in this module inherit from `src.detectors.base_detector.BaseDetector`. This abstract class mandates a unified interface:
```python
def detect(self, frame: np.ndarray) -> List[DetectionResult]:
```
* **Input:** A NumPy array representing an image frame (BGR format from OpenCV).
* **Output:** A list of `DetectionResult` objects.

### Detection Output Format
The `DetectionResult` dataclass structures the output of any detection. It includes the detected class label, class ID, confidence score (0.0 to 1.0), and the bounding box.

**Bounding Box Convention:**
Bounding boxes are structured as `[x_min, y_min, x_max, y_max]`.
* `x_min, y_min`: The absolute pixel coordinates of the top-left corner.
* `x_max, y_max`: The absolute pixel coordinates of the bottom-right corner.
Coordinates are strictly integers.

**Example Output:**
```python
DetectionResult(
    class_name='person', 
    class_id=0, 
    confidence=0.88, 
    bbox=BoundingBox(x_min=150, y_min=200, x_max=350, y_max=600), 
    timestamp=1690000000.5, 
    camera_id='cam_north'
)
```

### Configuration
Configuration settings are managed in `src.core.config.DetectionConfig`. Values can be overridden seamlessly via environment variables without modifying the code:
* `IBVAP_MODEL_PATH` (default: `models/yolo_default.pt`) - Path to the pretrained model.
* `IBVAP_DEVICE` (default: `cpu`) - Device used for inference (e.g., `cpu`, `cuda`).
* `IBVAP_CONF_THRESH` (default: `0.5`) - Minimum confidence score to register a detection.
* `IBVAP_NMS_THRESH` (default: `0.45`) - Non-maximum suppression threshold for overlapping bounding boxes.
* `IBVAP_INPUT_SIZE` (default: `640`) - Input frame scaling size for inference.

## Setup Instructions

1. Create a virtual environment:
   ```bash
   py -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run tests:
   ```bash
   pytest tests/
   ```

## Running the YOLO Detector Demo (Image)

You can run the built-in demonstration script which automatically downloads a test image, runs inference, and saves the annotated output. Ensure the `PYTHONPATH` is set to the project root:

**PowerShell:**
```bash
$env:PYTHONPATH="."
python src/detectors/run_detection_demo.py
```

## Running the Video Benchmark

To properly test continuous frame processing and measure FPS:

1. Place your own test video (`.mp4` or `.avi`) inside the `data/sample_videos/` directory. (e.g., `data/sample_videos/border_cam1.mp4`).
2. Run the benchmark script:
```bash
$env:PYTHONPATH="."
python tests/benchmark_video.py
```
*Note: If no sample video is provided, the script will generate a lightweight synthetic video internally to execute the test pipeline without silently downloading large files.*

The script will separate initialization/warm-up time from actual inference time and output an annotated video (`annotated_<your_video>.mp4`) to the same folder.

## YOLO Implementation

The `YOLOObjectDetector` currently tracks the following COCO classes:
- Person
- Car
- Motorcycle
- Bus
- Truck

*Note:* If `models/yolo_default.pt` does not exist, it will fallback to downloading Ultralytics' `yolov8n.pt` weight file automatically for development purposes.

### Known Limitations
* **Execution Time:** The initial frame takes longer due to PyTorch memory allocation and model warm-up. Subsequent inference times on a CPU will stabilize. Measured cold-start performance is approximately `0.34 FPS`, but real-time FPS should be tested over a video stream.
* **Coordinate Mapping:** Bounding boxes strictly adhere to `[x_min, y_min, x_max, y_max]`. Any module converting this to `[center_x, center_y, width, height]` (such as DeepSORT) must implement a utility for conversion.

### Face Detection Implementation

The `FaceDetector` utilizes OpenCV's built-in **YuNet** model. YuNet is a lightweight CNN-based face detector specifically optimized for edge devices and CPU execution.
* The detector strictly identifies visible human faces without running recognition, embeddings, or person identification.
* Face detections output the `class_name` as `"face"` and use the distinct `class_id` of `1000` to prevent any overlap with the COCO classes output by the YOLO detector.
* It uses the same `DetectionResult` and `BoundingBox` schemas to ensure a uniform API downstream.

To run the dedicated face detection video benchmark:
```bash
$env:PYTHONPATH="."
python tests/benchmark_face_video.py
```

## Note
Do not commit model weights (`.pt`, `.onnx`) or large sample videos to the repository. Place them in the `models/` and `data/` directories respectively.

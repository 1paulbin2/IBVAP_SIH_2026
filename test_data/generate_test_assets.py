"""
Generates synthetic test assets and scenario datasets for Person 3 testing and demonstrations.
Avoids storing real private vehicle data by generating programmatic synthetic plate crops and detection sequences.
"""

import json
import os
import cv2
import numpy as np


def generate_mock_detection_scenarios(output_path: str) -> None:
    """
    Creates multi-frame mock detection scenarios:
    1. Linear motion (Car 1 and Truck 1 moving across frames)
    2. Occlusion / Missed detections (Car 1 disappears for 3 frames then reappears)
    3. Trajectory crossing (Two cars pass each other without identity swap)
    """
    scenarios = {
        "linear_motion": {
            "description": "Two vehicles moving steadily across 8 frames",
            "frames": [
                {
                    "frame_seq": f,
                    "timestamp": f"2026-09-27T10:00:0{f}.000Z",
                    "detections": [
                        {
                            "detection_id": f"det_c1_f{f}",
                            "class_name": "car",
                            "confidence": 0.92,
                            "bbox": [100.0 + f * 20.0, 200.0 + f * 5.0, 220.0 + f * 20.0, 300.0 + f * 5.0],
                            "metadata": {"mock_plate_text": "DL01AB1234"}
                        },
                        {
                            "detection_id": f"det_t1_f{f}",
                            "class_name": "truck",
                            "confidence": 0.88,
                            "bbox": [400.0 - f * 15.0, 150.0 + f * 10.0, 580.0 - f * 15.0, 320.0 + f * 10.0],
                            "metadata": {"mock_plate_text": "MH12DE1433"}
                        }
                    ]
                }
                for f in range(1, 9)
            ]
        },
        "missed_detections_occlusion": {
            "description": "Vehicle visible frames 1-3, occluded/missed in frames 4-5, reappears frames 6-8",
            "frames": [
                # Frame 1-3: Visible
                {
                    "frame_seq": 1,
                    "timestamp": "2026-09-27T10:05:01.000Z",
                    "detections": [{
                        "detection_id": "det_occ_f1",
                        "class_name": "car",
                        "confidence": 0.95,
                        "bbox": [150.0, 200.0, 270.0, 300.0],
                        "metadata": {"mock_plate_text": "KA05MB9990"}
                    }]
                },
                {
                    "frame_seq": 2,
                    "timestamp": "2026-09-27T10:05:02.000Z",
                    "detections": [{
                        "detection_id": "det_occ_f2",
                        "class_name": "car",
                        "confidence": 0.94,
                        "bbox": [170.0, 205.0, 290.0, 305.0],
                        "metadata": {"mock_plate_text": "KA05MB9990"}
                    }]
                },
                {
                    "frame_seq": 3,
                    "timestamp": "2026-09-27T10:05:03.000Z",
                    "detections": [{
                        "detection_id": "det_occ_f3",
                        "class_name": "car",
                        "confidence": 0.93,
                        "bbox": [190.0, 210.0, 310.0, 310.0],
                        "metadata": {"mock_plate_text": "KA05MB9990"}
                    }]
                },
                # Frames 4-5: Missed / Occluded (empty detections)
                {
                    "frame_seq": 4,
                    "timestamp": "2026-09-27T10:05:04.000Z",
                    "detections": []
                },
                {
                    "frame_seq": 5,
                    "timestamp": "2026-09-27T10:05:05.000Z",
                    "detections": []
                },
                # Frames 6-8: Reappears along predictable trajectory
                {
                    "frame_seq": 6,
                    "timestamp": "2026-09-27T10:05:06.000Z",
                    "detections": [{
                        "detection_id": "det_occ_f6",
                        "class_name": "car",
                        "confidence": 0.89,
                        "bbox": [250.0, 225.0, 370.0, 325.0],
                        "metadata": {"mock_plate_text": "KA05MB9990"}
                    }]
                },
                {
                    "frame_seq": 7,
                    "timestamp": "2026-09-27T10:05:07.000Z",
                    "detections": [{
                        "detection_id": "det_occ_f7",
                        "class_name": "car",
                        "confidence": 0.91,
                        "bbox": [270.0, 230.0, 390.0, 330.0],
                        "metadata": {"mock_plate_text": "KA05MB9990"}
                    }]
                }
            ]
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2)


def create_synthetic_plate_image(
    text: str,
    width: int = 240,
    height: int = 60,
    blur: bool = False,
    low_contrast: bool = False,
) -> np.ndarray:
    """
    Renders a synthetic license plate image for testing without any personal data.
    """
    # White background with black border
    bg_color = (128, 128, 128) if low_contrast else (245, 245, 245)
    img = np.full((height, width, 3), bg_color, dtype=np.uint8)

    # Plate border
    border_color = (110, 110, 110) if low_contrast else (20, 20, 20)
    cv2.rectangle(img, (2, 2), (width - 3, height - 3), border_color, 2)

    # Blue strip on left (IND standard)
    cv2.rectangle(img, (4, 4), (28, height - 4), (180, 50, 0), -1)

    # Plate text
    text_color = (100, 100, 100) if low_contrast else (10, 10, 10)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.85
    thickness = 2
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    tx = 35 + max(0, (width - 40 - tw) // 2)
    ty = (height + th) // 2

    cv2.putText(img, text, (tx, ty), font, font_scale, text_color, thickness, cv2.LINE_AA)

    if blur:
        img = cv2.GaussianBlur(img, (15, 15), 0)

    return img


if __name__ == "__main__":
    test_data_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(test_data_dir, "mock_detections.json")
    generate_mock_detection_scenarios(json_path)
    print(f"Generated mock detection scenarios: {json_path}")

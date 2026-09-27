"""
Plate region detection and cropping for Person 3 ANPR pipeline.
Extracts number plate candidate regions from full frames or vehicle bounding box crops
using either Person 2's direct detection bboxes or classical morphological edge analysis.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
import cv2
import numpy as np

from schemas.detection import BoundingBox, DetectionRecord


class PlateCandidate:
    """Represents a cropped license plate candidate with coordinates."""
    def __init__(
        self,
        crop: np.ndarray,
        bbox_in_frame: BoundingBox,
        confidence: float,
        detection_source: str,  # 'person2_detector' or 'morphological_fallback'
        parent_vehicle_bbox: Optional[BoundingBox] = None,
    ):
        self.crop = crop
        self.bbox_in_frame = bbox_in_frame
        self.confidence = confidence
        self.detection_source = detection_source
        self.parent_vehicle_bbox = parent_vehicle_bbox


class PlateDetector:
    """
    Localizes license plate regions inside vehicle detections or full frames.
    """

    def __init__(
        self,
        min_aspect_ratio: float = 2.0,
        max_aspect_ratio: float = 5.8,
        min_area: float = 600.0,
        max_relative_vehicle_height: float = 0.5,
    ):
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.min_area = min_area
        self.max_relative_vehicle_height = max_relative_vehicle_height

    def extract_from_frame(
        self,
        frame: np.ndarray,
        vehicle_detections: List[DetectionRecord],
        plate_detections: Optional[List[DetectionRecord]] = None,
    ) -> List[PlateCandidate]:
        """
        Extract plate candidates from frame given vehicle detections and optional explicit plate detections.
        """
        candidates: List[PlateCandidate] = []
        frame_h, frame_w = frame.shape[:2]

        # 1. First priority: Use explicit plate detections if provided by Person 2
        if plate_detections:
            for p_det in plate_detections:
                p_box = p_det.bounding_box
                crop = p_box.crop_from(frame)
                if crop.size > 0:
                    candidates.append(
                        PlateCandidate(
                            crop=crop,
                            bbox_in_frame=p_box,
                            confidence=p_det.confidence,
                            detection_source="person2_detector"
                        )
                    )

        # 2. Check if any vehicle detection has an attached plate_bounding_box
        for v_det in vehicle_detections:
            if v_det.plate_bounding_box is not None:
                p_box = v_det.plate_bounding_box
                crop = p_box.crop_from(frame)
                if crop.size > 0:
                    candidates.append(
                        PlateCandidate(
                            crop=crop,
                            bbox_in_frame=p_box,
                            confidence=v_det.confidence,
                            detection_source="person2_detector",
                            parent_vehicle_bbox=v_det.bounding_box,
                        )
                    )
            else:
                # 3. Fallback: Classical morphological candidate extraction within vehicle crop
                v_box = v_det.bounding_box
                v_crop = v_box.crop_from(frame)
                if v_crop.size > 0:
                    morph_candidates = self._find_plate_candidates_in_vehicle_crop(
                        vehicle_crop=v_crop,
                        vehicle_bbox=v_box,
                        frame_w=frame_w,
                        frame_h=frame_h,
                    )
                    candidates.extend(morph_candidates)

        return candidates

    def _find_plate_candidates_in_vehicle_crop(
        self,
        vehicle_crop: np.ndarray,
        vehicle_bbox: BoundingBox,
        frame_w: int,
        frame_h: int,
    ) -> List[PlateCandidate]:
        """
        Locate plate-like rectangular regions in vehicle crop using edge and contour analysis.
        Targeting Indian plate proportions (aspect ratio ~2.5 - 5.0).
        """
        vh, vw = vehicle_crop.shape[:2]
        if vh < 40 or vw < 80:
            return []

        # Convert to grayscale
        gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)

        # Contrast stretch
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Sobel vertical edges (character strokes on horizontal plate create vertical edges)
        grad_x = cv2.Sobel(enhanced, cv2.CV_16S, 1, 0, ksize=3)
        abs_grad_x = cv2.convertScaleAbs(grad_x)

        # Morphological closing to bridge character strokes into a solid plate rectangle
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        closed = cv2.morphologyEx(abs_grad_x, cv2.MORPH_CLOSE, kernel)

        # Otsu thresholding
        _, thresh = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Clean small noise
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_clean)

        # Find contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: List[PlateCandidate] = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            aspect_ratio = w / max(float(h), 1e-4)

            # Filter by area, aspect ratio, and vertical position in vehicle
            if (
                area >= self.min_area
                and self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio
                and h <= (vh * self.max_relative_vehicle_height)
            ):
                # Map relative coordinates to global frame
                gx1 = min(frame_w - 1, max(0.0, vehicle_bbox.x1 + x))
                gy1 = min(frame_h - 1, max(0.0, vehicle_bbox.y1 + y))
                gx2 = min(frame_w, max(gx1 + 1.0, vehicle_bbox.x1 + x + w))
                gy2 = min(frame_h, max(gy1 + 1.0, vehicle_bbox.y1 + y + h))

                plate_crop = vehicle_crop[y:y+h, x:x+w].copy()
                if plate_crop.size > 0:
                    candidates.append(
                        PlateCandidate(
                            crop=plate_crop,
                            bbox_in_frame=BoundingBox(x1=gx1, y1=gy1, x2=gx2, y2=gy2),
                            confidence=0.75,
                            detection_source="morphological_fallback",
                            parent_vehicle_bbox=vehicle_bbox,
                        )
                    )

        # Sort candidates by area descending and return top 2 to avoid flooding
        candidates.sort(key=lambda c: c.crop.shape[0] * c.crop.shape[1], reverse=True)
        return candidates[:2]

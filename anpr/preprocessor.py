"""
Image preprocessing and quality assessment pipeline for license plate OCR.
Performs blur detection, contrast checks, CLAHE enhancement, deskewing, and binarization.
"""

from __future__ import annotations
from typing import List, Tuple
import cv2
import numpy as np


class PreprocessingResult:
    """Holds intermediate and final preprocessed representations of a plate crop."""
    def __init__(
        self,
        original: np.ndarray,
        gray: np.ndarray,
        enhanced: np.ndarray,
        binary_standard: np.ndarray,
        binary_inverted: np.ndarray,
        is_blurry: bool,
        blur_score: float,
        is_low_contrast: bool,
        contrast_score: float,
        deskew_angle: float,
        quality_issues: List[str],
    ):
        self.original = original
        self.gray = gray
        self.enhanced = enhanced
        self.binary_standard = binary_standard
        self.binary_inverted = binary_inverted
        self.is_blurry = is_blurry
        self.blur_score = blur_score
        self.is_low_contrast = is_low_contrast
        self.contrast_score = contrast_score
        self.deskew_angle = deskew_angle
        self.quality_issues = quality_issues

    @property
    def is_acceptable_for_ocr(self) -> bool:
        """Returns True if the image is readable enough for meaningful OCR."""
        return not self.is_blurry and not self.is_low_contrast


class PlatePreprocessor:
    """
    Applies computer vision filters and deskewing to optimize license plate crops for OCR.
    """

    def __init__(
        self,
        target_height: int = 64,
        blur_threshold: float = 40.0,
        contrast_threshold: float = 22.0,
        max_deskew_angle: float = 30.0,
    ):
        self.target_height = target_height
        self.blur_threshold = blur_threshold
        self.contrast_threshold = contrast_threshold
        self.max_deskew_angle = max_deskew_angle

    def process(self, plate_crop: np.ndarray) -> PreprocessingResult:
        """
        Execute full preprocessing sequence on plate crop.
        """
        quality_issues: List[str] = []

        if plate_crop is None or plate_crop.size == 0:
            empty_arr = np.zeros((self.target_height, self.target_height * 3), dtype=np.uint8)
            return PreprocessingResult(
                original=empty_arr,
                gray=empty_arr,
                enhanced=empty_arr,
                binary_standard=empty_arr,
                binary_inverted=empty_arr,
                is_blurry=True,
                blur_score=0.0,
                is_low_contrast=True,
                contrast_score=0.0,
                deskew_angle=0.0,
                quality_issues=["Empty image crop"],
            )

        # 1. Normalize height to standard canonical size
        h, w = plate_crop.shape[:2]
        if h != self.target_height:
            new_w = max(32, int(w * (self.target_height / max(float(h), 1.0))))
            resized = cv2.resize(plate_crop, (new_w, self.target_height), interpolation=cv2.INTER_CUBIC)
        else:
            resized = plate_crop.copy()

        # 2. Grayscale conversion
        if len(resized.shape) == 3 and resized.shape[2] == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized.copy()

        # 3. Quality Diagnostics: Blur and Contrast
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < self.blur_threshold
        if is_blurry:
            quality_issues.append(f"Image too blurry (Laplacian variance {laplacian_var:.1f} < {self.blur_threshold})")

        contrast_std = float(np.std(gray))
        is_low_contrast = contrast_std < self.contrast_threshold
        if is_low_contrast:
            quality_issues.append(f"Low contrast crop (std dev {contrast_std:.1f} < {self.contrast_threshold})")

        # 4. Deskewing
        deskewed_gray, angle = self._deskew(gray)

        # 5. Noise reduction & edge preservation with Bilateral Filter
        smoothed = cv2.bilateralFilter(deskewed_gray, d=7, sigmaColor=50, sigmaSpace=50)

        # 6. Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(smoothed)

        # 7. Adaptive & Otsu Binarization
        _, bin_std = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bin_inv = cv2.bitwise_not(bin_std)

        return PreprocessingResult(
            original=resized,
            gray=deskewed_gray,
            enhanced=enhanced,
            binary_standard=bin_std,
            binary_inverted=bin_inv,
            is_blurry=is_blurry,
            blur_score=round(laplacian_var, 2),
            is_low_contrast=is_low_contrast,
            contrast_score=round(contrast_std, 2),
            deskew_angle=round(angle, 2),
            quality_issues=quality_issues,
        )

    def _deskew(self, gray: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Estimate skew angle via bounding rectangle of thresholded image and rotate.
        """
        # Threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 50:
            return gray, 0.0

        rect = cv2.minAreaRect(coords)
        angle = rect[-1]

        # OpenCV minAreaRect returns angle in [-90, 0)
        if angle < -45.0:
            angle = -(90.0 + angle)
        else:
            angle = -angle

        # If angle is beyond realistic plate tilt, skip rotation
        if abs(angle) > self.max_deskew_angle or abs(angle) < 1.0:
            return gray, 0.0

        # Rotate image
        h, w = gray.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated, float(angle)

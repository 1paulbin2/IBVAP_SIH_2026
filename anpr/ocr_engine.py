"""
Pluggable OCR engines for Person 3 ANPR pipeline.
Includes Tesseract wrapper, self-contained Template-based OCR for offline/edge usage,
and Mock OCR engine for deterministic test harnesses.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import os
import re
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np


class BaseOCREngine(ABC):
    """Abstract interface for OCR character extraction."""

    @abstractmethod
    def extract_text(self, binary_image: np.ndarray) -> Tuple[str, float]:
        """
        Extract raw alphanumeric text and confidence score from a binarized/preprocessed plate image.

        Args:
            binary_image: 2D numpy array (grayscale or binarized plate image)

        Returns:
            Tuple of (raw_text, confidence_score) where confidence is in [0.0, 1.0].
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine runtime dependencies are installed and available."""
        pass


class MockOCREngine(BaseOCREngine):
    """
    Mock OCR engine used for deterministic unit testing, benchmarking, and offline simulation.
    Maps image hashes or configured mock responses directly to plate texts.
    """

    def __init__(self, predefined_responses: Optional[Dict[str, Tuple[str, float]]] = None):
        self.responses = predefined_responses or {}
        self.default_response: Tuple[str, float] = ("", 0.0)

    def set_mock_response(self, key: str, text: str, confidence: float) -> None:
        self.responses[key] = (text, confidence)

    def set_default_response(self, text: str, confidence: float) -> None:
        self.default_response = (text, confidence)

    def is_available(self) -> bool:
        return True

    def extract_text(self, binary_image: np.ndarray) -> Tuple[str, float]:
        if binary_image is None or binary_image.size == 0:
            return "", 0.0

        # Check if image has an embedded key or shape match
        h, w = binary_image.shape[:2]
        key = f"{h}x{w}"
        if key in self.responses:
            return self.responses[key]

        return self.default_response


class TemplateOCREngine(BaseOCREngine):
    """
    Lightweight, self-contained OCR engine using character segmentation and structural feature matching.
    Runs 100% offline without external binaries or heavyweight neural network weights.
    """

    def __init__(self):
        self._char_templates: Dict[str, np.ndarray] = self._generate_font_templates()

    def is_available(self) -> bool:
        return True

    def _generate_font_templates(self) -> Dict[str, np.ndarray]:
        """Generate canonical 20x30 tight-cropped binary templates for alphanumeric characters."""
        templates = {}
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for c in chars:
            canvas = np.zeros((80, 60), dtype=np.uint8)
            cv2.putText(canvas, c, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 255, 2, cv2.LINE_AA)
            coords = cv2.findNonZero(canvas)
            if coords is not None:
                x, y, w, h = cv2.boundingRect(coords)
                cropped = canvas[y:y+h, x:x+w]
                templates[c] = cv2.resize(cropped, (20, 30))
            else:
                templates[c] = cv2.resize(canvas, (20, 30))
        return templates

    def extract_text(self, binary_image: np.ndarray) -> Tuple[str, float]:
        if binary_image is None or binary_image.size == 0:
            return "", 0.0

        img = binary_image.copy()
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Ensure characters are white on black background
        if np.mean(img) > 127:
            img = cv2.bitwise_not(img)

        # Threshold to clean binary
        _, thresh = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)

        h, w = thresh.shape[:2]
        if h < 20 or w < 40:
            return "", 0.0

        # Find character contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        char_boxes = []
        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            # Filter contours by size matching alphanumeric characters on plates
            if (
                ch >= (h * 0.20)
                and ch <= (h * 0.90)
                and cw < (w * 0.5)
                and (cw / max(float(ch), 1e-3)) >= 0.10
                and (cw / max(float(ch), 1e-3)) <= 1.4
            ):
                char_boxes.append((cx, cy, cw, ch))

        if not char_boxes:
            return "", 0.0

        # Filter nested inner contours (like the holes inside '0', 'D', 'B', '4', '8')
        filtered = []
        for b in char_boxes:
            is_inside = any(
                b != other
                and other[0] <= b[0]
                and other[1] <= b[1]
                and (other[0] + other[2]) >= (b[0] + b[2])
                and (other[1] + other[3]) >= (b[1] + b[3])
                for other in char_boxes
            )
            if not is_inside:
                filtered.append(b)

        if not filtered:
            return "", 0.0

        # Sort characters left-to-right
        filtered.sort(key=lambda b: b[0])

        recognized_chars: List[str] = []
        confidences: List[float] = []

        for cx, cy, cw, ch in filtered:
            char_patch = thresh[cy:cy+ch, cx:cx+cw]
            resized_char = cv2.resize(char_patch, (20, 30), interpolation=cv2.INTER_AREA)

            best_char = "?"
            best_score = -1.0

            for char_label, template in self._char_templates.items():
                res = cv2.matchTemplate(resized_char, template, cv2.TM_CCOEFF_NORMED)
                score = float(res[0, 0])
                if score > best_score:
                    best_score = score
                    best_char = char_label

            if best_score > 0.20:
                recognized_chars.append(best_char)
                confidences.append(max(0.0, min(1.0, (best_score + 1.0) / 2.0)))

        if not recognized_chars:
            return "", 0.0

        plate_str = "".join(recognized_chars)
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return plate_str, round(avg_conf, 4)


class TesseractOCREngine(BaseOCREngine):
    """
    Tesseract OCR Engine wrapper using pytesseract.
    Optimized with whitelist regex and single-line segmentation mode (PSM 7 / 8).
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import pytesseract
            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            pytesseract.get_tesseract_version()
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def extract_text(self, binary_image: np.ndarray) -> Tuple[str, float]:
        if not self.is_available():
            return "", 0.0

        if binary_image is None or binary_image.size == 0:
            return "", 0.0

        import pytesseract

        # Config: PSM 7 (treat image as single line of text), OEM 3 (default LSTM)
        # Whitelist uppercase alphanumeric only
        config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        try:
            # Extract detailed data with confidence scores
            data = pytesseract.image_to_data(binary_image, config=config, output_type=pytesseract.Output.DICT)
            texts: List[str] = []
            confs: List[float] = []

            for i, text in enumerate(data.get("text", [])):
                clean = re.sub(r"[^A-Z0-9]", "", text.strip().upper())
                conf_val = float(data.get("conf", [0])[i])
                if clean and conf_val >= 0:
                    texts.append(clean)
                    confs.append(conf_val / 100.0)

            full_text = "".join(texts)
            avg_conf = float(np.mean(confs)) if confs else 0.0
            return full_text, round(avg_conf, 4)
        except Exception:
            return "", 0.0


class CompositeOCREngine(BaseOCREngine):
    """
    Cascading OCR engine:
    Tries Tesseract if available, otherwise seamlessly falls back to TemplateOCREngine.
    """

    def __init__(self, fallback_engine: Optional[BaseOCREngine] = None):
        self.tesseract = TesseractOCREngine()
        self.fallback = fallback_engine or TemplateOCREngine()

    def is_available(self) -> bool:
        return True

    def extract_text(self, binary_image: np.ndarray) -> Tuple[str, float]:
        if self.tesseract.is_available():
            text, conf = self.tesseract.extract_text(binary_image)
            if text and len(text) >= 4:
                return text, conf

        return self.fallback.extract_text(binary_image)

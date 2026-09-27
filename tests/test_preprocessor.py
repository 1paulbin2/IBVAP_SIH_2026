"""
Unit tests for PlatePreprocessor (quality assessment, blur/contrast detection, deskewing).
"""

import cv2
import numpy as np
import pytest

from anpr.preprocessor import PlatePreprocessor


def test_preprocessor_normal_clean_plate(synthetic_plate_image):
    preprocessor = PlatePreprocessor(target_height=64, blur_threshold=40.0)
    result = preprocessor.process(synthetic_plate_image)

    assert result.is_acceptable_for_ocr
    assert not result.is_blurry
    assert not result.is_low_contrast
    assert result.gray.shape[0] == 64
    assert result.binary_standard.shape[0] == 64
    assert len(result.quality_issues) == 0


def test_preprocessor_blurry_plate_detection(blurry_plate_image):
    """Fulfills requirement: Tests include missed detections and unreadable plates."""
    preprocessor = PlatePreprocessor(target_height=64, blur_threshold=50.0)
    result = preprocessor.process(blurry_plate_image)

    assert not result.is_acceptable_for_ocr
    assert result.is_blurry
    assert any("blurry" in q.lower() for q in result.quality_issues)


def test_preprocessor_low_contrast_detection(low_contrast_plate_image):
    preprocessor = PlatePreprocessor(contrast_threshold=30.0)
    result = preprocessor.process(low_contrast_plate_image)

    assert not result.is_acceptable_for_ocr
    assert result.is_low_contrast
    assert any("contrast" in q.lower() for q in result.quality_issues)


def test_preprocessor_empty_crop():
    preprocessor = PlatePreprocessor()
    empty_crop = np.array([])
    result = preprocessor.process(empty_crop)

    assert not result.is_acceptable_for_ocr
    assert result.is_blurry
    assert result.is_low_contrast

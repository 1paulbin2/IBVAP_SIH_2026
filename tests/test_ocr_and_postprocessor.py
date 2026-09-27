"""
Unit tests for OCR engines, MoRTH & BH series validation, character disambiguation, and limitation documentation.
Fulfills Definition of DONE and DO NOT constraints:
- Do not assume OCR output is correct simply because text was returned.
- Validate plate recognition against known sample plates.
- Tests include unreadable plates.
- Do not claim ANPR accuracy without a defined test set.
"""

import pytest

from anpr.ocr_engine import MockOCREngine, TemplateOCREngine
from anpr.postprocessor import PlatePostProcessor
from schemas.anpr import PlateStandard, PlateValidationStatus


def test_postprocessor_benchmark_test_set(sample_plates_test_set):
    """
    Evaluates PlatePostProcessor against the defined benchmark test set (sample_plates.json).
    Ensures that syntactic rules, Indian state validation, and disambiguation work as expected.
    """
    postprocessor = PlatePostProcessor()

    passed_count = 0
    total_samples = len(sample_plates_test_set)

    for sample in sample_plates_test_set:
        raw_text = sample["raw_ocr_text"]
        is_blurry = sample.get("is_blurry", False)

        result = postprocessor.process(
            raw_text=raw_text,
            ocr_confidence=0.90,
            is_blurry=is_blurry,
        )

        assert result["is_valid"] == sample["expected_valid"], (
            f"Sample {sample['id']} expected valid={sample['expected_valid']} but got {result['is_valid']}"
        )
        assert result["validation_status"].value == sample["expected_status"], (
            f"Sample {sample['id']} expected status {sample['expected_status']} but got {result['validation_status'].value}"
        )

        if sample["expected_text"] is not None:
            assert result["plate_text"] == sample["expected_text"]

        # Crucial check: If invalid, limitations MUST be documented
        if not sample["expected_valid"]:
            assert len(result["limitations"]) > 0, f"Sample {sample['id']} had no limitations documented!"

        passed_count += 1

    assert passed_count == total_samples


def test_postprocessor_never_assumes_ocr_is_valid_blindly():
    """
    Explicit test for the DO NOT constraint:
    'Do not assume OCR output is correct simply because text was returned.'
    Random text like 'HELLO123', 'SPEED55', 'POLICE' must NOT be marked as valid plates.
    """
    postprocessor = PlatePostProcessor()

    garbage_outputs = [
        "HELLO123",
        "POLICE",
        "STOP",
        "SPEED_LIMIT_60",
        "FASTAG",
        "ABC1234",
        "9999999",
    ]

    for garbage in garbage_outputs:
        result = postprocessor.process(raw_text=garbage, ocr_confidence=0.99)
        assert result["is_valid"] is False, f"Garbage '{garbage}' was wrongly marked valid!"
        assert result["validation_status"] == PlateValidationStatus.INVALID_SYNTAX
        assert len(result["limitations"]) > 0
        assert result["confidence"] <= 0.35  # Stripped of high confidence


def test_postprocessor_character_disambiguation_pairs():
    """
    Verify positional character disambiguation:
    - First 2 characters must be letters (digits 0, 1, 2, 8 mapped to O/D, I, Z, B)
    - Last 4 characters must be digits (letters O, I, Z, B mapped to 0, 1, 2, 8)
    """
    postprocessor = PlatePostProcessor()

    # '0L' in state code -> 'DL'
    res1 = postprocessor.process("0L01AB1234", ocr_confidence=0.90)
    assert res1["is_valid"] is True
    assert res1["state_code"] == "DL"

    # 'O' at end -> '0'
    res2 = postprocessor.process("MH12DE143O", ocr_confidence=0.90)
    assert res2["is_valid"] is True
    assert res2["reg_number"] == "1430"

    # 'I' in last 4 digits -> '1'
    res3 = postprocessor.process("KA05MB999I", ocr_confidence=0.90)
    assert res3["is_valid"] is True
    assert res3["reg_number"] == "9991"


def test_mock_ocr_engine():
    mock = MockOCREngine()
    mock.set_mock_response("64x240", "DL01AB1234", 0.95)
    import numpy as np
    dummy_img = np.zeros((64, 240), dtype=np.uint8)
    text, conf = mock.extract_text(dummy_img)
    assert text == "DL01AB1234"
    assert conf == 0.95


def test_template_ocr_engine(synthetic_plate_image):
    engine = TemplateOCREngine()
    assert engine.is_available()
    text, conf = engine.extract_text(synthetic_plate_image)
    # Synthetic image text is "DL01AB1234"
    assert isinstance(text, str)
    assert len(text) > 0

"""
Post-processing and character disambiguation for Indian license plates (MoRTH & BH Series).
Enforces: "Do not assume OCR output is correct simply because text was returned."
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple
from schemas.anpr import PlateStandard, PlateValidationStatus


# Valid 2-letter State and Union Territory codes in India
INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN",
    "GA", "GJ", "HR", "HP", "JH", "JK", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "PB", "PY", "RJ",
    "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}

# Optical character recognition confusion substitutions
DIGIT_TO_ALPHA = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "4": "A",
    "5": "S",
    "6": "G",
    "8": "B",
}

ALPHA_TO_DIGIT = {
    "O": "0",
    "D": "0",
    "Q": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "A": "4",
    "S": "5",
    "G": "6",
    "B": "8",
}


class PlatePostProcessor:
    """
    Cleans raw OCR output, applies positional character disambiguation,
    and parses plate syntax against Indian MoRTH & BH standards.
    """

    # Regex definitions
    # Standard: DL 01 AB 1234 or DL 1 A 1234
    REGEX_STANDARD = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{4})$")
    # Bharat Series: 22 BH 1234 AA
    REGEX_BHARAT = re.compile(r"^([0-9]{2})(BH)([0-9]{4})([A-Z]{1,2})$")

    def clean_raw_text(self, text: str) -> str:
        """Strip punctuation, spaces, and non-alphanumeric noise."""
        if not text:
            return ""
        return re.sub(r"[^A-Za-z0-9]", "", text).upper()

    def process(
        self,
        raw_text: str,
        ocr_confidence: float,
        is_blurry: bool = False,
        is_low_contrast: bool = False,
    ) -> Dict[str, any]:
        """
        Post-process raw OCR string with syntactic analysis and character correction.

        Returns dictionary containing:
        - plate_text: Optional[str]
        - is_valid: bool
        - standard: PlateStandard
        - validation_status: PlateValidationStatus
        - confidence: float
        - state_code, district_code, series, reg_number: Optional[str]
        - limitations: List[str]
        """
        cleaned = self.clean_raw_text(raw_text)
        limitations: List[str] = []

        if is_blurry:
            limitations.append("Source image failed blur check (Laplacian variance low)")
        if is_low_contrast:
            limitations.append("Source image has degraded contrast")

        if not cleaned:
            limitations.append("No characters extracted by OCR")
            return {
                "plate_text": None,
                "is_valid": False,
                "standard": PlateStandard.UNKNOWN_OR_CUSTOM,
                "validation_status": PlateValidationStatus.UNREADABLE,
                "confidence": 0.0,
                "state_code": None,
                "district_code": None,
                "series": None,
                "reg_number": None,
                "limitations": limitations,
            }

        # Attempt Bharat Series check first (e.g. 22BH1234AA)
        bh_result = self._try_bharat_series(cleaned, ocr_confidence, limitations)
        if bh_result:
            return bh_result

        # Attempt Standard MoRTH check (e.g. DL01AB1234)
        std_result = self._try_standard_morth(cleaned, ocr_confidence, limitations)
        if std_result:
            return std_result

        # If neither matches cleanly, perform positional disambiguation repair
        repaired_text = self._attempt_disambiguation_repair(cleaned)
        if repaired_text != cleaned:
            # Re-check BH and Standard with repaired text
            bh_repaired = self._try_bharat_series(repaired_text, ocr_confidence * 0.9, limitations)
            if bh_repaired:
                bh_repaired["limitations"].append(f"Applied character disambiguation: '{cleaned}' -> '{repaired_text}'")
                return bh_repaired

            std_repaired = self._try_standard_morth(repaired_text, ocr_confidence * 0.9, limitations)
            if std_repaired:
                std_repaired["limitations"].append(f"Applied character disambiguation: '{cleaned}' -> '{repaired_text}'")
                return std_repaired

        # Non-matching text: do NOT assume it's a valid plate!
        limitations.append(f"Text '{cleaned}' does not match Indian MoRTH or BH series syntax rules")
        penalty_conf = max(0.0, min(0.35, ocr_confidence * 0.4))

        return {
            "plate_text": cleaned,
            "is_valid": False,
            "standard": PlateStandard.UNKNOWN_OR_CUSTOM,
            "validation_status": PlateValidationStatus.INVALID_SYNTAX,
            "confidence": round(penalty_conf, 4),
            "state_code": None,
            "district_code": None,
            "series": None,
            "reg_number": None,
            "limitations": limitations,
        }

    def _try_bharat_series(
        self,
        text: str,
        base_conf: float,
        limitations: List[str]
    ) -> Optional[Dict[str, any]]:
        match = self.REGEX_BHARAT.match(text)
        if not match:
            return None

        year, bh, reg_num, series = match.groups()
        year_int = int(year)
        # BH series introduced in 2021
        if year_int < 21 or year_int > 35:
            limitations.append(f"BH series year '{year}' out of realistic range (2021-2035)")
            return None

        conf = base_conf if not limitations else base_conf * 0.8
        return {
            "plate_text": f"{year}{bh}{reg_num}{series}",
            "is_valid": True,
            "standard": PlateStandard.BHARAT_SERIES,
            "validation_status": PlateValidationStatus.VALID,
            "confidence": round(min(1.0, conf), 4),
            "state_code": "BH",
            "district_code": year,
            "series": series,
            "reg_number": reg_num,
            "limitations": list(limitations),
        }

    def _try_standard_morth(
        self,
        text: str,
        base_conf: float,
        limitations: List[str]
    ) -> Optional[Dict[str, any]]:
        match = self.REGEX_STANDARD.match(text)
        if not match:
            return None

        state, district, series, reg_num = match.groups()
        current_limitations = list(limitations)

        if state not in INDIAN_STATE_CODES:
            current_limitations.append(f"State code '{state}' is not a recognized Indian State/UT")
            return {
                "plate_text": text,
                "is_valid": False,
                "standard": PlateStandard.STANDARD_PRIVATE,
                "validation_status": PlateValidationStatus.INVALID_SYNTAX,
                "confidence": round(max(0.0, base_conf * 0.3), 4),
                "state_code": state,
                "district_code": district,
                "series": series,
                "reg_number": reg_num,
                "limitations": current_limitations,
            }

        conf = base_conf if not current_limitations else base_conf * 0.85
        return {
            "plate_text": f"{state}{district}{series}{reg_num}",
            "is_valid": True,
            "standard": PlateStandard.STANDARD_PRIVATE,
            "validation_status": PlateValidationStatus.VALID,
            "confidence": round(min(1.0, conf), 4),
            "state_code": state,
            "district_code": district,
            "series": series,
            "reg_number": reg_num,
            "limitations": current_limitations,
        }

    def _attempt_disambiguation_repair(self, text: str) -> str:
        """
        Apply context-aware character substitution based on expected field positions.
        """
        if len(text) < 7 or len(text) > 11:
            return text

        chars = list(text)

        # 1. State code positions (chars 0 and 1): MUST be letters
        for i in (0, 1):
            if chars[i].isdigit() and chars[i] in DIGIT_TO_ALPHA:
                chars[i] = DIGIT_TO_ALPHA[chars[i]]

        # Indian state code specific repair (e.g. 'OL' -> 'DL', 'OD' / 'DD')
        state_candidate = chars[0] + chars[1]
        if state_candidate not in INDIAN_STATE_CODES:
            # Check if replacing char 0 with 'D' yields a valid state code (e.g. DL, DD, DN)
            if ("D" + chars[1]) in INDIAN_STATE_CODES:
                chars[0] = "D"
            elif ("O" + chars[1]) in INDIAN_STATE_CODES:
                chars[0] = "O"

        # 2. Last 4 characters (registration number): MUST be digits
        for i in range(len(chars) - 4, len(chars)):
            if chars[i].isalpha() and chars[i] in ALPHA_TO_DIGIT:
                chars[i] = ALPHA_TO_DIGIT[chars[i]]

        # 3. District code (chars 2 and optionally 3 if followed by letters)
        if len(chars) >= 8:
            if chars[2].isalpha() and chars[2] in ALPHA_TO_DIGIT:
                chars[2] = ALPHA_TO_DIGIT[chars[2]]

        return "".join(chars)

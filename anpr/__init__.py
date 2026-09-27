"""
ANPR module exports for Person 3.
"""

from .plate_detector import PlateCandidate, PlateDetector
from .preprocessor import PlatePreprocessor, PreprocessingResult
from .ocr_engine import BaseOCREngine, CompositeOCREngine, MockOCREngine, TemplateOCREngine, TesseractOCREngine
from .postprocessor import PlatePostProcessor, INDIAN_STATE_CODES
from .track_associator import TrackPlateAssociator
from .pipeline import ANPRPipeline

__all__ = [
    "PlateCandidate",
    "PlateDetector",
    "PlatePreprocessor",
    "PreprocessingResult",
    "BaseOCREngine",
    "CompositeOCREngine",
    "MockOCREngine",
    "TemplateOCREngine",
    "TesseractOCREngine",
    "PlatePostProcessor",
    "INDIAN_STATE_CODES",
    "TrackPlateAssociator",
    "ANPRPipeline",
]

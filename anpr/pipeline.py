"""
Unified ANPR Pipeline orchestrator for Person 3.
Coordinates plate detection/cropping, image quality preprocessing, OCR extraction,
MoRTH/BH postprocessing, track association, and evidence reference creation.
"""

from __future__ import annotations
from datetime import datetime, timezone
import os
import uuid
from typing import Dict, List, Optional
import cv2
import numpy as np

from schemas.detection import BoundingBox, DetectionRecord
from schemas.tracking import TrackedObject
from schemas.anpr import EvidenceReference, PlateRecord, PlateStandard, PlateValidationStatus
from .plate_detector import PlateCandidate, PlateDetector
from .preprocessor import PlatePreprocessor, PreprocessingResult
from .ocr_engine import BaseOCREngine, CompositeOCREngine
from .postprocessor import PlatePostProcessor
from .track_associator import TrackPlateAssociator


class ANPRPipeline:
    """
    Complete end-to-end ANPR Pipeline conforming to Person 3 specification card.
    """

    def __init__(
        self,
        ocr_engine: Optional[BaseOCREngine] = None,
        plate_detector: Optional[PlateDetector] = None,
        preprocessor: Optional[PlatePreprocessor] = None,
        postprocessor: Optional[PlatePostProcessor] = None,
        evidence_dir: Optional[str] = None,
    ):
        self.ocr_engine = ocr_engine or CompositeOCREngine()
        self.plate_detector = plate_detector or PlateDetector()
        self.preprocessor = preprocessor or PlatePreprocessor()
        self.postprocessor = postprocessor or PlatePostProcessor()
        self.associator = TrackPlateAssociator()
        self.evidence_dir = evidence_dir

        if self.evidence_dir and not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir, exist_ok=True)

    def process(
        self,
        frame: Optional[np.ndarray],
        frame_sequence_number: int,
        timestamp: datetime,
        camera_id: str,
        tracks: List[TrackedObject],
        detections: Optional[List[DetectionRecord]] = None,
    ) -> List[PlateRecord]:
        """
        Process a single frame to recognize number plates and associate them with vehicle tracks.
        Accepts real frame image arrays or mock detections.
        """
        plate_records: List[PlateRecord] = []
        raw_detections = detections or []

        # -------------------------------------------------------------
        # Mode A: Mock Detections (without raw frame pixels)
        # -------------------------------------------------------------
        if frame is None or frame.size == 0:
            for det in raw_detections:
                # Check if mock detection carries mock plate text in metadata
                mock_text = det.metadata.get("mock_plate_text")
                if mock_text is not None or det.class_name.lower() in ("license_plate", "plate"):
                    raw_str = mock_text or det.metadata.get("plate_text", "")
                    post_res = self.postprocessor.process(
                        raw_text=raw_str,
                        ocr_confidence=det.confidence,
                    )
                    v_track_id = self.associator.associate_plate_with_tracks(det.bounding_box, tracks)

                    ev_ref = EvidenceReference(
                        evidence_id=str(uuid.uuid4()),
                        camera_id=camera_id,
                        frame_sequence_number=frame_sequence_number,
                        timestamp=timestamp,
                        vehicle_track_id=v_track_id,
                        plate_bounding_box=det.bounding_box,
                        image_uri=None,
                        metadata={"source": "mock_detection"},
                    )

                    record = PlateRecord(
                        plate_text=post_res["plate_text"],
                        raw_text=raw_str,
                        plate_confidence=post_res["confidence"],
                        vehicle_track_id=v_track_id,
                        evidence_reference=ev_ref,
                        plate_bounding_box=det.bounding_box,
                        is_valid_format=post_res["is_valid"],
                        validation_status=post_res["validation_status"],
                        standard=post_res["standard"],
                        state_code=post_res["state_code"],
                        district_code=post_res["district_code"],
                        series=post_res["series"],
                        registration_number=post_res["reg_number"],
                        limitations=post_res["limitations"],
                        frame_sequence_number=frame_sequence_number,
                        timestamp=timestamp,
                    )

                    if v_track_id is not None:
                        self.associator.record_observation(v_track_id, record)
                        consensus = self.associator.get_consensus_plate(v_track_id)
                        for t in tracks:
                            if t.track_id == v_track_id and consensus and consensus.plate_text:
                                t.associated_plate_text = consensus.plate_text
                                t.associated_plate_confidence = consensus.plate_confidence

                    plate_records.append(record)
            return plate_records

        # -------------------------------------------------------------
        # Mode B: Real Frame Processing with Vision & OCR Pipeline
        # -------------------------------------------------------------
        # Extract vehicle and plate detection records
        v_dets = [d for d in raw_detections if d.class_name.lower() in ("car", "truck", "bus", "motorcycle", "van", "vehicle")]
        p_dets = [d for d in raw_detections if d.class_name.lower() in ("license_plate", "plate", "number_plate")]

        # Extract plate candidates
        candidates = self.plate_detector.extract_from_frame(
            frame=frame,
            vehicle_detections=v_dets,
            plate_detections=p_dets,
        )

        for cand in candidates:
            # 1. Preprocess crop
            prep_res: PreprocessingResult = self.preprocessor.process(cand.crop)

            # 2. Extract text via OCR
            raw_text = ""
            ocr_conf = 0.0

            if prep_res.is_acceptable_for_ocr:
                # Try OCR on both standard and inverted binary representations
                t1, c1 = self.ocr_engine.extract_text(prep_res.binary_standard)
                t2, c2 = self.ocr_engine.extract_text(prep_res.binary_inverted)
                if c2 > c1 and len(t2) >= len(t1):
                    raw_text, ocr_conf = t2, c2
                else:
                    raw_text, ocr_conf = t1, c1
            else:
                # Unacceptable quality (e.g. severe blur or zero contrast)
                ocr_conf = 0.0

            # 3. Post-process and validate against Indian standards
            post_res = self.postprocessor.process(
                raw_text=raw_text,
                ocr_confidence=ocr_conf,
                is_blurry=prep_res.is_blurry,
                is_low_contrast=prep_res.is_low_contrast,
            )

            # Add preprocessing quality issues to limitations documentation
            all_limitations = list(post_res["limitations"]) + prep_res.quality_issues

            # 4. Associate plate with vehicle tracks
            v_track_id = self.associator.associate_plate_with_tracks(cand.bbox_in_frame, tracks)

            # 5. Build Evidence Reference
            ev_id = str(uuid.uuid4())
            saved_uri: Optional[str] = None
            if self.evidence_dir:
                evidence_filename = f"plate_{camera_id}_f{frame_sequence_number}_{ev_id[:8]}.jpg"
                saved_path = os.path.join(self.evidence_dir, evidence_filename)
                cv2.imwrite(saved_path, cand.crop)
                saved_uri = saved_path

            ev_ref = EvidenceReference(
                evidence_id=ev_id,
                camera_id=camera_id,
                frame_sequence_number=frame_sequence_number,
                timestamp=timestamp,
                vehicle_track_id=v_track_id,
                plate_bounding_box=cand.bbox_in_frame,
                vehicle_bounding_box=cand.parent_vehicle_bbox,
                image_uri=saved_uri,
                metadata={
                    "detection_source": cand.detection_source,
                    "blur_score": prep_res.blur_score,
                    "contrast_score": prep_res.contrast_score,
                },
            )

            record = PlateRecord(
                plate_text=post_res["plate_text"],
                raw_text=raw_text,
                plate_confidence=post_res["confidence"],
                vehicle_track_id=v_track_id,
                evidence_reference=ev_ref,
                plate_bounding_box=cand.bbox_in_frame,
                is_valid_format=post_res["is_valid"],
                validation_status=post_res["validation_status"],
                standard=post_res["standard"],
                state_code=post_res["state_code"],
                district_code=post_res["district_code"],
                series=post_res["series"],
                registration_number=post_res["reg_number"],
                limitations=all_limitations,
                frame_sequence_number=frame_sequence_number,
                timestamp=timestamp,
            )

            # 6. Multi-frame track consensus
            if v_track_id is not None:
                self.associator.record_observation(v_track_id, record)
                consensus = self.associator.get_consensus_plate(v_track_id)
                for t in tracks:
                    if t.track_id == v_track_id and consensus and consensus.plate_text:
                        t.associated_plate_text = consensus.plate_text
                        t.associated_plate_confidence = consensus.plate_confidence

            plate_records.append(record)

        return plate_records

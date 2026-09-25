import pytest
from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.models import (
    Base,
    Camera,
    Detection,
    Track,
    ANPRRecord,
    Event,
    Alert
)

def test_models_import_and_table_names():
    assert Camera.__tablename__ == "cameras"
    assert Detection.__tablename__ == "detections"
    assert Track.__tablename__ == "tracks"
    assert ANPRRecord.__tablename__ == "anpr_records"
    assert Event.__tablename__ == "events"
    assert Alert.__tablename__ == "alerts"

def test_camera_model_structure():
    assert Camera.__table__.primary_key.columns.keys() == ["camera_id"]
    assert "is_active" in Camera.__table__.columns
    assert "stream_url" in Camera.__table__.columns
    assert Camera.__table__.columns["created_at"].type.timezone is True

def test_detection_model_structure():
    assert Detection.__table__.primary_key.columns.keys() == ["id"]
    camera_fk = list(Detection.__table__.columns["camera_id"].foreign_keys)[0]
    assert camera_fk.target_fullname == "cameras.camera_id"
    assert camera_fk.ondelete == "RESTRICT"
    assert isinstance(Detection.__table__.columns["bbox"].type, JSONB)
    assert Detection.__table__.columns["timestamp"].type.timezone is True

    # Verify check constraint
    constraints = [c.name for c in Detection.__table__.constraints if hasattr(c, "name")]
    assert "check_detection_confidence_range" in constraints

def test_tracking_model_structure():
    assert Track.__table__.primary_key.columns.keys() == ["id"]
    camera_fk = list(Track.__table__.columns["camera_id"].foreign_keys)[0]
    assert camera_fk.target_fullname == "cameras.camera_id"
    assert camera_fk.ondelete == "RESTRICT"
    assert "track_id" in Track.__table__.columns
    assert isinstance(Track.__table__.columns["bbox"].type, JSONB)
    assert isinstance(Track.__table__.columns["tracking_metadata"].type, JSONB)

def test_anpr_model_structure():
    assert ANPRRecord.__table__.primary_key.columns.keys() == ["id"]
    # Verify no foreign key exists on track_id
    assert len(ANPRRecord.__table__.columns["track_id"].foreign_keys) == 0
    assert "plate_text" in ANPRRecord.__table__.columns

    # Verify check constraint
    constraints = [c.name for c in ANPRRecord.__table__.constraints if hasattr(c, "name")]
    assert "check_anpr_confidence_range" in constraints

def test_event_model_structure():
    assert Event.__table__.primary_key.columns.keys() == ["event_id"]
    camera_fk = list(Event.__table__.columns["camera_id"].foreign_keys)[0]
    assert camera_fk.target_fullname == "cameras.camera_id"
    assert camera_fk.ondelete == "RESTRICT"
    assert "object_track" in Event.__table__.columns

    # Verify check constraint
    constraints = [c.name for c in Event.__table__.constraints if hasattr(c, "name")]
    assert "check_event_type_valid" in constraints

def test_alert_model_structure():
    assert Alert.__table__.primary_key.columns.keys() == ["id"]
    event_fk = list(Alert.__table__.columns["event_id"].foreign_keys)[0]
    assert event_fk.target_fullname == "events.event_id"
    assert event_fk.ondelete == "RESTRICT"

    # Verify check constraints
    constraints = [c.name for c in Alert.__table__.constraints if hasattr(c, "name")]
    assert "check_alert_priority_valid" in constraints
    assert "check_alert_status_valid" in constraints

def test_indexes_exist():
    def get_index_names(table):
        return [idx.name for idx in table.indexes]

    assert "idx_detections_camera_ts" in get_index_names(Detection.__table__)
    assert "idx_tracks_camera_track" in get_index_names(Track.__table__)
    assert "idx_anpr_plate_text" in get_index_names(ANPRRecord.__table__)
    assert "idx_events_camera_ts" in get_index_names(Event.__table__)
    assert "idx_alerts_status_priority_ts" in get_index_names(Alert.__table__)

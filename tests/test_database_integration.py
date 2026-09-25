import os
import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError, DBAPIError

from backend.app.models import (
    Base,
    Camera,
    Detection,
    Track,
    ANPRRecord,
    Event,
    Alert,
)

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL") or os.getenv("DATABASE_URL")

# Helper to check if PostgreSQL is accessible
async def _check_postgres_connection(url: str) -> bool:
    try:
        engine = create_async_engine(url, connect_args={"connect_timeout": 3})
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False

# Determine availability at module collection time or test time
POSTGRES_AVAILABLE = False
if TEST_POSTGRES_URL:
    try:
        POSTGRES_AVAILABLE = asyncio.run(_check_postgres_connection(TEST_POSTGRES_URL))
    except Exception:
        POSTGRES_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not POSTGRES_AVAILABLE,
    reason="PostgreSQL database is not available. Set TEST_POSTGRES_URL or DATABASE_URL to a valid PostgreSQL connection string."
)


@pytest.fixture(scope="module")
def postgres_engine():
    """Module-scoped async engine connected to PostgreSQL."""
    engine = create_async_engine(TEST_POSTGRES_URL, echo=False)
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(scope="module", autouse=True)
def run_alembic_migrations(postgres_engine):
    """Run Alembic migrations to head before tests and downgrade after."""
    ini_path = BASE_DIR / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(BASE_DIR / "database" / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_POSTGRES_URL)

    # Upgrade schema to head
    command.upgrade(alembic_cfg, "head")
    yield
    # Downgrade schema back to base for clean tear down
    try:
        command.downgrade(alembic_cfg, "base")
    except Exception:
        pass


@pytest.fixture
async def db_session(postgres_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional AsyncSession for each integration test with automatic rollback."""
    async_session_factory = async_sessionmaker(postgres_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# --- PostgreSQL Integration Test Cases ---

def test_alembic_upgrade_to_head_and_table_existence(postgres_engine):
    """Verify Alembic migration executed and all six target tables exist in PostgreSQL."""
    def inspect_tables(sync_conn):
        inspector = inspect(sync_conn)
        return set(inspector.get_table_names())

    async def get_tables():
        async with postgres_engine.connect() as conn:
            return await conn.run_sync(inspect_tables)

    existing_tables = asyncio.run(get_tables())
    expected_tables = {"cameras", "detections", "tracks", "anpr_records", "events", "alerts"}
    assert expected_tables.issubset(existing_tables), f"Missing tables: {expected_tables - existing_tables}"


@pytest.mark.asyncio
async def test_primary_keys_and_foreign_keys_work(db_session: AsyncSession):
    """Verify primary keys and camera -> detection/track/event foreign keys work."""
    cam = Camera(
        camera_id="cam_test_001",
        name="Test Camera North Gate",
        location="North Entrance",
        stream_url="rtsp://synthetic.local/live",
        is_active=True
    )
    db_session.add(cam)
    await db_session.flush()

    det = Detection(
        camera_id="cam_test_001",
        timestamp=text("now()"),
        class_="person",
        confidence=0.92,
        bbox={"x_min": 10, "y_min": 20, "x_max": 50, "y_max": 100},
        model_version="v1.0.0"
    )
    db_session.add(det)
    await db_session.flush()
    assert det.id is not None

    trk = Track(
        camera_id="cam_test_001",
        track_id="trk_synthetic_99",
        class_="vehicle",
        bbox={"x_min": 5, "y_min": 5, "x_max": 40, "y_max": 60},
        timestamp=text("now()"),
        tracking_metadata={"speed_estimate": 25.5}
    )
    db_session.add(trk)
    await db_session.flush()
    assert trk.id is not None

    evt = Event(
        event_id="evt_synthetic_101",
        camera_id="cam_test_001",
        timestamp=text("now()"),
        event_type="virtual_fence",
        object_track="trk_synthetic_99",
        zone_rule="perimeter_alpha",
        evidence_reference="http://storage.local/evidence/evt_101.mp4"
    )
    db_session.add(evt)
    await db_session.flush()
    assert evt.event_id == "evt_synthetic_101"


@pytest.mark.asyncio
async def test_on_delete_restrict_enforced(db_session: AsyncSession):
    """Verify ON DELETE RESTRICT behavior prevents deleting a camera referenced by a detection."""
    cam = Camera(camera_id="cam_test_restrict", name="Restrict Test Cam")
    db_session.add(cam)
    await db_session.flush()

    det = Detection(
        camera_id="cam_test_restrict",
        timestamp=text("now()"),
        class_="person",
        confidence=0.85,
        bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1}
    )
    db_session.add(det)
    await db_session.flush()

    # Attempt to delete the parent camera
    await db_session.delete(cam)
    with pytest.raises((IntegrityError, DBAPIError)):
        await db_session.flush()


@pytest.mark.asyncio
async def test_anpr_soft_reference_without_track(db_session: AsyncSession):
    """Verify ANPR record track_id remains a soft reference and does not require a corresponding track."""
    anpr = ANPRRecord(
        track_id="non_existent_track_9999",
        vehicle_reference="veh_ref_abc",
        plate_text="KA01AB1234",
        confidence=0.98,
        evidence_reference="http://storage.local/anpr/plate1.jpg"
    )
    db_session.add(anpr)
    await db_session.flush()
    assert anpr.id is not None
    assert anpr.track_id == "non_existent_track_9999"


@pytest.mark.asyncio
async def test_detection_confidence_check_constraint(db_session: AsyncSession):
    """Verify detection confidence rejects values outside 0..1 range."""
    cam = Camera(camera_id="cam_test_conf", name="Conf Test Cam")
    db_session.add(cam)
    await db_session.flush()

    invalid_det_high = Detection(
        camera_id="cam_test_conf",
        timestamp=text("now()"),
        class_="person",
        confidence=1.5,
        bbox={"x": 0, "y": 0}
    )
    db_session.add(invalid_det_high)
    with pytest.raises((IntegrityError, DBAPIError)):
        await db_session.flush()


@pytest.mark.asyncio
async def test_anpr_confidence_check_constraint(db_session: AsyncSession):
    """Verify ANPR confidence rejects values outside 0..1 range."""
    invalid_anpr_low = ANPRRecord(
        plate_text="MH12CD5678",
        confidence=-0.1
    )
    db_session.add(invalid_anpr_low)
    with pytest.raises((IntegrityError, DBAPIError)):
        await db_session.flush()


@pytest.mark.asyncio
async def test_event_type_check_constraint(db_session: AsyncSession):
    """Verify event_type rejects unsupported values."""
    cam = Camera(camera_id="cam_test_evt_type", name="Evt Type Cam")
    db_session.add(cam)
    await db_session.flush()

    invalid_evt = Event(
        event_id="evt_invalid_type_01",
        camera_id="cam_test_evt_type",
        timestamp=text("now()"),
        event_type="invalid_custom_event",
        object_track="trk_01",
        zone_rule="zone_01",
        evidence_reference="ref"
    )
    db_session.add(invalid_evt)
    with pytest.raises((IntegrityError, DBAPIError)):
        await db_session.flush()


@pytest.mark.asyncio
async def test_alert_priority_and_status_check_constraints(db_session: AsyncSession):
    """Verify alert priority and status reject unsupported values."""
    cam = Camera(camera_id="cam_test_alert_chk", name="Alert Check Cam")
    db_session.add(cam)
    await db_session.flush()

    evt = Event(
        event_id="evt_valid_001",
        camera_id="cam_test_alert_chk",
        timestamp=text("now()"),
        event_type="night_movement",
        object_track="trk_01",
        zone_rule="zone_01",
        evidence_reference="ref"
    )
    db_session.add(evt)
    await db_session.flush()

    invalid_priority_alert = Alert(
        event_id="evt_valid_001",
        priority="SUPER_HIGH",
        timestamp=text("now()"),
        status="UNREAD",
        message="Test msg"
    )
    db_session.add(invalid_priority_alert)
    with pytest.raises((IntegrityError, DBAPIError)):
        await db_session.flush()


@pytest.mark.asyncio
async def test_approved_indexes_exist(postgres_engine):
    """Verify all approved database indexes exist in PostgreSQL schema."""
    def inspect_indexes(sync_conn):
        inspector = inspect(sync_conn)
        indexes = {}
        for table_name in ["detections", "tracks", "anpr_records", "events", "alerts"]:
            indexes[table_name] = [idx["name"] for idx in inspector.get_indexes(table_name)]
        return indexes

    async def get_indexes():
        async with postgres_engine.connect() as conn:
            return await conn.run_sync(inspect_indexes)

    table_indexes = await get_indexes()
    assert "idx_detections_camera_ts" in table_indexes["detections"]
    assert "idx_tracks_camera_track" in table_indexes["tracks"]
    assert "idx_tracks_timestamp" in table_indexes["tracks"]
    assert "idx_anpr_plate_text" in table_indexes["anpr_records"]
    assert "idx_anpr_track_id" in table_indexes["anpr_records"]
    assert "idx_events_camera_ts" in table_indexes["events"]
    assert "idx_events_type_ts" in table_indexes["events"]
    assert "idx_events_object_track" in table_indexes["events"]
    assert "idx_alerts_status_priority_ts" in table_indexes["alerts"]
    assert "idx_alerts_event_id" in table_indexes["alerts"]


@pytest.mark.asyncio
async def test_jsonb_columns_structured_data(db_session: AsyncSession):
    """Verify JSONB columns accept valid structured dictionary data."""
    cam = Camera(camera_id="cam_test_jsonb", name="JSONB Test Cam")
    db_session.add(cam)
    await db_session.flush()

    det = Detection(
        camera_id="cam_test_jsonb",
        timestamp=text("now()"),
        class_="car",
        confidence=0.88,
        bbox={"x_min": 10.5, "y_min": 20.2, "x_max": 100.0, "y_max": 200.0, "nested": {"key": "val"}},
        model_version="v2.1"
    )
    db_session.add(det)
    await db_session.flush()
    assert det.bbox["nested"]["key"] == "val"


@pytest.mark.asyncio
async def test_timestamp_columns_timezone_aware(db_session: AsyncSession):
    """Verify timestamp columns handle timezone-aware datetime values properly."""
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)

    cam = Camera(camera_id="cam_test_tz", name="TZ Test Cam")
    db_session.add(cam)
    await db_session.flush()

    det = Detection(
        camera_id="cam_test_tz",
        timestamp=now_utc,
        class_="person",
        confidence=0.95,
        bbox={"x": 0, "y": 0}
    )
    db_session.add(det)
    await db_session.flush()
    assert det.timestamp.tzinfo is not None


@pytest.mark.asyncio
async def test_event_alert_relationship(db_session: AsyncSession):
    """Verify Event -> Alert ORM relationship and database behavior."""
    cam = Camera(camera_id="cam_test_rel", name="Rel Test Cam")
    db_session.add(cam)
    await db_session.flush()

    evt = Event(
        event_id="evt_rel_001",
        camera_id="cam_test_rel",
        timestamp=text("now()"),
        event_type="dwell_presence",
        object_track="trk_rel_1",
        zone_rule="restricted_bay",
        evidence_reference="http://storage.local/rel.mp4"
    )
    db_session.add(evt)
    await db_session.flush()

    alt1 = Alert(
        event_id="evt_rel_001",
        priority="HIGH",
        timestamp=text("now()"),
        status="UNREAD",
        message="Loitering detected in bay"
    )
    alt2 = Alert(
        event_id="evt_rel_001",
        priority="CRITICAL",
        timestamp=text("now()"),
        status="ACKNOWLEDGED",
        message="Escalated loitering alert"
    )
    db_session.add_all([alt1, alt2])
    await db_session.flush()

    assert len(evt.alerts) == 2
    assert alt1.event.event_id == "evt_rel_001"


@pytest.mark.asyncio
async def test_camera_relationships(db_session: AsyncSession):
    """Verify Camera -> Detection/Track/Event ORM relationships."""
    cam = Camera(camera_id="cam_test_rel_all", name="Camera Rel All")
    db_session.add(cam)
    await db_session.flush()

    det = Detection(camera_id="cam_test_rel_all", timestamp=text("now()"), class_="person", confidence=0.8, bbox={})
    trk = Track(camera_id="cam_test_rel_all", track_id="trk_all_1", class_="person", bbox={}, timestamp=text("now()"))
    evt = Event(event_id="evt_all_1", camera_id="cam_test_rel_all", timestamp=text("now()"), event_type="suspicious_rule", object_track="trk_all_1", zone_rule="zone_x", evidence_reference="ref")

    db_session.add_all([det, trk, evt])
    await db_session.flush()

    assert len(cam.detections) == 1
    assert len(cam.tracks) == 1
    assert len(cam.events) == 1


@pytest.mark.asyncio
async def test_repository_layer_crud_operations(db_session: AsyncSession):
    """Verify repository layer CRUD operations against live PostgreSQL schema."""
    from datetime import datetime, timezone
    from backend.app.repositories import (
        CameraRepository,
        DetectionRepository,
        TrackRepository,
        ANPRRepository,
        EventRepository,
        AlertRepository
    )

    cam_repo = CameraRepository(db_session)
    det_repo = DetectionRepository(db_session)
    trk_repo = TrackRepository(db_session)
    anpr_repo = ANPRRepository(db_session)
    evt_repo = EventRepository(db_session)
    alt_repo = AlertRepository(db_session)

    now = datetime.now(timezone.utc)

    # 1. Camera CRUD
    cam = await cam_repo.create(camera_id="cam_repo_pg", name="PG Repo Cam", location="East Gate")
    assert (await cam_repo.get_by_id("cam_repo_pg")) is not None
    cams = await cam_repo.list_all(is_active_only=True)
    assert any(c.camera_id == "cam_repo_pg" for c in cams)
    updated_cam = await cam_repo.update_active_status("cam_repo_pg", False)
    assert updated_cam.is_active is False

    # 2. Detection CRUD
    det = await det_repo.create(camera_id="cam_repo_pg", timestamp=now, class_name="person", confidence=0.88, bbox=[10, 20, 30, 40])
    assert det.id is not None
    dets = await det_repo.query_by_camera_and_time("cam_repo_pg")
    assert len(dets) >= 1
    recent_dets = await det_repo.query_recent(limit=5, camera_id="cam_repo_pg")
    assert len(recent_dets) >= 1

    # 3. Track CRUD
    trk = await trk_repo.create(camera_id="cam_repo_pg", track_id="trk_repo_pg_1", class_name="person", bbox=[5, 5, 25, 25], timestamp=now)
    assert trk.id is not None
    trks = await trk_repo.query_tracks(camera_id="cam_repo_pg", track_id="trk_repo_pg_1")
    assert len(trks) >= 1

    # 4. ANPR CRUD
    anpr = await anpr_repo.create(plate_text="MH02CL9999", confidence=0.96, track_id="trk_repo_pg_1", timestamp=now)
    assert anpr.id is not None
    anpr_by_plate = await anpr_repo.query_by_plate_text("MH02CL9999")
    assert len(anpr_by_plate) >= 1
    anpr_by_trk = await anpr_repo.query_by_track_id("trk_repo_pg_1")
    assert len(anpr_by_trk) >= 1

    # 5. Event CRUD
    evt = await evt_repo.create(
        event_id="evt_repo_pg_1",
        camera_id="cam_repo_pg",
        timestamp=now,
        event_type="virtual_fence",
        object_track="trk_repo_pg_1",
        zone_rule="zone_east",
        evidence_reference="http://evidence.local/evt1.mp4"
    )
    assert (await evt_repo.get_by_id("evt_repo_pg_1")) is not None
    evts = await evt_repo.query_events(camera_id="cam_repo_pg", event_type="virtual_fence")
    assert len(evts) >= 1

    # 6. Alert CRUD
    alt = await alt_repo.create(event_id="evt_repo_pg_1", priority="CRITICAL", timestamp=now, message="Boundary breached")
    assert alt.id is not None
    alts = await alt_repo.list_alerts(status="UNREAD", priority="CRITICAL")
    assert len(alts) >= 1
    updated_alt = await alt_repo.update_status(alt.id, "ACKNOWLEDGED")
    assert updated_alt.status == "ACKNOWLEDGED"
    recent_alts = await alt_repo.query_recent(limit=5)
    assert len(recent_alts) >= 1


@pytest.mark.asyncio
async def test_api_persistence_integration(db_session: AsyncSession):
    """Verify FastAPI endpoint persistence flow against live PostgreSQL database."""
    from backend.app.api.v1.endpoints.ingestion import ingest_detection, ingest_event, ingest_alert
    from backend.app.schemas.contracts import DetectionSchema, EventSchema, AlertSchema, AlertPriorityEnum, AlertStatusEnum

    det_payload = DetectionSchema(
        camera_id="CAM_PG_API_01",
        timestamp="2026-09-24T21:00:00Z",
        class_name="human",
        confidence=0.91,
        bbox=[10.0, 20.0, 30.0, 40.0],
        model_version="v1.0"
    )
    det_res = await ingest_detection(payload=det_payload, db=db_session)
    assert det_res["status"] == "success"
    assert det_res["data"]["class"] == "human"

    evt_payload = EventSchema(
        event_id="EVT_PG_API_101",
        camera_id="CAM_PG_API_01",
        timestamp="2026-09-24T21:00:05Z",
        event_type="virtual_fence",
        object_track="TRK_PG_99",
        zone_rule="ZONE_NORTH",
        evidence_reference="/ref/evt101.mp4"
    )
    evt_res = await ingest_event(payload=evt_payload, db=db_session)
    assert evt_res["status"] == "success"
    assert evt_res["data"]["event_id"] == "EVT_PG_API_101"

    alt_payload = AlertSchema(
        event_id="EVT_PG_API_101",
        priority=AlertPriorityEnum.HIGH,
        timestamp="2026-09-24T21:00:06Z",
        status=AlertStatusEnum.UNREAD,
        message="Fence breach detected on CAM_PG_API_01",
        reference="/ref/evt101.mp4"
    )
    alt_res = await ingest_alert(payload=alt_payload, db=db_session)
    assert alt_res["status"] == "success"
    assert alt_res["data"]["event_id"] == "EVT_PG_API_101"



import os
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from backend.app.models import Base

BASE_DIR = Path(__file__).resolve().parents[1]

def test_alembic_ini_file_exists():
    ini_path = BASE_DIR / "alembic.ini"
    assert ini_path.exists()

def test_alembic_config_and_script_location():
    ini_path = BASE_DIR / "alembic.ini"
    config = Config(str(ini_path))
    assert config.get_main_option("script_location") == "IBVAP_SIH_2026/database/alembic"

def test_alembic_target_metadata_coverage():
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {"cameras", "detections", "tracks", "anpr_records", "events", "alerts"}
    assert table_names == expected_tables
    # Confirm frame metadata is transient and NOT a persistent database table
    assert "frames" not in table_names

def test_alembic_migration_revision_exists():
    ini_path = BASE_DIR / "alembic.ini"
    config = Config(str(ini_path))
    config.set_main_option("script_location", str(BASE_DIR / "database" / "alembic"))
    script = ScriptDirectory.from_config(config)
    revisions = list(script.walk_revisions())
    assert len(revisions) == 1
    assert revisions[0].revision == "001_initial_schema"

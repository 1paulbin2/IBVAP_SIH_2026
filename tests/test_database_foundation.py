import pytest
from backend.app.core.config import Settings
from backend.app.core.database import engine, AsyncSessionLocal, check_db_connection

def test_settings_default_and_database_url():
    test_settings = Settings(
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test_db",
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password"
    )
    assert test_settings.database_url == "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"

def test_async_engine_and_session_factory():
    assert engine.name == "postgresql"
    assert engine.driver == "asyncpg"
    assert AsyncSessionLocal is not None

@pytest.mark.asyncio
async def test_check_db_connection_graceful_fallback():
    # Unless a live PostgreSQL server is running at localhost:5432 with valid credentials,
    # check_db_connection should safely return False without raising unhandled exceptions.
    is_connected = await check_db_connection()
    assert isinstance(is_connected, bool)

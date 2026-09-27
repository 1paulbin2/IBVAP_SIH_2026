import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from backend.app.api.v1.endpoints.ingestion import router as ingestion_router
from backend.app.api.v1.endpoints.websocket import router as websocket_router
from backend.app.core.redis import check_redis_connection, close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # --- Startup ---
    redis_ok = await check_redis_connection()
    if redis_ok:
        logger.info("Redis connection established")
    else:
        logger.warning(
            "Redis is not available – features that depend on Redis will be disabled"
        )
    yield
    # --- Shutdown ---
    await close_redis()
    logger.info("Redis connection closed")


app = FastAPI(
    title="IBVAP - Intelligent Border Video Analytics Platform API",
    description="Person 6 Backend & Ingestion API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "Person 6 Backend"}

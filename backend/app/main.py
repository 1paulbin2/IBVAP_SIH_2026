from fastapi import FastAPI
from backend.app.api.v1.endpoints.ingestion import router as ingestion_router

app = FastAPI(
    title="IBVAP - Intelligent Border Video Analytics Platform API",
    description="Person 6 Backend & Ingestion API",
    version="0.1.0"
)

app.include_router(ingestion_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "Person 6 Backend"}

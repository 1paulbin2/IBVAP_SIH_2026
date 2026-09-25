from fastapi import FastAPI, HTTPException

from schemas.event_schema import SecurityEvent
from security.security import validate_event
from alerts.alert_manager import generate_alert
from evidence.evidence import create_event_hash


app = FastAPI(title="IBVAP Security and Alert API")

previous_hash = ""


@app.get("/")
def home():
    return {"message": "IBVAP Security API is running"}


@app.post("/events")
def receive_event(event: SecurityEvent):
    global previous_hash

    valid, message = validate_event(event)

    if not valid:
        raise HTTPException(status_code=400, detail=message)

    event_data = event.model_dump(mode="json")

    current_hash = create_event_hash(
        event_data,
        previous_hash
    )

    previous_hash = current_hash

    alert = generate_alert(event)

    return {
        "status": "accepted",
        "event": event_data,
        "evidence_hash": current_hash,
        "alert": alert
    }
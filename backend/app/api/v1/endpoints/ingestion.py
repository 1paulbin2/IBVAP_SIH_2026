from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError, IntegrityError
from backend.app.core.redis_pubsub import publish_event
import logging

from backend.app.core.database import get_db
from backend.app.schemas.contracts import (
    FrameSchema,
    DetectionSchema,
    TrackingSchema,
    ANPRSchema,
    EventSchema,
    AlertSchema
)
from backend.app.services import (
    DetectionService,
    TrackService,
    ANPRService,
    EventService,
    AlertService,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ServiceValidationError
)
from backend.app.services.helpers import parse_iso_datetime
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/frame", status_code=status.HTTP_201_CREATED)
async def ingest_frame(payload: FrameSchema) -> Dict[str, Any]:
    """Frame metadata ingestion (ephemeral, not persisted to DB)."""
    return {
        "status": "success",
        "message": "Frame ingested",
        "data": payload.model_dump()
    }


@router.post("/detection", status_code=status.HTTP_201_CREATED)
async def ingest_detection(
    payload: DetectionSchema,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Ingest object detection record into PostgreSQL."""
    try:
        service = DetectionService(db)
        dt = parse_iso_datetime(payload.timestamp)
        detection = await service.ingest_detection(
            camera_id=payload.camera_id,
            timestamp=dt,
            class_name=payload.class_name,
            confidence=payload.confidence,
            bbox=payload.bbox,
            model_version=payload.model_version
        )
        await db.commit()
        return {
            "status": "success",
            "message": "Detection ingested",
            "data": {
                "id": detection.id,
                "camera_id": detection.camera_id,
                "class": detection.class_name,
                "confidence": detection.confidence,
                "bbox": detection.bbox,
            "model_version": detection.model_version
        }
    }
    except EntityNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EntityAlreadyExistsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ServiceValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (IntegrityError, DBAPIError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity error processing detection.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing detection.")


@router.post("/tracking", status_code=status.HTTP_201_CREATED)
async def ingest_tracking(
    payload: TrackingSchema,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Ingest object track record into PostgreSQL."""
    try:
        service = TrackService(db)
        dt = parse_iso_datetime(payload.timestamp)
        track = await service.ingest_track(
            camera_id=payload.camera_id,
            track_id=payload.track_id,
            class_name=payload.class_name,
            bbox=payload.bbox,
            timestamp=dt,
            tracking_metadata=payload.tracking_metadata
        )
        await db.commit()
        return {
            "status": "success",
            "message": "Tracking ingested",
            "data": {
                "id": track.id,
                "camera_id": track.camera_id,
                "track_id": track.track_id,
                "class": track.class_name,
                "bbox": track.bbox,
                "timestamp": payload.timestamp,
                "tracking_metadata": track.tracking_metadata
            }
        }
    except EntityNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EntityAlreadyExistsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ServiceValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (IntegrityError, DBAPIError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity error processing track.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing track.")


@router.post("/anpr", status_code=status.HTTP_201_CREATED)
async def ingest_anpr(
    payload: ANPRSchema,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Ingest ANPR record into PostgreSQL."""
    try:
        service = ANPRService(db)
        anpr = await service.ingest_anpr_record(
            plate_text=payload.plate_text,
            confidence=payload.confidence,
            track_id=payload.track_id,
            vehicle_reference=payload.vehicle_reference,
            evidence_reference=payload.evidence_reference
        )
        await db.commit()
        return {
            "status": "success",
            "message": "ANPR ingested",
            "data": {
                "id": anpr.id,
                "track_id": anpr.track_id,
                "vehicle_reference": anpr.vehicle_reference,
                "plate_text": anpr.plate_text,
                "confidence": anpr.confidence,
                "evidence_reference": anpr.evidence_reference
            }
        }
    except EntityNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EntityAlreadyExistsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ServiceValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (IntegrityError, DBAPIError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity error processing ANPR record.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing ANPR record.")


@router.post("/event", status_code=status.HTTP_201_CREATED)
async def ingest_event(
    payload: EventSchema,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Ingest analytics event into PostgreSQL."""
    try:
        service = EventService(db)
        dt = parse_iso_datetime(payload.timestamp)
        event = await service.record_event(
            event_id=payload.event_id,
            camera_id=payload.camera_id,
            timestamp=dt,
            event_type=payload.event_type,
            object_track=payload.object_track,
            zone_rule=payload.zone_rule,
            evidence_reference=payload.evidence_reference
        )
        await db.commit()

        try:
            await publish_event({
                "type": "event.created",
                "event_id": event.event_id,
                "camera_id": event.camera_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),})
        except Exception:
            logger.exception("Failed to publish event to Redis")
        return {
            "status": "success",
            "message": "Event ingested",
            "data": {
                "event_id": event.event_id,
                "camera_id": event.camera_id,
                "timestamp": payload.timestamp,
                "event_type": event.event_type,
                "object_track": event.object_track,
                "zone_rule": event.zone_rule,
                "evidence_reference": event.evidence_reference
            }
        }
    except EntityAlreadyExistsError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except EntityNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (IntegrityError, DBAPIError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity error processing event.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing event.")


@router.post("/alert", status_code=status.HTTP_201_CREATED)
async def ingest_alert(
    payload: AlertSchema,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Ingest alert into PostgreSQL."""
    try:
        service = AlertService(db)
        dt = parse_iso_datetime(payload.timestamp)
        alert = await service.create_alert_from_event(
            event_id=payload.event_id,
            priority=payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority),
            timestamp=dt,
            message=payload.message,
            status=payload.status.value if hasattr(payload.status, "value") else str(payload.status),
            reference=payload.reference
        )
        await db.commit()

        try:
            await publish_event({
                "type": "alert.created",
                "alert_id": alert.id,
                "event_id": alert.event_id,
                "priority": alert.priority,
                "status": alert.status,
                "message": alert.message,
            })
        except Exception:
            logger.exception("Failed to publish alert to Redis")

        return {
            "status": "success",
            "message": "Alert ingested",
            "data": {
                "id": alert.id,
                "event_id": alert.event_id,
                "priority": alert.priority,
                "timestamp": payload.timestamp,
                "status": alert.status,
                "message": alert.message,
                "reference": alert.reference
            }
        }
    except EntityNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (EntityAlreadyExistsError, ServiceValidationError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (IntegrityError, DBAPIError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity error processing alert.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing alert.")

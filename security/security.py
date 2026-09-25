from schemas.event_schema import SecurityEvent


def validate_event(event: SecurityEvent):
    if not event.event_id:
        return False, "Missing event ID"

    if not event.camera_id:
        return False, "Missing camera ID"

    if not event.event_type:
        return False, "Missing event type"

    if not 0 <= event.confidence <= 1:
        return False, "Invalid confidence"

    if not event.location:
        return False, "Missing location"

    return True, "Event validated"
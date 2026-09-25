def generate_alert(event):
    high_priority_events = [
        "VIRTUAL_FENCE_BREACH",
        "SUSPICIOUS_ACTIVITY",
        "NIGHT_MOVEMENT"
    ]

    if event.event_type in high_priority_events:
        return {
            "event_id": event.event_id,
            "severity": "HIGH",
            "message": f"Security event detected at {event.location}",
            "status": "NEW"
        }

    return {
        "event_id": event.event_id,
        "severity": "MEDIUM",
        "message": f"{event.event_type} detected",
        "status": "NEW"
    }
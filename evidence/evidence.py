import hashlib
import json


def create_event_hash(event_data, previous_hash=""):
    record = {
        "event": event_data,
        "previous_hash": previous_hash
    }

    record_string = json.dumps(record, sort_keys=True)

    return hashlib.sha256(record_string.encode()).hexdigest()
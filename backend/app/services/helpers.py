from datetime import datetime
from typing import Dict, Any, Optional

def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO formatted timestamp string into datetime object."""
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)

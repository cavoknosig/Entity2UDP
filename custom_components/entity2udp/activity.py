"""Recent Entity2UDP activity shared by all destination entries."""
from collections import deque
from datetime import datetime, timezone

from .const import DOMAIN

_KEY = f"{DOMAIN}.activity"
LIMIT = 200


def record_activity(hass, entry, kind: str, message: str) -> None:
    events = hass.data.setdefault(_KEY, deque(maxlen=LIMIT))
    events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "destination_id": entry.entry_id,
        "destination": entry.title,
        "kind": kind,
        "message": message,
    })


def recent_activity(hass) -> list[dict]:
    return list(reversed(hass.data.get(_KEY, ())))

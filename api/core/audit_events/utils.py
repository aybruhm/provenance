import hashlib
import json
from typing import Any, Dict

# Initialize constants
GENESIS_HASH = hashlib.sha256(b"PROVENANCE:GENESIS").hexdigest()


def hash_payload(payload: Dict[str, Any]) -> str:
    """
    Deterministic SHA-256 of a JSON payload (canonical sort, no whitespace).

    Args:
        payload: The JSON-serializable dictionary to hash.
    """
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def chain_hash(event_id: str, timestamp: str, payload_hash: str) -> str:
    """
    Hash that the *next* event will store as its prev_hash.

    Args:
        event_id: The ID of the event.
        timestamp: The timestamp of the event.
        payload_hash: The hash of the event's payload.

    Returns:
        The chained hash.
    """
    raw = f"{event_id}|{timestamp}|{payload_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()

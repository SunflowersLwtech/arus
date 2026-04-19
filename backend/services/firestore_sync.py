"""Firestore mission log persistence.

Every completed agent cycle is persisted to Firestore so that post-event
review, auditing (for Malaysian civil-defence reporting), and multi-device
sync across command consoles all work out of the box.

Gracefully degrades to an in-memory stub if Firestore credentials are not
available (e.g., local dev without ADC). This keeps the demo robust when
running on a laptop without service-account JSON.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger("arus.firestore")

_client = None
_enabled = os.environ.get("FIRESTORE_ENABLED", "true").lower() == "true"


def _init_client():
    """Lazy-init Firestore client. Fails silently if ADC unavailable."""
    global _client
    if not _enabled:
        return None
    if _client is not None:
        return _client
    try:
        from google.cloud import firestore
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        database = os.environ.get("FIRESTORE_DATABASE", "(default)")
        _client = firestore.Client(project=project, database=database)
        logger.info(f"Firestore client initialised: project={project} db={database}")
    except Exception as e:
        logger.warning(f"Firestore disabled (reason: {e})")
        _client = None
    return _client


# Local fallback: keep last N cycles in memory
_memory_log: list[dict[str, Any]] = []
MAX_MEMORY = 200


def log_cycle(mission_id: str, cycle: int, payload: dict[str, Any]) -> None:
    """Append one agent-cycle record to Firestore (or memory if unavailable)."""
    record = {
        "mission_id": mission_id,
        "cycle": cycle,
        "ts": time.time(),
        **payload,
    }
    client = _init_client()
    if client is not None:
        try:
            client.collection("arus").document(mission_id)\
                  .collection("cycles").document(str(cycle)).set(record)
            return
        except Exception as e:
            logger.warning(f"Firestore write failed, falling back to memory: {e}")

    _memory_log.append(record)
    if len(_memory_log) > MAX_MEMORY:
        _memory_log.pop(0)


def get_recent_cycles(mission_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch recent cycles for a mission."""
    client = _init_client()
    if client is not None:
        try:
            docs = (client.collection("arus")
                          .document(mission_id)
                          .collection("cycles")
                          .order_by("cycle", direction="DESCENDING")
                          .limit(limit)
                          .stream())
            return [d.to_dict() for d in docs]
        except Exception as e:
            logger.warning(f"Firestore read failed: {e}")

    return [r for r in _memory_log if r.get("mission_id") == mission_id][-limit:][::-1]


def log_handoff(mission_id: str, agency: str, brief: dict[str, Any]) -> None:
    """Record an agency hand-off (audit trail for Malaysian civil-defence reporting)."""
    client = _init_client()
    record = {
        "mission_id": mission_id,
        "agency": agency,
        "ts": time.time(),
        **brief,
    }
    if client is not None:
        try:
            client.collection("arus")\
                  .document(mission_id)\
                  .collection("handoffs")\
                  .add(record)
            return
        except Exception as e:
            logger.warning(f"Firestore handoff write failed: {e}")
    _memory_log.append({"handoff": True, **record})

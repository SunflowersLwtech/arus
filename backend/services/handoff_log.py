"""In-memory ring buffer of recent bilingual agency hand-offs.

Why this exists:
  Judges and auditors want to curl a single endpoint and see the 5th-stage
  agent's actual bilingual output. Reading `/api/logs` works but is noisy.
  This module parses hand-off blocks as the agency_dispatcher emits them
  and keeps the last N in a structured list.
"""
from __future__ import annotations

import re
import time
from collections import deque
from typing import Any

_HANDOFFS: deque[dict[str, Any]] = deque(maxlen=50)

# Hand-off format is produced by `backend/agents/prompts.yaml :: dispatcher_agency`.
_BLOCK_RE = re.compile(
    r"AGENSI:\s*(?P<agensi>\w+)\s*"
    r"KOORDINAT:\s*(?P<koord>[^\n]+)\s*"
    r"KEUTAMAAN:\s*(?P<pri>\w+)\s*"
    r"RINGKASAN\s*\(BM\):\s*(?P<bm>[^\n]+(?:\n\s{2,}[^\n]+)*)\s*"
    r"SUMMARY\s*\(EN\):\s*(?P<en>[^\n]+(?:\n\s{2,}[^\n]+)*)\s*"
    r"CADANGAN TINDAKAN\s*/\s*RECOMMENDED ACTION:\s*(?P<action>[^\n]+(?:\n\s{2,}[^\n]+)*)",
    re.MULTILINE,
)


def ingest_agency_text(text: str, cycle: int, mission_id: str) -> list[dict]:
    """Parse zero or more hand-off blocks out of raw agency_dispatcher text.

    Silently skips the sentinel "NO NEW HANDOFFS THIS CYCLE" response.
    Returns the freshly-added hand-off records for ease of testing.
    """
    if not text or "NO NEW HANDOFFS" in text:
        return []
    found: list[dict] = []
    for m in _BLOCK_RE.finditer(text):
        record = {
            "ts": time.time(),
            "mission_id": mission_id,
            "cycle": cycle,
            "agency": m.group("agensi").strip().upper(),
            "coord": m.group("koord").strip(),
            "priority": m.group("pri").strip().upper(),
            "bm": _clean(m.group("bm")),
            "en": _clean(m.group("en")),
            "action": _clean(m.group("action")),
        }
        _HANDOFFS.append(record)
        found.append(record)
    return found


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def recent(limit: int = 20) -> list[dict]:
    items = list(_HANDOFFS)
    return items[-limit:][::-1]  # newest first

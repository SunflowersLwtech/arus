"""MetMalaysia live weather warning feed.

Public API: https://api.data.gov.my/weather/warning/ — no auth, BM+EN, official.
Arus injects these warnings into the Assessor agent's prompt and surfaces them
on the dashboard status bar. Purpose: prove that Arus is "Malaysia-integrated",
not just "Malaysia-themed".

Cached 5 minutes to avoid hammering the upstream during agent cycles.
Falls back to an empty list if the upstream is down (degrades gracefully).
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger("arus.met")

API_URL = "https://api.data.gov.my/weather/warning/"
CACHE_TTL_SEC = 300  # 5 min

_cache: dict[str, Any] = {"ts": 0.0, "data": []}
_lock = asyncio.Lock()


async def fetch_warnings(limit: int = 10) -> list[dict]:
    """Return a trimmed list of current warnings. Cached for 5 minutes."""
    now = time.time()
    async with _lock:
        if now - _cache["ts"] < CACHE_TTL_SEC and _cache["data"]:
            return _cache["data"][:limit]
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                r = await client.get(API_URL, params={"limit": limit})
                r.raise_for_status()
                raw = r.json()
        except Exception as e:
            logger.warning(f"MetMalaysia fetch failed: {e}")
            return _cache["data"][:limit] if _cache["data"] else []

        trimmed: list[dict] = []
        for item in raw[:limit] if isinstance(raw, list) else []:
            issue = item.get("warning_issue") or {}
            trimmed.append({
                "issued": issue.get("issued"),
                "title_bm": issue.get("title_bm"),
                "title_en": issue.get("title_en"),
                "valid_from": item.get("valid_from"),
                "valid_to": item.get("valid_to"),
                "heading_en": item.get("heading_en"),
                "heading_bm": item.get("heading_bm"),
                "text_en": (item.get("text_en") or "")[:400],
                "text_bm": (item.get("text_bm") or "")[:400],
            })

        _cache["data"] = trimmed
        _cache["ts"] = now
        return trimmed


def summarise_for_prompt(warnings: list[dict], max_items: int = 3) -> str:
    """Single-block text block ready to drop into an Assessor prompt."""
    if not warnings:
        return "MetMalaysia live feed: no active warnings at this cycle."
    lines = [f"MetMalaysia live feed ({len(warnings)} active warnings, showing {min(max_items, len(warnings))}):"]
    for w in warnings[:max_items]:
        lines.append(f"- [{w.get('issued')}] {w.get('title_en')} · {w.get('heading_en')}")
        if w.get("text_en"):
            lines.append(f"    EN: {w['text_en']}")
    return "\n".join(lines)

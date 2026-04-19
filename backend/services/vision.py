"""Gemini Vision victim-detection service.

Exposed as REST endpoint: field teams upload a drone photo or geotagged screenshot,
Gemini 2.5 Flash vision analyses it and returns:
  - victim_count (integer)
  - severity (LOW | MODERATE | CRITICAL)
  - description (BM + EN)
  - recommended_agency (BOMBA | NADMA | APM | MMEA)

This gives commanders an AI second-opinion on ambiguous recon footage without
pulling a human analyst away from the command console.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger("arus.vision")

VISION_MODEL = os.environ.get("VISION_MODEL", "gemini-2.5-flash")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


class VisionAnalysis(BaseModel):
    victim_count: int
    severity: str  # LOW | MODERATE | CRITICAL
    description_bm: str
    description_en: str
    recommended_agency: str  # BOMBA | NADMA | APM | MMEA
    hazards: list[str]
    confidence: float  # 0-1


PROMPT = """You are a Malaysian disaster-response AI analyst viewing a drone photo
from a monsoon flood zone. Identify:

1. victim_count: integer number of people visible needing rescue
2. severity: LOW (dry roof, waving) | MODERATE (waist-deep water, no injuries) | CRITICAL (submerged, elderly, children, injured)
3. description_bm: one sentence description in Bahasa Malaysia
4. description_en: one sentence description in English
5. recommended_agency: BOMBA (fire/rescue, trapped) | NADMA (coordination) | APM (evacuation) | MMEA (maritime/boat)
6. hazards: list of observed hazards (e.g., "downed power line", "fast current", "debris")
7. confidence: 0-1 how confident you are in the victim count

Respond STRICTLY as valid JSON matching the VisionAnalysis schema above.
No markdown fences. No prose. JSON only."""


def _fallback_data(reason: str) -> dict:
    return {
        "victim_count": 0,
        "severity": "LOW",
        "description_bm": f"Analisis gagal: {reason}",
        "description_en": f"Analysis failed: {reason}",
        "recommended_agency": "NADMA",
        "hazards": [],
        "confidence": 0.0,
    }


def _coerce(data: dict) -> dict:
    """Harden the Vision output so pydantic validation never 500s."""
    out = {
        "victim_count": 0,
        "severity": "LOW",
        "description_bm": "",
        "description_en": "",
        "recommended_agency": "NADMA",
        "hazards": [],
        "confidence": 0.5,
    }
    out.update({k: v for k, v in data.items() if v is not None})
    try:
        out["victim_count"] = max(0, int(out.get("victim_count", 0)))
    except (TypeError, ValueError):
        out["victim_count"] = 0
    out["severity"] = str(out.get("severity") or "LOW").upper()
    if out["severity"] not in ("LOW", "MODERATE", "CRITICAL"):
        out["severity"] = "LOW"
    out["recommended_agency"] = str(out.get("recommended_agency") or "NADMA").upper()
    if out["recommended_agency"] not in ("BOMBA", "NADMA", "APM", "MMEA"):
        out["recommended_agency"] = "NADMA"
    out["hazards"] = list(out.get("hazards") or [])
    try:
        out["confidence"] = float(out.get("confidence", 0.5))
    except (TypeError, ValueError):
        out["confidence"] = 0.5
    out["description_bm"] = str(out.get("description_bm") or "")[:400]
    out["description_en"] = str(out.get("description_en") or "")[:400]
    return out


async def analyse_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> VisionAnalysis:
    """Send a drone image to Gemini Vision. Non-blocking + 429-aware + defensive."""
    client = _get_client()

    def _call():
        return client.models.generate_content(
            model=VISION_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

    # Run blocking SDK call off the event loop. Retry twice on 429/RESOURCE_EXHAUSTED.
    resp = None
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            resp = await asyncio.to_thread(_call)
            break
        except Exception as e:
            last_err = e
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            break

    if resp is None:
        logger.exception(f"vision API failure: {last_err}")
        return VisionAnalysis(**_coerce(_fallback_data("gemini_unavailable")))

    text = (getattr(resp, "text", "") or "{}").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", text, flags=re.MULTILINE)
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("vision returned non-object JSON")
    except Exception as e:
        logger.warning(f"Vision JSON parse failed ({e}): {text[:200]}")
        data = _fallback_data("non_json_response")

    return VisionAnalysis(**_coerce(data))


def analyse_image_sync(image_b64: str, mime_type: str = "image/jpeg") -> dict:
    """Sync wrapper that accepts base64 and returns a plain dict (for REST use)."""
    import asyncio
    image_bytes = base64.b64decode(image_b64)
    result = asyncio.run(analyse_image(image_bytes, mime_type))
    return result.model_dump()

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


async def analyse_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> VisionAnalysis:
    """Send a drone image to Gemini Vision and parse the structured response."""
    client = _get_client()
    resp = client.models.generate_content(
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
    text = resp.text or "{}"
    # Strip accidental code fences
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        data: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Vision returned non-JSON: {text[:200]}")
        # Fallback minimal parse
        data = {
            "victim_count": 0,
            "severity": "LOW",
            "description_bm": "Analisis gagal",
            "description_en": "Analysis failed",
            "recommended_agency": "NADMA",
            "hazards": [],
            "confidence": 0.0,
        }

    # Defensive coercion
    data.setdefault("hazards", [])
    data.setdefault("confidence", 0.5)
    data["victim_count"] = int(data.get("victim_count", 0))
    data["severity"] = str(data.get("severity", "LOW")).upper()
    data["recommended_agency"] = str(data.get("recommended_agency", "NADMA")).upper()

    return VisionAnalysis(**data)


def analyse_image_sync(image_b64: str, mime_type: str = "image/jpeg") -> dict:
    """Sync wrapper that accepts base64 and returns a plain dict (for REST use)."""
    import asyncio
    image_bytes = base64.b64decode(image_b64)
    result = asyncio.run(analyse_image(image_bytes, mime_type))
    return result.model_dump()

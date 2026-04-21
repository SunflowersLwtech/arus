"""Gemini narrator service for Arus Banjir Drill.

Used in two non-critical-path positions:

  (a) generate_intro(scenario, locale) — opening monologue from a NADMA
      liaison officer at the start of a session
  (b) generate_debrief(debrief_data, locale) — 3-paragraph personalised
      commentary at the end of a session, tying the player's choices to
      the 2021 Klang Valley flood post-mortem

Neither call is on the tick loop — intro fires once per /api/game/start,
debrief fires once per /api/game/debrief. Both are async, cached, and
have a hardcoded fallback so the UI never blocks waiting for Gemini.
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import asdict, is_dataclass
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger("arus.narrator")

NARRATOR_MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")

_client: genai.Client | None = None
_intro_cache: dict[str, dict] = {}


def _get_client() -> genai.Client | None:
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None
        _client = genai.Client(api_key=api_key)
    return _client


INTRO_PROMPT = """You are Datuk Nadia, senior liaison officer at NADMA's
Kuala Lumpur operations centre on the night of the 2021 Klang Valley floods.
You are briefing a new dispatcher (the player) over radio. The tone is
calm, professional, slightly worn from hours on shift — not dramatic.

Scenario: {scenario_name}
Situation: {intro_hook}
Target: coordinate rescue for at least {target_saved} civilians across
the 7-minute session while keeping inter-agency trust intact.

Produce a JSON object with TWO keys:
  "en": 2-3 sentence English radio briefing (~45 words)
  "bm": same content translated into natural Bahasa Malaysia (~45 words)

Use specific Malaysian references where appropriate (Sungai Klang, BOMBA,
APM, JKM relief centres). Do NOT use markdown. Do NOT add salutations.
Open directly with the situation report.

Return valid JSON only. No prose outside the JSON."""


DEBRIEF_PROMPT = """You are writing the after-action commentary for a
citizen who just finished a 7-minute Malaysian flood-coordination
simulation. They played NADMA dispatcher during the 2021 Klang Valley
floods scenario.

Their session:
  Outcome: {status}
  Lives saved: {saved} of {target_saved}
  Ending trust: {trust}%
  Ending assets: {assets}%
  Grade: {grade}
  Choices made (card → option): {choices_summary}

Real 2021 Klang Valley flood facts for grounding:
  - 40,000 displaced, 54 deaths, 16-hour median rescue wait time
  - BOMBA/NADMA/APM/MMEA ran parallel WhatsApp groups
  - Residents at Taman Sri Muda waited on rooftops for 16+ hours
  - A RM3.7M lawsuit with 1,500 claimants was later filed
  - MDPI 2025 post-mortem named "public awareness" and "coordination &
    communication" as systemic gaps

Write a three-paragraph debrief in BOTH English AND natural Bahasa Malaysia.
The two versions must be semantically equivalent, not a literal word-for-word
translation. Both fields are mandatory — never leave "bm" empty.

Paragraph 1 — reflect on what the player did (cite a specific choice if
possible, otherwise the overall pattern).
Paragraph 2 — tie it to what NADMA actually faced in December 2021.
Paragraph 3 — one concrete takeaway for the citizen reader about why
civilian awareness matters, pointing at Portal Bencana / InfoBanjir as
follow-up.

Tone: educational, not judgemental. Never mock a poor performance — the
point is for the player to feel the weight of coordination.

CRITICAL FORMATTING RULES — any violation = the output is rejected:
  • NEVER include internal identifiers like card_id or option_id in the
    prose. Words like "c01_sri_muda", "send_bomba_now", "ask_mmea_boats",
    "wait_daylight", "log_only" must NOT appear. Use natural English or
    Bahasa Malaysia phrases only (e.g. "your decision to send BOMBA
    immediately" not "your 'send_bomba_now' choice").
  • NEVER include raw quotation marks wrapping action strings. Speak as
    Datuk Nadia, not as a system log.
  • NEVER use underscores in any user-visible word.

Return a JSON object with EXACTLY two keys: "en" (English) and "bm"
(Bahasa Malaysia). Each value is the full 3-paragraph commentary as one
string with \\n\\n between paragraphs. No markdown. No extra fields."""


def _fallback_intro(scenario: Any, intro_hook_bm: str, intro_hook_en: str) -> dict:
    return {
        "en": intro_hook_en or "NADMA operations centre, you have the watch. Keep trust high, save as many as you can.",
        "bm": intro_hook_bm or "Pusat operasi NADMA, anda memegang giliran. Kekalkan kepercayaan, selamatkan seramai mungkin.",
        "source": "fallback",
    }


def _fallback_debrief(debrief: dict) -> dict:
    saved = debrief.get("gauges", {}).get("saved", 0)
    target = debrief.get("target_saved", 1)
    status = debrief.get("status", "partial")
    return {
        "en": (
            f"You ended the drill having saved {saved} of {target} civilians. "
            f"In December 2021, NADMA coordinators at the actual Klang Valley floods faced "
            f"exactly this kind of resource-bounded triage — four agencies, no shared dashboard, "
            f"40,000 displaced, 54 deaths, a 16-hour median rescue wait for rooftop cases.\n\n"
            f"The MDPI 2025 post-mortem named public awareness and inter-agency coordination as the "
            f"two systemic gaps that made things worse than they had to be. The drill you just played "
            f"is a flattened version of those tradeoffs.\n\n"
            f"The real follow-up is civic: keep an eye on Public InfoBanjir during monsoon season, "
            f"know your nearest JKM relief centre, and remember that coordination — not courage — "
            f"is the bottleneck when water is rising."
        ),
        "bm": (
            f"Anda menamatkan latihan dengan menyelamatkan {saved} daripada {target} orang awam. "
            f"Pada Disember 2021, penyelaras NADMA di banjir Lembah Klang sebenar berhadapan dengan "
            f"bentuk triage berikat-sumber yang sama — empat agensi, tiada papan pemuka dikongsi, "
            f"40,000 dipindahkan, 54 kematian, masa tindak balas median 16 jam untuk kes bumbung.\n\n"
            f"Post-mortem MDPI 2025 menamakan kesedaran awam dan penyelarasan antara agensi sebagai "
            f"dua jurang sistemik yang menjadikan keadaan lebih buruk daripada sepatutnya. Latihan "
            f"yang anda baru mainkan ini ialah versi dimampatkan bagi trade-off tersebut.\n\n"
            f"Lanjutan sebenar adalah sivik: pantau Public InfoBanjir semasa musim monsun, kenali pusat "
            f"pemindahan JKM terdekat anda, dan ingat bahawa penyelarasan — bukan keberanian — ialah "
            f"titik sekatan apabila air sedang naik."
        ),
        "source": "fallback",
    }


async def _call_gemini_json(prompt: str) -> dict | None:
    client = _get_client()
    if client is None:
        logger.info("narrator: GOOGLE_API_KEY not set, returning None for Gemini call")
        return None

    def _call():
        return client.models.generate_content(
            model=NARRATOR_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.35,
            ),
        )

    last_err: Exception | None = None
    for attempt in range(2):
        try:
            resp = await asyncio.to_thread(_call)
            break
        except Exception as e:
            last_err = e
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            logger.warning("narrator gemini call failed: %s", e)
            return None
    else:
        logger.warning("narrator gemini exhausted retries: %s", last_err)
        return None

    text = (getattr(resp, "text", "") or "{}").strip()
    import json, re
    text = re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", text, flags=re.MULTILINE)
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:
        logger.warning("narrator json parse failed (%s): %s", e, text[:200])
        return None


async def generate_intro(scenario, locale: str = "en") -> dict:
    """Return {en, bm, source} for scenario opening briefing."""
    cache_key = f"{scenario.id}:{locale}"
    if cache_key in _intro_cache:
        return _intro_cache[cache_key]

    prompt = INTRO_PROMPT.format(
        scenario_name=scenario.name_en,
        intro_hook=scenario.intro_hook_en,
        target_saved=scenario.target_saved,
    )
    data = await _call_gemini_json(prompt)
    if data and data.get("en") and data.get("bm"):
        result = {"en": str(data["en"])[:1200], "bm": str(data["bm"])[:1200], "source": "gemini"}
    else:
        result = _fallback_intro(scenario, scenario.intro_hook_bm, scenario.intro_hook_en)

    _intro_cache[cache_key] = result
    return result


async def generate_debrief(debrief: dict, locale: str = "en") -> dict:
    """Return {en, bm, source} for 3-paragraph end-of-game commentary."""
    choices = debrief.get("choices", [])
    # Use human-readable labels, not raw card_id/option_id, so Gemini never
    # paraphrases identifiers into its prose.
    choices_summary = "; ".join(
        f"chose \"{(c.get('option_label_en') or c['option_id']).strip()}\" for \"{(c.get('card_title_en') or c['card_id']).strip()}\""
        for c in choices
    ) or "(no choices made)"

    prompt = DEBRIEF_PROMPT.format(
        status=debrief.get("status", "partial"),
        saved=debrief.get("gauges", {}).get("saved", 0),
        target_saved=debrief.get("target_saved", 1),
        trust=round(debrief.get("gauges", {}).get("trust", 0)),
        assets=round(debrief.get("gauges", {}).get("assets", 0)),
        grade=debrief.get("grade", "F"),
        choices_summary=choices_summary,
    )
    data = await _call_gemini_json(prompt)
    if data and data.get("en") and data.get("bm"):
        return {
            "en": _scrub_action_ids(str(data["en"]))[:4000],
            "bm": _scrub_action_ids(str(data["bm"]))[:4000],
            "source": "gemini",
        }
    return _fallback_debrief(debrief)


_SNAKE_CASE_RX = None


def _scrub_action_ids(text: str) -> str:
    """Safety net: strip snake_case tokens (card_id / option_id leaks).

    Converts 'send_bomba_now' → 'send bomba now' and unwraps surrounding
    quotes so Gemini's hallucinated identifiers read naturally.
    """
    import re
    global _SNAKE_CASE_RX
    if _SNAKE_CASE_RX is None:
        # match words with at least one underscore between alphanum chars
        _SNAKE_CASE_RX = re.compile(r"[\"'`]?([A-Za-z]+(?:_[A-Za-z0-9]+)+)[\"'`]?")
    return _SNAKE_CASE_RX.sub(lambda m: m.group(1).replace("_", " "), text)

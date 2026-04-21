"""CoachAgent — 2-stage ADK agent that advises the human player.

Fires once per incoming Decision Card in COACH mode (not on a timer).
Stage 1 (Assessor): reads fleet/world state via MCP tools.
Stage 2 (Recommender): reads the card + its options and returns a
structured JSON recommendation with reasoning in BM + EN.

The recommender's CoT is streamed to the UI via the shared broadcast
function so the player sees *how an expert thinks* before committing.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Awaitable, Callable, Optional

import yaml
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.genai import types as genai_types

from backend.agents.auto_commander import AGENT_MODEL, MCP_URL
from backend.core.grid_world import GridWorld

logger = logging.getLogger("arus.coach")

_PROMPTS_PATH = Path(__file__).parent / "prompts.yaml"
with _PROMPTS_PATH.open() as _f:
    _PROMPTS = yaml.safe_load(_f)


def build_coach_pipeline(mcp_url: str = MCP_URL) -> SequentialAgent:
    """Create the 2-stage COACH pipeline."""
    conn = StreamableHTTPConnectionParams(url=mcp_url, timeout=30)
    fleet_tools = McpToolset(connection_params=conn)

    assessor = LlmAgent(
        name="coach_assessor",
        model=AGENT_MODEL,
        instruction=_PROMPTS["coach_assessor"]["instruction"],
        tools=[fleet_tools],
        output_key="coach_briefing",
    )
    recommender = LlmAgent(
        name="coach_recommender",
        model=AGENT_MODEL,
        instruction=_PROMPTS["coach_recommender"]["instruction"],
        tools=[],  # no tools — pure reasoning + JSON output
        output_key="coach_recommendation",
    )
    return SequentialAgent(
        name="arus_coach",
        sub_agents=[assessor, recommender],
    )


class CoachAgent:
    """Wraps the 2-stage pipeline with broadcast + JSON parsing.

    Parameters
    ----------
    world : GridWorld
        Read-only reference for context (the recommender never mutates).
    broadcast_fn : async callable
        WebSocket broadcast fn — gets `agent_log`/`agent_status` events.
    """

    def __init__(
        self,
        world: GridWorld,
        broadcast_fn: Callable[[dict], Awaitable[None]],
        mcp_url: str = MCP_URL,
    ) -> None:
        self.world = world
        self._broadcast = broadcast_fn
        self._agent = build_coach_pipeline(mcp_url)
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self._agent,
            app_name="arus-coach",
            session_service=self._session_service,
        )
        self._user_id = "player"
        self._session_id: Optional[str] = None
        self._busy = False
        self._last_recommendation: Optional[dict] = None
        # Keyed by card_id → recommendation dict. Lets the game engine
        # compute alignment between player choice and AI suggestion.
        self._recs_by_card: dict[str, dict] = {}

    def get_recommendation_for(self, card_id: str) -> Optional[dict]:
        """Return the cached recommendation for a specific card, if any."""
        return self._recs_by_card.get(card_id)

    async def _ensure_session(self) -> str:
        if self._session_id is None:
            sess = await self._session_service.create_session(
                app_name="arus-coach", user_id=self._user_id,
            )
            self._session_id = sess.id
        return self._session_id

    async def recommend_for_card(self, card_payload: dict, gauges: dict) -> Optional[dict]:
        """Run the 2-stage pipeline for the given card. Idempotent per call."""
        if self._busy:
            logger.info("coach already running; skipping overlap")
            return None
        self._busy = True
        started = time.time()
        session_id = await self._ensure_session()

        # Tell the frontend the coach is thinking.
        await self._broadcast({
            "type": "agent_status",
            "payload": {"status": "thinking", "mode": "COACH", "card_id": card_payload.get("id")},
        })

        # Serialise the card + gauges + fleet summary into a single
        # prompt input — the recommender reads this verbatim.
        fleet_summary = [
            {
                "id": u.id,
                "agency": _agency_for(u.id),
                "status": u.status.value if hasattr(u.status, "value") else str(u.status),
                "power": round(u.power, 1),
                "pos": [u.x, u.y],
            }
            for u in self.world.fleet.values()
        ]
        message = (
            "CARD JSON:\n"
            + json.dumps(card_payload, ensure_ascii=False)
            + "\n\nGAUGES:\n"
            + json.dumps(gauges, ensure_ascii=False)
            + "\n\nFLEET SNAPSHOT:\n"
            + json.dumps(fleet_summary, ensure_ascii=False)
            + "\n\nProceed: Assessor, then Recommender."
        )

        content = genai_types.Content(role="user", parts=[genai_types.Part(text=message)])

        try:
            async for event in self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                new_message=content,
            ):
                await self._process_event(event, card_payload.get("id", "?"))

            recommendation = self._last_recommendation
            elapsed = time.time() - started
            if recommendation and card_payload.get("id"):
                # Cache keyed by card so the engine can resolve alignment
                # when the player later picks an option.
                self._recs_by_card[card_payload["id"]] = recommendation
            await self._broadcast({
                "type": "agent_status",
                "payload": {
                    "status": "idle",
                    "mode": "COACH",
                    "card_id": card_payload.get("id"),
                    "elapsed": round(elapsed, 1),
                    "recommendation": recommendation,
                },
            })
            if recommendation:
                await self._broadcast({
                    "type": "coach_recommendation",
                    "payload": {**recommendation, "card_id": card_payload.get("id")},
                })
            return recommendation
        except Exception as e:
            err = str(e)[:300]
            logger.exception("coach run failed: %s", err)
            await self._broadcast({
                "type": "agent_status",
                "payload": {"status": "error", "mode": "COACH", "message": err},
            })
            return None
        finally:
            self._busy = False

    async def _process_event(self, event, card_id: str) -> None:
        agent_name = getattr(event, "author", "coach")
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            return
        for part in content.parts:
            if getattr(part, "text", None):
                await self._broadcast({
                    "type": "agent_log",
                    "payload": {
                        "kind": "reasoning",
                        "agent": agent_name,
                        "text": part.text[:1000],
                        "card_id": card_id,
                        "timestamp": time.time(),
                    },
                })
                # Last agent (recommender) outputs JSON — parse and store.
                if agent_name == "coach_recommender":
                    parsed = _parse_recommendation(part.text)
                    if parsed is not None:
                        self._last_recommendation = parsed
            # Tool call stream
            fc = getattr(part, "function_call", None)
            if fc is not None:
                await self._broadcast({
                    "type": "agent_log",
                    "payload": {
                        "kind": "tool_call",
                        "agent": agent_name,
                        "tool": fc.name,
                        "args": dict(fc.args) if hasattr(fc, "args") else {},
                        "card_id": card_id,
                        "timestamp": time.time(),
                    },
                })
            fr = getattr(part, "function_response", None)
            if fr is not None:
                resp = getattr(fr, "response", None)
                short = str(resp)[:300] if resp is not None else ""
                await self._broadcast({
                    "type": "agent_log",
                    "payload": {
                        "kind": "tool_result",
                        "agent": agent_name,
                        "tool": fr.name,
                        "result": short,
                        "card_id": card_id,
                        "timestamp": time.time(),
                    },
                })


def _parse_recommendation(text: str) -> Optional[dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(cleaned)
    except Exception:
        # Try to locate a JSON object within the text.
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except Exception:
            return None
    if not isinstance(data, dict):
        return None
    required = {"option_id", "reasoning_en", "reasoning_bm"}
    if not required.issubset(data.keys()):
        return None
    # Sanitize — keep only known keys + defensive truncation.
    return {
        "option_id": str(data.get("option_id"))[:64],
        "reasoning_en": str(data.get("reasoning_en", ""))[:1200],
        "reasoning_bm": str(data.get("reasoning_bm", ""))[:1200],
        "suggested_drone": str(data.get("suggested_drone", ""))[:32],
        "confidence": str(data.get("confidence", ""))[:16],
    }


def _agency_for(callsign: str) -> str:
    # Avoid pulling agencies module here to keep coach.py lean.
    return {
        "Alpha": "BOMBA", "Bravo": "BOMBA",
        "Charlie": "APM", "Delta": "MMEA", "Echo": "NADMA",
    }.get(callsign, "NADMA")

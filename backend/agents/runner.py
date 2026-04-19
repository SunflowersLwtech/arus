"""AgentRunner — drives ADK SequentialAgent and streams CoT to frontend.

The agent communicates with drones exclusively through MCP protocol.
This module only reads world state for situational briefing — all
drone commands flow through:  Agent → McpToolset → MCP Server → GridWorld
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Awaitable, Callable

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from backend.agents.commander import build_pipeline, MCP_URL
from backend.core.grid_world import GridWorld
from backend.services import firestore_sync, met_feed, handoff_log
from backend.utils.blackbox import blackbox

logger = logging.getLogger("arus.agent")

# Session rotation: prevent unbounded context window growth.
# After N cycles, create a fresh session so the LLM doesn't degrade
# from accumulating ~2000 tokens/cycle in conversation history.
SESSION_MAX_CYCLES = 15


def _extract_result_text(response) -> str:
    """Extract readable text from MCP tool response.

    MCP responses are typically: {'content': [{'type': 'text', 'text': '...'}]}
    This extracts the inner text and truncates to 300 chars.
    """
    try:
        if isinstance(response, dict):
            content = response.get("content", [])
            if isinstance(content, list) and content:
                text = content[0].get("text", "")
                if text:
                    return text[:300]
        return str(response)[:300]
    except Exception:
        return str(response)[:300]


class AgentRunner:
    """Runs the 4-stage ADK pipeline and broadcasts events via WebSocket.

    Parameters
    ----------
    world : GridWorld
        Read-only reference for building situational briefings.
        The agent does NOT mutate world directly — all commands go through MCP.
    broadcast_fn : async callable
        WebSocket broadcast function for CoT streaming.
    mcp_url : str
        MCP server endpoint (default: http://127.0.0.1:8001/mcp).
    """

    def __init__(
        self,
        world: GridWorld,
        broadcast_fn: Callable[[dict], Awaitable[None]],
        mcp_url: str = MCP_URL,
        mission_id: str | None = None,
    ):
        import uuid as _uuid
        self.world = world
        self._broadcast = broadcast_fn
        self._running = False
        self._cancelled = False
        self._cycle = 0
        self.mission_id = mission_id or f"mission-{_uuid.uuid4().hex[:8]}"
        self._agent = build_pipeline(mcp_url)
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self._agent,
            app_name="arus",
            session_service=self._session_service,
        )
        self._session_id: str | None = None
        self._backoff_until: int = 0  # Skip cycles until this cycle number (rate limit)

    def cancel(self) -> None:
        """Mark runner as cancelled. In-flight run_cycle() will exit early."""
        self._cancelled = True

    def try_start(self) -> bool:
        """Atomic compare-and-swap: returns True only if we won the race.

        Safe in single-threaded asyncio — no await between check and set.
        """
        if self._running:
            return False
        self._running = True
        return True

    async def run_cycle(self) -> None:
        """Execute one full agent pipeline cycle."""
        if self._cancelled:
            self._running = False
            return

        self._cycle += 1

        # Rate-limit backoff: skip this cycle if we were recently throttled
        if self._cycle < self._backoff_until:
            logger.info(f"Skipping cycle {self._cycle} (rate-limit backoff until {self._backoff_until})")
            self._running = False
            return
        cycle = self._cycle

        try:
            # Session rotation: prevent context window bloat (runs even if cycle fails)
            if self._session_id and self._cycle % SESSION_MAX_CYCLES == 0:
                logger.info(f"Rotating session after {SESSION_MAX_CYCLES} cycles")
                self._session_id = None

            # Verify credentials: either API key or Vertex AI ADC
            has_api_key = os.environ.get("GOOGLE_API_KEY")
            has_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"
            if not has_api_key and not has_vertex:
                raise RuntimeError("No Gemini credentials — set GOOGLE_API_KEY or GOOGLE_GENAI_USE_VERTEXAI=TRUE")

            # Broadcast thinking status
            await self._broadcast({
                "type": "agent_status",
                "payload": {"status": "thinking", "cycle": cycle},
            })

            # Build situational briefing (read-only world access)
            progress = self.world.get_search_progress()
            fleet = self.world.get_fleet_status()

            # Drone summary with positions
            drone_lines = []
            for drone in self.world.drones.values():
                u = drone.uav
                mission_str = ""
                if drone.current_mission:
                    mission_str = f" mission={drone.current_mission.type.value}"
                    if drone.current_mission.target:
                        mission_str += f"→{drone.current_mission.target}"
                drone_lines.append(
                    f"  {u.id}: {u.status.value} at ({u.x},{u.y}) "
                    f"power={u.power:.0f}%{mission_str}"
                )

            # Pull live MetMalaysia warnings (cached 5 min). Falls back silently on error.
            try:
                met_warnings = await met_feed.fetch_warnings(limit=3)
            except Exception:
                met_warnings = []
            met_block = met_feed.summarise_for_prompt(met_warnings, max_items=3)

            briefing = (
                f"Cycle {cycle} | Tick {self.world.tick} | "
                f"Grid {self.world.size}x{self.world.size} | "
                f"Base at {list(self.world.base_position)}\n"
                f"Coverage {progress.coverage_pct:.1f}% | "
                f"Objectives {progress.objectives_found}/{progress.objectives_total} | "
                f"Fleet: {fleet.active}/{fleet.total} active, avg power {fleet.avg_power:.0f}%\n"
                f"Drones:\n" + "\n".join(drone_lines) + "\n\n"
                + met_block
            )

            blackbox.log("system", f"Agent cycle {cycle} started: {briefing}")

            # Create or reuse session
            if self._session_id is None:
                session = await self._session_service.create_session(
                    app_name="arus", user_id="simulation",
                )
                self._session_id = session.id

            from google.genai import types

            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=briefing)],
            )

            # Stream events from the agent pipeline (retry on rate limit)
            max_retries = 2
            for attempt in range(max_retries + 1):
                if self._cancelled:
                    logger.info(f"Cycle {cycle} cancelled before run_async")
                    return
                try:
                    async for event in self._runner.run_async(
                        user_id="simulation",
                        session_id=self._session_id,
                        new_message=user_content,
                    ):
                        if self._cancelled:
                            logger.info(f"Cycle {cycle} cancelled mid-stream")
                            return
                        await self._process_event(event, cycle)
                    break  # Success — exit retry loop
                except Exception as retry_err:
                    if attempt < max_retries and ("429" in str(retry_err) or "RESOURCE_EXHAUSTED" in str(retry_err)):
                        # Free-tier Gemini is 10 RPM. After a hit, we need to wait
                        # ~60s for the rolling window to clear before the next pipeline
                        # can fit all ~10-15 requests. 5s is too short.
                        wait = 35 + 25 * attempt  # 35s, 60s
                        logger.warning(f"Rate limited (attempt {attempt+1}), retrying in {wait}s...")
                        blackbox.log("system", f"Rate limited — waiting {wait}s before retry")
                        await asyncio.sleep(wait)
                        # Fresh session to avoid stale context
                        self._session_id = None
                        session = await self._session_service.create_session(
                            app_name="arus", user_id="simulation",
                        )
                        self._session_id = session.id
                    else:
                        raise  # Non-retryable or exhausted retries

            if self._cancelled:
                logger.info(f"Cycle {cycle} cancelled before persist")
                return

            # Persist cycle to Firestore for audit trail (civil-defence reporting)
            try:
                progress_end = self.world.get_search_progress()
                firestore_sync.log_cycle(
                    mission_id=self.mission_id,
                    cycle=cycle,
                    payload={
                        "tick": self.world.tick,
                        "coverage_pct": progress_end.coverage_pct,
                        "objectives_found": progress_end.objectives_found,
                        "objectives_total": progress_end.objectives_total,
                        "fleet_size": len(self.world.fleet),
                    },
                )
            except Exception as persist_err:
                logger.warning(f"Firestore persist failed (non-fatal): {persist_err}")

            # Cycle complete
            blackbox.log("system", f"Agent cycle {cycle} completed")
            await self._broadcast({
                "type": "agent_status",
                "payload": {"status": "idle", "cycle": cycle, "mission_id": self.mission_id},
            })

        except Exception as e:
            err_str = str(e)
            logger.error(f"Agent cycle {cycle} failed: {err_str}", exc_info=True)
            blackbox.error("system", err_str)

            # Rate limit: skip the next 6 cycles. With AGENT_INTERVAL=200 that
            # gives the free-tier 10-RPM rolling window ~4 minutes to fully
            # clear before we try again.
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                self._backoff_until = self._cycle + 6
                logger.warning(f"Rate limited — backing off until cycle {self._backoff_until}")

            await self._broadcast({
                "type": "agent_status",
                "payload": {
                    "status": "error",
                    "cycle": cycle,
                    "message": err_str[:200],
                },
            })

        finally:
            self._running = False

    async def _process_event(self, event, cycle: int) -> None:
        """Extract reasoning, tool_call, and tool_result from ADK events."""
        agent_name = getattr(event, "author", "unknown")

        if not hasattr(event, "content") or not event.content:
            return
        if not hasattr(event.content, "parts") or not event.content.parts:
            return

        for part in event.content.parts:
            # Reasoning text
            if hasattr(part, "text") and part.text:
                blackbox.reasoning(agent_name, agent_name, part.text[:500])

                # Stage-5 outputs structured BM/EN hand-offs — capture them
                # into a dedicated ring buffer so judges can curl a clean
                # endpoint instead of grepping /api/logs.
                if agent_name == "agency_dispatcher":
                    try:
                        new_records = handoff_log.ingest_agency_text(
                            part.text, cycle=cycle, mission_id=self.mission_id,
                        )
                        for rec in new_records:
                            try:
                                firestore_sync.log_handoff(
                                    mission_id=self.mission_id,
                                    agency=rec["agency"],
                                    brief=rec,
                                )
                            except Exception as fs_err:
                                logger.debug(f"handoff persist skipped: {fs_err}")
                    except Exception as hi_err:
                        logger.debug(f"handoff ingest failed: {hi_err}")

                await self._broadcast({
                    "type": "agent_log",
                    "payload": {
                        "phase": agent_name,
                        "agent": agent_name,
                        "action": "reasoning",
                        "detail": part.text[:500],
                        "cycle": cycle,
                        "timestamp": time.time(),
                    },
                })

            # Tool call
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                args = dict(fc.args) if fc.args else {}
                blackbox.tool_call(agent_name, fc.name, args)
                await self._broadcast({
                    "type": "agent_log",
                    "payload": {
                        "phase": agent_name,
                        "agent": agent_name,
                        "action": "tool_call",
                        "detail": f"{fc.name}({args})",
                        "cycle": cycle,
                        "timestamp": time.time(),
                    },
                })

            # Tool result
            if hasattr(part, "function_response") and part.function_response:
                fr = part.function_response
                result_str = _extract_result_text(fr.response)
                blackbox.tool_result(agent_name, fr.name, result_str)
                await self._broadcast({
                    "type": "agent_log",
                    "payload": {
                        "phase": agent_name,
                        "agent": agent_name,
                        "action": "tool_result",
                        "detail": f"{fr.name} → {result_str}",
                        "cycle": cycle,
                        "timestamp": time.time(),
                    },
                })

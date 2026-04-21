"""GameEngine — drives the Banjir Drill loop.

Responsibilities:
1. Own a Gauges state + a Scenario.
2. On each tick, surface the card whose trigger_tick has passed.
3. Apply a player's choice to the gauges + record the card into history.
4. Translate `map_action` hints into GridWorld missions so the 3D scene
   reflects the player's decisions (drones fly, kampungs light up).
5. Produce a debrief payload when the game ends.

The engine does not talk to Gemini directly — narrator.py does that when
the game starts (intro) and when the game ends (debrief). This keeps the
tick loop deterministic and the critical path zero-latency.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from backend.core.grid_world import GridWorld
from backend.game.scenario import Card, Scenario, load_real_stats, load_scenario
from backend.game.score import Gauges, apply_delta, compute_grade, evaluate


@dataclass
class ChoiceRecord:
    card_id: str
    option_id: str
    tick: int
    deltas: dict
    gauges_after: dict
    flavor_bm: str
    flavor_en: str


@dataclass
class GameEngine:
    world: GridWorld
    scenario: Scenario
    locale: str = "en"
    session_id: str = field(default_factory=lambda: uuid4().hex[:8])
    started_at: float = field(default_factory=time.time)
    gauges: Gauges = field(default_factory=Gauges)
    _pending_card: Optional[Card] = None
    _fired_card_ids: set[str] = field(default_factory=set)
    _history: list[ChoiceRecord] = field(default_factory=list)
    _status: str = "running"  # running|won|partial|failed
    _status_reason: str = ""
    _last_tick: int = 0

    @classmethod
    def start_new(
        cls,
        world: GridWorld,
        scenario_id: str = "shah_alam_hard",
        locale: str = "en",
    ) -> "GameEngine":
        scenario = load_scenario(scenario_id)
        engine = cls(
            world=world,
            scenario=scenario,
            locale=locale,
            gauges=Gauges(time_remaining=scenario.duration_seconds),
        )
        # Seed a few objectives on the map that the game intro references.
        # GridWorld already spawns victims via ObjectiveField; we just make
        # sure the player sees something immediately.
        return engine

    # ─── Per-tick advancement ─────────────────────────────────

    def on_tick(self, tick: int) -> list[dict]:
        """Advance timer, surface card if due, evaluate game end.

        Returns a list of broadcast events suitable for `manager.broadcast`.
        """
        events: list[dict] = []
        if self._status != "running":
            return events

        # Advance wall-time gauge (world.step runs ~5 Hz → 0.2 s per tick)
        if tick != self._last_tick:
            self.gauges.time_remaining = max(0.0, self.gauges.time_remaining - 0.2)
            self._last_tick = tick

        # Surface the next card whose trigger tick has passed.
        if self._pending_card is None:
            for card in self.scenario.cards:
                if card.id in self._fired_card_ids:
                    continue
                if tick >= card.trigger_tick:
                    self._pending_card = card
                    self._fired_card_ids.add(card.id)
                    events.append({
                        "type": "game_card",
                        "payload": self._card_payload(card),
                    })
                    break

        # Evaluate win/lose every tick.
        verdict = evaluate(self.gauges, self.scenario.target_saved)
        if verdict["status"] != "in_progress":
            self._status = verdict["status"]
            self._status_reason = verdict["reason"]
            events.append({
                "type": "game_over",
                "payload": {
                    "status": self._status,
                    "reason": self._status_reason,
                    "gauges": self.gauges.as_dict(),
                },
            })

        return events

    # ─── Player action ─────────────────────────────────────────

    def choose(self, card_id: str, option_id: str) -> dict:
        """Apply a player's choice. Returns a broadcastable event payload."""
        if self._pending_card is None or self._pending_card.id != card_id:
            return {"type": "player_command_result", "payload": {"ok": False, "reason": "no_card_pending"}}
        option = next((o for o in self._pending_card.options if o.id == option_id), None)
        if option is None:
            return {"type": "player_command_result", "payload": {"ok": False, "reason": "unknown_option"}}

        apply_delta(self.gauges, option.deltas)

        # Visual feedback on the 3D map: fire a drone mission to the card's
        # coordinate if the option calls for a rescue.
        if option.map_action == "dispatch_rescue" and self.world.fleet:
            uav_id = random.choice(list(self.world.fleet.keys()))
            try:
                tx, ty = self._pending_card.coord
                self.world.set_waypoint(uav_id, int(tx), int(ty))
            except Exception:
                pass  # non-fatal — gauges still updated

        record = ChoiceRecord(
            card_id=self._pending_card.id,
            option_id=option.id,
            tick=self.world.tick,
            deltas=dict(option.deltas),
            gauges_after=self.gauges.as_dict(),
            flavor_bm=option.flavor_bm,
            flavor_en=option.flavor_en,
        )
        self._history.append(record)
        self._pending_card = None

        return {
            "type": "player_command_result",
            "payload": {
                "ok": True,
                "card_id": record.card_id,
                "option_id": record.option_id,
                "flavor": {"bm": option.flavor_bm, "en": option.flavor_en},
                "gauges": self.gauges.as_dict(),
                "deltas": dict(option.deltas),
            },
        }

    # ─── Serialisation ─────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            "session_id": self.session_id,
            "scenario": {
                "id": self.scenario.id,
                "name_bm": self.scenario.name_bm,
                "name_en": self.scenario.name_en,
                "target_saved": self.scenario.target_saved,
                "duration_seconds": self.scenario.duration_seconds,
            },
            "locale": self.locale,
            "gauges": self.gauges.as_dict(),
            "status": self._status,
            "status_reason": self._status_reason,
            "current_card": self._card_payload(self._pending_card) if self._pending_card else None,
            "history": [
                {
                    "card_id": h.card_id,
                    "option_id": h.option_id,
                    "tick": h.tick,
                    "deltas": h.deltas,
                    "flavor": {"bm": h.flavor_bm, "en": h.flavor_en},
                }
                for h in self._history
            ],
        }

    def _card_payload(self, card: Card | None) -> dict | None:
        if card is None:
            return None
        return {
            "id": card.id,
            "title_bm": card.title_bm,
            "title_en": card.title_en,
            "body_bm": card.body_bm,
            "body_en": card.body_en,
            "coord": card.coord,
            "options": [
                {
                    "id": o.id,
                    "label_bm": o.label_bm,
                    "label_en": o.label_en,
                    "deltas": dict(o.deltas),  # surfaced for risk-preview UI
                }
                for o in card.options
            ],
        }

    # ─── Debrief ───────────────────────────────────────────────

    def is_over(self) -> bool:
        return self._status in ("won", "partial", "failed")

    def compute_debrief(self) -> dict:
        stats = load_real_stats(self.scenario.real_event_key)
        return {
            "session_id": self.session_id,
            "status": self._status,
            "grade": compute_grade(self.gauges, self.scenario.target_saved),
            "gauges": self.gauges.as_dict(),
            "target_saved": self.scenario.target_saved,
            "choices": [
                {
                    "card_id": h.card_id,
                    "option_id": h.option_id,
                    "flavor": {"bm": h.flavor_bm, "en": h.flavor_en},
                }
                for h in self._history
            ],
            "real_event": stats,
            "extension_links": {
                "nadma_portal_bencana": "https://portalbencana.nadma.gov.my/en/",
                "public_infobanjir": "https://publicinfobanjir.water.gov.my/",
                "metmalaysia_warnings": "https://api.data.gov.my/weather/warning",
            },
        }

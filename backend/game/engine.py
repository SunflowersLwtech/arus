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
from backend.game.agencies import CALLSIGN_TO_AGENCY, idle_drone_for_agency
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


# Atmospheric "while you wait" lines. Short, Malaysia-flavoured, low
# information density — they fill the map's wait-period silence without
# demanding player attention.
PASSIVE_TICKS = [
    {
        "speaker": "Klang water gauge",
        "en": "Sungai Klang +0.2 m in the last 10 minutes.",
        "bm": "Sungai Klang naik 0.2 m dalam 10 minit terakhir.",
    },
    {
        "speaker": "MetMalaysia",
        "en": "Red warning for Petaling. Continuous rain next 6 hours.",
        "bm": "Amaran merah untuk Petaling. Hujan berterusan 6 jam akan datang.",
    },
    {
        "speaker": "BOMBA HQ",
        "en": "Swift-water team Bravo is refuelling at base.",
        "bm": "Pasukan air deras Bravo sedang mengisi bahan api di pangkalan.",
    },
    {
        "speaker": "NADMA ops",
        "en": "JKM has opened 4 more relief centres in Shah Alam.",
        "bm": "JKM membuka 4 lagi pusat bantuan di Shah Alam.",
    },
    {
        "speaker": "APM radio",
        "en": "Orang Asli liaison ping — Kg. Pos Bihai still holding.",
        "bm": "Perhubungan Orang Asli — Kg. Pos Bihai masih bertahan.",
    },
    {
        "speaker": "MMEA ops",
        "en": "Klang river mouth: current 1.8 m/s, boats holding station.",
        "bm": "Kuala Sungai Klang: arus 1.8 m/s, bot kekal di stesen.",
    },
]


PASSIVE_INTERVAL_TICKS = 60  # ~12 s of wall time at 5 Hz


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
    _last_passive_tick: int = 0
    _passive_index: int = 0

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

        # Between-card filler: every ~12 s while no card is open, emit a
        # passive atmospheric log entry so the NADMA Radio panel keeps
        # moving and the map doesn't feel abandoned.
        if (
            self._pending_card is None
            and tick - self._last_passive_tick >= PASSIVE_INTERVAL_TICKS
            and tick > 20  # let the intro breathe
        ):
            line = PASSIVE_TICKS[self._passive_index % len(PASSIVE_TICKS)]
            self._passive_index += 1
            self._last_passive_tick = tick
            events.append({
                "type": "narrator_log",
                "payload": {
                    "id": f"passive-{tick}",
                    "speaker": line["speaker"],
                    "text_en": line["en"],
                    "text_bm": line["bm"],
                    "tone": "passive",
                    "timestamp_tick": tick,
                },
            })

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

        # Visual feedback on the 3D map: dispatch the drone that belongs to
        # the option's agency (falls back to any idle drone, or a random
        # one if nobody is free). This gives the fleet meaning — picking
        # "send BOMBA" makes a BOMBA-liveried drone move.
        assigned_drone: str | None = None
        if option.map_action == "dispatch_rescue" and self.world.fleet:
            fleet_state = [u.to_dict() for u in self.world.fleet.values()]
            assigned_drone = idle_drone_for_agency(fleet_state, option.agency or None)
            if assigned_drone is None:
                assigned_drone = random.choice(list(self.world.fleet.keys()))
            try:
                tx, ty = self._pending_card.coord
                self.world.set_waypoint(assigned_drone, int(tx), int(ty))
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
                "assigned_drone": assigned_drone,
                "agency": option.agency or (CALLSIGN_TO_AGENCY.get(assigned_drone or "") if assigned_drone else ""),
            },
        }

    # ─── Serialisation ─────────────────────────────────────────

    def snapshot(self) -> dict:
        next_card = next(
            (c for c in self.scenario.cards if c.id not in self._fired_card_ids),
            None,
        )
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
            "next_card_tick": next_card.trigger_tick if next_card and self._pending_card is None else None,
            "tick": self._last_tick,
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
                    "deltas": dict(o.deltas),
                    "agency": o.agency or None,
                }
                for o in card.options
            ],
        }

    # ─── Debrief ───────────────────────────────────────────────

    def is_over(self) -> bool:
        return self._status in ("won", "partial", "failed")

    def compute_debrief(self) -> dict:
        stats = load_real_stats(self.scenario.real_event_key)
        cards_by_id = {c.id: c for c in self.scenario.cards}

        def _enrich(h: ChoiceRecord) -> dict:
            card = cards_by_id.get(h.card_id)
            option = None
            if card:
                option = next((o for o in card.options if o.id == h.option_id), None)
            return {
                "card_id": h.card_id,
                "option_id": h.option_id,
                "tick": h.tick,
                "deltas": dict(h.deltas),
                "gauges_after": dict(h.gauges_after),
                "flavor": {"bm": h.flavor_bm, "en": h.flavor_en},
                "card_title_en": card.title_en if card else h.card_id,
                "card_title_bm": card.title_bm if card else h.card_id,
                "option_label_en": option.label_en if option else h.option_id,
                "option_label_bm": option.label_bm if option else h.option_id,
                "agency": option.agency if option and option.agency else "",
            }

        return {
            "session_id": self.session_id,
            "status": self._status,
            "grade": compute_grade(self.gauges, self.scenario.target_saved),
            "gauges": self.gauges.as_dict(),
            "target_saved": self.scenario.target_saved,
            "choices": [_enrich(h) for h in self._history],
            "real_event": stats,
            "extension_links": {
                "nadma_portal_bencana": "https://portalbencana.nadma.gov.my/en/",
                "public_infobanjir": "https://publicinfobanjir.water.gov.my/",
                "metmalaysia_warnings": "https://api.data.gov.my/weather/warning",
            },
        }

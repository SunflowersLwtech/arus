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

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from backend.core.grid_world import GridWorld
from backend.game.agencies import CALLSIGN_TO_AGENCY, idle_drone_for_agency
from backend.game.scenario import Card, Scenario, load_real_stats, load_scenario
from backend.game.score import Gauges, apply_delta, compute_grade, evaluate

logger = logging.getLogger("arus.engine")


@dataclass
class ChoiceRecord:
    card_id: str
    option_id: str
    tick: int
    deltas: dict
    gauges_after: dict
    flavor_bm: str
    flavor_en: str
    ai_option_id: str = ""   # what COACH recommended (if any) — for alignment metric


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

# Manual scouting reward: each newly-detected objective gives +1 life,
# capped so that the card-based score remains the primary axis.
SCOUT_BONUS_CAP = 5


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
    _detected_ids: set[str] = field(default_factory=set)
    _scout_bonus_used: int = 0
    _prealerts_fired: set[str] = field(default_factory=set)
    live_warnings: list = field(default_factory=list)

    @classmethod
    def start_new(
        cls,
        world: GridWorld,
        scenario_id: str = "shah_alam_hard",
        locale: str = "en",
        live_warnings: list | None = None,
    ) -> "GameEngine":
        # If MetMalaysia has active warnings today, tighten the card cadence
        # by up to 20%. Today's real weather reshapes today's drill.
        warnings = list(live_warnings or [])
        difficulty_squeeze = min(0.2, 0.05 * len(warnings))
        scenario = load_scenario(scenario_id)
        if difficulty_squeeze > 0:
            for card in scenario.cards:
                card.trigger_tick = max(10, int(card.trigger_tick * (1.0 - difficulty_squeeze)))
        engine = cls(
            world=world,
            scenario=scenario,
            locale=locale,
            gauges=Gauges(time_remaining=scenario.duration_seconds),
        )
        engine.live_warnings = warnings
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

        # Pre-alert: 60 ticks (~12 s) before a card's trigger_tick, paint
        # its coord on the map as a pulsing hotspot. Players who scout it
        # early gain an advantage when the call actually comes in.
        if self._pending_card is None:
            for card in self.scenario.cards:
                if card.id in self._fired_card_ids or card.id in self._prealerts_fired:
                    continue
                if card.trigger_tick - tick <= 60 and tick < card.trigger_tick:
                    self._prealerts_fired.add(card.id)
                    events.append({
                        "type": "prealert",
                        "payload": {
                            "card_id": card.id,
                            "coord": list(card.coord or [0, 0]),
                            "eta_ticks": max(0, card.trigger_tick - tick),
                            "title_en": card.title_en,
                            "title_bm": card.title_bm,
                        },
                    })

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

        # Atmospheric radio chatter: every ~12 s, emit a passive log entry
        # so the NADMA Radio panel keeps moving. We fire this whether a
        # card is open or not — the illusion of a live situation room
        # breaks the moment the radio goes silent.
        if (
            tick - self._last_passive_tick >= PASSIVE_INTERVAL_TICKS
            and tick > 20
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

        # Scouting reward: each newly-detected objective gives +1 saved,
        # capped by SCOUT_BONUS_CAP. This turns the map into a real
        # second scoring axis — manual drone dispatch now matters.
        try:
            objectives = getattr(self.world.objective_field, "objectives", {}) or {}
            for obj in objectives.values():
                obj_id = getattr(obj, "id", None)
                detected = bool(getattr(obj, "detected", False))
                if obj_id is None or not detected:
                    continue
                if obj_id in self._detected_ids:
                    continue
                self._detected_ids.add(obj_id)
                if self._scout_bonus_used >= SCOUT_BONUS_CAP:
                    continue
                self._scout_bonus_used += 1
                self.gauges.saved += 1
                x = getattr(obj, "x", 0)
                y = getattr(obj, "y", 0)
                events.append({
                    "type": "narrator_log",
                    "payload": {
                        "id": f"scout-{obj_id}",
                        "speaker": "Dispatcher log",
                        "text_en": f"Victim confirmed at grid ({x},{y}) via recon (+1 lives).",
                        "text_bm": f"Mangsa disahkan di petak ({x},{y}) melalui pengintipan (+1 nyawa).",
                        "tone": "system",
                        "timestamp_tick": tick,
                    },
                })
        except Exception as exc:  # pragma: no cover
            logger.debug("scout check failed: %s", exc)

        # Evaluate win/lose every tick — BUT never terminate while a
        # card is still pending. Judge found that aggressive card-7 picks
        # could flip status to "won" on the tick between game_card(c08)
        # broadcast and the player's click, leaving card 8 invisible in
        # debrief. Deferring the verdict to post-resolution closes that
        # race and also keeps the session duration predictable for demos.
        if self._pending_card is None:
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

    def choose(self, card_id: str, option_id: str, ai_option_id: str = "") -> dict:
        """Apply a player's choice. Returns a broadcastable event payload.

        `ai_option_id` is the option the COACH agent recommended for this
        card (empty if not in COACH or no recommendation yet). Stored on
        the ChoiceRecord so debrief can compute alignment + counterfactual.
        """
        if self._pending_card is None or self._pending_card.id != card_id:
            return {"type": "player_command_result", "payload": {"ok": False, "reason": "no_card_pending"}}
        option = next((o for o in self._pending_card.options if o.id == option_id), None)
        if option is None:
            return {"type": "player_command_result", "payload": {"ok": False, "reason": "unknown_option"}}

        # Resource-scarcity check: if the option requires a specific agency
        # and no idle drone is available, halve the saved delta (the response
        # "happens" but is degraded) and emit a narrator warning so the
        # player sees WHY they got fewer lives than the preview promised.
        effective_deltas = dict(option.deltas)
        degraded = False
        if option.agency and option.map_action == "dispatch_rescue":
            fleet_state_pre = [u.to_dict() for u in self.world.fleet.values()]
            any_idle = any(
                CALLSIGN_TO_AGENCY.get(u["id"]) == option.agency
                and u.get("status") == "idle"
                for u in fleet_state_pre
            )
            if not any_idle:
                saved = int(effective_deltas.get("saved", 0))
                effective_deltas["saved"] = max(0, saved // 2)
                effective_deltas["trust"] = float(effective_deltas.get("trust", 0)) - 5
                degraded = True

        apply_delta(self.gauges, effective_deltas)

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
            deltas=dict(effective_deltas),
            gauges_after=self.gauges.as_dict(),
            flavor_bm=option.flavor_bm,
            flavor_en=option.flavor_en,
            ai_option_id=ai_option_id or "",
        )
        self._history.append(record)
        self._pending_card = None

        # Post-resolution evaluation. on_tick defers while a card is
        # pending; here we settle immediately so the game-over broadcast
        # fires in lockstep with the last card's player_command_result.
        post_verdict = evaluate(self.gauges, self.scenario.target_saved)
        if post_verdict["status"] != "in_progress":
            self._status = post_verdict["status"]
            self._status_reason = post_verdict["reason"]

        return {
            "type": "player_command_result",
            "payload": {
                "ok": True,
                "card_id": record.card_id,
                "option_id": record.option_id,
                "flavor": {"bm": option.flavor_bm, "en": option.flavor_en},
                "gauges": self.gauges.as_dict(),
                "deltas": dict(effective_deltas),
                "assigned_drone": assigned_drone,
                "agency": option.agency or (CALLSIGN_TO_AGENCY.get(assigned_drone or "") if assigned_drone else ""),
                "degraded": degraded,
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
            "live_warnings_count": len(self.live_warnings),
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
            ai_option = None
            if card and h.ai_option_id:
                ai_option = next((o for o in card.options if o.id == h.ai_option_id), None)
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
                "ai_option_id": h.ai_option_id,
                "ai_option_label_en": ai_option.label_en if ai_option else "",
                "ai_option_label_bm": ai_option.label_bm if ai_option else "",
                "ai_deltas": dict(ai_option.deltas) if ai_option else {},
            }

        choices = [_enrich(h) for h in self._history]

        # Alignment: how often did the player follow the AI's recommendation?
        with_ai = [c for c in choices if c["ai_option_id"]]
        aligned = sum(1 for c in with_ai if c["ai_option_id"] == c["option_id"])
        alignment = {
            "total_with_ai": len(with_ai),
            "aligned": aligned,
            "pct": round(100 * aligned / len(with_ai)) if with_ai else 0,
        } if with_ai else None

        # Counterfactual: what gauges would you have ended with if you'd
        # followed the AI on every card it had a recommendation for?
        counterfactual = None
        if with_ai:
            hypo = Gauges(time_remaining=self.scenario.duration_seconds)
            for c in choices:
                d = c["ai_deltas"] if c["ai_option_id"] else c["deltas"]
                apply_delta(hypo, d)
            counterfactual = {
                "gauges": hypo.as_dict(),
                "grade": compute_grade(hypo, self.scenario.target_saved),
            }

        return {
            "session_id": self.session_id,
            "status": self._status,
            "grade": compute_grade(self.gauges, self.scenario.target_saved),
            "gauges": self.gauges.as_dict(),
            "target_saved": self.scenario.target_saved,
            "choices": choices,
            "alignment": alignment,
            "counterfactual": counterfactual,
            "real_event": stats,
            "live_warnings": self.live_warnings,
            "extension_links": {
                "nadma_portal_bencana": "https://portalbencana.nadma.gov.my/en/",
                "public_infobanjir": "https://publicinfobanjir.water.gov.my/",
                "metmalaysia_warnings": "https://api.data.gov.my/weather/warning",
            },
        }

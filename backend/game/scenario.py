"""Scenario loader — reads cards.yaml + real_stats.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_CARDS_PATH = Path(__file__).parent / "cards.yaml"
_STATS_PATH = Path(__file__).parent / "real_stats.json"


@dataclass
class Option:
    id: str
    label_bm: str
    label_en: str
    deltas: dict
    flavor_bm: str = ""
    flavor_en: str = ""
    map_action: str = ""
    agency: str = ""       # e.g. "BOMBA" — which drone class to dispatch


@dataclass
class Card:
    id: str
    trigger_tick: int
    title_bm: str
    title_en: str
    body_bm: str
    body_en: str
    coord: list[int] = field(default_factory=lambda: [0, 0])
    options: list[Option] = field(default_factory=list)


@dataclass
class Scenario:
    id: str
    name_bm: str
    name_en: str
    intro_hook_bm: str
    intro_hook_en: str
    target_saved: int
    duration_seconds: float
    real_event_key: str
    cards: list[Card]


def _load_raw() -> dict[str, Any]:
    with _CARDS_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_scenario(scenario_id: str = "shah_alam_hard") -> Scenario:
    """Load a scenario by id. Falls back to the only shipped scenario."""
    raw = _load_raw()
    scenarios = raw.get("scenarios", {})
    all_cards = raw.get("cards", {})

    sc_def = scenarios.get(scenario_id)
    if sc_def is None:
        # Fallback to first available scenario if the requested one is missing.
        scenario_id, sc_def = next(iter(scenarios.items()))

    card_list: list[Card] = []
    for cid in sc_def.get("cards", []):
        c_def = all_cards.get(cid)
        if c_def is None:
            continue
        options = [
            Option(
                id=o["id"],
                label_bm=o.get("label_bm", ""),
                label_en=o.get("label_en", ""),
                deltas=o.get("deltas", {}),
                flavor_bm=o.get("flavor_bm", ""),
                flavor_en=o.get("flavor_en", ""),
                map_action=o.get("map_action", ""),
                agency=str(o.get("agency", "") or "").upper(),
            )
            for o in c_def.get("options", [])
        ]
        card_list.append(
            Card(
                id=cid,
                trigger_tick=int(c_def.get("trigger_tick", 0)),
                title_bm=c_def.get("title_bm", ""),
                title_en=c_def.get("title_en", ""),
                body_bm=c_def.get("body_bm", ""),
                body_en=c_def.get("body_en", ""),
                coord=list(c_def.get("coord", [0, 0])),
                options=options,
            )
        )

    return Scenario(
        id=scenario_id,
        name_bm=sc_def.get("name_bm", scenario_id),
        name_en=sc_def.get("name_en", scenario_id),
        intro_hook_bm=sc_def.get("intro_hook_bm", ""),
        intro_hook_en=sc_def.get("intro_hook_en", ""),
        target_saved=int(sc_def.get("target_saved", 0)),
        duration_seconds=float(sc_def.get("duration_seconds", 420.0)),
        real_event_key=sc_def.get("real_event_key", ""),
        cards=sorted(card_list, key=lambda c: c.trigger_tick),
    )


def load_real_stats(key: str) -> dict:
    """Load canonical 2021/2024 flood statistics used in debrief."""
    with _STATS_PATH.open("r", encoding="utf-8") as fh:
        stats = json.load(fh)
    return stats.get(key, {})


def available_scenarios() -> list[str]:
    raw = _load_raw()
    return list(raw.get("scenarios", {}).keys())

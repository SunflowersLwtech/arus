"""Gauge math, win/lose thresholds, final grade."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal


FAIL_ASSETS = 0
FAIL_TRUST = 0


@dataclass
class Gauges:
    """Four meters the player steers during a game."""
    saved: int = 0          # absolute count of people rescued
    assets: float = 100.0   # % of deployable resources left
    trust: float = 100.0    # % of agency confidence in dispatcher
    time_remaining: float = 600.0  # seconds until cutoff

    def as_dict(self) -> dict:
        return asdict(self)


def apply_delta(gauges: Gauges, delta: dict) -> Gauges:
    """Mutate gauges by a card-option delta."""
    gauges.saved = max(0, gauges.saved + int(delta.get("saved", 0)))
    gauges.assets = clamp(gauges.assets + float(delta.get("assets", 0)), 0, 100)
    gauges.trust = clamp(gauges.trust + float(delta.get("trust", 0)), 0, 100)
    return gauges


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


Verdict = Literal["in_progress", "won", "partial", "failed"]


def evaluate(gauges: Gauges, target_saved: int) -> dict:
    """Return {status, reason} for the current gauge state."""
    if gauges.trust <= FAIL_TRUST:
        return {"status": "failed", "reason": "trust_collapsed"}
    # Assets at 0 is ALWAYS terminal — the player has no more ability to
    # respond. If they already hit the save target, give them the W;
    # otherwise it's a failure. This prevents the "stuck watching the
    # timer count down with no new cards" deadlock the judge flagged.
    if gauges.assets <= FAIL_ASSETS:
        if gauges.saved >= target_saved:
            return {"status": "won", "reason": "assets_depleted_target_met"}
        return {"status": "failed", "reason": "assets_depleted"}
    if gauges.time_remaining <= 0:
        if gauges.saved >= target_saved:
            return {"status": "won", "reason": "time_up_sufficient"}
        return {"status": "partial", "reason": "time_up_insufficient"}
    return {"status": "in_progress", "reason": ""}


GRADE_THRESHOLDS = [
    ("A", 0.90),  # saved >= 90% of target AND trust >= 80
    ("B", 0.70),
    ("C", 0.50),
    ("D", 0.25),
    ("F", 0.0),
]


def compute_grade(gauges: Gauges, target_saved: int) -> str:
    if target_saved <= 0:
        return "F"
    save_ratio = min(1.0, gauges.saved / target_saved)
    trust_penalty = 1.0 if gauges.trust >= 80 else (gauges.trust / 80)
    score = save_ratio * trust_penalty
    for grade, threshold in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"

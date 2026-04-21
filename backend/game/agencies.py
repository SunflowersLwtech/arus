"""Agency ↔ UAV mapping + shared colour/label metadata.

Banjir Drill represents Malaysia's four disaster-response agencies as
five drones on the 3D map:

    Alpha   → BOMBA   (Fire & Rescue — swift-water, rooftop extraction)
    Bravo   → BOMBA   (second swift-water team)
    Charlie → APM     (Civil Defence — evacuation convoys, air lift)
    Delta   → MMEA    (Maritime — boats, coast)
    Echo    → NADMA   (Coordination — liaison, comms, command relay)

When the player picks a card option tagged with an agency, the game
engine dispatches that agency's drone (not a random one) so the map
shows a meaningful cause-effect between decisions and assets.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgencyInfo:
    code: str
    name_en: str
    name_bm: str
    color: str        # hex — used by the 3D scene and left sidebar
    short: str        # 3-4 char label painted on the drone glyph


AGENCIES: dict[str, AgencyInfo] = {
    "BOMBA": AgencyInfo("BOMBA", "Fire & Rescue", "BOMBA (Bomba & Penyelamat)", "#FF6A3D", "BMB"),
    "APM":   AgencyInfo("APM", "Civil Defence", "APM (Angkatan Pertahanan Awam)", "#06D6A0", "APM"),
    "MMEA":  AgencyInfo("MMEA", "Maritime Enforcement", "MMEA (Penguatkuasaan Maritim)", "#4DA8DA", "MMEA"),
    "NADMA": AgencyInfo("NADMA", "Disaster Coordinator", "NADMA (Agensi Pengurusan Bencana)", "#FFCC00", "NDMA"),
}

# Deterministic callsign → agency assignment for the default 5-drone fleet.
CALLSIGN_TO_AGENCY: dict[str, str] = {
    "Alpha":   "BOMBA",
    "Bravo":   "BOMBA",
    "Charlie": "APM",
    "Delta":   "MMEA",
    "Echo":    "NADMA",
}


def agency_for_callsign(callsign: str) -> AgencyInfo:
    code = CALLSIGN_TO_AGENCY.get(callsign, "NADMA")
    return AGENCIES[code]


def augment_fleet(fleet: list[dict]) -> list[dict]:
    """Given a fleet snapshot list from GridWorld.to_dict, append agency fields."""
    out = []
    for u in fleet:
        info = agency_for_callsign(u["id"])
        out.append({
            **u,
            "agency": info.code,
            "agency_color": info.color,
            "agency_short": info.short,
            "agency_label_en": info.name_en,
            "agency_label_bm": info.name_bm,
        })
    return out


def idle_drone_for_agency(fleet_state: list[dict], agency: str | None) -> str | None:
    """Pick an idle drone of the given agency (fallback to any idle drone)."""
    # Match exact agency + idle status first
    if agency:
        for u in fleet_state:
            if CALLSIGN_TO_AGENCY.get(u["id"]) == agency and u.get("status") == "idle":
                return u["id"]
        # Same agency but any status (may still be reassigned, with flavor cost)
        for u in fleet_state:
            if CALLSIGN_TO_AGENCY.get(u["id"]) == agency:
                return u["id"]
    # Any idle drone
    for u in fleet_state:
        if u.get("status") == "idle":
            return u["id"]
    return fleet_state[0]["id"] if fleet_state else None

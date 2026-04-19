"""Smoke tests for the bilingual hand-off ring buffer."""
from __future__ import annotations

from backend.services.handoff_log import ingest_agency_text, recent, _HANDOFFS


SAMPLE = """AGENSI: BOMBA
KOORDINAT: (2, 16) — Kg. Kubang Puteh, Kuala Krai, Kelantan
KEUTAMAAN: TINGGI
RINGKASAN (BM): Mangsa telah dikesan di Kg. Kubang Puteh, Kuala Krai,
  Kelantan, memerlukan bantuan segera.
SUMMARY (EN): A victim has been detected at Kg. Kubang Puteh, Kuala Krai,
  Kelantan, requiring immediate assistance.
CADANGAN TINDAKAN / RECOMMENDED ACTION: Hantar pasukan penyelamat untuk
  penilaian dan tindakan segera. / Deploy rescue team for immediate
  assessment and action.

AGENSI: NADMA
KOORDINAT: (15, 5) — Kg. Panti, Kota Tinggi, Johor
KEUTAMAAN: SEDERHANA
RINGKASAN (BM): Koordinasi evakuasi diperlukan.
SUMMARY (EN): Evacuation coordination required.
CADANGAN TINDAKAN / RECOMMENDED ACTION: Aktifkan PPS terdekat. / Activate
  the nearest PPS shelter.
"""


def setup_function():
    _HANDOFFS.clear()


def test_parses_both_blocks():
    rows = ingest_agency_text(SAMPLE, cycle=1, mission_id="t1")
    assert len(rows) == 2
    agencies = {r["agency"] for r in rows}
    assert agencies == {"BOMBA", "NADMA"}


def test_populates_fields():
    rows = ingest_agency_text(SAMPLE, cycle=1, mission_id="t1")
    bomba = next(r for r in rows if r["agency"] == "BOMBA")
    assert "Kg. Kubang Puteh" in bomba["coord"]
    assert bomba["priority"] == "TINGGI"
    assert "Mangsa" in bomba["bm"]
    assert "victim" in bomba["en"].lower()
    assert "Deploy rescue team" in bomba["action"]


def test_no_new_handoffs_sentinel():
    assert ingest_agency_text("NO NEW HANDOFFS THIS CYCLE / TIADA HANDOFF BARU", 1, "t") == []
    assert ingest_agency_text("", 1, "t") == []


def test_recent_returns_newest_first():
    ingest_agency_text(SAMPLE, cycle=1, mission_id="t1")
    recs = recent(10)
    assert len(recs) == 2
    # NADMA was emitted after BOMBA in the sample, so newest-first
    assert recs[0]["agency"] == "NADMA"
    assert recs[1]["agency"] == "BOMBA"


def test_ring_buffer_bounded():
    for i in range(60):
        ingest_agency_text(SAMPLE.replace("BOMBA", f"BOMBA"), cycle=i, mission_id="t")
    assert len(recent(100)) <= 50

"""Smoke tests for the Malaysian locality mapping."""
from __future__ import annotations

from backend.core.locality import locate, summarise_zone


def test_kelantan_covers_northern_half():
    # Grid cells (0..9, 0..19) should resolve to Kelantan
    for (x, y) in [(0, 0), (5, 5), (9, 5), (2, 16)]:
        r = locate(x, y)
        assert r["state"] == "Kelantan", f"({x},{y}) → {r}"


def test_johor_covers_southern_half():
    for (x, y) in [(15, 5), (15, 15), (19, 19), (10, 0)]:
        r = locate(x, y)
        assert r["state"] == "Johor", f"({x},{y}) → {r}"


def test_resolves_named_kampung():
    r = locate(5, 5)
    assert "Kg." in r["kampung"]
    assert r["district"]


def test_summarise_zone_mentions_both_states():
    s = summarise_zone()
    assert "Kelantan" in s
    assert "Johor" in s

"""Smoke tests for the MetMalaysia feed.

Note: these tests actually hit the upstream api.data.gov.my. Since the
upstream is public + unauthenticated, we keep them real. A CI job
running without internet would skip this.
"""
from __future__ import annotations

import asyncio
import pytest

from backend.services.met_feed import fetch_warnings, summarise_for_prompt


@pytest.mark.timeout(15)
def test_fetch_returns_list_or_falls_back():
    data = asyncio.run(fetch_warnings(3))
    assert isinstance(data, list)
    # Upstream may or may not have warnings on any given day; both are fine
    for item in data:
        assert "title_en" in item
        assert "text_en" in item


def test_summarise_empty():
    s = summarise_for_prompt([])
    assert "no active" in s


def test_summarise_populated():
    fake = [{"issued": "2026-04-20T00:30:00", "title_en": "Thunderstorms Warning",
             "heading_en": "Warning on Thunderstorms",
             "text_en": "Thunderstorms over East Johor..."}]
    s = summarise_for_prompt(fake)
    assert "Thunderstorms Warning" in s
    assert "East Johor" in s

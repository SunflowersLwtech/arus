"""REST endpoints for Arus Banjir Drill game mode.

Exposed under /api/game/* (prefix applied in backend/main.py):

    POST /api/game/start     — boot a new session, return intro + scenario
    POST /api/game/choose    — apply a player's option
    GET  /api/game/state     — current game snapshot
    GET  /api/game/debrief   — end-of-game summary + real-flood stats
    GET  /api/game/scenarios — list shipped scenarios
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.game.engine import GameEngine
from backend.game.scenario import available_scenarios

router = APIRouter()


# ─── Request / response models ─────────────────────────────────

class StartRequest(BaseModel):
    scenario_id: str = "shah_alam_hard"
    locale: str = "en"


class ChooseRequest(BaseModel):
    card_id: str
    option_id: str


# ─── Endpoints ─────────────────────────────────────────────────

@router.get("/scenarios")
async def list_scenarios():
    return {"status": "ok", "data": available_scenarios()}


@router.post("/start")
async def start_game(req: StartRequest):
    from backend import main  # lazy import to avoid circular

    world = main.reset_world()
    main.start_simulation()
    engine = GameEngine.start_new(world, scenario_id=req.scenario_id, locale=req.locale)
    main.set_game_engine(engine)

    return {
        "status": "ok",
        "data": {
            "session_id": engine.session_id,
            "scenario": {
                "id": engine.scenario.id,
                "name_bm": engine.scenario.name_bm,
                "name_en": engine.scenario.name_en,
                "intro_hook_bm": engine.scenario.intro_hook_bm,
                "intro_hook_en": engine.scenario.intro_hook_en,
                "target_saved": engine.scenario.target_saved,
                "duration_seconds": engine.scenario.duration_seconds,
            },
            "gauges": engine.gauges.as_dict(),
        },
    }


@router.post("/choose")
async def choose_option(req: ChooseRequest):
    from backend import main

    engine = main.get_game_engine()
    if engine is None:
        raise HTTPException(status_code=409, detail="No game in progress — POST /api/game/start first")

    result = engine.choose(req.card_id, req.option_id)
    return {"status": "ok", "data": result["payload"]}


@router.get("/state")
async def game_state():
    from backend import main

    engine = main.get_game_engine()
    if engine is None:
        return {"status": "ok", "data": None}
    return {"status": "ok", "data": engine.snapshot()}


@router.get("/debrief")
async def game_debrief():
    from backend import main

    engine = main.get_game_engine()
    if engine is None:
        raise HTTPException(status_code=409, detail="No game session")
    if not engine.is_over():
        raise HTTPException(status_code=425, detail="Game still in progress")
    return {"status": "ok", "data": engine.compute_debrief()}

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
from backend.services import narrator

router = APIRouter()


# ─── Request / response models ─────────────────────────────────

class StartRequest(BaseModel):
    scenario_id: str = "shah_alam_hard"
    locale: str = "en"
    mode: str = "PLAY"  # PLAY | COACH | AUTO


class ChooseRequest(BaseModel):
    card_id: str
    option_id: str


class DispatchRequest(BaseModel):
    drone_id: str
    x: int
    y: int


# ─── Endpoints ─────────────────────────────────────────────────

@router.get("/scenarios")
async def list_scenarios():
    return {"status": "ok", "data": available_scenarios()}


@router.post("/start")
async def start_game(req: StartRequest):
    from backend import main  # lazy import to avoid circular

    mode = (req.mode or "PLAY").upper()
    if mode not in ("PLAY", "COACH", "AUTO"):
        raise HTTPException(status_code=400, detail=f"Unknown mode: {req.mode}")

    world = main.reset_world()
    main.set_mode(mode)
    main.start_simulation()

    # Tear down any previous mode's runners.
    main.set_coach_agent(None)
    prev_auto = main.get_auto_runner()
    if prev_auto is not None:
        try:
            prev_auto.cancel()
        except Exception:
            pass
    main.set_auto_runner(None)

    if mode == "AUTO":
        # AUTO mode: no GameEngine, v1 commander pipeline drives the world.
        from backend.agents.auto_runner import AgentRunner as AutoRunner
        main.set_game_engine(None)
        main.set_auto_runner(AutoRunner(world=world, broadcast_fn=main.manager.broadcast))
        return {
            "status": "ok",
            "data": {
                "mode": "AUTO",
                "session_id": main.get_auto_runner().mission_id,
                "scenario": None,
                "gauges": None,
                "intro": None,
            },
        }

    # PLAY + COACH share the GameEngine.
    engine = GameEngine.start_new(world, scenario_id=req.scenario_id, locale=req.locale)
    main.set_game_engine(engine)
    intro = await narrator.generate_intro(engine.scenario, req.locale)

    if mode == "COACH":
        from backend.agents.coach import CoachAgent
        main.set_coach_agent(CoachAgent(world=world, broadcast_fn=main.manager.broadcast))

    return {
        "status": "ok",
        "data": {
            "mode": mode,
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
            "intro": intro,
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


@router.post("/dispatch")
async def manual_dispatch(req: DispatchRequest):
    """Player-issued waypoint. Used by click-to-target on the 3D map."""
    from backend import main

    world = main.get_world()
    if req.drone_id not in world.fleet:
        raise HTTPException(status_code=404, detail="drone not found")
    if not (0 <= req.x < world.size and 0 <= req.y < world.size):
        raise HTTPException(status_code=400, detail="coord out of bounds")
    try:
        world.set_waypoint(req.drone_id, req.x, req.y)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "ok", "data": {"drone_id": req.drone_id, "target": [req.x, req.y]}}


@router.get("/debrief")
async def game_debrief():
    from backend import main

    engine = main.get_game_engine()
    if engine is None:
        raise HTTPException(status_code=409, detail="No game session")
    if not engine.is_over():
        raise HTTPException(status_code=425, detail="Game still in progress")

    debrief = engine.compute_debrief()
    commentary = await narrator.generate_debrief(debrief, engine.locale)
    debrief["commentary"] = commentary
    return {"status": "ok", "data": debrief}

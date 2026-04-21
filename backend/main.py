"""Arus Banjir Drill — FastAPI Gateway.

Responsibilities:
1. WebSocket /ws/live — broadcast world + game state at 5 Hz
2. REST /api/game/*    — start / choose / debrief (see backend.routes.game)
3. REST /api/health, /api/state, /api/locality, /api/live/warnings
4. REST /api/vision/analyse — Gemini Vision (bonus feature)
5. Static frontend hosting

Run:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local", override=True)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.core.grid_world import GridWorld
from backend.core.locality import locate, summarise_zone
from backend.game.agencies import AGENCIES, augment_fleet
from backend.services import vision, met_feed, tool_server as mcp_tool_server

logger = logging.getLogger("arus")
logging.basicConfig(level=logging.INFO)


# ─── Simulation + Game State ───────────────────────────────────

world = GridWorld(size=20, num_uavs=5, num_objectives=8, num_obstacles=15)
simulation_running = False
simulation_speed = 1.0

# Game engine is lazy-initialised on /api/game/start so the server can boot
# without a game context (judges will see the idle world first).
game_engine = None  # type: ignore[assignment]
coach_agent = None  # type: ignore[assignment]
auto_runner = None  # type: ignore[assignment]
current_mode: str = "PLAY"  # PLAY | COACH | AUTO


def get_world() -> GridWorld:
    return world


def get_game_engine():
    return game_engine


def set_game_engine(engine) -> None:
    global game_engine
    game_engine = engine


def get_coach_agent():
    return coach_agent


def set_coach_agent(agent) -> None:
    global coach_agent
    coach_agent = agent


def get_auto_runner():
    return auto_runner


def set_auto_runner(runner) -> None:
    global auto_runner
    auto_runner = runner


def get_mode() -> str:
    return current_mode


def set_mode(mode: str) -> None:
    global current_mode
    current_mode = mode


def reset_world(size: int = 20, uavs: int = 5, objs: int = 8, obstacles: int = 15) -> GridWorld:
    """Rebuild the underlying GridWorld (called when a new game starts)."""
    global world, simulation_running
    simulation_running = False
    world = GridWorld(size=size, num_uavs=uavs, num_objectives=objs, num_obstacles=obstacles)
    # Re-wire the MCP tool server to the new world (same-process shared ref)
    try:
        mcp_tool_server.set_shared_world(world)
    except Exception:
        pass
    return world


def start_simulation() -> None:
    global simulation_running
    simulation_running = True
    world.mission_status = "running"


def stop_simulation() -> None:
    global simulation_running
    simulation_running = False


# ─── WebSocket Connection Manager ──────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, ws: WebSocket):
        await ws.accept()
        self.active[client_id] = ws
        logger.info(f"WS client {client_id} connected ({len(self.active)} total)")

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)
        logger.info(f"WS client {client_id} disconnected ({len(self.active)} total)")

    async def broadcast(self, message: dict):
        if not self.active:
            return
        dead = []
        for cid, ws in self.active.items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(cid)
        for cid in dead:
            self.active.pop(cid, None)


manager = ConnectionManager()


# ─── Lifespan ──────────────────────────────────────────────────

async def _start_mcp_server():
    """MCP tool server runs alongside FastAPI on port 8001 (127.0.0.1 only).

    Agents (COACH + AUTO) connect to it via StreamableHTTP. Not exposed
    externally — same container, internal loopback.
    """
    import uvicorn
    mcp_tool_server.set_shared_world(world)
    config = uvicorn.Config(
        mcp_tool_server.mcp.streamable_http_app(),
        host="127.0.0.1",
        port=8001,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    await server.serve()


_mcp_task = None


@asynccontextmanager
async def lifespan(app):
    global _mcp_task
    _mcp_task = asyncio.create_task(_start_mcp_server())
    asyncio.create_task(simulation_loop())
    logger.info("Arus Banjir Drill started on port 8000, MCP on 8001")
    yield
    if _mcp_task:
        _mcp_task.cancel()


app = FastAPI(title="Arus — Banjir Drill", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Background simulation loop ─────────────────────────────────

def _world_snapshot_with_agencies() -> dict:
    snap = world.get_state_snapshot()
    snap["fleet"] = augment_fleet(snap.get("fleet", []))
    return snap


AUTO_INTERVAL_TICKS = 200  # ~40 s at 5 Hz — v1 cadence


async def simulation_loop():
    """Advance world tick + drive game/coach/auto per mode + broadcast state."""
    while True:
        if simulation_running:
            world.step()
            # PLAY / COACH drive the GameEngine (cards + gauges)
            if game_engine is not None and current_mode in ("PLAY", "COACH"):
                try:
                    events = game_engine.on_tick(world.tick)
                    for ev in events:
                        await manager.broadcast(ev)
                        # In COACH, fire the advisor whenever a new card appears
                        if (
                            current_mode == "COACH"
                            and coach_agent is not None
                            and ev.get("type") == "game_card"
                        ):
                            asyncio.create_task(_coach_on_card(ev["payload"]))
                except Exception as exc:
                    logger.exception("game_engine.on_tick failed: %s", exc)
            # AUTO drives the 5-stage commander pipeline
            if current_mode == "AUTO" and auto_runner is not None:
                first_cycle = world.tick == 25 and auto_runner._cycle == 0
                periodic = world.tick > 0 and world.tick % AUTO_INTERVAL_TICKS == 0
                if (first_cycle or periodic) and auto_runner.try_start():
                    asyncio.create_task(auto_runner.run_cycle())

            await manager.broadcast({
                "type": "state_update",
                "payload": _world_snapshot_with_agencies(),
                "game": game_engine.snapshot() if game_engine else None,
                "mode": current_mode,
            })
        await asyncio.sleep(0.2 / max(simulation_speed, 0.1))


async def _coach_on_card(card_payload: dict) -> None:
    """Background: run COACH agent for a newly surfaced card."""
    if coach_agent is None or game_engine is None:
        return
    try:
        await coach_agent.recommend_for_card(card_payload, game_engine.gauges.as_dict())
    except Exception as exc:
        logger.exception("coach recommend_for_card failed: %s", exc)


# ─── WebSocket endpoint ────────────────────────────────────────

@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    client_id = str(uuid.uuid4())[:8]
    await manager.connect(client_id, ws)
    try:
        await ws.send_json({
            "type": "initial_state",
            "payload": _world_snapshot_with_agencies(),
            "game": game_engine.snapshot() if game_engine else None,
        })
        while True:
            raw = await ws.receive_text()
            try:
                _ = json.loads(raw)  # game actions go through REST /api/game/*
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WS error {client_id}: {e}")
        manager.disconnect(client_id)


# ─── Core REST ─────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "arus-banjir-drill", "zone": summarise_zone()}


@app.get("/api/state")
async def get_state():
    return {
        "status": "ok",
        "data": _world_snapshot_with_agencies(),
        "game": game_engine.snapshot() if game_engine else None,
    }


@app.get("/api/agencies")
async def list_agencies():
    """Agency metadata used by the frontend sidebar (labels, colours)."""
    return {"status": "ok", "data": {code: a.__dict__ for code, a in AGENCIES.items()}}


@app.get("/api/locality/{x}/{y}")
async def locality(x: int, y: int):
    return {"status": "ok", "data": locate(x, y)}


@app.get("/api/live/warnings")
async def live_warnings(limit: int = 10):
    warnings = await met_feed.fetch_warnings(limit)
    return {
        "status": "ok",
        "count": len(warnings),
        "data": warnings,
        "source": "api.data.gov.my/weather/warning",
    }


@app.post("/api/vision/analyse")
async def vision_analyse(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail=f"Unsupported type {file.content_type}")
    image_bytes = await file.read()
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image > 8MB")
    try:
        result = await vision.analyse_image(image_bytes, file.content_type)
    except Exception as e:
        logger.exception("vision analyse failed")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "data": result.model_dump()}


# ─── Game routes ───────────────────────────────────────────────

from backend.routes.game import router as game_router  # noqa: E402  (circular-safe import)

app.include_router(game_router, prefix="/api/game", tags=["game"])


# ─── Static frontend ───────────────────────────────────────────

_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith(("api/", "ws/")):
            return JSONResponse({"error": "Not found"}, status_code=404)
        file = _frontend_dist / full_path
        if file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(_frontend_dist / "index.html")

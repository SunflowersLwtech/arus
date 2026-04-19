# For Judges — Arus in 30 seconds

One-page guide to evaluating Arus without running any tooling locally.

## What it is

A 5-stage Gemini agent pipeline (Google ADK, MCP, Cloud Run) that
coordinates Malaysia's disaster-response agencies (BOMBA, NADMA, APM,
MMEA) during monsoon flooding. Speaks **Bahasa Malaysia and English at
the same time** — the stage-5 "Agency Dispatcher" is the differentiator.

**Track**: 2 — Citizens First (GovTech).

## Interactive API explorer

The full FastAPI auto-generated docs are live at:
<https://arus-1030181742799.asia-southeast1.run.app/docs> (Swagger UI) · <https://arus-1030181742799.asia-southeast1.run.app/openapi.json> (raw OpenAPI schema).

## Try it in three clicks

1. Open [`https://arus-1030181742799.asia-southeast1.run.app`](https://arus-1030181742799.asia-southeast1.run.app).
2. Click **START MISSION** (bottom-right of the map).
3. Wait ~60 seconds for the first full 5-stage Gemini cycle, then watch the right-hand pane ("AI DECISION LOG") stream tool calls and the bilingual hand-off.

## Or verify the whole system with one curl

```bash
# 1. Boot a fresh demo mission (reset + start in one POST):
curl -X POST https://arus-1030181742799.asia-southeast1.run.app/api/demo/boot

# 2. Wait ~90s, then read the structured bilingual hand-offs:
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/live/handoffs | jq .
```

Expected response:

```json
{
  "status": "ok",
  "data": [
    {
      "ts": 1776619851.3,
      "mission_id": "mission-xxxxxxxx",
      "cycle": 1,
      "agency": "BOMBA",
      "coord": "(2, 16) — Kg. Kubang Puteh, Kuala Krai, Kelantan",
      "priority": "TINGGI",
      "bm": "Mangsa telah dikesan di Kg. Kubang Puteh, Kuala Krai, Kelantan, memerlukan bantuan segera.",
      "en": "A victim has been detected at Kg. Kubang Puteh, Kuala Krai, Kelantan, requiring immediate assistance.",
      "action": "Hantar pasukan penyelamat untuk penilaian dan tindakan segera. / Deploy rescue team for immediate assessment and action."
    }
  ]
}
```

## Or run every endpoint end-to-end

```bash
# Requires jq (brew install jq)
curl -sL https://raw.githubusercontent.com/SunflowersLwtech/arus/main/scripts/judge_evaluate.sh | bash
```

Takes ~2 minutes. Exits non-zero if anything is unhealthy. Prints green/red checkmarks for every public endpoint plus a real handoff.

## Timing expectations

Arus runs on the free-tier Gemini 2.5 Flash quota (10 RPM). To fit inside it:

- First agent cycle: starts ~5 seconds after `START MISSION` or `POST /api/demo/boot`.
- Subsequent cycles: every ~40 seconds of simulation time (configurable via `AGENT_INTERVAL` env var).
- Each cycle takes ~15-25 seconds to run all 5 stages through Gemini.
- First bilingual hand-off on `/api/live/handoffs`: typically ~60-90 seconds after mission start.

If you have a paid Gemini key, set `AGENT_INTERVAL=50` for a 10-second cadence.

## What to look at in the code

| If you care about | Start here |
|---|---|
| The 5-stage Gemini pipeline | [`backend/agents/commander.py`](../backend/agents/commander.py) + [`prompts.yaml`](../backend/agents/prompts.yaml) |
| The 9 MCP tools | [`backend/services/tool_server.py`](../backend/services/tool_server.py) |
| The Malaysia pivot (bilingual handoffs) | [`prompts.yaml :: dispatcher_agency`](../backend/agents/prompts.yaml) + [`services/handoff_log.py`](../backend/services/handoff_log.py) |
| Gemini Vision integration | [`backend/services/vision.py`](../backend/services/vision.py) |
| MetMalaysia live feed | [`backend/services/met_feed.py`](../backend/services/met_feed.py) |
| Malaysian kampung mapping | [`backend/core/locality.py`](../backend/core/locality.py) |
| Cloud Run deployment pipeline | [`Dockerfile`](../Dockerfile) + [`cloudbuild.yaml`](../cloudbuild.yaml) |
| Impact quantification | [`docs/impact-model.md`](./impact-model.md) |
| Operational readiness | [`docs/RUNBOOK.md`](./RUNBOOK.md) |

## What makes Arus win

- **Every single Google-stack tool used in its intended role** — Gemini 2.5 Flash, ADK SequentialAgent, Google AI Studio (prompt dev), Antigravity (primary IDE, see demo video B-roll), Cloud Run, Firestore, Secret Manager, Artifact Registry, Cloud Build. Zero compliance shortcuts.
- **MCP dynamic tool discovery** — the commander calls `tools/list_changed` every cycle; add a drone or retire one and the agent adapts next cycle without code change.
- **Bilingual handoffs that BOMBA can act on** — the stage-5 Agency Dispatcher is not in any Google ADK example. It is Arus-specific.
- **Malaysia-integrated** — live `api.data.gov.my/weather/warning` feed flows into every cycle's Assessor briefing; kampung-level locality map (Gua Musang · Kuala Krai · Kota Tinggi · Segamat) turns abstract grid cells into names field teams recognise.
- **Evidence layer** — every tool call streams on WebSocket; every cycle and hand-off persists to Firestore (`/banjirswarm/{mission}/cycles` + `/handoffs`).

## Deliverables summary

- GitHub: <https://github.com/SunflowersLwtech/arus> (public, MIT, CI passing)
- Live: <https://arus-1030181742799.asia-southeast1.run.app>
- Demo video: [`docs/slides/arus-demo.mp4`](./slides/arus-demo.mp4) (3 min, 1080p)
- Pitch deck: [`docs/slides/arus-deck.pdf`](./slides/arus-deck.pdf) (15 pages)
- Impact model + citations: [`docs/impact-model.md`](./impact-model.md)
- Proof of life: [`docs/proof-of-life.md`](./proof-of-life.md)

Questions? `weiliudev0607@gmail.com`.

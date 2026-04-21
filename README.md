<div align="center">

# Arus — Banjir Drill

### _arus_ (Bahasa Malaysia, n.) — the current of a river; the flow of people, information, and intent.

**When the monsoon drowned Taman Sri Muda in 2021, residents waited 16 hours on rooftops.**
**Arus is a 7-minute simulator that lets a Malaysian citizen feel exactly why.**

[![Google Antigravity](https://img.shields.io/badge/Built_in_Antigravity-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://antigravity.google.com)
[![Gemini 2.5 Flash](https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Cloud Run](https://img.shields.io/badge/Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![MetMalaysia](https://img.shields.io/badge/data.gov.my-LIVE_FEED-E63946?style=for-the-badge)](https://api.data.gov.my/weather/warning)

**MyAI Future Hackathon 2026 · Track 2 — Citizens First (GovTech)**

🔴 **Play now** · [`arus-1030181742799.asia-southeast1.run.app`](https://arus-1030181742799.asia-southeast1.run.app) · 🎥 [3-min demo](./docs/slides/arus-demo.mp4) · 📊 [15-page deck](./docs/slides/arus-deck.pdf) · 👨‍⚖️ [for judges](./docs/FOR-JUDGES.md)

</div>

---

## What this is

**Arus — Banjir Drill** is a browser-playable Malaysian flood-coordination
simulator. You are Datuk Nadia, NADMA liaison officer on the night of the
December 2021 Klang Valley floods. Over 7 minutes you field 8 incoming
calls from BOMBA / APM / MMEA / media / utilities and pick between 2-3
response options each. Four gauges move under your decisions:

- **Lives saved** — 0 to target (Hard mode: 14 of 14)
- **Assets** — % of deployable resources left
- **Trust** — % of inter-agency confidence in your chain of command
- **Time** — countdown to cutoff

At the end, you see your grade. Then we show you the **real 2021 Shah
Alam numbers** — 40,000 displaced, 54 deaths, a 16-hour median rescue
wait time, a RM3.7M lawsuit — and a Gemini-authored commentary that
ties your specific choices to the systemic coordination gaps the
[MDPI 2025 post-mortem](https://www.mdpi.com/2073-4441/17/4/513) named.

The point is not to entertain. The point is that public awareness of
coordination difficulty — named in the MDPI paper as a systemic policy
gap — is something citizens can build through **experience, not PDFs**.
Portal Bencana, InfoBanjir and MetMalaysia's warning API are linked at
the end of every session so the citizen carries the lesson into real
preparedness.

## Why Track 2 (Citizens First)

Track 2's reference apps are MyJPJ and MySejahtera — **citizen-facing
digital services**. Arus — Banjir Drill is a digital public-education
service that aligns directly with MyDIGITAL's Budget 2026 "Accelerating
Digital Transformation for All" agenda and the six _teras_ of the
Digital Education Policy under Kerajaan Madani. UNICEF Malaysia + MoE +
SEADPRI already deploy paper Disaster Risk Reduction modules in
primary schools; Arus is the digital-native counterpart those modules
need.

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│  Frontend (React 18 + R3F + Zustand, mobile-friendly)             │
│   Start screen → game loop → debrief. BM/EN toggle live.          │
│   Event cards overlay the 3D tactical map. 4 gauges always-on.    │
└─────────────────────────────┬─────────────────────────────────────┘
                              │ WebSocket (state 5 Hz) + REST
┌─────────────────────────────▼─────────────────────────────────────┐
│  FastAPI Gateway (Cloud Run, asia-southeast1)                     │
│   /api/game/{start,choose,state,debrief,scenarios}                │
│   /api/live/warnings (MetMalaysia real feed) · /api/vision/analyse│
│   /api/locality/{x}/{y}  (grid → kampung)                         │
└────────┬───────────────────────────────────┬──────────────────────┘
         │                                   │
┌────────▼────────────────────┐   ┌──────────▼─────────────────────┐
│  Game Engine (deterministic)│   │  Gemini Narrator (off-loop)    │
│   - Gauges, event queue     │   │   - NADMA intro (per scenario) │
│   - 8-card scenario YAML    │   │   - Personalised debrief        │
│   - Score + grade           │   │   - Cache, fallback, retry      │
└────────┬────────────────────┘   └────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────────┐
│  GridWorld simulation (20×20, Malaysian kampung mapping)          │
│   - Floods, obstacles, autonomous drone path execution            │
│   - Real kampung names in Kelantan / Pahang / Johor flood belt    │
└───────────────────────────────────────────────────────────────────┘
```

**Why Gemini is off-loop**: LLMs in a 200 ms game tick are a 2024
mistake. Arus runs a fully deterministic game engine (zero latency,
predictable) and uses Gemini 2.5 Flash only at session boundaries —
intro narration + end-of-game commentary. The [CESCG 2025 LIGS paper
on LLM-infused game systems](https://cescg.org/wp-content/uploads/2025/04/A-Quest-for-Information-Enhancing-Game-Based-Learning-with-LLM-Driven-NPCs-2.pdf)
frames this as the 2026 pattern.

## 30-second evaluation

Judges — **open the live URL on any phone and play it**. That's the
evaluation.

```
https://arus-1030181742799.asia-southeast1.run.app
```

1. Tap **Start drill**. Toggle BM / EN in the top-right at any time.
2. Wait ~10 seconds for the first "Incoming call" card.
3. Pick an option. Your 4 gauges move. The 3D map animates a rescue.
4. Field 7 more cards over 7 minutes.
5. Read the debrief: your numbers + Gemini-authored NADMA commentary
   + the real 2021 Klang Valley flood facts that shaped the scenario.

## Design spine (research-backed)

| Pattern | Source | Applied in Arus as |
|---|---|---|
| Card-deck event queue | Reigns (Nerial, 2016) | EventCard + Options, gauges recompute card deck |
| "Game + debrief" beats game alone | JMIR Serious Games 2024 scoping review | 3-section debrief (your results / 2021 reality / links to real civic tools) |
| LLM for writing, deterministic for gameplay | CESCG 2025 LIGS | Gemini narrator off-loop; engine tick is pure code |
| Shareable score | Wordle (NYT) | Planned (Day 3 stretch) |

Sources consolidated in [docs/FOR-JUDGES.md](./docs/FOR-JUDGES.md).

## Quick start (local)

```bash
# 1. Python
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Frontend
cd frontend && npm ci && cd ..

# 3. Configure Gemini key (narrator uses GOOGLE_API_KEY)
cp .env.example .env.local
# Edit .env.local — GOOGLE_API_KEY from https://aistudio.google.com/apikey

# 4. Run backend (no MCP server, no agent dispatch — just game + narrator)
uvicorn backend.main:app --reload --port 8000

# 5. Frontend (separate terminal)
cd frontend && npm run dev
# → http://localhost:5173
```

## Deploy to Cloud Run

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
    artifactregistry.googleapis.com generativelanguage.googleapis.com

echo -n "$GOOGLE_API_KEY" | gcloud secrets create arus-gemini-key \
    --data-file=- --replication-policy=automatic

gcloud builds submit --config=cloudbuild.yaml --region=asia-southeast1
```

Live build target: `asia-southeast1` · single instance · `--set-secrets=GOOGLE_API_KEY=arus-gemini-key:latest`.

## AI tools used

_(as required by the hackathon rules — disclosed in full.)_

| Tool | Where | Why |
|---|---|---|
| **Google Antigravity** | Primary IDE for the entire hackathon window (2026-03-15 → 2026-04-21, extended to 2026-04-24) | Mandated by rule |
| **Google AI Studio** | Prompt design iteration for `backend/services/narrator.py` | Prompt engineering |
| **Gemini 2.5 Flash** | Narrator (intro + debrief) + Vision (optional bonus) | Off-loop writing |
| **Google Cloud Run** | Deployment (asia-southeast1) | Mandated by rule |
| **Google Secret Manager** | `GOOGLE_API_KEY` storage | Standard hygiene |

> **AI-assistance disclosure**: Arus — Banjir Drill was built end-to-end
> inside Google Antigravity during the hackathon window (2026-03-15 →
> 2026-04-24) with Gemini 2.5 Flash assistance. Prompt design iterated
> in Google AI Studio. No Codex / Cursor / VS Code / Gemini CLI
> involvement.

## Project evolution

The repository first shipped an autonomous-agent coordinator (5-stage
ADK pipeline) — preserved for reference at git tag `v1-coordinator`.
On 2026-04-21 we pivoted the product to a player-controlled simulator
after re-reading Track 2's citizen-facing framing and the MDPI 2025
post-mortem that names public awareness as a documented policy gap. The
simulation engine (grid_world, locality, terrain, objective,
pathplanner) was preserved across the pivot; only the agent
orchestration layer was replaced.

## Repo layout

```
arus/
├── backend/
│   ├── main.py                 FastAPI + WS broadcaster + game tick loop
│   ├── core/                   simulation engine (reused from v1)
│   │   ├── grid_world.py
│   │   ├── uav.py, drone.py, terrain.py, objective.py, pathplanner.py
│   │   └── locality.py         grid → real Malaysian kampung names
│   ├── game/                   NEW — player-driven game
│   │   ├── engine.py           GameEngine (deterministic tick)
│   │   ├── scenario.py         YAML loader, real-stats loader
│   │   ├── score.py            gauge math, grade computation
│   │   ├── cards.yaml          8-card Shah Alam 2021 hard scenario
│   │   └── real_stats.json     2021 Shah Alam + 2024 Kelantan facts
│   ├── routes/
│   │   └── game.py             /api/game/* endpoints
│   └── services/
│       ├── narrator.py         NEW — Gemini intro + debrief (off-loop)
│       ├── vision.py           bonus: /api/vision/analyse
│       └── met_feed.py         MetMalaysia real warnings feed
├── frontend/
│   └── src/
│       ├── scene/              3D R3F tactical map (reused from v1)
│       ├── panels/GlobalStatusBar.jsx
│       ├── components/         NEW — game UI
│       │   ├── StartScreen.jsx  BM/EN + Start button
│       │   ├── EventCard.jsx    Reigns-style decision card
│       │   ├── GaugePanel.jsx   4 always-on meters
│       │   ├── NarratorPanel.jsx NADMA radio log
│       │   ├── DebriefScreen.jsx 3-section end-of-game screen
│       │   └── LanguageToggle.jsx
│       └── hooks/, stores/
├── cloudbuild.yaml · Dockerfile
├── docs/FOR-JUDGES.md · docs/slides/
└── README.md
```

## License

MIT. See [`LICENSE`](./LICENSE).

# For Judges — Arus — Banjir Drill in 30 seconds

One-page guide to evaluating Arus without reading source code.

## What it is

**A 7-minute Malaysian flood-coordination simulator** you play in a
browser. Citizens play NADMA liaison officer Datuk Nadia during the
December 2021 Klang Valley floods. Eight incoming calls, three response
options each, four gauges (lives saved · assets · trust · time). Gemini
2.5 Flash narrates the intro and a personalised debrief in Bahasa
Malaysia + English.

**Track**: 2 — Citizens First (GovTech).

## Try it in 90 seconds

1. On any phone: open [`https://arus-1030181742799.asia-southeast1.run.app`](https://arus-1030181742799.asia-southeast1.run.app).
2. Toggle **BM/EN** top-right if you want Bahasa Malaysia.
3. Tap **Start drill**.
4. Read Datuk Nadia's briefing (Gemini-authored).
5. Wait ~10 seconds → first card appears. Pick an option. Watch gauges move.
6. Field 7 more cards across 7 minutes. Read the debrief.

## Interactive API explorer (optional)

FastAPI Swagger at:
<https://arus-1030181742799.asia-southeast1.run.app/docs> · Raw OpenAPI schema: `/openapi.json`.

Quick verification from the command line:

```bash
# List available scenarios
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/game/scenarios | jq .

# Start a fresh session (prints Gemini intro + scenario + gauges)
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"scenario_id":"shah_alam_hard","locale":"en"}' \
  https://arus-1030181742799.asia-southeast1.run.app/api/game/start | jq .

# Inspect current game state
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/game/state | jq '.data | {gauges, current_card: .current_card.id, status}'

# MetMalaysia real feed (proof of MY integration)
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/live/warnings | jq '{count, first: .data[0].title_en}'
```

## Timing expectations

- Cloud Run cold start: ~5 seconds.
- First card after tapping Start: ~10 seconds.
- Full play session: 7 minutes by design.
- Gemini debrief generation at end-of-game: ~2 seconds.

## What to look at in the code

| If you care about | Start here |
|---|---|
| The game engine (deterministic) | [`backend/game/engine.py`](../backend/game/engine.py) + [`cards.yaml`](../backend/game/cards.yaml) |
| Gemini narrator (off-loop) | [`backend/services/narrator.py`](../backend/services/narrator.py) |
| Scoring + grade logic | [`backend/game/score.py`](../backend/game/score.py) |
| Real 2021 Shah Alam stats (debrief ground truth) | [`backend/game/real_stats.json`](../backend/game/real_stats.json) |
| REST endpoints | [`backend/routes/game.py`](../backend/routes/game.py) |
| 3D tactical map (R3F, kept from v1 for visual distinctiveness) | [`frontend/src/scene/`](../frontend/src/scene/) |
| Reigns-style event card | [`frontend/src/components/EventCard.jsx`](../frontend/src/components/EventCard.jsx) |
| Debrief screen | [`frontend/src/components/DebriefScreen.jsx`](../frontend/src/components/DebriefScreen.jsx) |
| MetMalaysia live feed | [`backend/services/met_feed.py`](../backend/services/met_feed.py) |
| Malaysian kampung mapping | [`backend/core/locality.py`](../backend/core/locality.py) |
| Cloud Run deployment pipeline | [`Dockerfile`](../Dockerfile) + [`cloudbuild.yaml`](../cloudbuild.yaml) |
| Earlier v1 autonomous-coordinator architecture | `git checkout v1-coordinator` |

## Design rationale (research-backed)

- **Game + debrief beats game alone** — [JMIR Serious Games 2024 scoping review](https://games.jmir.org/2024/1/e64939/): civic games only teach when paired with a debrief. Our debrief is the load-bearing educational layer.
- **Reigns card mechanic** — [Nerial 2016](https://en.wikipedia.org/wiki/Reigns_(video_game)): proven short-session decision-under-pressure pattern.
- **LLM off-loop, engine deterministic** — [CESCG 2025 LIGS paper](https://cescg.org/wp-content/uploads/2025/04/A-Quest-for-Information-Enhancing-Game-Based-Learning-with-LLM-Driven-NPCs-2.pdf): the 2026 pattern is Gemini for writing, deterministic code for the tick loop. We don't put Gemini in the critical path.
- **Real data anchor** — [MDPI Water 2025 flood post-mortem](https://www.mdpi.com/2073-4441/17/4/513) names "public awareness" and "inter-agency coordination" as the two systemic gaps of the 2021 Shah Alam event. Every card, every debrief paragraph traces back to this.

## What makes Arus — Banjir Drill win

- **First citizen-facing disaster-coordination simulator for Malaysia** — InfoBanjir, Portal Bencana, and UNICEF MY's DRR modules are all static/paper; zero deployed precedent in the civic-sim space locally.
- **Track 2 fit is clean** — citizen-facing digital service, same layer as MyJPJ/MySejahtera, aligned to MyDIGITAL Budget 2026 + Kerajaan Madani DPD.
- **Judge can play it in 90 seconds on their phone** — documented hackathon-winning pattern (Devpost judging guide).
- **Real Malaysian data + real policy anchor** — MetMalaysia live feed, real Kelantan/Johor kampung names, 2021 flood numbers with MDPI/ReliefWeb/AHA Centre sources cited in `real_stats.json`.
- **Bilingual end-to-end** — BM/EN toggle live during play; Gemini generates both locales for intro + debrief.

## Deliverables summary

- GitHub: <https://github.com/SunflowersLwtech/arus> (public, MIT)
- Git tag `v1-coordinator` — earlier autonomous-agent version preserved for audit
- Live Cloud Run: <https://arus-1030181742799.asia-southeast1.run.app>
- Demo video: `docs/slides/arus-demo.mp4` (new Day-3 recording required — see `hackathon/reports/SUBMIT-ME.md`)
- Pitch deck: `docs/slides/arus-deck.pdf` (new Day-3 rewrite required)

Questions: `weiliudev0607@gmail.com`.

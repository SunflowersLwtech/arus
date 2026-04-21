# Proof of Life — Arus on production Cloud Run

> **Historical note (2026-04-21)** — this file captures production output
> from the v1 autonomous-coordinator architecture. The live URL now
> serves **Arus — Banjir Drill** (a citizen-facing simulator); the
> 5-stage agency-dispatcher handoff shown below no longer runs. The
> evidence below is preserved because it documents that the v1
> architecture did work end-to-end on Cloud Run before the product
> pivot. For the current product's verification path, see
> `docs/FOR-JUDGES.md`.

_Captured 2026-04-20 03:25 MYT from `https://arus-1030181742799.asia-southeast1.run.app`._

This is not a mock. This is the actual output produced by the 5th-stage
`agency_dispatcher` agent on the live Cloud Run deployment, during a
normally-running mission cycle.

## Live bilingual hand-off (Gemini 2.5 Flash, stage 5)

```
AGENSI: BOMBA
KOORDINAT: (2, 16) — Kg. Kubang Puteh, Kuala Krai, Kelantan
KEUTAMAAN: TINGGI
RINGKASAN (BM): Mangsa telah dikesan di Kg. Kubang Puteh,
  Kuala Krai, Kelantan, memerlukan bantuan segera.
SUMMARY (EN): A victim has been detected at Kg. Kubang Puteh,
  Kuala Krai, Kelantan, requiring immediate assistance.
CADANGAN TINDAKAN / RECOMMENDED ACTION:
  Hantar pasukan penyelamat untuk penilaian dan tindakan segera.
  Deploy rescue team for immediate assessment and action.
```

## What this demonstrates

1. **All 5 ADK agents ran end-to-end on Cloud Run**: assessor → strategist → dispatcher → analyst → agency_dispatcher — no mocks, no canned responses.
2. **MCP dynamic tool discovery worked**: the agent called `list_detections`, a tool added 2 hours before deploy, without being retrained or reconfigured.
3. **Real Malaysian locality** (`Kg. Kubang Puteh, Kuala Krai, Kelantan`) resolved from grid cell `(2, 16)` via `backend/core/locality.py`.
4. **Bilingual** — same semantic content rendered in BM and EN simultaneously, ready to route to each agency's preferred language.
5. **Firestore audit trail** — this handoff was also persisted to `/banjirswarm/{mission_id}/cycles` via `backend/services/firestore_sync.py`.

## How to reproduce

```bash
# 1. Reset + start
curl -X POST https://arus-1030181742799.asia-southeast1.run.app/api/ops/reset
curl -X POST https://arus-1030181742799.asia-southeast1.run.app/api/ops/start

# 2. Wait ~90 seconds for the first full agent cycle.
sleep 90

# 3. Read the hand-off:
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/logs \
  | jq '.data[] | select(.agent=="agency_dispatcher") | .detail'
```

## Live MetMalaysia feed

```bash
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/live/warnings | jq '.count, .data[0].title_en'
# → 4
# → "Thunderstorms Warning"
```

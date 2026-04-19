# Arus Operations Runbook

For the 48 hours around submission and Demo Day. Short and oriented
toward what you actually need to do if something breaks.

## Quick facts

- **Project**: `project-349f30a3-7c3e-46dd-b95`
- **Region**: `asia-southeast1`
- **Service**: `arus` (Cloud Run, `--allow-unauthenticated`, `--max-instances=1`, `--min-instances=1`)
- **Base image**: `asia-southeast1-docker.pkg.dev/project-349f30a3-7c3e-46dd-b95/arus/app:latest`
- **Active secret**: `arus-gemini-key:latest` (Secret Manager, mounted as `GOOGLE_API_KEY`)
- **Firestore database**: `(default)` in `asia-southeast1`
- **URL**: <https://arus-1030181742799.asia-southeast1.run.app>

## Redeploy

```bash
cd /Users/sunfl/Documents/study/MyAI/arus
gcloud builds submit --config=cloudbuild.yaml \
  --region=asia-southeast1 \
  --project=project-349f30a3-7c3e-46dd-b95 .
# ~6 minutes for multi-stage Docker build + Cloud Run rollout
```

## Roll back (if the latest revision misbehaves during judging)

```bash
# List last 5 revisions
gcloud run revisions list --service=arus --region=asia-southeast1 \
  --project=project-349f30a3-7c3e-46dd-b95 --limit=5

# Pin 100% of traffic to a known-good revision
gcloud run services update-traffic arus \
  --region=asia-southeast1 \
  --project=project-349f30a3-7c3e-46dd-b95 \
  --to-revisions=arus-00003-kzm=100
```

`arus-00004-pfz` was the first revision with the MetMalaysia badge in the UI.
`arus-00003-kzm` was the first revision with the MetMalaysia feed on the
backend. Either is a safe fallback if a later revision regresses.

## Rotate the Gemini API key (do this AFTER submission)

```bash
# 1. Revoke the old key in Google AI Studio (https://aistudio.google.com/apikey)
# 2. Issue a new key, then:
echo -n "NEW_KEY_HERE" | gcloud secrets versions add arus-gemini-key \
  --data-file=- \
  --project=project-349f30a3-7c3e-46dd-b95
# 3. Redeploy so the service picks up the new version
gcloud run services update arus \
  --region=asia-southeast1 \
  --project=project-349f30a3-7c3e-46dd-b95
# 4. Update .env.local on your laptop too
```

## Production health check

```bash
# 30-second automated sweep: every endpoint + one full agent cycle + real handoff
./scripts/judge_evaluate.sh https://arus-1030181742799.asia-southeast1.run.app
```

## "It's slow" — usual causes

1. **Cold start**: should not happen with `--min-instances=1`, but if it does, the first request can take ~8 seconds.
2. **Gemini rate limit**: look for `429` or `RESOURCE_EXHAUSTED` in `gcloud run services logs read arus`. Runner auto-backs off for 3 cycles.
3. **MetMalaysia upstream down**: backend serves cached last-known response for 5 min; after that, `summarise_for_prompt` returns "no active warnings" — not fatal.

## "The dashboard shows a stale mission"

Cloud Run single-instance means state is in-memory. If the instance was
restarted (deploy, auto-restart, OOM), the mission state resets. Just:

```bash
curl -X POST https://arus-1030181742799.asia-southeast1.run.app/api/ops/reset
curl -X POST https://arus-1030181742799.asia-southeast1.run.app/api/ops/start
```

Firestore retains all prior cycles + handoffs in `/banjirswarm/{mission_id}/*`.

## "Agent cycle 1 never completed"

Check the MCP server came up inside the container:

```bash
gcloud run services logs read arus \
  --region=asia-southeast1 \
  --project=project-349f30a3-7c3e-46dd-b95 \
  --limit=80 \
  | grep -E "MCP|port 8001"
```

Expected: `Gateway started on port 8000, MCP on port 8001`. If MCP is missing, the `_start_mcp_server` task died — redeploy.

## Costs (rough)

- Cloud Run: negligible at 1 instance / 1 vCPU / 1 GiB with the idle auto-scaling most of the day.
- Gemini 2.5 Flash API: ~1–2 USD / hour of continuous agent cycles.
- Firestore: well inside free tier at this volume.

Budget for Demo Day (3 hours of running demos): **< 10 USD**.

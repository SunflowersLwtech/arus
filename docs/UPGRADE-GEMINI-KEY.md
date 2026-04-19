# Upgrade the Gemini API key to paid tier (2-minute action)

**Do this before submission / Demo Day.** The current key is on the
Google AI Studio **free tier (10 RPM, 1500 RPD)**, and a single Arus
cycle emits 10-15 Gemini requests (5 stages × 2-3 tool calls each).
That means:

- On free tier, the first agent cycle hits 429 mid-pipeline. With the
  current 35s/60s retry schedule and 6-cycle backoff, the service will
  eventually produce a handoff but it can take 2-4 minutes per cycle.
- On paid tier, one cycle completes in ~20 seconds, and the
  `/api/live/handoffs` endpoint fills within 30 seconds of boot.

## Option A — bump the existing key to paid

1. Open **<https://console.cloud.google.com/billing>** in the same
   project (`project-349f30a3-7c3e-46dd-b95`).
2. Link a billing account (you already have "My Billing Account 1" —
   enable it).
3. Open **<https://aistudio.google.com/apikey>**, confirm the existing
   key is now under the billed project. If not, issue a new key from
   the billed project.
4. If the key changed, rotate the Secret Manager value:
   ```bash
   echo -n "NEW_KEY" | gcloud secrets versions add arus-gemini-key \
     --data-file=- \
     --project=project-349f30a3-7c3e-46dd-b95
   ```
5. Force a new revision so Cloud Run reloads the secret:
   ```bash
   gcloud run services update arus \
     --region=asia-southeast1 \
     --update-env-vars=AGENT_INTERVAL=50 \
     --project=project-349f30a3-7c3e-46dd-b95
   ```
   (Also sets the paced-down cycle interval back to 10 s so the demo feels snappy.)

## Option B — switch to Vertex AI (GCP-native, paid)

Vertex AI has much higher per-project RPM quotas. Requires code change:

```bash
gcloud run services update arus \
  --region=asia-southeast1 \
  --update-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=asia-southeast1,AGENT_INTERVAL=50 \
  --remove-secrets=GOOGLE_API_KEY \
  --project=project-349f30a3-7c3e-46dd-b95
```

Then grant the Cloud Run service account `roles/aiplatform.user`:

```bash
PROJECT_NUMBER=1030181742799
gcloud projects add-iam-policy-binding project-349f30a3-7c3e-46dd-b95 \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## How to verify it worked

```bash
curl -X POST https://arus-1030181742799.asia-southeast1.run.app/api/demo/boot
sleep 45
curl -s https://arus-1030181742799.asia-southeast1.run.app/api/live/handoffs | jq '.data | length'
# Expect: >= 1 within ~45s  (was 2-4 minutes on free tier)
```

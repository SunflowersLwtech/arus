#!/usr/bin/env bash
# Arus — 30-second judge evaluation script.
#
# Usage:
#   ./scripts/judge_evaluate.sh [URL]
#
# Defaults to the Cloud Run production URL. Exercises every documented
# endpoint + waits for one full 5-stage agent cycle. Exit code non-zero
# if anything looks unhealthy.

set -euo pipefail

URL="${1:-https://arus-1030181742799.asia-southeast1.run.app}"
ok(){ printf "  \033[0;32m✓\033[0m %s\n" "$1"; }
bad(){ printf "  \033[0;31m✗\033[0m %s\n" "$1" >&2; exit 1; }
hr(){ printf "\n\033[1;34m── %s ──\033[0m\n" "$1"; }

need_jq() { command -v jq >/dev/null 2>&1 || bad "jq required: brew install jq"; }
need_jq

hr "1. Health"
resp=$(curl -sf "$URL/api/health")
echo "$resp" | jq -r '.status' | grep -q "^ok$" || bad "health /api/health"
zone=$(echo "$resp" | jq -r '.zone')
[[ "$zone" =~ "Johor" ]] && ok "zone includes Johor: $zone" || bad "zone missing Johor"

hr "2. Malaysian locality (grid → kampung)"
resp=$(curl -sf "$URL/api/locality/5/5")
echo "$resp" | jq -r '.data.state' | grep -q "Kelantan" || bad "5,5 should be Kelantan"
ok "(5,5) → $(echo "$resp" | jq -r '[.data.kampung, .data.district] | join(", ")')"
resp=$(curl -sf "$URL/api/locality/15/15")
echo "$resp" | jq -r '.data.state' | grep -q "Johor" || bad "15,15 should be Johor"
ok "(15,15) → $(echo "$resp" | jq -r '[.data.kampung, .data.district] | join(", ")')"

hr "3. MetMalaysia live feed"
resp=$(curl -sf "$URL/api/live/warnings?limit=3")
count=$(echo "$resp" | jq -r '.count')
[[ "$count" =~ ^[0-9]+$ ]] || bad "/api/live/warnings returned non-integer count"
ok "api.data.gov.my returned $count active warnings"
[[ "$count" -gt 0 ]] && ok "first warning: $(echo "$resp" | jq -r '.data[0].title_en // "—"')"

hr "4. Mission lifecycle"
curl -sf -X POST "$URL/api/ops/reset" >/dev/null && ok "POST /api/ops/reset"
curl -sf -X POST "$URL/api/ops/start" >/dev/null && ok "POST /api/ops/start"

hr "5. Waiting for full 5-stage cycle (max 180s) …"
start_ts=$(date +%s)
while :; do
  now_ts=$(date +%s)
  elapsed=$(( now_ts - start_ts ))
  agents=$(curl -sf "$URL/api/logs" | jq -r '.data[] | .agent' 2>/dev/null | sort -u | paste -sd, -)
  printf "    [%3ds] agents so far: %s\n" "$elapsed" "$agents"
  echo "$agents" | grep -q "agency_dispatcher" && { ok "all 5 stages fired"; break; }
  [[ $elapsed -gt 180 ]] && bad "timeout waiting for agency_dispatcher"
  sleep 10
done

hr "6. Bilingual handoff endpoint"
resp=$(curl -sf "$URL/api/live/handoffs?limit=5")
n=$(echo "$resp" | jq -r '.data | length')
ok "captured $n bilingual hand-offs so far"
if [[ "$n" -gt 0 ]]; then
  echo "$resp" | jq -r '.data[0] | "    agency=" + .agency + " · " + .coord + "\n    BM: " + .bm + "\n    EN: " + .en'
fi

hr "7. State snapshot"
resp=$(curl -sf "$URL/api/state")
echo "$resp" | jq -r '.data | "    tick=" + (.tick|tostring) + " coverage=" + (.coverage_pct|tostring) + "% victims=" + (.objectives_found|tostring) + "/" + (.objectives_total|tostring)'

printf "\n\033[1;32m✓ Arus is production-healthy.\033[0m  %s\n\n" "$URL"

#!/usr/bin/env bash
set -euo pipefail

TARGET=${1:-"https://www.example.com"}
COUNT=${COUNT:-5}
API=${API_ENDPOINT:-"http://localhost:8000/api/detection/one-off"}
TOKEN=${TOKEN:-""}

for i in $(seq 1 $COUNT); do
  echo "[Benchmark] Triggering detection #$i for $TARGET"
  curl -sS -X POST "$API" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"target\": \"$TARGET\", \"protocol\": \"HTTPS\", \"timeout_seconds\": 5}" >/dev/null
  sleep 1
done

echo "Benchmark requests submitted. Check metrics for latency distribution."

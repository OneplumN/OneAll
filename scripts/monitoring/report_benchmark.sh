#!/usr/bin/env bash
set -euo pipefail

START=$(date +%s)
API=${API_ENDPOINT:-"http://localhost:8000/api/analytics/reports"}
TOKEN=${TOKEN:-""}

curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"range": {"start": "2025-10-01", "end": "2025-10-31"}, "metrics": ["success_rate"], "format": "csv"}' >/dev/null

END=$(date +%s)
echo "Report generation triggered in $((END-START))s. Monitor Celery worker for completion time."

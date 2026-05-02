#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

API_URL="${API_URL:-http://localhost:8080}"
API_KEY="${API_SECRET_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  echo "Error: API_SECRET_KEY env var is required"
  exit 1
fi

QUESTION="${*:-}"
if [[ -z "$QUESTION" ]]; then
  echo "Usage: $0 <question>"
  echo "Example: $0 payment-service OOMKilled, what should I do?"
  exit 1
fi

payload="$(jq -n --arg question "$QUESTION" '{question: $question}')"
response="$(curl -sf -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d "$payload")"

printf '%s\n' "$response" | jq -r '"Answer: \(.answer)\nSources: \(.sources | join(", "))\nConfidence: \(.confidence)"'

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

API_URL="${API_URL:-http://localhost:8080}"
QUESTION="${1:-payment service OOMKilled, what should I do?}"
INGEST_TARGET="${2:-./docs/runbook-template.md}"

echo "==> Building and starting Docker stack"
docker compose up -d --build

echo "==> Container status"
docker compose ps

echo "==> API health"
for attempt in {1..30}; do
  if curl -sf "${API_URL}/health"; then
    echo
    break
  fi

  if [[ "$attempt" -eq 30 ]]; then
    echo "API did not become healthy in time"
    docker compose logs --tail=80 api
    exit 1
  fi

  sleep 2
done

echo "==> Ingesting ${INGEST_TARGET}"
./scripts/ingest_local.sh "${INGEST_TARGET}"

echo "==> Querying: ${QUESTION}"
./scripts/query_cli.sh "${QUESTION}"

echo "==> Validation complete"

#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8080}"
API_KEY="${API_SECRET_KEY:-}"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <file_or_directory>"
  exit 1
fi

if [[ -z "$API_KEY" ]]; then
  echo "Error: API_SECRET_KEY env var is required"
  exit 1
fi

ingest_file() {
  local file="$1"
  echo "Ingesting: $file"
  curl -sf -X POST "${API_URL}/ingest/file" \
    -H "X-API-Key: ${API_KEY}" \
    -F "file=@${file}" | jq .
}

if [[ -f "$TARGET" ]]; then
  ingest_file "$TARGET"
elif [[ -d "$TARGET" ]]; then
  find "$TARGET" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.json" -o -name "*.log" \) | while read -r f; do
    ingest_file "$f"
  done
else
  echo "Error: '$TARGET' is not a file or directory"
  exit 1
fi

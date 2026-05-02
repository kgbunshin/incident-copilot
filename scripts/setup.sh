#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/kgbunshin/incident-copilot.git}"
APP_DIR="${APP_DIR:-/opt/incident-copilot}"
COMPOSE_FILE="docker-compose.prod.yml"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo $0"
  exit 1
fi

echo "==> Updating Debian packages"
apt-get update
apt-get upgrade -y
apt-get install -y ca-certificates curl git jq openssl ufw

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker"
  curl -fsSL https://get.docker.com | sh
else
  echo "==> Docker already installed"
fi

systemctl enable --now docker

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is not available"
  exit 1
fi

if [[ ! -d "${APP_DIR}/.git" ]]; then
  echo "==> Cloning ${REPO_URL} into ${APP_DIR}"
  git clone "${REPO_URL}" "${APP_DIR}"
else
  echo "==> Updating existing repository in ${APP_DIR}"
  git -C "${APP_DIR}" pull --ff-only
fi

cd "${APP_DIR}"

if [[ ! -f .env ]]; then
  echo "==> Creating .env"
  cp .env.example .env
  api_key="$(openssl rand -hex 32)"
  api_key_name="API_SECRET_KEY"
  sed -i "s/^${api_key_name}=.*/${api_key_name}=${api_key}/" .env
  chmod 600 .env
else
  echo "==> Keeping existing .env"
fi

mkdir -p data/incoming

echo "==> Starting base services"
docker compose -f "${COMPOSE_FILE}" up -d --build ollama chromadb

echo "==> Pulling Ollama models"
docker exec sre-rag-ollama ollama pull nomic-embed-text
docker exec sre-rag-ollama ollama pull mistral:7b-instruct-q4_K_M

echo "==> Starting API"
docker compose -f "${COMPOSE_FILE}" up -d --build api

echo "==> Waiting for API health"
for attempt in {1..60}; do
  if curl -sf "http://127.0.0.1:${API_PORT:-8080}/health" | jq .; then
    echo "==> incident-copilot is running"
    break
  fi

  if [[ "${attempt}" -eq 60 ]]; then
    echo "API did not become healthy in time"
    docker compose -f "${COMPOSE_FILE}" logs --tail=120 api
    exit 1
  fi

  sleep 2
done

cat <<EOF

Next steps:
1. Edit ${APP_DIR}/.env and set API_BIND_IP to the VPS 2 private IP.
2. Restart the API:
   cd ${APP_DIR}
   docker compose -f ${COMPOSE_FILE} up -d api
3. Allow port 8080 only from VPS 1 private IP, not from the public internet.
4. Test from VPS 1:
   curl http://<VPS2-PRIVATE-IP>:8080/health

EOF

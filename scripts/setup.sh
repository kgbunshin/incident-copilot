#!/usr/bin/env bash
set -euo pipefail

echo "==> Updating system packages"
apt update && apt upgrade -y

echo "==> Installing Docker"
curl -fsSL https://get.docker.com | sh
usermod -aG docker "$USER"

echo "==> Cloning repository"
git clone https://github.com/allansilva/sre-rag.git /opt/sre-rag
cd /opt/sre-rag

echo "==> Configuring environment"
cp .env.example .env
echo "Edit /opt/sre-rag/.env with your values, then run:"
echo "  docker compose up -d"
echo "  docker exec -it sre-rag-ollama ollama pull mistral:7b-instruct-q4_K_M"
echo "  docker exec -it sre-rag-ollama ollama pull nomic-embed-text"

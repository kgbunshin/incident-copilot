# Contributing to Incident Copilot

Thank you for your interest in contributing! This document covers how to set up
your local environment, project conventions, and how to submit changes.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM (local) | Ollama + Mistral 7B Q4 |
| Vector DB | ChromaDB |
| API | FastAPI (Python 3.11+) |
| Embeddings | nomic-embed-text (via Ollama) |
| Orchestration | Docker Compose |
| CI/CD | GitHub Actions |
| OS (recommended) | Debian 12 / Ubuntu 22.04 |

---

## 📁 Project Structure

```
incident-copilot/
├── README.md
├── CONTRIBUTING.md              # this file
├── docker-compose.yml           # Ollama + ChromaDB + API
├── .env.example                 # environment variable template
├── .gitignore
│
├── api/                         # FastAPI backend
│   ├── main.py
│   ├── routes/
│   │   ├── ingest.py            # ingestion endpoints
│   │   ├── query.py             # RAG query endpoints
│   │   └── health.py
│   ├── services/
│   │   ├── embedder.py          # embedding generation via Ollama
│   │   ├── retriever.py         # vector search on ChromaDB
│   │   └── llm.py               # Ollama LLM calls
│   └── models/
│       └── schemas.py           # Pydantic models
│
├── ingestor/                    # ingestion pipeline
│   ├── parsers/
│   │   ├── markdown.py          # runbooks and post-mortems (.md)
│   │   ├── json_logs.py         # structured JSON logs
│   │   └── alertmanager.py      # Alertmanager alert payloads
│   ├── chunker.py               # chunking strategy
│   └── pipeline.py              # ingestion orchestration
│
├── scripts/
│   ├── setup.sh                 # initial server setup
│   ├── ingest_local.sh          # manual local file ingestion
│   └── query_cli.sh             # quick terminal query
│
├── tests/
│   ├── test_ingest.py
│   └── test_query.py
│
└── docs/
    ├── architecture.md
    ├── runbook-template.md
    └── postmortem-template.md
```

---

## 🚀 Local Setup

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- 8GB+ RAM (for Ollama models)
- 20GB+ free disk space

### Step by step

```bash
# 1. Clone the repository
git clone https://github.com/kgbunshin/incident-copilot.git
cd incident-copilot

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Start services
docker compose up -d

# 4. Pull Ollama models
docker exec -it sre-rag-ollama ollama pull mistral:7b-instruct-q4_K_M
docker exec -it sre-rag-ollama ollama pull nomic-embed-text

# 5. Verify everything is running
docker compose ps
curl http://localhost:8080/health
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest/file` | Ingest a file (md, json, txt) |
| POST | `/ingest/alert` | Ingest Alertmanager alert payload |
| POST | `/query` | Natural language RAG query |
| GET | `/query/similar` | Find similar incidents by text |
| GET | `/health` | Health check |
| GET | `/stats` | Vector database stats |

### Example query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"question": "payment-service OOMKilled, what should I do?"}'
```

### Example response

```json
{
  "answer": "Similar incident found. Likely cause: memory leak after recent deploy. Recommended action: check deployed version, consider rollback, increase memory limit to 512Mi.",
  "sources": ["postmortem-2024-01-14.md", "runbook-oom-k8s.md"],
  "confidence": 0.87
}
```

---

## 🧹 Code Conventions

- **Language:** Python 3.11+
- **Formatter:** `black` + `isort`
- **Linter:** `ruff`
- **Tests:** `pytest`
- **Commit style:** [Conventional Commits](https://www.conventionalcommits.org/)

```
feat: add alertmanager webhook ingestion
fix: handle empty chunks in embedder
docs: update setup instructions
chore: upgrade chromadb to 0.5.x
```

---

## 🌿 Branch Strategy

- `main` is the stable public branch.
- Use short-lived feature branches for changes.
- Open PRs when collaboration/review is useful.
- Never commit local-only context or secret files.

---

## 🔐 Security Notes

- **Never commit** `.env`, secrets, API keys, or internal IPs
- The `.gitignore` already covers common cases — check before pushing
- Sanitize logs before ingesting (remove tokens, passwords, PII)
- API authentication uses `X-API-Key` header

---

## 🐛 Reporting Issues

Please include:
- What you were trying to do
- What happened
- Relevant logs (`docker compose logs api`)
- Your environment (OS, Docker version, available RAM)

---

## 📄 License

MIT — see [LICENSE](LICENSE)

# Project Context — incident-copilot (SRE RAG System)

> Universal context file. Any AI assistant should read this before working on this project.
> Last updated: 2026-05-02

---

## What This Project Is

A RAG (Retrieval-Augmented Generation) system for SRE/Platform Engineering built by Allan Silva (Senior SRE/Platform Engineer). Ingests logs, alerts, runbooks, and post-mortems into a local vector knowledge base to accelerate incident diagnosis and runbook retrieval.

**Primary goal:** Reduce MTTR (Mean Time To Resolve) via semantic retrieval of similar incidents.
**Secondary goal:** Portfolio project for remote Platform Engineer roles (~$10k/month).

---

## Owner

- **Name:** Allan Silva
- **Role:** Senior SRE / Platform Engineer
- **Language:** Portuguese (BR) — respond in pt-BR unless asked otherwise
- **GitHub:** github.com/kgbunshin

---

## Infrastructure

```
VPS 1 — Hostinger KVM (EXISTING — do NOT touch)
  Debian 12, k3s + ArgoCD, Grafana + Alertmanager
  CI/CD: Azure DevOps (private, do NOT migrate)
  4 cores / 16GB RAM / 200GB SSD

VPS 2 — Hostinger KVM (NOT YET contracted as of 2026-05-02)
  Will host: Ollama + ChromaDB + FastAPI (this project)
  2 vCPU / 8GB RAM / 100GB SSD

LOCAL (dev machine):
  Docker Compose running all services on localhost
  Stack: sre-rag-ollama :11434 | sre-rag-chroma :8000 | sre-rag-api :8080
```

---

## Tech Stack (locked decisions)

| Layer | Choice | Reason |
|-------|--------|--------|
| LLM | `mistral:7b-instruct-q4_K_M` | Best cost/quality for 8GB RAM |
| Embeddings | `nomic-embed-text` | Lightweight, good for technical text |
| Vector DB | ChromaDB 1.0.12 | Python-native, no extra infra |
| API | FastAPI 0.115.9 | Async, Pydantic, auto-docs |
| Orchestration | Docker Compose | Simple, reproducible |
| Repo | GitHub public | Portfolio visibility |

---

## Project Structure

```
incident-copilot/
├── api/                  FastAPI app
│   ├── main.py           App entrypoint, lifespan
│   ├── auth.py           X-API-Key header validation
│   ├── models/schemas.py Pydantic request/response models
│   ├── routes/
│   │   ├── health.py     GET /health, GET /stats
│   │   ├── ingest.py     POST /ingest/file, POST /ingest/alert
│   │   └── query.py      POST /query, GET /query/similar
│   └── services/
│       ├── embedder.py   Ollama nomic-embed-text calls
│       ├── retriever.py  ChromaDB async upsert + search
│       └── llm.py        Ollama Mistral generate calls
│
├── ingestor/             Ingestion pipeline
│   ├── parsers/
│   │   ├── markdown.py   Split by H2/H3 headings
│   │   ├── json_logs.py  NDJSON + secret sanitization
│   │   └── alertmanager.py Alertmanager webhook payloads
│   ├── chunker.py        Sliding window chunking (~1000 chars, 100 overlap)
│   └── pipeline.py       Orchestrates parse → chunk
│
├── mcp_server/
│   └── sre_rag_mcp.py    Claude Code MCP server (sre_query, sre_ingest, sre_stats)
│
├── scripts/
│   ├── setup.sh          VPS 2 initial setup
│   ├── ingest_local.sh   Ingest file or directory via API
│   └── query_cli.sh      Terminal RAG query
│
├── tests/
│   ├── test_ingest.py    10 tests: parsers + pipeline (no external deps)
│   └── test_query.py     2 tests: LLM service (mocked httpx)
│
├── docs/
│   ├── context.md        ← this file (universal AI context)
│   ├── handoff.md        Handoff / resume guide
│   ├── architecture.md   Component diagram + request flow
│   ├── runbook-template.md
│   └── postmortem-template.md
│
├── docker-compose.yml    Ollama + ChromaDB + API
├── Dockerfile            python:3.11-slim, copies api/ + ingestor/
├── requirements.txt      FastAPI 0.115.9, chromadb 1.0.12, httpx, mcp
├── .env.example          Template (never commit .env)
└── .mcp.json.example     MCP server template (never commit .mcp.json)
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Checks Ollama + ChromaDB connectivity |
| GET | `/stats` | key | Collection chunk count + sources |
| POST | `/ingest/file` | key | Upload .md/.txt/.json/.log |
| POST | `/ingest/alert` | — | Alertmanager webhook payload |
| POST | `/query` | key | RAG query → answer + sources + confidence |
| GET | `/query/similar` | key | Find similar chunks by text |

Authentication: `X-API-Key: <API_SECRET_KEY>` header.

---

## MCP Server (Claude Code)

File: `mcp_server/sre_rag_mcp.py`
Registered via: `.mcp.json` (local only, not committed)
Python venv: `/home/seneca/.venv-sre-rag/`

Tools:
- `sre_query(question, top_k=5)` — RAG query via POST /query
- `sre_ingest(content, filename)` — ingest text via POST /ingest/file
- `sre_stats()` — collection stats via GET /stats

---

## Current State (2026-05-02)

### Done ✅
- Full MVP stack running locally via Docker Compose
- Ollama models installed: `nomic-embed-text` + `mistral:7b-instruct-q4_K_M`
- MCP server registered and working in Claude Code
- All code committed and pushed to GitHub (github.com/kgbunshin/incident-copilot)

### Known issue ⚠️
`sre_query` MCP tool times out on first call (Mistral cold-start ~60s).
Fix options:
1. Pre-warm Ollama on API startup with a dummy generation request
2. The MCP transport may have a shorter timeout than httpx — investigate

### Next (Phase 2)
- [ ] Contract Hostinger KVM 2
- [ ] Deploy Docker stack to VPS 2
- [ ] Configure Alertmanager webhook: VPS 1 → VPS 2 private IP
- [ ] Test end-to-end alert ingestion

---

## Security Rules (always enforce)

- Never commit: `.env`, `.mcp.json`, `CLAUDE.md`, `*.key`, `*.pem`, `*secret*`
- `.gitignore` already covers all of the above
- API key goes in `.env` only — never hardcoded in source
- Ports 11434 (Ollama) and 8000 (ChromaDB) must remain localhost-only
- Sanitize logs before ingestion (json_logs.py strips token/password/secret keys)

---

## How to Resume Work

```bash
# Start stack
docker compose up -d

# Check health
curl http://localhost:8080/health

# Run tests (no Docker needed)
python3 -m pytest tests/ -v

# Ingest a document
./scripts/ingest_local.sh ./docs/runbook-template.md

# Query
./scripts/query_cli.sh "payment service OOMKilled, what should I do?"
```

---

## Instructions for AI Assistants

1. Always respond in **Portuguese (BR)** unless told otherwise.
2. Respect the locked tech decisions — do not suggest replacing ChromaDB, Ollama, or FastAPI.
3. VPS 1 infra (k3s, ArgoCD, Azure DevOps) is **out of scope** — never suggest changes there.
4. Keep VPS 2 constraints in mind: **2 vCPU / 8GB RAM / 100GB SSD**.
5. This is a **portfolio project** — prioritize clarity and simplicity over enterprise patterns.
6. Before suggesting any new file, check if it would be caught by `.gitignore` security rules.

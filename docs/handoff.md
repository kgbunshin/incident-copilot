# Handoff Document — SRE RAG System

> Context document for continuity across AI sessions or tools.
> Last updated: 2026-05-02

---

## What This Project Is

A RAG (Retrieval-Augmented Generation) system for SRE/Platform Engineering.
Ingests logs, alerts, runbooks, and post-mortems into a vector knowledge base
to accelerate incident diagnosis and runbook retrieval.

**Goal:** Reduce MTTR + portfolio project for remote Platform Engineer roles.

---

## Current State (as of 2026-05-02)

### Phase 1 MVP — COMPLETE and RUNNING

All services are up via Docker Compose on localhost:

| Service | Container | Port | Status |
|---------|-----------|------|--------|
| FastAPI | sre-rag-api | 8080 | ✅ Up |
| ChromaDB | sre-rag-chroma | 8000 | ✅ Up |
| Ollama | sre-rag-ollama | 11434 | ✅ Up |

### Models installed in Ollama
- `nomic-embed-text` (274 MB) — embeddings
- `mistral:7b-instruct-q4_K_M` (4.1 GB) — LLM for generation

### MCP Server
- File: `mcp_server/sre_rag_mcp.py`
- Registered in `.mcp.json` (project root)
- Python venv: `/home/seneca/.venv-sre-rag/`
- Tools: `sre_query`, `sre_ingest`, `sre_stats`
- Status: ✅ Registered and working in Claude Code

---

## Known Issues / Next Steps

### Bug to fix
The `sre_query` MCP tool returns `MCP error -32000: Connection closed` when
the Mistral LLM call takes too long (first query cold-starts the model, ~60s).
Options:
1. Increase MCP client timeout in `mcp_server/sre_rag_mcp.py` (httpx timeout is 120s — may be the MCP transport layer that times out first)
2. Pre-warm Ollama by sending a dummy request on startup
3. Return a streaming response

### Roadmap next (Phase 2)
- [ ] Contract Hostinger KVM 2
- [ ] Deploy stack to VPS 2
- [ ] Configure Alertmanager webhook on VPS 1 → VPS 2 private IP
- [ ] Test end-to-end: alert fires → ingested → queryable

---

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| LLM | Mistral 7B Q4 | Best fit for 8GB RAM |
| Embeddings | nomic-embed-text | Lightweight, good for technical text |
| Vector DB | ChromaDB 1.0.12 | Python-native, no extra infra |
| API | FastAPI 0.115.9 | Async, Pydantic, auto docs |
| Orchestration | Docker Compose | Simple, reproducible |

---

## Project Structure

```
incident-copilot/
├── api/              FastAPI app (main.py, routes/, services/, models/)
├── ingestor/         Parse + chunk pipeline (parsers/, chunker.py, pipeline.py)
├── mcp_server/       Claude Code MCP server (sre_rag_mcp.py)
├── scripts/          setup.sh, ingest_local.sh, query_cli.sh
├── tests/            pytest tests (test_ingest.py, test_query.py)
├── docs/             architecture.md, templates, this file
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example      (never commit .env)
└── .mcp.json         MCP server registration for Claude Code
```

---

## How to Resume

```bash
# 1. Start the stack
docker compose up -d

# 2. Verify health
curl http://localhost:8080/health

# 3. Run tests (no external deps needed)
python3 -m pytest tests/test_ingest.py -v

# 4. Ingest a document
./scripts/ingest_local.sh ./docs/runbook-template.md

# 5. Query
./scripts/query_cli.sh "payment service OOMKilled, what should I do?"
```

---

## Environment Variables

See `.env.example`. The running `.env` (not committed) has:
- `OLLAMA_HOST=http://ollama:11434`
- `CHROMA_HOST=http://chromadb:8000`
- `API_PORT=8080`
- `API_SECRET_KEY=<32-byte hex, generate with openssl rand -hex 32>`

---

## Infrastructure (not in this repo)

- **VPS 1** (existing): Hostinger KVM, Debian 12, k3s + ArgoCD + Grafana + Alertmanager. Managed via Azure DevOps — do NOT migrate.
- **VPS 2** (not yet contracted): Will host this Docker stack.
- Private network between VPS 1 and VPS 2 via Hostinger internal network.

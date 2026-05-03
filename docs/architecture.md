# Architecture

## Overview

```
VPS 1 (k3s + Grafana)          VPS 2 (SRE RAG)
────────────────────           ────────────────────────────
Alertmanager ──webhook──►  FastAPI :8080
                               │
Grafana                        ├── /ingest/file   (manual upload)
                               ├── /ingest/alert  (Alertmanager webhook)
                               ├── /query         (RAG query)
                               └── /health        (healthcheck)
                                      │
                              ┌───────┴──────────┐
                           ChromaDB :8000     Ollama :11434
                           (vector store)    (LLM + embeddings)
```

## Request Flow

### Ingestion

1. File upload or Alertmanager webhook hits `/ingest/*`
2. Parser extracts text based on file type (Markdown, JSON, alert payload)
3. Chunker splits text into overlapping chunks (~1000 chars)
4. Embedder calls Ollama (`nomic-embed-text`) to generate vectors
5. Retriever upserts chunks + embeddings into ChromaDB

### Query (RAG)

1. User question hits `POST /query`
2. Embedder converts question to vector
3. Retriever searches ChromaDB for top-k similar chunks
4. LLM service sends context + question to Ollama (`mistral:7b-instruct-q4_K_M`)
5. Answer, sources, and confidence score returned

## Component Responsibilities

| Component | File | Responsibility |
|-----------|------|---------------|
| FastAPI app | `api/main.py` | Router setup, lifespan |
| Auth | `api/auth.py` | X-API-Key validation |
| Embedder | `api/services/embedder.py` | Ollama embed calls |
| Retriever | `api/services/retriever.py` | ChromaDB read/write |
| LLM | `api/services/llm.py` | Ollama generate calls |
| Markdown parser | `ingestor/parsers/markdown.py` | Split by H2/H3 |
| JSON parser | `ingestor/parsers/json_logs.py` | NDJSON / JSON array |
| Alert parser | `ingestor/parsers/alertmanager.py` | Alertmanager payloads |
| Chunker | `ingestor/chunker.py` | Sliding window chunking |
| Pipeline | `ingestor/pipeline.py` | Orchestrate parse → chunk |

## Security Boundaries

- Ollama (:11434) and ChromaDB (:8000) bound to localhost only
- FastAPI (:8080) bound to private Hostinger network only
- All write endpoints require `X-API-Key` header
- Alert webhook (`/ingest/alert`) requires `X-API-Key` header (set via Alertmanager `http_config.headers`)
- Sensitive keys are redacted in JSON log parser before storage

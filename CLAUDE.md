# CLAUDE.md — SRE RAG System (PRIVADO)

> ⚠️ Este arquivo está no .gitignore. Nunca commitar.
> Contexto interno do projeto para uso com Claude CLI e agentes de IA.

---

## 🎯 Visão Geral do Projeto

Sistema RAG (Retrieval-Augmented Generation) focado em SRE/Platform Engineering.
Ingere logs, alertas, runbooks e post-mortems para construir uma base de conhecimento
vetorial que cresce com o tempo e acelera diagnóstico de incidentes.

**Objetivo principal:** Reduzir MTTR (Mean Time To Resolve) via recuperação semântica
de incidentes similares e geração de runbooks automáticos.

**Objetivo secundário:** Portfolio técnico para vagas remotas gringas como
Platform Engineer ($10k/mês).

---

## 🏗️ Infraestrutura Real

```
VPS 1 — Hostinger KVM (existente)        VPS 2 — Hostinger KVM 2 (novo)
─────────────────────────────────        ────────────────────────────────
Debian 12                                Debian 12 (Bookworm)
k3s + ArgoCD                             Ollama (LLM local)
Grafana + Alertmanager                   ChromaDB (base vetorial)
Apps e serviços                          FastAPI (API REST)
CI/CD: Azure DevOps (privado)            Crawler / Ingestor
4 cores / 16GB RAM / 200GB SSD           2 vCPU / 8GB RAM / 100GB SSD
```

### Comunicação entre VPS
- Rede privada interna Hostinger (sem exposição pública)
- VPS 1 → VPS 2: webhooks de alertas via Alertmanager, export de logs/métricas
- VPS 2 → VPS 1: API interna consultável por serviços no k3s
- IP da VPS 2: definir após contratação — registrar aqui

### Repositórios
- Infra atual (privado): Azure DevOps — NÃO migrar
- Este projeto (público): GitHub — `github.com/<user>/sre-rag`

---

## ⚙️ Variáveis de Ambiente

```bash
# .env — nunca commitar, apenas .env.example vai pro GitHub

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct-q4_K_M
OLLAMA_EMBED_MODEL=nomic-embed-text

# ChromaDB
CHROMA_HOST=http://localhost:8000
CHROMA_COLLECTION=sre_knowledge

# API
API_PORT=8080
API_SECRET_KEY=<gerar com: openssl rand -hex 32>

# Ingestão
INGEST_WATCH_DIR=/data/incoming
LOG_LEVEL=INFO

# Alertmanager webhook (VPS 1 → VPS 2)
# URL interna: http://<VPS2-PRIVATE-IP>:8080/ingest/alert
```

---

## 🚀 Setup Inicial — VPS 2

```bash
# 1. Atualizar sistema
apt update && apt upgrade -y

# 2. Instalar Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# 3. Clonar repositório
git clone https://github.com/<user>/sre-rag.git
cd sre-rag

# 4. Configurar ambiente
cp .env.example .env
nano .env  # preencher valores reais

# 5. Subir serviços
docker compose up -d

# 6. Pull dos modelos Ollama
docker exec -it sre-rag-ollama-1 ollama pull mistral:7b-instruct-q4_K_M
docker exec -it sre-rag-ollama-1 ollama pull nomic-embed-text

# 7. Verificar
docker compose ps
curl http://localhost:8080/health
```

---

## 📥 Ingestão de Dados

### Manual

```bash
# Diretório inteiro
./scripts/ingest_local.sh ./docs/runbooks/

# Arquivo único
curl -X POST http://localhost:8080/ingest/file \
  -H "X-API-Key: <API_SECRET_KEY>" \
  -F "file=@postmortem-2024-01-14.md"
```

### Alertmanager (VPS 1)

```yaml
# alertmanager.yml na VPS 1
receivers:
  - name: sre-rag
    webhook_configs:
      - url: http://<VPS2-PRIVATE-IP>:8080/ingest/alert
        send_resolved: true
```

---

## 🔐 Segurança

- `.env`, `CLAUDE.md`, IPs internos → sempre no `.gitignore`
- API autenticada via header `X-API-Key`
- Portas 11434 (Ollama) e 8000 (ChromaDB) — apenas localhost, nunca expor publicamente
- Porta 8080 (FastAPI) — apenas rede privada Hostinger
- Sanitizar logs antes de ingerir (remover tokens, senhas, PII)

---

## 📊 Roadmap

### Fase 1 — MVP local ← estamos aqui
- [ ] Docker Compose com Ollama + ChromaDB + FastAPI
- [ ] Ingestão de arquivos markdown
- [ ] Endpoint de query RAG básico
- [ ] Script CLI para consultas

### Fase 2 — VPS 2
- [ ] Contratação KVM 2 Hostinger
- [ ] Deploy e setup inicial
- [ ] Ingestão automática via webhook Alertmanager
- [ ] Integração rede privada com VPS 1

### Fase 3 — Enriquecimento
- [ ] Crawler OpenClaw (free tier)
- [ ] Interface web simples (Streamlit)
- [ ] Detecção de padrões recorrentes
- [ ] Export de relatórios

### Fase 4 — Portfolio
- [ ] README completo em inglês
- [ ] Demo gravado
- [ ] Blog post técnico (dev.to / Medium)

---

## 🧠 Decisões Técnicas Registradas

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| LLM | Mistral 7B Q4 | Melhor custo/qualidade pra 8GB RAM |
| Embeddings | nomic-embed-text | Leve, bom pra textos técnicos |
| Vector DB | ChromaDB | Simples, sem infra extra, Python-native |
| API | FastAPI | Async, tipagem, docs automáticas |
| Infra RAG | VPS separada | Isolamento de risco da infra principal |
| Repo | GitHub público | Portfolio pra vagas gringas |
| Infra atual | Azure DevOps | Não migrar, custo/risco desnecessário |

---

*Última atualização: maio/2026*
*Autor: Allan Silva — Senior SRE/Platform Engineer*

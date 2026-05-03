# Hostinger VPS 2 Deployment

Deploy target: Debian 12 KVM with 2 vCPU, 8GB RAM, 100GB SSD.

This VPS runs only incident-copilot:
- Ollama on localhost only: `127.0.0.1:11434`
- ChromaDB on localhost only: `127.0.0.1:8000`
- FastAPI on either:
  - VPS 2 private IP, if Hostinger private networking is available
  - VPS 2 public IP restricted by firewall to VPS 1 public IP only

Do not expose Ollama or ChromaDB publicly.
Do not expose FastAPI `8080` to the whole internet.

---

## 1. Provision VPS 2

Create a Hostinger KVM VPS with Debian 12.

Recommended:
- 2 vCPU
- 8GB RAM
- 100GB SSD
- Private network enabled between VPS 1 and VPS 2, if Hostinger offers it

Record:

```bash
VPS2_PUBLIC_IP=<fill-after-provisioning>
VPS1_PUBLIC_IP=<existing-vps-public-ip>
VPS2_PRIVATE_IP=<optional-if-available>
VPS1_PRIVATE_IP=<optional-if-available>
```

---

## 2. Bootstrap Server

SSH into VPS 2:

```bash
ssh root@<VPS2-PUBLIC-IP>
```

Run:

```bash
curl -fsSL https://raw.githubusercontent.com/kgbunshin/incident-copilot/master/scripts/setup.sh -o /tmp/incident-copilot-setup.sh
chmod +x /tmp/incident-copilot-setup.sh
sudo /tmp/incident-copilot-setup.sh
```

The script will:
- update Debian packages
- install Docker and Docker Compose plugin
- clone the repo into `/opt/incident-copilot`
- create `/opt/incident-copilot/.env`
- generate `API_SECRET_KEY`
- pull Ollama models
- start the Docker stack

---

## 3. Choose Network Mode

Prefer private networking if Hostinger provides it.

If Hostinger only gives public IPs, use public-restricted mode:

- API binds on `0.0.0.0:8080`
- UFW allows `8080/tcp` only from `VPS1_PUBLIC_IP`
- UFW denies `8080/tcp` from everywhere else
- Ollama and ChromaDB remain on `127.0.0.1`

---

## 4. Bind API

Edit:

```bash
sudo nano /opt/incident-copilot/.env
```

Private network mode:

```bash
API_BIND_IP=<VPS2_PRIVATE_IP>
API_PORT=8080
```

Public-restricted mode:

```bash
API_BIND_IP=0.0.0.0
API_PORT=8080
```

Keep:

```bash
OLLAMA_HOST=http://ollama:11434
CHROMA_HOST=http://chromadb:8000
OLLAMA_MODEL=mistral:7b-instruct-q4_K_M
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_PREWARM=true
```

Restart API:

```bash
cd /opt/incident-copilot
docker compose -f docker-compose.prod.yml up -d api
```

---

## 5. Firewall

Keep port `8080` restricted to VPS 1.

Private network mode:

```bash
sudo ufw allow OpenSSH
sudo ufw allow from <VPS1_PRIVATE_IP> to any port 8080 proto tcp
sudo ufw deny 8080/tcp
sudo ufw enable
sudo ufw status verbose
```

Public-restricted mode:

```bash
sudo ufw allow OpenSSH
sudo ufw allow from <VPS1_PUBLIC_IP> to any port 8080 proto tcp
sudo ufw deny 8080/tcp
sudo ufw enable
sudo ufw status verbose
```

Do not open:
- `11434/tcp`
- `8000/tcp`

They are bound to `127.0.0.1` by Compose.

---

## 6. Validate On VPS 2

On VPS 2:

```bash
cd /opt/incident-copilot
docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1:8080/health
```

Expected:

```json
{"status":"ok","ollama":"ok","chromadb":"ok"}
```

Run local server validation:

```bash
./scripts/ingest_local.sh ./docs/runbook-template.md
./scripts/query_cli.sh "payment service OOMKilled, what should I do?"
```

---

## 7. Validate From VPS 1

From VPS 1, only test reachability. Do not change k3s, ArgoCD, or Azure DevOps.

Private network mode:

```bash
curl http://<VPS2_PRIVATE_IP>:8080/health
```

Public-restricted mode:

```bash
curl http://<VPS2_PUBLIC_IP>:8080/health
```

Expected:

```json
{"status":"ok","ollama":"ok","chromadb":"ok"}
```

---

## 8. Alertmanager Webhook

After connectivity is validated, add a receiver on VPS 1 Alertmanager:

Private network mode:

```yaml
receivers:
  - name: incident-copilot
    webhook_configs:
      - url: http://<VPS2_PRIVATE_IP>:8080/ingest/alert
        send_resolved: true
```

Public-restricted mode:

```yaml
receivers:
  - name: incident-copilot
    webhook_configs:
      - url: http://<VPS2_PUBLIC_IP>:8080/ingest/alert
        send_resolved: true
```

The `/ingest/alert` endpoint is intentionally unauthenticated for Alertmanager webhook compatibility.
That is why public-restricted mode must firewall `8080/tcp` to VPS 1 public IP only.

---

## 9. Operations

Start:

```bash
cd /opt/incident-copilot
docker compose -f docker-compose.prod.yml up -d
```

Stop:

```bash
cd /opt/incident-copilot
docker compose -f docker-compose.prod.yml stop
```

Logs:

```bash
cd /opt/incident-copilot
docker compose -f docker-compose.prod.yml logs -f api
```

Update:

```bash
cd /opt/incident-copilot
git pull --ff-only
docker compose -f docker-compose.prod.yml up -d --build
```

Stats:

```bash
cd /opt/incident-copilot
set -a
source .env
set +a
curl -H "X-API-Key: ${API_SECRET_KEY}" http://127.0.0.1:8080/stats | jq .
```

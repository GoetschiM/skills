# LiteLLM Proxy Architecture — Nova → LXC 100

**Stand:** 31.05.2026

## Übersicht

Es existiere zwei LiteLLM-Instanzen im Homelab:

```
Hermes / Agenten
    │
    ▼
Nova (10.0.60.167:4000)    ← LiteLLM Proxy (venv + systemd, database_url: null)
    │
    │  api_base: http://10.0.60.121:4000/v1
    │  api_key: sk-zB0...-ONA  /  sk-ZC3...PtPw  (Virtual Keys)
    ▼
LXC 100 (10.0.60.121:4000)  ← LiteLLM Gateway (Docker + PostgreSQL)
    │
    ├── OpenAI (GPT-4o-mini)
    ├── Gemini (Flash, Flash-Lite)
    ├── DeepSeek (v4-flash)
    ├── OpenRouter (Claude, weitere)
    └── Ollama (lokal: llama3.2, Qwen, Mistral)
```

## Nova (Proxy, 10.0.60.167)

**Setup:** Bare Python venv + systemd-Service
**Config:** `/opt/ai-routing-system/config/litellm_nova.yaml`
**Env:** `/opt/ai-routing-system/.env`
**Systemd:** `litellm-nova.service` (EnvironmentFile = `.env`)

**Besonderheite:**
- `database_url: null` → kei DB, reine Proxy-Modus
- Forwarded alli Requests a LXC 100 via `api_base`
- Authentifiziert sich mit Virtual Keys (`sk-zB0...-ONA`, `sk-ZC3...PtPw`)
- Nur `127.0.0.1:4000` (localhost) — nid vo usse erreichbar
- Eigete Master Key: `sk-nov...JomZ` (für lokali API-Zuegriff)

**Key-Konfiguration:**
```yaml
general_settings:
  database_url: null
  master_key: sk-nov...JomZ
  allowed_origins: ["*"]
model_list:
  - model_name: gemini-flash
    litellm_params:
      api_base: http://10.0.60.121:4000/v1
      api_key: sk-zB0...-ONA
      model: openai/gemini-flash
  - model_name: deepseek-v4-flash
    litellm_params:
      api_base: http://10.0.60.121:4000/v1
      api_key: sk-ZC3...PtPw
      model: openai/deepseek-v4-flash
```

## LXC 100 (Gateway, 10.0.60.121)

**Setup:** Docker via Dokploy
**Image:** `ghcr.io/berriai/litellm:main-latest`
**DB:** PostgreSQL 16 (Container `litellm-db`)
**Master Key:** `sk-S64...eQRA`

**Besonderheite:**
- `STORE_MODEL_IN_DB=True` → Models via LiteLLM Dashboard definiert
- Virtual Keys via `/key/generate` API oder DB-Direct-Insert
- Alli Provider-Keys via `.env` (Dokploy) oder Dashboard (DB, encrypted)
- Port 4000 au vo usse erreichbar (10.0.60.121:4000)

## Key Lifecycle

### Virtual Keys erstelle (normaler Wäg)

```bash
curl -X POST http://10.0.60.121:4000/key/generate \
  -H "Authorization: Bearer sk-S64...eQRA" \
  -H "Content-Type: application/json" \
  -d '{"models": ["deepseek-v4-flash"], "metadata": {"user": "nova-proxy"}}'
```

### Virtual Keys wiederherstelle (nach Verlust)

Wänn d'Virtual Keys verlore gönd (z. B. nach LiteLLM-Resets):

```bash
# 1. Hash vom gwünschte Key berechne
echo -n "sk-zB0...-ONA" | sha256sum

# 2. In DB iisetze
docker exec litellm-db psql -U litellm -d litellm -c "
INSERT INTO \"LiteLLM_VerificationToken\" (token, key_alias, models, metadata, spend, blocked)
VALUES ('<sha256-hash>', 'nova-gemini-proxy', '{}', '{\"user\": \"nova-proxy\"}', 0, false);"
```

**Wichtig:** Au de Master Key muess als Token i de DB existiere. Wänn er fählt → gliiche Insert-Prozess.

### Config corruption recovery

Wänn d'Config-Datei vom Proxy kaputt goht (z. B. sed-Fehler):

```bash
# Backup vorhande? (.bak)
ls -la /opt/ai-routing-system/config/litellm_nova.yaml.bak

# Restore
cp /opt/ai-routing-system/config/litellm_nova.yaml.bak \
   /opt/ai-routing-system/config/litellm_nova.yaml

# Systemd neustarte
systemctl restart litellm-nova.service
```

## SSH Verbindige

| Host | Addrässe | Credentials |
|------|----------|-------------|
| Nova | `ssh root@10.0.60.167` | Passwort |
| LXC 100 | `ssh root@10.0.60.121` | `Louis_one_13` (langsam, Disk 100%) |

## Verifikation

```bash
# Proxy test (Nova)
curl -s -H "Authorization: Bearer sk-nov...JomZ" \
  http://127.0.0.1:4000/v1/models

# Gateway test (LXC 100)
curl -s -H "Authorization: Bearer sk-S64...eQRA" \
  http://10.0.60.121:4000/v1/models

# Chat Completion (via Proxy → Gateway → Provider)
curl -X POST http://127.0.0.1:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-nov...JomZ" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'
```

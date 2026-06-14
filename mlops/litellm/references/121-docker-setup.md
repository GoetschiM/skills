# Apollo 121 — LiteLLM Docker/Dokploy Setup

**Host:** 10.0.60.121
**User:** root
**Pass:** Louis_one_13
**LiteLLM:** Docker via Dokploy (ghcr.io/berriai/litellm:main-latest)
**Port:** 4000

## Architektur

```
┌─────────────────────┐
│  10.0.60.121 (Host) │
│  ┌───────────────┐  │
│  │ litellm (v1.x) │─── Port 4000
│  │  Docker-Cont.  │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ litellm-db    │  │
│  │ PostgreSQL 16 │  │
│  │ Alpine        │  │
│  └───────────────┘  │
└─────────────────────┘
```

## Config-Standort (Dokploy)

D'Docker-Compose-Config isch über Dokploy deployt:

| Pfad | Zweck |
|------|-------|
| `/etc/dokploy/compose/goetschi-labs-litellm-tyvi0d/code/docker-compose.yml` | Compose-Definition |
| `/etc/dokploy/compose/goetschi-labs-litellm-tyvi0d/code/.env` | Alle Umgebungsvariable + API-Keys |

## Models (via SQL-Tabelle `LiteLLM_ProxyModelTable`)

Models sind in de DB via LiteLLM-Dashboard definiert (STORE_MODEL_IN_DB=True). D'Config **nid** inere YAML-Datei.

**Verfügbari Models (Stand 16.05.2026):**
- deepseek-v4-flash (via Dashboard, custom_llm_provider: deepseek)
- gpt-4o-mini
- gpt-4.1-mini
- gemini-2.5-flash
- gemini/gemini-2.5-flash-lite
- gemini/gemini-3-flash-preview
- gemini/gemini-3.1-flash-lite-preview
- openrouter-claude-sonnet
- llama3.2 (lokali Ollama-Instanz)
- Qwen3.5:9B (lokali Ollama)
- Test Routing mit Free (Complexity Router)
- daleford2 (via DB)
- yarn-mistral:7b (lokali Ollama)

## Credentials (encrypted in DB)

API-Keys für Provider sind entweder via `.env` (Host-Ebene, Dokploy) oder via LiteLLM-Dashboard (DB) gsetzt:

| Key | Quelle | Sichtbar? |
|-----|--------|-----------|
| OPENAI_API_KEY | `.env` (Dokploy) | ✅ Klartext im .env |
| GEMINI_API_KEY | `.env` (Dokploy) | ✅ Klartext im .env |
| OR_API_KEY | `.env` (Dokploy) | ✅ Klartext im .env |
| DeepSeek | LiteLLM Dashboard → `LiteLLM_CredentialsTable` | ❌ Encrypted, nüme extrahierbar |
| Gemini (AI Studio) | LiteLLM Dashboard → `LiteLLM_CredentialsTable` | ❌ Encrypted |
| OpenAI (ChatGPT) | LiteLLM Dashboard → `LiteLLM_CredentialsTable` | ❌ Encrypted |

## DeepSeek Routing auf 121

De DeepSeek-Key isch über s'LiteLLM-Dashboard i d'Credential-Tabelle gschribe worde. D'Model-Definition zeigt:

```json
{
  "model_name": "deepseek-v4-flash",
  "litellm_params": {
    "custom_llm_provider": "deepseek",
    "model": "deepseek-v4-flash"
  }
}
```

Es wird de **native DeepSeek-Provider** brucht (nid OpenRouter). De Key isch bi Iigab über's Dashboard i d'DB gflosse und **nüme im Plaintext verfügbar**.

## SSH-Zugriff vo usse

- **Direkt:** `ssh root@10.0.60.121` (Passwort `Louis_one_13`)
- **Über 156:** `ssh root@10.0.60.156` → vo det us `ssh root@10.0.60.121` (Fall SSH-Key vorhande, suscht Passwort)
- **Vo Hermes-Container:** via paramiko (ke sshpass, kei Root im Container)

```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.0.60.121', username='root', password='Louis_one_13', timeout=15)
stdin, stdout, stderr = ssh.exec_command('docker exec <container> env')
print(stdout.read().decode())
ssh.close()
```

## Verifikation

```bash
# Läuft?
docker ps | grep litellm
curl http://localhost:4000/health

# Models via API (mit Master-Key)
curl -s -H "Authorization: Bearer sk-S64fDNhg6ecWrWbvx4eQRA" \
  http://localhost:4000/v1/models | python3 -m json.tool

# Credentials (maskiert)
curl -s -H "Authorization: Bearer sk-S64fDNhg6ecWrWbvx4eQRA" \
  http://localhost:4000/credentials | python3 -m json.tool

# Model-Detail
curl -s -H "Authorization: Bearer sk-S64fDNhg6ecWrWbvx4eQRA" \
  http://localhost:4000/model/info | python3 -m json.tool
```

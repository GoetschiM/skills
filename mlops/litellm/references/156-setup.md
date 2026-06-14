# Apollo 156 — LiteLLM Setup

**Host:** 10.0.60.156 (Hostname: Apollo)  
**User:** root  
**Pass:** Louis_one_13  
**OS:** Debian/Ubuntu on Proxmox (Kernel 6.8.12-18-pve)

## Config (Stand 16.05.2026: deaktiviert, 121 in Bruuch)

| Pfad | Zweck |
|------|-------|
| `/opt/apollo156/litellm/` | Config + .env (bare-metal) |
| `/opt/apollo156/litellm-docker/` | Docker-Compose-Setup (nid aktiv) |
| `/opt/apollo156/venvs/litellm/` | Python-Venv mit LiteLLM 1.84.0 |
| `/opt/apollo156/app/` | Hermes Agent (vorbereitet, no nid aktiv) |

## Systemd Service

- **File:** `/etc/systemd/system/litellm.service`
- **Status:** `systemctl status litellm`
- **Logs:** `journalctl -u litellm -f`
- **Autostart:** ✅ Enabled
- **Port:** 4000

## Env-Vars (via /opt/apollo156/litellm/.env)

- `LITELLM_MASTER_KEY` = sk-S64fDNhg6ecWrWbvx4eQRA (✅ identisch mit 121)
- `OPENAI_API_KEY` = sk-proj-... (✅ identisch mit 121)
- `GEMINI_API_KEY` = AIzaSyCtm... (✅ identisch mit 121)
- `OR_API_KEY` = sk-or-v1-... (✅ identisch mit 121)

## Models

| Modell | Provider | Key |
|--------|----------|-----|
| deepseek-v4-flash | deepseek/deepseek-v4-flash | DEEPSEEK_API_KEY (⚠️ OPENAI_API_KEY funktioniert NID!) |
| gpt-4o-mini | gpt-4o-mini | OPENAI_API_KEY |
| gpt-4.1-mini | gpt-4.1-mini | OPENAI_API_KEY |
| gemini-2.5-flash | gemini/gemini-2.5-flash | GEMINI_API_KEY |
| openrouter-claude-sonnet | openrouter/anthropic/claude-sonnet-4 | OR_API_KEY |

## Verwendung vo anderne Hosts us

Hermes Config muess uf `http://10.0.60.156:4000/v1` zeige statt 10.0.60.121.

## Restart / Ändrige

```bash
# Config ändere
vim /opt/apollo156/litellm/config.yaml

# .env ändere (Keys, Provider)
vim /opt/apollo156/litellm/.env

# Neustarte
systemctl restart litellm

# Prüfe
systemctl status litellm --no-pager -l
curl http://localhost:4000/v1/models
```

## Known Issues

### Prisma Engine Binary (Stand 16.05.2026)

LiteLLM 1.84.0 in bare-metal Venv startet mit `DATABASE_URL` nur, we de Prisma Client korrekt inkl. Engine Binary installiert isch. Uf 156 fählt de Binary (`lib`-Verzeichnis het nur `constants.py` / `platform.py`, kei Binaries):

**Symptom:** `httpx.ConnectError: All connection attempts failed` — de Prisma Engine Go-Process chummt nid zstande.

**Fix-Versuech (no nid erfolgrich):**
1. `prisma generate` us em Venv → ✅ Klappt, generiert Python-Code
2. Engine Binary wird aber nid glade (fählt im `binaries/`-Verzeichnis)
3. `pip install prisma` installiert d'Library aber ned de Binary
4. `npx prisma generate` → brucht JS-Generator, nid `prisma-client-py`

**Workaround (aktiv):**
- Hermes uf 156 zeigt uf **121s LiteLLM** (10.0.60.121:4000) statt lokali 156-Instanz
- Systemd-Service litellm isch gstoppt + disabled
- **Docker-Installation** uf 156 isch de empfohlene Weg für en fallback (de Prisma Binary isch im Docker-Image integriert)
- Docker-Image: `ghcr.io/berriai/litellm:main-latest`

## Verifikation (Stand 16.05.2026)

121's LiteLLM isch **voll funktionsfähig** ✅ — verfügbari Models:
- deepseek-v4-flash ✅
- gpt-4o-mini ✅
- gpt-4.1-mini ✅
- gemini-2.5-flash ✅
- openrouter-claude-sonnet ✅
- Qwen3.5:9B, yarn-mistral:7b + Gemini 3.1- / 2.5-Lite-Previews

**API Key (produktiv):** `sk-S64fDNhg6ecWrWbvx4eQRA`

# LiteLLM Bare-Metal (Nova 10.0.60.156)

**Gelöscht am:** 07.06.2026 (Backup vor Löschig -> Litellm-hermes-108_backup.tar.gz)
**Host:** Nova Container 10.0.60.156 (kein Dokploy/Docker — **bare-metal/Venv frei**)

## Letzter Stand (vor Löschig)

### Installation
- **Binary:** `/usr/local/bin/litellm` — via `pip install litellm[proxy]` (global, no venv)
- **Config:** `/etc/litellm/config.yaml`
- **Alternative Config:** `/opt/litellm/config.yaml` + `/opt/litellm/docker-compose.yml` (ungenutzt)
- **Env:** `/etc/litellm/litellm.env` (DEEPSEEK_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY)
- **Keys us Hermes `.env`:** `LITELLM_API_KEY`, `OPENAI_API_KEY`
- **Port:** 4000 (0.0.0.0)
- **Systemd:** ❌ Kein Service — gestartet via:
  ```
  litellm --config /etc/litellm/config.yaml --host 0.0.0.0 --port 4000
  ```
- **Prozess:** Python 3.12, root

### Config `model_list` (6 aliases)
- `gemini-flash` — 2x Gemini 2.5 Flash (redundant)
- `deepseek-v4-flash`, `deepseek-fast-1/2/3` — 4x DeepSeek (load-balanced)
- `openrouter-free` — 3 OpenRouter Free-Models (owl-alpha, cobuddy, laguna)
- `openai-mini` — GPT-4.1 Mini
- `openai-nano` — GPT-4.1 Nano

### Proxy API Keys (6 Stück)
- sk-ap... → gemini-flash
- sk-ap... → deepseek-fast-1/2/3
- sk-ap... → openrouter-free
- sk-ap... → openai-mini/nano

### Deployment-Unterschied zu 121 (Docker)
| Aspekt | 121 (Docker) | 156 (Bare-Metal) |
|--------|-------------|-------------------|
| Installation | Docker Image | pip global |
| Konfiguration | Config in Docker:ro Volumes | `/etc/litellm/config.yaml` |
| DB | PostgreSQL via Docker Litellm-DB | **Kei DB** (config-file-only mode) |
| Keys | Via DB + Dashboard (encrypted) | Via `/etc/litellm/litellm.env` + `.env` |
| Keys generiere | `/key/generate` (DB-needed) | `proxy_api_keys` in Config |
| Startup | Dokploy/Docker Compose | `litellm --config ...` |
| Autostart | Docker Restart Policy | ❌ Kein Systemd |

### Netzzugriff
- **MinIO (10.0.60.106:9000)** — ❌ NICHT erreichbar (kein Route)
- **GitHub** — ✅ via HTTPS

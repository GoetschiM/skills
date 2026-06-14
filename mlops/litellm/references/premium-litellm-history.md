# Premium LiteLLM (Apollo 10.0.60.156:4001) — Historisch

## Status: ❌ OFFLINE (Stand 14.06.2026)

**Host:** Apollo (10.0.60.156) — Debian, 5GB RAM, 2 Cores i5-6500T
**Installation:** Docker-Container (`litellm-premium`)
**Port:** 4001
**Docker-Service:** inactive (Docker läuft nid)

## Warum offline?

- De Docker-Service (docker.socket/docker.service) isch **inactive** — entweder nie gestartet (disabled) oder nach Host-Reboot nid mitstartet
- Kei Port uf 4000-4011 offe — de Container läuft nid
- Hermes selber isch im LXC Container (Hermes-old), ohni direkte Docker-Zugriff uf Apollo
- Letzti bestätigti Health-Check: **23.05.2026, 23:00**

## Health-Check (letzte bekannte Stand, 23.05.2026)

| Model | Health | Grund |
|-------|--------|-------|
| `gemini/gemini-2.5-flash` (Key 1) | ✅ Healthy | Free Tier OK |
| `gemini/gemini-2.5-flash` (Key 2) | ✅ Healthy | Free Tier OK |
| `deepseek/deepseek-v4-pro` | 🚫 BLOCKED | Nur mit "nim Pro" |
| `gemini/gemini-2.5-pro` | ❌ 429 Quota | Free Tier Limit erreicht |
| `openrouter/claude-sonnet-4` | ❌ 401 | OpenRouter Key dead |
| `openrouter/claude-opus-4` | ❌ 401 | OpenRouter Key dead |

## Gesetzte API Keys (Docker Env Vars, Stand Mai 2026)

- `GEMINI_API_KEY_1` + `GEMINI_API_KEY_2` — 2 Geminii Free Keys
- `DEEPSEEK_API_KEY_1` — DeepSeek Paid Key (Pro-fähig)
- `OPENROUTER_API_KEY_1` — Tot (401)
- `OPENAI_API_KEY_1` — Status unbekannt

## Wiiderherstellig

Falls de Premium LiteLLM wider startet werde söll:

1. **Docker starte:** `systemctl start docker` (uf Apollo via SSH)
2. **Container starte:** `docker start litellm-premium`
3. **Prüefe:** `curl http://10.0.60.156:4001/health`

**SSH-Zugriff:** root@10.0.60.156, PW `Louis_one_13`
**Hinweis:** LXC Container "Hermes-old" het **kei** direkte Docker-Socket — SSH isch nötig

## Verhältnis zu aktiver Instanz

- **Premium (156:4001)** isch im Mai 2026 dur d'**121:4000**-Instanz ersetzt worde
- Hermes-Config zeigt uf 121:4000, nid uf 156
- D'Premium-Instanz isch nur nötig, wenn d'121:4000 usfällt oder wenn Premium-Models brucht wärded wo 121 nid het

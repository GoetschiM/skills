---
name: mcphub-gateway
description: "MCPHub — zentrale MCP Gateway Server uf LXC 107 (10.0.60.170:3000). Orchestriert multi MCP Backends (Subprozesse + URL-MCPs) für Hermes, Nova und anderi Agents. Dual-Auth: Session Token (UI/API) + API Key (MCP Endpoint). Health unter /health."
tags: [mcphub, mcp, gateway, lxc107, central-mcp, v1.0.11]
category: mcp
related_skills:
  - google-mcp-server
  - native-mcp
---

# MCPHub Gateway — Zentraler MCP-Server

MCPHub isch de zentrali MCP Gateway uf **LXC 107 (10.0.60.170:3000)**. Alli MCPs sölle det laufe — entweder als Subprozess (npx) oder als URL-MCP (für extern laufendi Dienste).

**User-Entscheid (06.06.2026):** ALLES MCP zentral uf LXC 107. Kei MCPs via Dokploy betriebe. Google, WhatsApp, Telegram etc. sölle als eigenständigi Services uf LXC 107 deployet werde.

## Infra

- **Host:** LXC 107 uf pve01 (10.0.60.10)
- **IP:** 10.0.60.170
- **Port:** 3000
- **Version:** v1.0.11
- **Container:** `mcphub` (Docker, Up seit 9+ Min)
- **Config:** `/opt/mcphub/mcp_settings.json` (im Container-Layer)
- **Login-UI:** `http://10.0.60.170:3000/` — Login: **Hermes / Louis_one_13** (seit 11.06.2026)
- **Login-API:** `POST http://10.0.60.170:3000/api/auth/login`
- **Health:** `GET http://10.0.60.170:3000/health` (kein Auth nötig)
- **Status:** `degraded` (19 Server, 16 online, 3 disconnected)
- **Context footprint:** 27.5k

## Authentication — Dual System

MCPHub v1.0.11 verwendet **zwei separate Auth-Systeme**:

### 1. Session Token (Web-UI + API)
Für Web-Interface (`/`) und interne API (`/api/*`):
```bash
TOKEN=$(curl -s -X POST http://10.0.60.170:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Hermes","password":"Louis_one_13"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Token wird im localStorage als 'mcphub_token' gspicheret:
# → key: "mcphub_token" (JWT, gültig 24h)
# → User: Hermes (isAdmin: true, permissions: ["*","x"])

# API-Call mit Session-Token (funktioniert für /api/servers, /api/users, etc.):
curl -s http://10.0.60.170:3000/api/servers \
  -H "Authorization: Bearer ***
```

### 2. MCP API Key (für /mcp Endpoint)
Der MCP-Interface-Endpunkt `/mcp` benötigt **einen separaten API Key**, der im **Settings → Keys** Bereich erstellt wird:

```bash
# Mit gültigem API Key:
curl -s http://10.0.60.170:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer *** \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**⚠️ Stand 11.06.2026: Noch kein API Key konfiguriert!** (Settings → Keys → "No keys configured yet")

Der Session-Token vom Login funktioniert NICHT für den /mcp-Endpunkt (gibt "Invalid bearer token").

### API Key erstellen
1. MCPHub WebUI öffnen (`http://10.0.60.170:3000/`)
2. Login mit Hermes / Louis_one_13
3. Settings → Keys → "Add key"
4. API Key generieren (label setzen, Scope wählen)
5. Key in Hermes Config verwenden

## Endpoints

| Endpoint | Auth | Methode | Beschrieb |
|----------|------|---------|-----------|
| `/health` | Nei | GET | Server-Status (degraded/healthy) + MCP-Liste |
| `/api/auth/login` | Nei | POST | Login (JSON: username + password) |
| `/api/servers` | Bearer (Session Token) | GET | Alli MCPs mit Status, Tools, Resources |
| `/mcp` | Bearer (API Key) | POST | MCP JSON-RPC Endpoint (tools/list, tools/call) |
| `/mcp/{server_name}` | Bearer (API Key) | POST | Direkter MCP-Zugriff uf einzelne Server (smart routing) |
| `/` | Nei | GET | WebUI Dashboard (HTML) |

## Health-Response Format

```json
{
  "status": "degraded",
  "message": "Some enabled MCP servers are not ready",
  "servers": {
    "total": 19,
    "connected": 16,
    "disconnected": 3
  },
  "timestamp": "2026-06-11T18:43:27.603Z"
}
```

Status-Werte: `healthy` (alli connected), `degraded` (es fehlt eis oder meh), `unhealthy` (nüt verbunde).

## MCP-Status (Stand 14.06.2026)

**Gesamt:** 19 Server · 16 Online · 3 Disconnected
**Context footprint:** 27.5k
**Health check response:** `{"status": "degraded", "message": "Some enabled MCP servers are not ready", "servers": {"total": 19, "connected": 16, "disconnected": 3}}`

**Alle 19 Server (via API, authentifiziert):**
| Status | Server | Tools | 
|--------|--------|-------|
| 🟢 | google-workspace | 12 Tools |
| 🟢 | home-assistant | 8 Tools |
| 🟢 | qdrant | 3 Tools |
| 🟢 | proxmox | 5 Tools |
| 🟢 | paperless | — |
| 🟢 | bash | stdio |
| 🟢 | mysql | stdio |
| 🟢 | notion | stdio |
| 🟢 | os-and-sys | stdio |
| 🟢 | python-tool | stdio |
| 🟢 | +6 weitere online | (Seiten 2-4 WebUI) |
| 🔴 | 3 disconnected | unbekannt |

**API-Credentials (aktuell gültig):**
- **Login:** Hermes / Louis_one_13 ✅ funktioniert
- **JWT Token:** 24h gültig, isAdmin: true
- **MCP API Key:** Noch immer KEIN Key erstellt (Settings → Keys → "No keys configured yet")

### MCP Endpoints (pro Server)
MCPHub unterstützt **Smart Routing** pro Server:
```
http://10.0.60.170:3000/mcp                    # Default (alle Tools)
http://10.0.60.170:3000/mcp/google-workspace   # Nur Google Workspace Tools
http://10.0.60.170:3000/mcp/proxmox            # Nur Proxmox Tools
http://10.0.60.170:3000/mcp/$smart             # Smart Routing (auto-detect)
```

## MCP Config Patterns

MCPHub unterstützt zwei Modi für MCPs:

**1. Subprozess (npx)** — für MCPs wo als npm-Package verfüegbar sind:
```json
{
  "name": "github",
  "type": "npx",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_TOKEN": "..."
  }
}
```

**2. URL-MCP** — für extern laufendi MCP-Server:
```json
{
  "name": "google-workspace",
  "type": "url",
  "url": "http://10.0.60.121:8002/mcp"
}
```

**User-Präferenz (06.06.2026):** Eigeständigi Services uf LXC 107 deploye (Docker) und via URL-MCP iibinde — nid als npx-Subprozess. Grund: Entlastet MCPHub, alles zentral uf eim Host, easy neu authentifiziere.

## References

For detailed session-specific MCPHub deployment and troubleshooting, see:
- `references/initial-status-2026-06-05.md` — Initial MCPHub status: 6/15 connected, discovery patterns, user decisions
- `references/mcphub-deployment.md` — Setup, first-run, config structure
- `references/mcphub-troubleshooting.md` — Common failures and recoveries
- `references/mcphub-client-access-guide.md` — Wie en andere Agent (Profil/Bot) Zugriff uf MCPHub überchunnt (Session Token vs API Key, Login, Host-Zugriff)
- `references/dokploy-db-access.md` — Docker-Postgres Password Reset Pattern (Dokploy + Coolify + generic), nützlich für alli LXC-DB-Dienste
- `references/mcphub-quickref.md` — Kurz-Referenz (1 Seite), für Subagenten/Hacker-Bot geeignet

## Pitfalls

### Session Token ≠ API Key (kritisch!)
MCPHub v1.0.11 het **zwei auth-Systeme**. De Session-Token (vo login) isch NUR für web-UI + REST API. Für de `/mcp` endpoint bruchts en separat **API Key**:

```bash
# Session-Token — funktioniert für Web-UI + API
curl -s http://10.0.60.170:3000/api/servers -H "Authorization: Bearer $SESSION_TOKEN"

# API-Key — funktioniert für MCP Endpoint
curl -s http://10.0.60.170:3000/mcp -H "Authorization: Bearer $API_KEY" -d '...'

# Session-Token am /mcp endpoint → 401 "Invalid bearer token"
# API-Key am /api/servers → different error
```

### No keys configured yet — /mcp ist blockiert
Wenn Settings → Keys leer isch, antwortet `/mcp` mit 401. Lösig: API Key erstelle via Web-UI.

### Degraded Status isch normal am Afang
Bi 19 MCPs sind selte alli verbunde. `degraded` isch de Normalzustand solang nid alli Credentials korrekt sind. Prüf mit:
```bash
curl -s http://10.0.60.170:3000/api/servers -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### npx MCPs bruuche Internet-Zugriff
Wenn de LXC kei Internet-Zugriff het oder d'npx Registry blockiert isch, schlond npx-basierti MCPs mit Timeout fähl. Lösig: URL-MCPs für extern laufendi MCPs verwende.

### MCPHub wird nöi gstartet — wie d'Config verfüegbar mache

Nachdäm d'MCPHub Config (`mcphubSettings.json`) gänderet worde isch, muess de Docker-Container neigstartet werde:

```bash
# Config isch READ-ONLY gemountet! (mcp_settings.json:ro)
# Nur Container-Neustart ladt sie nöi
lxc-attach -n 107 -- docker restart mcphub
sleep 5
lxc-attach -n 107 -- curl -s http://localhost:3000/health
```

**Pitfall:** Config isch vom Container mountet (`mcp_settings.json:ro`) → Nur `docker restart` hilft. Kei hot-reload.

### Container Name isch "mcphub"
Docker Container: `mcphub`. Läuft mit Docker-Netzwerk default bridge (172.17.0.x).
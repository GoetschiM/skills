# MCPHub Agenten-Zugriff (Goetschi Labs)

## Stand: 07.06.2026

## Übersicht

**MCPHub (CT107)** — `http://10.0.60.170:3000` — ist der zentrale MCP-Server-Hub für Goetschi Labs.
**12 MCPs registriert**, 9 aktiv verbunden.

## Authentication

### Bearer Token

```
Authorization: Bearer hermes-artemis-master-2026
```

Dieser Token ist **für alle Agenten gleich** — kein User-Scoping vorhanden. Aus diesem Grund wurde der **Gmail MCP deaktiviert** (enabled: false) — volle Gmail/Calendar/Drive-Rechte sind zu breit für einen Shared-Token.

### Admin Login (MCPHub Dashboard)

- **User:** `admin`
- **Passwort:** Im MCPHub-Log generiert (aktuell unbekannt — SyntaxError beim Login)

### Endpoints

| Endpoint | Auth | Beschreibung |
|----------|------|-------------|
| `GET /health` | öffentlich | Server-Status (kein Token nötig) |
| `GET /api/servers` | Bearer | Liste aller MCP-Server + Verbindungsstatus |
| `GET /api/servers/:name/tools` | Bearer | Tools eines MCP-Servers |
| `POST /api/servers/:name/call` | Bearer | Tool aufrufen |
| `POST /api/tools/call` | Bearer | Tool callen (Server-agnostisch) |
| `GET /` | öffentlich | MCPHub Dashboard (Web UI) |

## Verfügbare MCP-Server

| Name | Beschreibung | Tools | Status |
|------|-------------|-------|--------|
| `proxmox` | Proxmox VE Management | 7 | ✅ |
| `jira-confluence` | Atlassian Jira + Confluence | 9 | ✅ |
| `notion` | Notion API | 22 | ✅ |
| `qdrant` | Qdrant Vektordatenbank | 6 | ✅ |
| `home-assistant` | Home Assistant | 8 | ✅ |
| `paperless` | Paperless-ngx | 7 | ✅ |
| `minio` | MinIO S3 Storage | 6 | ✅ |
| `postgres-pgvector` | PostgreSQL + PGVector | 7 | ✅ |
| `google-workspace` | Google Workspace (Docs/Sheets) | 5 | ✅ |
| `asterisk-ari` | Asterisk ARI Telefonie | 0 | ⚠️ disconnected |
| `unifi` | UniFi Controller | 0 | ⚠️ disconnected |
| `goetschi-gmail` | Google Gmail (Search, Read, Send, Label, Trash) | 6 | ⛔ enabled: false |

## Gmail MCP — Nur via N8N

Der Google Gmail MCP (`goetschi-gmail`) ist **nicht im MCPHub aktiv**. Er läuft nur als Teil des
N8N Workflows auf `http://10.0.60.121:5678` — abgesichert durch N8N-eigene Auth.

**Zugriff auf Gmail nur über den N8N Workflow** (Michel's Telegram-Entscheidung).

## Code-Beispiele

### Über curl
```bash
# Server-Liste
curl -s -H "Authorization: Bearer hermes-artemis-master-2026" \
  http://10.0.60.170:3000/api/servers | jq .

# Tools eines Servers
curl -s -H "Authorization: Bearer hermes-artemis-master-2026" \
  http://10.0.60.170:3000/api/servers/proxmox/tools | jq .

# Tool aufrufen
curl -s -X POST \
  -H "Authorization: Bearer hermes-artemis-master-2026" \
  -H "Content-Type: application/json" \
  -d '{"tool":"list_containers","params":{"node":"pve01"}}' \
  http://10.0.60.170:3000/api/servers/proxmox/call | jq .
```

### Über Python
```python
import requests

BASE = "http://10.0.60.170:3000"
TOKEN = "hermes-artemis-master-2026"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Verfügbare Server
r = requests.get(f"{BASE}/api/servers", headers=HEADERS)
servers = r.json()

# Tool aufrufen
r = requests.post(
    f"{BASE}/api/servers/proxmox/call",
    headers=HEADERS,
    json={"tool": "list_containers", "params": {"node": "pve01"}}
)
```

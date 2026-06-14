# MCPHub — Quick-Reference für Subagenten

## Core Facts

| Aspekt | Wert |
|--------|------|
| **URL** | `http://10.0.60.170:3000` |
| **Health (kein Auth)** | `GET http://10.0.60.170:3000/health` |
| **Login (UI + API)** | `Hermes` / `Louis_one_13` |
| **Host-Zugriff** | LXC 107 via Proxmox: `pct exec 107` (SSH: Riotstar_PROXMOX_13) |
| **Status** | 19 Server, 16 online, 3 disconnected („degraded" = normal) |

## Dual-Auth (WICHTIG!)

| Endpoint | Brucht | Wie becho |
|----------|--------|-----------|
| `/`, `/api/*` | **Session Token** | `POST /api/auth/login` (24h gültig) |
| `/mcp` (Tools) | **API Key** | WebUI → Settings → Keys → Add Key |

⚠️ **Session Token ≠ API Key!** `/mcp` schlaht fähl mit Session Token. Es git NOCH kein API Key — mues im WebUI erstellt werde.

## Nützlichi API-Calls

```bash
# Login
TOKEN=$(curl -s -X POST http://10.0.60.170:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Hermes","password":"Louis_one_13"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Alli Server
curl -s http://10.0.60.170:3000/api/servers \
  -H "Authorization: Bearer $TOKEN"

# Tools uf emne bestimmte Server (mit API Key)
curl -s http://10.0.60.170:3000/mcp/proxmox \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Cheat: MCPHub für Hacker-Zweck

Wenn en Hacker/Subagent MCPHub bruuche will, bruchts:
1. Session-Token für API (via Login)
2. Eifach über `/health` starte zum Status z'checke
3. WebUI (10.0.60.170:3000) für Key-Management

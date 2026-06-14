# MCPHub Client Access Guide

Wie en andere Agent (Profil, Bot) Zugriff uf MCPHub überchunnt.

## Übersicht

De Hacker (Profil) oder en andere Agent bruucht **drei Sache** für MCPHub-Zugriff:

1. **MCPHub URL + Port** — `http://10.0.60.170:3000`
2. **Session Token** — für `GET /api/servers` (Server-Liste + Status abfroge)
3. **MCP API Key** — für `POST /mcp` (Tatsächliche Tool-Usfüehrig)

## Schritt-für-Schritt für en neue Agent

### 1. MCPHub-Login (Session Token hole)

```bash
TOKEN=$(curl -s -X POST http://10.0.60.170:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Hermes","password":"Louis_one_13"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

→ JWT Token, 24h gültig

### 2. Server-Liste abfroge (nur mit Session Token)

```bash
curl -s http://10.0.60.170:3000/api/servers \
  -H "Authorization: Bearer $TOKEN"
```

### 3. MCP API Key erstelle

Muss via **WebUI** erstellt werde (kein API-Endpunkt für Key-Generierig):

1. Browser: `http://10.0.60.170:3000/`
2. Login: **Hermes / Louis_one_13**
3. Settings → Keys → "Add key"
4. Label setze (z.B. `hacker-agent`), Scope wähle
5. **API Key kopiere und im Agent sine `.env` iitrage**

### 4. MCP-Tools nutze (mit API Key)

```bash
# Alle Tools vom Hub abfroge
curl -s http://10.0.60.170:3000/mcp \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Tool direkt uf eme Server ufrüefe
curl -s http://10.0.60.170:3000/mcp/proxmox \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_vms"}}'
```

## Wichtigi Regle

- **Session Token ≠ API Key** — zwei komplett trennti Auth-System
- **API Key existiert aktuell NOCH NID** — mues via WebUI erstellt werde
- **Token läuft ab (24h)** — bi langlebige Agenten muss de Token regelmässig erneuert werde
- **Host-Zugriff nur via Proxmox** — kei SSH uf LXC 107 möglich
- **Bi Config-Änderige** → `pct exec 107 -- docker restart mcphub`

## Host-Zugriff (für Admin)

```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10
pct exec 107 -- bash
# Config
cat /opt/mcphub/mcp_settings.json
# Container restart
docker restart mcphub
```

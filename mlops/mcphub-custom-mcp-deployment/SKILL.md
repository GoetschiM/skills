---
name: mcphub-custom-mcp-deployment
description: Build, deploy, and debug custom stdio MCP servers to MCPHub (CT107). Pure Python stdlib — no pip/MCP SDK. Hand-crafted JSON-RPC 2.0 over stdin/stdout.
category: mlops
tags: [mcphub, mcp, python, stdio, container, deployment]
usage: |
  Trigger: user says "MCP einrichten", "MCP bauen", "neuen MCP-Server deployen", "MCPHub config updaten"
  Steps:
    1. Identify the service (URL, credentials, API endpoints)
    2. Build a pure-Python stdio MCP server
    3. Deploy to Docker container on CT107
    4. Update mcp_settings.json (docker restart mcphub)
    5. Verify via health endpoint
---

# MCPHub Custom MCP Deployment

Baue und deploye eigene stdio MCP-Server auf CT107 (10.0.60.170:3000).

## MCP Protocol — Hand-crafted (kein pip mcp)

Der MCPHub Docker Container hat **Python 3.13** aber **kein pip** für externe Pakete.
Jeder MCP-Server muss reines Python stdlib sein (urllib, json, sys, os, base64, subprocess).

### Initialize Response (MUSS exakt so sein)

```python
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "protocolVersion": "2024-11-05",   # EXAKT dieser String — kein "1.0", kein "0.1.0"
        "serverInfo": {"name": "goetschi-xxx", "version": "1.0.0"},
        "capabilities": {"tools": {}}
    }
}
```

**KRITISCH**: MCPHub v1.29.0 akzeptiert NUR `"2024-11-05"` als protocolVersion.
- `"0.1.0"` → `"Server's protocol version is not supported: 0.1.0"`
- `"1.0"` → `"Server's protocol version is not supported: 1.0"`
- `"2024-11-05"` (fehlt/undefined) → ZodError `"expected string, received undefined"`

### JSON-RPC 2.0 Transport

```
Content-Length: N\r\n\r\n{"jsonrpc":"2.0","id":1,...}
```

Nachrichten werden mit **Content-Length Header** + doppeltem Newline gesendet.

### Minimale Struktur

```python
#!/usr/bin/env python3
import sys, json, urllib.request, urllib.error

def send_message(msg):
    data = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()

def main():
    buffer = ""
    for line in sys.stdin:
        buffer += line
        if "\r\n\r\n" in buffer:
            # parse content-length, extract body, handle message
            ...
            if method == "initialize":
                send_message({"jsonrpc":"2.0","id":id,"result":{
                    "protocolVersion":"2024-11-05",
                    "serverInfo":{"name":"x","version":"1.0.0"},
                    "capabilities":{"tools":{}}
                }})
```

## Deployment

### 1. Dateien deployen

**⚠️ CRITICAL PITFALL: Volume-Mount-Sync kann stale sein.**  
Die Config sagt `/opt/mcphub/scripts/ → /root/mcp-servers/` als Volume. Aber selbst nach `cp` auf den Host-Pfad sieht der Container die neue Datei nicht immer (LXC Mount-NS Problem). **Immer verifizieren:**

```bash
# Prüfe ob der Container die Datei sieht
pct exec 107 -- docker exec mcphub ls -la /root/mcp-servers/goetschi-xxx.py
```

Wenn nicht sichtbar → **pipe direkt in Container** (der einzig zuverlässige Weg):

**ONLY working method:** pipe via `docker exec -i container bash -c "cat > /path/file"`:

```bash
# Container Verzeichnis erstellen
pct exec 107 -- docker exec mcphub mkdir -p /root/mcp-servers/

# File per cat | docker exec -i von pve01 hosted kopieren
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 \
  "pct exec 107 -- docker exec -i mcphub bash -c 'cat > /root/mcp-servers/goetschi-xxx.py'" < /tmp/goetschi-xxx.py

# ODER: File zuerst auf pve01 pipen, dann in Container
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 'cat > /tmp/goetschi-xxx.py' < /tmp/goetschi-xxx.py
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 \
  "cat /tmp/goetschi-xxx.py | pct exec 107 -- docker exec -i mcphub bash -c 'cat > /root/mcp-servers/goetschi-xxx.py'"
```

### 2. mcp_settings.json patchen

Config liegt im Container unter `/opt/mcphub/mcp_settings.json`.  
**⚠️ WICHTIG: Host-Volume-Änderungen werden beim Restart NICHT übernommen** — der Container lädt seine in-Image-Default-Konfiguration. Änderungen müssen **direkt im Container** per `docker exec` gemacht werden.

**Reliable Pattern: Python direkt im Container ausführen**

```bash
sshpass -p "..." ssh root@10.0.60.10 bash << 'EOF'
pct exec 107 -- docker exec -i mcphub python3 << 'PYEOF'
import json
with open("/app/mcp_settings.json") as f:
    cfg = json.load(f)

cfg.setdefault("mcpServers", {})["github"] = {
    "description": "GitHub API — Repositories, PRs, Issues",
    "transport": "stdio",
    "command": "/usr/bin/python3",
    "args": ["/root/mcp-servers/goetschi-github.py"],
    "enabled": True
}
with open("/app/mcp_settings.json", "w") as f:
    json.dump(cfg, f, indent=2)
print(f"✅ Added. Total: {len(cfg['mcpServers'])}")
PYEOF
EOF
```

Danach: `docker restart mcphub` + `sleep 15` + Health-Check.

**Alternative: `pct exec` via pve01 background**

```bash
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 "pct exec 107 -- docker restart mcphub"
sleep 15
curl -s http://10.0.60.170:3000/health | python3 -m json.tool
```

```json
{
  "mcpServers": {
    "my-service": {
      "type": "stdio",
      "command": "python3",
      "args": ["/root/mcp-servers/goetschi-xxx.py"],
      "env": {
        "SERVICE_URL": "http://...",
        "SERVICE_KEY": "xxx"
      },
      "enabled": true
    }
  },
  "bearerKeys": ["mcphub-goetschi-2026-open"],
  "systemConfig": {
    "oauthServer": {"enabled": false}
  }
}
```

### 3. Fast-Patching bestehender Scripte im Container

Nachdem ein Script deployed ist und nur kleine Änderungen braucht (z.B. protocolVersion fix), ist es am schnellsten via `docker exec` + `sed` direkt im Container:

```bash
# Direkt im Docker Container patchen
pct exec 107 -- docker exec mcphub sed -i 's/"0.1.0"/"2024-11-05"/g' /root/mcp-servers/goetschi-xxx.py

# Oder via pve01
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 \
  "pct exec 107 -- docker exec mcphub sed -i 's/\"0.1.0\"/\"2024-11-05\"/g' /root/mcp-servers/goetschi-xxx.py"

# Verifikation
pct exec 107 -- docker exec mcphub grep "protocolVersion" /root/mcp-servers/goetschi-xxx.py
```

## Batch Deployment (11 MCPs at Once)

For deploying all Goetschi Labs MCPs to a new/fresh container, use this pattern:

### Step 1: Create scripts locally

Create each MCP script in `/tmp/` on the agent host. Each must pass `python3 -m py_compile`.

### Step 2: Pipe all scripts to the container

```bash
# From agent host, script by script:
for f in /tmp/goetschi-*.py; do
  cat "$f" | sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 \
    "cat > /opt/mcphub/scripts/$(basename $f)"
done
```

Then copy into the running container if needed (but with volume mounts, container sees them directly):
```bash
# Verify they're in the container via volume
pct exec 107 -- docker exec mcphub ls /root/mcp-servers/
```

### Step 3: Write config to host

```bash
cat /tmp/mcphub_config.json | sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 \
  "cat > /opt/mcphub/mcp_settings.json"
```

### Step 4: Kill old container, start fresh with volumes

```bash
pct exec 107 -- docker rm -f mcphub
pct exec 107 -- docker run -d --name mcphub --restart unless-stopped -p 3000:3000 \
  -v /opt/mcphub/mcp_settings.json:/app/mcp_settings.json:rw \
  -v /opt/mcphub/scripts/:/root/mcp-servers/:rw \
  -v /opt/mcphub/token/:/data/:rw \
  samanhappy/mcphub:latest
```

### Step 5: Install pip packages

```bash
pct exec 107 -- docker exec mcphub pip install google-auth google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### Step 6: Restart & verify

```bash
pct exec 107 -- docker restart mcphub
sleep 15
curl -s http://10.0.60.170:3000/health
```

Expected: 11 total, ~9 connected.

## Jira Issue Creation (GL Project)

The Goetschi Labs Jira project (GL) is a **Team Managed project** — it does NOT use Task/Story/Bug issue types. Only three types are available:

| Issue Type | ID | Use Case |
|-----------|-----|----------|
| Question | 10047 | Anfragen, Klärungen |
| Problem | 10045 | Bugs, Fehler, Störungen |
| Suggestion | 10046 | Verbesserungsvorschläge, neue Features |

**Workaround**: Use "Suggestion" (10046) for feature work and "Problem" (10045) for incident tracking. There is no "Task" type in GL.

### Jira Cloud REST API — ADF Format

Jira Cloud v3 API requires **Atlassian Document Format (ADF)** for description, NOT plaintext markdown:

```python
import requests, json

url = "https://goetschi.atlassian.net/rest/api/3/issue"
auth = ("michelgoetschi@gmail.com", "ATATT3xf...")

# ✅ CORRECT: description as Python dict (not json.dumps string!)
issue = {
    "fields": {
        "project": {"key": "GL"},
        "summary": "Ticket-Titel",
        "issuetype": {"id": "10046"},  # Suggestion
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Ziel"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Beschreibungstext"}]}
            ]
        }
    }
}

r = requests.post(url, json=issue, auth=auth, ...)
# passes json=issue → requests serializes it, description stays as nested dict
```

**❌ WRONG**: `json.dumps(adf_doc)` inside the issue dict — results in double-escaped string
**✅ CORRECT**: Pass the ADF doc as a raw Python dict inside the issue dict, let `requests.post(json=...)` handle serialization

### 5. Restart & Verify

⚠️ **`pct exec` blocks during `docker restart`** — run in background:
```bash
# In background (use separate terminal calls)
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10 "pct exec 107 -- docker restart mcphub"

# Wait for warmup
sleep 15

# Health check
curl -s http://10.0.60.170:3000/health
```

Expected health format:
```json
{"status":"degraded","message":"Some enabled MCP servers are not ready","servers":{"total":11,"connected":N,"disconnected":M}}
```

Erwartung: ~80% der Server sollten connected sein. Die Logs geben den Rest:

```bash
pct exec 107 -- docker logs mcphub --tail 30 2>&1 | grep -E "Success|Error" | tail -20
```

## Auth-Config

- **OAuth deaktiviert**: `"oauthServer": {"enabled": false}`
- **Bearer Key**: `mcphub-goetschi-2026-open` (generischer Key für alle Agenten)
- **Kein Admin/User**: `"users": []` — kein Login für WebUI nötig
- **API-Zugriff für Agenten**: `Authorization: Bearer mcphub...`
- **PRINZIP**: Credentials hardcoded in MCP-Scripts — Agenten brauchen KEINE separaten Token

## Volumes & Config Persistence (NAGELSICHER — Updated 07.06.2026)

The MCPHub Docker container mounts **multiple host volumes** for persistence across restarts:

### Host Directory Structure (inside LXC 107)

```text
/opt/mcphub/
├── mcp_settings.json     # Config (mounted RW on host)
├── scripts/              # All Python MCP scripts (volume mount /root/mcp-servers/)
│   ├── goetschi-github.py           # NEU (15.06) — GitHub API
│   ├── goetschi-google-workspace.py
│   ├── goetschi-home-assistant.py
│   ├── goetschi-jira-confluence.py
│   ├── goetschi-qdrant.py
│   ├── goetschi-proxmox.py
│   ├── goetschi-paperless.py
│   ├── goetschi-asterisk-ari.py
│   ├── goetschi-postgres-pgvector.py
│   ├── goetschi-unifi.py
│   ├── goetschi-minio.py
│   └── (notion via npx, no script needed)
├── token/                # OAuth tokens (mounted /data/)
│   └── token.json        # Google OAuth refresh token
└── data/                 # Other persistent data
```

Aktueller Inventarstand: `references/mcp-inventory.md`
```

### Container Mounts (RW)

When creating the container, mount all three volumes RW so changes persist:

```bash
docker run -d --name mcphub --restart unless-stopped -p 3000:3000 \
  -v /opt/mcphub/mcp_settings.json:/app/mcp_settings.json:rw \
  -v /opt/mcphub/scripts/:/root/mcp-servers/:rw \
  -v /opt/mcphub/token/:/data/:rw \
  samanhappy/mcphub:latest
```

**THIS IS THE CORRECT PATTERN.** Never rely on scripts being inside the container image — they reset on restart.

### Full Setup (from scratch)

```bash
# 1. Create directory structure on host (inside LXC 107)
mkdir -p /opt/mcphub/scripts /opt/mcphub/token /opt/mcphub/data
chmod 755 /opt/mcphub/scripts /opt/mcphub/token /opt/mcphub/data

# 2. Write mcp_settings.json to /opt/mcphub/mcp_settings.json

# 3. Copy all MCP scripts to /opt/mcphub/scripts/

# 4. Place tokens (e.g., google token) in /opt/mcphub/token/

# 5. Stop old container
docker rm -f mcphub

# 6. Start new container with volumes
docker run -d --name mcphub --restart unless-stopped -p 3000:3000 \
  -v /opt/mcphub/mcp_settings.json:/app/mcp_settings.json:rw \
  -v /opt/mcphub/scripts/:/root/mcp-servers/:rw \
  -v /opt/mcphub/token/:/data/:rw \
  samanhappy/mcphub:latest

# 7. Install Python packages
docker exec mcphub pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests atlassian-python-api

# 8. Restart to pick up packages (packages are ephemeral — see caveat below)
docker restart mcphub
```

### Deploying New Scripts (after container is running)

Scripts go in `/opt/mcphub/scripts/` on the host (inside LXC 107):

```bash
# From pve01: copy script to host
cp /tmp/goetschi-xxx.py /opt/mcphub/scripts/

# The volume mount makes it immediately available in the container
# No restart needed unless you changed mcp_settings.json
```

### Updating OAuth Tokens (e.g., Google)

```bash
# Place token in host volume
echo '<BASE64_TOKEN>' | base64 -d > /opt/mcphub/token/token.json

# Verify
docker exec mcphub python3 -c "import json; tok=json.load(open('/data/token.json')); print('OK:', bool(tok.get('refresh_token')))"
```

### The OLD pattern (DO NOT USE)

```bash
# ❌ These do NOT persist across restart:
docker cp script.py mcphub:/root/mcp-servers/   # Lost on restart
docker exec mcphub python3 -c "..." > /app/mcp_settings.json  # Also lost on restart
pip install ...  # Lost on restart (unless in custom image)
```

## External Python Packages in MCPHub Container

**UPDATE**: The MCPHub container (`samanhappy/mcphub:latest`) has **pip available**. Install packages:
```bash
pct exec 107 -- docker exec mcphub pip install google-auth google-api-python-client google-auth-oauthlib
```

**CAVEAT**: Packages installed via `pip` are **ephemeral** — they reset on `docker restart`. After restart:
```bash
pct exec 107 -- docker exec mcphub pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests atlassian-python-api
```

## MCP Server Architecture: Fault-Tolerance Pattern

**CRITICAL rule**: MCP servers must NEVER crash or `sys.exit(1)` on API failures. Otherwise they disconnect from MCPHub and stay disconnected until restart.

### Pattern: tools/list always works

```python
def handle_request(req):
    if method == "tools/list":
        # Return tools REGARDLESS of API availability
        return {"jsonrpc":"2.0","id":rid,"result":{"tools":[...]}}
    elif method == "tools/call":
        try:
            # API call might fail
            result = api_call(params)
            return {"jsonrpc":"2.0","id":rid,"result":{...}}
        except Exception as e:
            # Return error, NEVER crash
            return {"jsonrpc":"2.0","id":rid,"error":{"code":-32000,"message":str(e)}}
```

### Pattern: Single-pass JSON-RPC loop (simpler than content-length parsing)

MCPHub sends one JSON-RPC request per line. You can use a **simple newline-separated loop** instead of Content-Length parsing:

```python
def handle_request(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})
    
    if method == "tools/list":
        return {"jsonrpc":"2.0","id":rid,"result":{"tools":[...]}}
    elif method == "tools/call":
        # handle tool call
        ...
    elif method == "initialize":
        return {"jsonrpc":"2.0","id":rid,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"goetschi-xxx","version":"1.0.0"}}}
    elif method in ("notifications/initialized",):
        return None  # No response needed for notifications
    elif method == "resources/list":
        return {"jsonrpc":"2.0","id":rid,"result":{"resources":[]}}
    return {"jsonrpc":"2.0","id":rid,"error":{"code":-32601,"message":f"Unknown method: {method}"}}

for line in sys.stdin:
    for p in line.strip().split("\n"):
        p = p.strip()
        if not p: continue
        try:
            req = json.loads(p)
            resp = handle_request(req)
            if resp:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
```

### Pattern: Env-var credentials (for MCPs without OAuth)

Set credentials in mcp_settings.json under `env` key; the MCPHub injects them as environment variables:

```json
{
  "mcpServers": {
    "my-service": {
      "description": "...",
      "transport": "stdio",
      "command": "/usr/bin/python3",
      "args": ["/root/mcp-servers/goetschi-xxx.py"],
      "env": {
        "API_URL": "http://10.0.60.xxx:port",
        "API_KEY": "secret-key-here",
        "API_USER": "username",
        "API_PASS": "password"
      },
      "enabled": true
    }
  }
}
```

In the script:
```python
import os
API_URL = os.environ.get("API_URL", "")
API_KEY = os.environ.get("API_KEY", "")
```

This avoids hardcoding secrets in the Python script.

## Template: Service-Typen

### REST API (urllib)
```python
req = urllib.request.Request(f"{URL}/api/endpoint")
req.add_header("Authorization", f"Bearer {TOKEN}")
resp = urllib.request.urlopen(req, context=ssl._create_unverified_context())
data = json.load(resp)
```

### subprocess + CLI (mc, psql)
```python
result = subprocess.run(["mc", "ls", "alias/"], capture_output=True, text=True, timeout=10)
lines = result.stdout.strip().split("\n")
```

### SSH Gateway (für nicht direkt erreichbare Hosts)
```python
result = subprocess.run([
    "sshpass", "-p", SSH_PASS, "ssh", "-o", "StrictHostKeyChecking=no",
    f"{SSH_USER}@{SSH_GATEWAY}",
    f"pct exec 105 -- psql -h localhost -U postgres -d nei -c \"SELECT ...\""
], capture_output=True, text=True, timeout=15)
```

## See Also
- `references/goetschi-mcp-inventory.md` — Alle 12 MCP-Server im Detail (live/in Arbeit/Tokens), Stand: 07.06.2026 (goetschi-gmail deployed)
- `references/paperless-nextcloud-architektur.md` — Paperless ↔ Nextcloud auf CasaOS Design
- `atlassian-jira-confluence` skill → `references/google-mcp-oauth.md` — Google OAuth Troubleshooting

1. **protocolVersion muss `"2024-11-05"` sein** — NICHTS ANDERES! Teste mit `docker exec mcphub grep "protocolVersion" /root/mcp-servers/xxx.py` nach jedem Fix
2. **pct push deployt nur ins LXC**, nicht in den Docker Container — man muss `docker exec -i mcphub cat > file` pipen
3. **Syntax-Check**: `docker exec mcphub python3 -c "compile(open('/root/mcp-servers/xxx.py').read(),'xxx','exec')"` — sonst silent fail
4. **Connection closed** Fehler: meist protocolVersion oder Syntax-Error im Script
5. **Timeout errors**: Script blockt in initialize (z.B. Token-Check). Initialize muss SOFORT antworten
6. **MCPHub Docker: keine externen Python-Pakete** — reines stdlib!
7. **env vars in mcp_settings.json** sind der einzige Weg Credentials zu setzen (kein .env im Container)
8. **subprocess SSH**: sshpass Pattern für Gateway-Zugriff (z.B. PostgreSQL auf CT105)
9. **Config Volume mount needs host file**: If `/opt/mcphub/mcp_settings.json` doesn't exist on host, container uses in-image defaults from `samanhappy/mcphub:latest`. Always save config to host mount path before restarting (`cp /tmp/mcp_settings.json /opt/mcphub/mcp_settings.json`).
10. **Docker restart via pct exec blocks**: The `docker restart` command holds the SSH session. Use terminal(background=true) + sleep + health check in separate calls. Don't chain with `&` in foreground mode.\n11. **Host volume mcp_settings.json changes DO NOT survive restart**: The container's `/app/mcp_settings.json` volume mount appears to load the host file only at creation time (`docker run`). Editing `/opt/mcphub/mcp_settings.json` on the host and doing `docker restart mcphub` may NOT pick up changes. **Fix**: Always patch `mcp_settings.json` directly inside the container via `pct exec 107 -- docker exec -i mcphub python3` (see "mcp_settings.json patchen" section). Or delete + recreate the container with fresh volumes.\n12. **Script auf Host-Pfad copy reicht nicht immer**: Docker-Volume-Sync via LXC kann stale sein. Nach `cp /tmp/goetschi-xxx.py /opt/mcphub/scripts/` muss verifiziert werden dass der Container die Datei sieht. Wenn nicht → pipe direkt per `docker exec -i mcphub bash -c 'cat > /root/mcp-servers/goetschi-xxx.py' < /tmp/goetschi-xxx.py`."
11. **Google MCP needs pip packages**: `google-auth`, `google-api-python-client`, `google-auth-oauthlib` must be pip installed. Packages are ephemeral — reset on `docker restart`. Either reinstall after restart, or build a custom Docker image.
12. **Architecture: ALL MCPs on MCPHub, always**: N8N and all other agents connect via MCPHub API, not directly to services. Never deploy a separate MCP container or give N8N direct OAuth access. The MCPHub is the single Source of Truth.
13. **Google Workspace MCP v2 (07.06.2026)**: Unified Gmail (6), Calendar (2), Drive (1), Sheets (2), Docs (1) — 12 tools in one server. Replaced the old google-workspace (5 tools) + goetschi-gmail (6 tools) split. Token in `/data/token.json`.
14. **npx path mismatch**: Notion MCP uses `npx` which lives at `/usr/bin/npx` in the MCPHub container, but `mcp_settings.json` often defaults to `/usr/local/bin/npx`. Fix: `sed -i 's|/usr/local/bin/npx|/usr/bin/npx|' /app/mcp_settings.json`
15. **MCPHub sends `initialize` before script is ready (race condition)**: stdio MCP servers with heavy top-level imports ... See `references/fast-startup-mcp-pattern.md`.
16. **Nach Deploy: immer einen read-only API-Call testen**: Nur weil `initialize` und `tols/list` antworten, heisst das nicht dass der Token gültig ist. Nach dem Deploy **immer** einen echten `tols/call` testen (z.B. `github_list_repos`) um 401/403 zu erkennen. MCPHub Health zeigt "connected" auch wenn jeder API-Call fehlschlägt.
17. **Disconnected MCP debugging workflow (3-step)**: Step 1: `curl -s .../health` -- note which servers are disconnected. Step 2: `docker logs mcphub 2>&1 | grep -B1 -A5 'ERROR.*serverName'` -- find failing server + see if there's a `[child] Traceback`. Step 3: Direct test in container -- `docker exec -i mcphub timeout 5 python3 /root/mcp-servers/goetschi-xxx.py <<< '{"jsonrpc":"2.0","id":1,"method":"initialize","params":...}'` -- if this works but MCPHub connection fails, it's a race condition (use fast-startup). If it fails, the error message is the root cause.
17. **`env` vars in mcp_settings.json are NOT passed to child processes in samanhappy/mcphub:latest**: Despite `env` being a documented field in the MCPHub config schema, this container version does NOT inject environment variables into child processes. The script will see `os.environ.get("FOO")` as `None`. **Fix**: hardcode credentials directly in the Python script (like all other Goetschi Labs MCPs do). The "Env-var credentials" pattern under ## MCP Server Architecture below is aspirational -- it does not work on this MCPHub version. Use hardcoded strings in the script instead.
19. **Jira API migration (June 2026)**: `/rest/api/3/search` returns HTTP 410: `The requested API has been removed. Please migrate to the /rest/api/3/search/jql API`. New endpoint: `/rest/api/3/search/jql?jql={encoded_jql}&maxResults={N}`. Same response schema (json with `issues[]`, `total`, etc.) -- only the URL path changes. If a Jira MCP server uses `search` instead of `search/jql`, it will get 410 on every tools/call for jira_search_issues.
20. **`notifications/initialized` returning errors is NORMAL** — After `initialize`, MCPHub sends `notifications/initialized`. This is a **notification** (no response expected). Some servers return `{"error": {"code": -32601, "message": "Method not found"}}` which is **harmless** — MCPHub only tracks connection state, not per-method errors. If `tools/list` succeeds, the server is connected. Do NOT patch the server to handle this notification.
21. **mcp-remote OAuth für Atlassian MCP** — Der offizielle Atlassian MCP Server erfordert einen **einmaligen OAuth 3LO Flow im Browser**. `mcp-remote --token` funktioniert nicht (wird ignoriert). Nach Autorisierung cached `mcp-remote` die Session in `~/.mcp-remote/locks/`. Bei Container-Neubau muss OAuth wiederholt werden. Alternativ: Python stdio-to-HTTP Proxy mit API-Token (headless).

## Architecture Principle: MCPHub = Source of Truth

**CRITICAL RULE for Goetschi Labs:** ALLE MCPs gehören auf den MCPHub (CT107:3000).  
N8N, Hermes, Nova und alle anderen Agenten **verbinden sich via MCPHub-API**, nicht via Direktzugriff auf Credentials/OAuth-Tokens.

- ❌ MCP auf separatem Container launch-en
- ❌ N8N direkt mit Google OAuth verbinden
- ✅ MCP auf MCPHub deployen, N8N greift via MCPHub API zu
- ✅ Ein MCP pro Service-Typ (z.B. ein Google MCP für Gmail+Calendar+Drive+Docs+Sheets)

## Pip Packages im MCPHub Container

**UPDATE**: `pip` ist verfügbar, aber **alle installierten Pakete gehen bei `docker restart` verloren** (ephemeral Container-Filesystem).

Aktuell benötigte Pakete für den Google Workspace MCP:
```bash
pct exec 107 -- docker exec mcphub pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**Strategie:** Aktzeptieren Sie, dass nach jedem `docker restart` pip installs nötig sind.  
Oder: Ein benutzerdefiniertes Docker-Image bauen das die Pakete vorinstalliert hat.

## Atlassian Official MCP Server (mcp-remote proxy)

Der offizielle Atlassian Rovo MCP Server (GitHub: atlassian/atlassian-mcp-server) ist ein **remote HTTP/SSE MCP** (Cloud-basiert, kein stdio). Lokale stdio-Clients (wie MCPHub) brauchen den **`mcp-remote` Proxy** von Atlassian als Brücke.

### Architektur

```
MCPHub (TCP/3000)  ←stdio→  mcp-remote (localhost)  ←OAuth+HTTPS→  https://mcp.atlassian.com/v1/mcp (Cloud)
```

### Ersteinrichtung (OAuth 3LO — 1x im Browser)

Beim ersten Start generiert `mcp-remote` eine **OAuth Authorize-URL**. Diese muss **einmalig im Browser** geöffnet werden, um die App zu autorisieren:

```bash
# Erster Start — OAuth wird angefordert
npx -y mcp-remote https://mcp.atlassian.com/v1/mcp

# Ausgabe: "Please authorize this client by visiting:"
# https://mcp.atlassian.com/v1/authorize?response_type=code&client_id=ouxR6Cz_...
```

Nach der Autorisierung speichert `mcp-remote` die Session in einer **Lockfile** (`~/.mcp-remote/locks/`). Danach läuft der Proxy **ohne Browser-Interaktion**.

### MCPHub Konfiguration

Da MCPHub stdio-Transport erwartet, wird `mcp-remote` als **Befehlszeile** eingetragen:

```json
{
  "mcpServers": {
    "atlassian": {
      "description": "Offizieller Atlassian MCP — Jira + Confluence + mehr",
      "transport": "stdio",
      "command": "/usr/bin/npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.atlassian.com/v1/mcp"
      ],
      "enabled": true
    }
  }
}
```

**⚠️ WICHTIG:** Der Token wird NICHT via `--token` an `mcp-remote` übergeben, da die aktuelle Version den Token ignoriert und immer 3LO OAuth verlangt. Stattdessen muss `mcp-remote` **einmalig auf einem Rechner mit Browser** autorisiert werden, dann die Lockfile auf den MCPHub-Container kopieren. ODER: Den Browser-Link vom Container-Log auf deinem Gerät öffnen.

### API-Token-Alternative

Laut Atlassian README kann man auch einen **API-Token** für Headless-Auth verwenden. Die `--token` Flag existiert, aber in der aktuellen `mcp-remote` Version (github: atlassian/atlassian-mcp-server) wird sie gegen OAuth ausgetauscht. API-Token brauchen Jira-Berechtigung (nicht nur Confluence).

### Nach der Autorisierung

Nach einmaliger OAuth-Autorisierung bleibt der Refresh-Token in der Lockfile erhalten (~/.mcp-remote/locks/). Der Proxy kann dann **ohne Browser** neu gestartet werden. Die Lockfile ist persistiert über Docker-Container-Neustarts hinweg — sie liegt im Home-Verzeichnis des Containers.

### Tools

Der offizielle Atlassian MCP bietet mehr Tools als ein selbstgebautes Jira-Python-Skript:
- Jira: Issue CRUD, Suchen, Übergänge, Epics, Sprints
- Confluence: Seiten lesen/suchen/erstellen/bearbeiten
- Compass: Komponenten-Management
- Automatische OAuth-Integration mit Scope-Management

## Credential Update Workflow (Hardcoded-Pattern)

If credentials change in an existing hardcoded MCP script, use this reliable multi-step approach:

### Short Tokens (< 50 chars, e.g. passwords, API keys)

```bash
# Direct sed works for short values without special chars
pct exec 107 -- docker exec mcphub sed -i 's|ARI_PASS = "HermesVB2026"|ARI_PASS = "NEW_PASS"|' /root/mcp-servers/goetschi-asterisk-ari.py
```

### Long Tokens (> 50 chars, e.g. JWTs, OAuth tokens)

**Problem**: All Hermes tools (`write_file`, `patch`, base64 encoding) truncate strings > ~100 characters silently. A 183-char JWT becomes 25 chars.

**Solution**: Write a fix script to a temp file on the Proxmox host (not through truncated channels), then execute it on the container:

```bash
# Step 1: Write fix as a script file on the Proxmox host via pve01
# Use a HERE document that SSH handles properly
sshpass -p "${PM_PASS}" ssh root@10.0.60.10 bash << 'FIXEOF'
# Write fix script directly inside the Docker container
pct exec 107 -- docker exec -i mcphub bash << 'DINNER'
cat > /tmp/fix_token.py << 'PYEOF'
import sys
# Use hex pattern for precision — find the corrupted line
# HA_TOKEN="old truncated value"
old_hex = "48415f544f4b454e0a"  # "HA_TOKEN\n" in hex — find your own with: python3 -c "print('HA_TOKEN'.encode().hex())"
old_bytes = bytes.fromhex(old_hex)

# Read what's currently at that location to find exact bytes to replace
with open("/root/mcp-servers/goetschi-xxx.py", "rb") as f:
    raw = f.read()

idx = raw.find(old_bytes)
if idx < 0:
    print("ERROR: pattern not found")
    sys.exit(1)
    
# Find end of current line
nl = raw.find(b"\n", idx)
current = raw[idx:nl]
print(f"Current: {current}")

# Build new line
jwt = "PART1" + "PART2"  # Manually concatenate both parts
new_line = f'HA_TOKEN="{jwt}"'.encode()

# Replace
new_raw = raw[:idx] + new_line + raw[nl+1:]  # skip old line + newline
with open("/root/mcp-servers/goetschi-xxx.py", "wb") as f:
    f.write(new_raw)

# Verify
with open("/root/mcp-servers/goetschi-xxx.py", "rb") as f:
    new_raw = f.read()
idx = new_raw.find(b"HA_TOKEN")
nl = new_raw.find(b"\n", idx)
result = new_raw[idx:nl]
print(f"Result: {result}")
print(f"Length: {len(result)}")
PYEOF
python3 /tmp/fix_token.py
DINNER
FIXEOF
```

**Alternative (even more reliable)**: Directly on the CT107, write the JWT in two parts using `sed`:

```bash
# On pve01, get a shell inside the Docker container:
pct exec 107 -- docker exec -it mcphub bash

# Then paste the two parts and set them:
# Inside container:
sed -i 's/HA_TOKEN=.*/HA_TOKEN="PART1PART2"/' /root/mcp-servers/goetschi-home-assistant.py
# Where PART1 and PART2 are the two halves of the JWT pasted from the user's message
```

**Root cause**: The home_assistant profile's tool-level output wrapping silently truncates. Long strings in `execute_code` f-strings, `memory` entries over 2000 chars, and `write_file` content over ~200 chars are all affected. The fix always requires concatenation on the **target** machine, not in the agent's tool output.

## Pitfall: SSH Quoting Through Multiple Layers

Going through `sshpass` → `ssh` → `bash` → `pct exec` → `docker exec` → `python3 -c '...'` creates a **quoting nightmare**. Each layer strips one level of quotes.

### Reliable Pattern: Write to tmp first, then execute

```bash
# BAD — seven layers of quoting, breaks on any special char
sshpass -p "${PASS}" ssh root@10.0.60.10 "pct exec 107 -- docker exec mcphub python3 -c \"
import os
print(os.environ.get('HA_TOKEN'))
\""

# GOOD — write to temp file on target, then run it
sshpass -p "${PASS}" ssh root@10.0.60.10 bash << 'EOF'
pct exec 107 -- docker exec -i mcphub bash << 'DINNER'
cat > /tmp/fix_script.py << 'PYEOF'
import os
print(os.environ.get('HA_TOKEN', 'NOT SET'))
PYEOF
python3 /tmp/fix_script.py
DINNER
EOF
```

The `<< 'EOF'` (quoted heredoc) prevents local shell expansion. `cat > file << 'PYEOF'` inside the container writes clean Python code with single quotes intact.

### Best Pattern: Base64 for Complex Scripts

For scripts longer than a few lines or containing complex quoting:

```python
# Step 1: In execute_code, base64 encode the script
import base64
fix_script = r'''...complex python code...'''
b64 = base64.b64encode(fix_script.encode()).decode()

# Step 2: On the server, decode and write to file
# echo "<b64>" | base64 -d | pct exec 107 -- docker exec -i mcphub python3
```

But beware: the b64 string itself gets truncated if it's > 100 chars! Split into multiple echo lines.

### Don't Use: `python3 -c "..."` through multiple ssh layers

The combo of single quotes inside double quotes inside sshpass arguments breaks with any special character (`$`, `"`, `'`, `\`, `${}`).

## Pitfall: `notifications/initialized` returns `"Method not found"` — this is NORMAL

After `initialize`, MCPHub sends `notifications/initialized`. Some MCP servers (like the Atlassian HTTP proxy) return `{"error": {"code": -32601, "message": "Method not found"}}` for this notification.

**This is NOT a problem.** The server correctly processes the next JSON-RPC request (e.g., `tools/list`) despite the error. MCPHub only tracks connection state, not individual method errors. If tools/list succeeds, the server is connected.

**Do not patch the server to handle `notifications/initialized`** — it's a notification, and some servers legitimately don't implement it. The error is harmless.

## HTTP/SSE Remote MCP via Python stdio Proxy

When an MCP server is a **remote HTTP/SSE endpoint** (not stdio), deploy a **Python stdio-to-HTTP proxy** instead of using `mcp-remote` (which requires OAuth 3LO browser flow). This pattern works headlessly with API tokens.

### Architecture

```
MCPHub (TCP/3000)  ←stdio→  atlassian-proxy.py  ←HTTPS+API-Key→  https://mcp.atlassian.com/v1/mcp
```

### Key Implementation Details

```python
#!/usr/bin/env python3
"""MCP stdio-to-HTTP proxy — headless, with SSE session management"""
import sys, json, ssl, traceback
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_TOKEN="your-token"
ATLASSIAN_URL = "https://mcp.atlassian.com/v1/mcp"

class Proxy:
    def __init__(self):
        self.session_id = None

    def call_mcp(self, req_data):
        data = json.dumps(req_data).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...",  # REQUIRED — Cloudflare blocks Python/urllib
            "Authorization": f"Bearer {API_TOKEN}"
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        req = Request(ATLASSIAN_URL, data=data, headers=headers)
        try:
            resp = urlopen(req, timeout=30, context=ssl._create_unverified_context())
            raw = resp.read().decode()
            # CRITICAL: Capture session ID from response
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
            if sid:
                self.session_id = sid
            # Parse SSE messages
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    return json.loads(line[5:])
            return json.loads(raw) if raw else {}
        except HTTPError as e:
            err_body = e.read().decode()
            try: return json.loads(err_body)
            except: return {"error": f"HTTP {e.code}: {err_body[:200]}"}

    def main(self):
        while True:
            line = sys.stdin.readline()
            if not line: break
            line = line.strip()
            if not line: continue
            try:
                req = json.loads(line)
                resp = self.call_mcp(req)
                if resp:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                sys.stderr.flush()

if __name__ == "__main__":
    Proxy().main()
```

### CRITICAL Gotchas

1. **User-Agent MUST be browser-like** — `mcp.atlassian.com` is behind Cloudflare which blocks Python `urllib`'s default User-Agent (Error 1010: "browser signature banned"). Set a Chrome/Safari UA string.
2. **Accept header MUST include both** — `"Accept": "application/json, text/event-stream"`. Without `text/event-stream`, the server returns HTTP 406 "Not Acceptable".
3. **SSE sessions are stateful** — After `initialize`, the server returns a `Mcp-Session-Id` header. All subsequent requests MUST include this header, or the server returns `"Request must be an initialize request if no session ID is provided."`.
4. **No OAuth needed if API token works** — The Atlassian MCP accepts the API token as Bearer token in the Authorization header. This works headlessly without the `mcp-remote` OAuth 3LO browser flow.
5. **Everything via stdin/stdout** — The proxy speaks line-delimited JSON-RPC on stdin/stdout (same as any stdio MCP server). No Content-Length parsing needed — MCPHub sends one JSON per line.

### vs. `mcp-remote` (Atlassian's official proxy)

`mcp-remote` is an alternative approach but has these drawbacks:
- **Requires OAuth 3LO in browser** on first run — impossible in headless Docker
- `--token` flag is **ignored** by current version — always falls back to browser-based OAuth
- **Lockfile-based** state persists in `~/.mcp-remote/locks/`
- **Browser needed** on a machine that can reach the Docker container's callback port (localhost:3736)
- **Node v20+ required** — v18 crashes with `ReferenceError: File is not defined`

Use the Python proxy approach when you have an API token; use `mcp-remote` only when OAuth is strictly required and you can complete the browser flow.

## See Also
- `references/goetschi-mcp-inventory.md` — Inventory aller 11 MCP-Server (Stand 08.06.2026)
- `references/google-workspace-mcp-v2.md` — Google Workspace MCP v2 mit 12 Tools
- `references/paperless-nextcloud-architektur.md` — Paperless ↔ Nextcloud + CasaOS Design
- `references/atlassian-http-mcp-proxy.md` — Reference for the Atlassian HTTP MCP proxy deployment
- `references/vaultwarden-credential-mcp.md` — Vaultwarden Passwort-Manager auf Dokploy-Host, MCP-Integration für Credential-Abfrage durch Agenten, Deployment-Anleitung
- `references/github-mcp-deployment.md` — GitHub MCP Server mit 7 Tools (Repos, PRs, Issues), Deployment + Token-Update

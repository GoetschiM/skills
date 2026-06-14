# MCPHub LXC 107 — Deployment & Config

## Überblick

MCPHub lauft als **Docker-Container** uf LXC 107 (10.0.60.170:3000).

- **Zugriff Proxmox Host:** `root@10.0.60.10` / Riotstar_PROXMOX_13
- **LXC Attach:** `ssh proxmox-host; lxc-attach -n 107 -- bash`
- **Docker Container:** `mcphub` (Node.js App)
- **Config:** `/opt/mcphub/mcp_settings.json` — mountet as `:ro` (read-only)
- **Health:** `curl http://10.0.60.170:3000/health`

## Config Update

```bash
lxc-attach -n 107 -- bash -c 'python3 << "PYEOF"
import json
with open("/opt/mcphub/mcp_settings.json") as f:
    c = json.load(f)

# MCP registriere
c["mcpServers"]["my-mcp"] = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "mcp-my-package"],
    "env": {"API_KEY": "..."},
    "enabled": true
}

with open("/opt/mcphub/mcp_settings.json", "w") as f:
    json.dump(c, f, indent=2)
PYEOF'

# Container neustarte (Config :ro)
docker restart mcphub
sleep 3
curl -s http://localhost:3000/health
```

## Fehlerbehebig

### MCP mit Node wird disconnected
Zod v4 Inkompatibilität: mcp-all-inkl@1.0.6 sendet kei `protocolVersion` im Initialize Response. Workaround: Python mcp-proxy starte.

### dpkg/apt kaputt
```bash
kill <PID>
dpkg --configure -a
apt-get install --fix-broken -y
```

### Node + npm fehlt
```bash
apt-get install -y nodejs npm
# Node 18.19.1 + npm 9.2.0
```

### Token gänderet
bearerKeys us Config: `cat /opt/mcphub/mcp_settings.json | python3 -c "import sys,json; print(json.load(sys.stdin).get('bearerKeys',[]))"`
Neustarte nach Änderig: `docker restart mcphub`

## Tools Übersicht (aktuell 12 MCPs)

Grund-Funktionsprüefig:
```bash
ssh proxmox-host "lxc-attach -n 107 -- docker logs mcphub --tail 50 2>&1 | grep -i 'error\|disconnect\|timeout' | tail -10"
```

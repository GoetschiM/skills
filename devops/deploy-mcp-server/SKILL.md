---
name: deploy-mcp-server
description: "Deploy MCP servers that ANY agent can use. Covers mcp-proxy (Python) for wrapping stdio MCPs as HTTP/SSE servers, Docker-based deployment, MCPHub integration, systemd services, and SDK incompatibility fixes. NOT about the Hermes Native MCP client itself."
version: 1.0.0
author: Hermes Agent
category: devops
tags: [mcp, deployment, mcphub, docker, systemd]
---

# Deploy MCP Server — für alli Agents

## Wenn du das bruchsch

Wen de **Hermes Native MCP client** nöd uf de Gateway konfiguriert werde cha (z.B. usserhalb vom Hermes Container, für NOVA/ORION/MAGOS G., oder Gateway-Neustart isch verbote), aber du wetsch dass **alli Agents en MCP Server chönd benutze**.

## Drei Wege

| Weg | Koschte | Autonomii | Use Case |
|-----|---------|-----------|----------|
| **1. mcp-proxy** | Mittel | Voll | stdio-MCP als HTTP Server wrappe |
| **2. Docker** | Höch | Voll | Isoliert + autarch, für production |
| **3. MCPHub (npx)** | Tief | Mittel | Wenn Node uf MCPHub Host verfüegbar |

---

## Weg 1: mcp-proxy (Python) — stdio → HTTP

### Install

```bash
pip install mcp-proxy
# Version prüefe: mcp-proxy 0.12.0+ wird bruucht
mcp-proxy --version
```

### Syntax

```bash
# Richtig (mit -- Trenner)
mcp-proxy --port 3103 --host 0.0.0.0 \
  -e MY_API_KEY wert1 \
  -e ANOTHER_KEY wert2 \
  -- /path/to/mcp-server.py
```

**⚠️ Wichtig!** De `--` trennt mcp-proxy-Argumänt vom MCP-Command:
- `-e KEY VALUE` mit **Leerschlag** (nit mit `=`) — `-e KAS_LOGIN=wert` git **Error: expected 2 arguments**
- `--port` / `--host` VOR de `-e` Flags
- De Command (Python Script oder npx) ganz AM ENDI nach `--`

```bash
# ❌ FALSCH — env wird gar nöd a subprozess gä
VAR=wert mcp-proxy --port 3103 -- mcp-server
# -> de subprozess kriegt KEI Env. mcp-proxy isoliert d'Environments wie systemd!

# ❌ FALSCH - expected 2 arguments
mcp-proxy -e KAS_LOGIN=w019000a -- mcp-all-inkl

# ✅ RICHTIG
mcp-proxy --port 3103 --host 0.0.0.0 -e KAS_LOGIN w019000a -e KAS_PASSWORD "myPass" -- mcp-all-inkl
```

### Env-Vars überge — DRINGEND lese

mcp-proxy **reinigt** d'Environment für de Subprozess. D. h.:

1. **`-e KEY VALUE`** — einzige sichere Weg Custom Env z'überge. Mues mit **Leerschlag** (2 Argumente), nöd `KEY=VALUE`
2. **`--pass-environment`** — git ALLI aktuelli Env wiiter. Praktisch aber unsicher.
3. **Ohni `-e` und ohni `--pass-environment`** → de Subprozess kriegt **gar nüt**. Au nid was du VOR mcp-proxy setzsch (`VAR=x mcp-proxy` funktioniert NIT).
4. **`VAR=x mcp-proxy` vor mcp-proxy setzt d'Env für mcp-proxy SÄLBER, nöd für de Subprozess.** De Subprozess isch ene Child-Prozess.

**Pitfall (Sonderzeiche im Passwort):** Bi `$`, `%`, `^`, `!` d'Env in Doppelaafüerig oder mit Bash-Export setze:
```bash
# ✅ Richtig
mcp-proxy -e KAS_PASSWORD "My%Speci@l!Pass" -- mcp-server

# ✅ Alternativ: via export
export KAS_PASSWORD='My%Speci@l!Pass'
mcp-proxy --pass-environment -e KAS_PASSWORD "$KAS_PASSWORD" -- mcp-server
```

### Als systemd Service

```ini
[Unit]
Description=My MCP Server
After=network.target

[Service]
Type=simple
User=root
Environment=API_KEY=mysecret
ExecStart=/usr/local/bin/mcp-proxy --port 3103 --host 0.0.0.0 -e API_KEY mysecret -- /path/to/mcp-server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Pitfalls:**
- `Environment=` im systemd **vor** `ExecStart=` setze
- `Restart=always` isch **entscheidend** — MCP Server starte nöd immer bi erschte Mal
- `ExecStart=` richtig setze — nüt i `EnvironmentFile=` wo `$`-Expansion brucht

### Test

```bash
# SSE-Endpoint
curl -s http://localhost:3103/sse | head -5
# -> event: endpoint
# -> data: /messages/?session_id=...

# Tools liste (JSON-RPC)
curl -s -X POST "http://localhost:3103/messages/?session_id=test" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## Weg 2: Docker Container

De **sichersti und autonomischti Weg** — MCP Server als isolierte Docker Container.

### Dockerfile

```dockerfile
FROM node:22-alpine
RUN npm install -g mcp-all-inkl@1.0.6
ENV KAS_LOGIN=w019000a
ENV KAS_PASSWORD=dein_passwort
EXPOSE 3103
CMD ["mcp-all-inkl"]
```

### Bau + Start

```bash
docker build -t all-inkl-mcp .
docker run -d --name all-inkl-mcp -p 3103:3103 all-inkl-mcp
```

### MCP SDK Inkompatibilität fixe (Zod v4)

Wenn MCPHub de MCP nit verbinde chund (`ZodError: expected string, received undefined` i MCPHub Logs):

1. **Ursach:** MCPHub (samanhappy/mcphub:latest, SDK v1.29.0) brucht **Zod v4** — erwartet `protocolVersion` als **string** i de Initialize Response. Alt MCPs (wie mcp-all-inkl@1.0.6) hends nöd/gänderet.

2. **Diagnose:**
```bash
docker logs mcphub 2>&1 | grep -i "all-inkl\|error\|ZodError"
# -> "ZodError: expected string, received undefined" = SDK Inkompat
# -> "Request timed out" = MCP chunt gar nöd z'initialize (Connection/Timeout)
```

3. **Fix-Workflows:**

**Fix A — Docker-Weg (empfohle):**
Deploy de MCP als eigenständige Docker Container, registriere als URL-MCP im MCPHub:
```json
{
  "all-inkl": {
    "type": "url",
    "url": "http://HOST_IP:PORT"
  }
}
```
Vo Teil: MCPHub muss KEIN Subprozess starte — kei SDK-Inkompat.

**Fix B — mcp-proxy Zwüscheschicht:**
`mcp-proxy` (Python) als Wrapper bruche — es vermittlet zwüsche stdio MCP und MCPHub als HTTP-MCP:
```bash
# auf Host mit Python
pip install mcp-proxy
mcp-proxy --port 3103 --host 0.0.0.0 \
  -e KAS_LOGIN w019000a -e KAS_PASSWORD "meinPass" \
  /path/to/mcp-server.py

# Im MCPHub als URL-MCP
{"all-inkl": {"type": "url", "url": "http://HOST_IP:3103"}}
```

**Fix C — MCP Server direkt patche** (wenn Quellcode zugänglich):
De Initialize Response e `protocolVersion` zuefüege.

4. **Test nach Fix:**
```bash
# Check ob MCPHub de MCP verbunde het
curl -s http://MCPHUB_HOST:3000/health | python3 -c \
  "import sys,json; h=json.load(sys.stdin); print(f'Total: {h[\"servers\"][\"total\"]}, Connected: {h[\"servers\"][\"connected\"]}')"
```

---

## Weg 3: MCPHub npx-Subprozess

Wen de MCPHub-Host **Node 18+ mit npx** het (und's apt-System intakt isch):

```json
{
  "mcpServers": {
    "all-inkl": {
      "type": "stdio",
      "command": "mcp-all-inkl",
      "args": [],
      "env": {
        "KAS_LOGIN": "w019000a",
        "KAS_PASSWORD": "dein_passwort"
      }
    }
  }
}
```

**⚠️ Achtig SDK-Inkompatibilität:**
MCPHub (samanhappy/mcphub:latest) nutzt **Zod v4** -> erwartet `protocolVersion` als **string** i de Initialize Response. Enige MCP Server (wie mcp-all-inkl@1.0.6) schickeds nöd/wills falsch — Resultat: `ZodError: expected string, received undefined` und de MCP chunnt nid verbunde.

**Fix-Möglichkeite:**
1. **Docker-Weg** statt npx-Subprozess (Weg 2)
2. En **neueri Version** vom MCP Server installiere wo Zod v4 supportet
3. De MCP Server **selber patche** (Initialize Response `protocolVersion` setze)
4. **mcp-proxy** zwüsche MCPHub und MCP Server schalte (Weg 1 + Weg 3 kombiniere)

---

## Deploy-Checklist

- [ ] Welche Agents söls bruche? (Nur Hermes? NOVA? Alli?)
- [ ] Bruchts Node? (Ja → Docker. Nai → Python.)
- [ ] Het de Host Docker? (Proxmox 29.5.3 ✅)
- [ ] Wird de MCPHub neigstartet? (Verbotä → URL-MCP, erlaubt → stdio)
- [ ] SDK-Kompatibilität prüefe (Zod v3 vs v4)
- [ ] `mcp-proxy --help` für di aktuelli Syntax luege (ändert sich mit Version!)
- [ ] Service teste: `curl -s POST http://HOST:PORT/mcp -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`
- [ ] Systemd Restart-Policy: `Restart=always`

---

## Pitfalls (us Live-Deployments)

| Problem | Lösig |
|---------|-------|
| mcp-proxy: `expected 2 arguments` | `-e KEY VALUE` mit Leerschlag, nit `-e KEY=VALUE` |
| mcp-proxy: `Either command_or_url ... required` | `--` vergässe — de Command muess nach `--` cho |
| Environment nöd im Subprozess | `-e KEY VALUE` verwende, nöd `--pass-environment` |
| Systemd startet nöd | `Restart=always` + `Environment=` vor `ExecStart=` |
| Docker `bad substitution` | Single Quotes im heredoc `<< 'EOF'` |
| KAS SOAP Login failt | Endpoint isch `KasApi.php`, nöd `?wsdl` |
| Sonderzeiche ($, %, ^, !) expandiert | Single Quotes `'...'` oder Heredoc `<< 'EOF'` |
| MCPHub: `ZodError: expected string` | SDK-Inkompatibilität -> Docker-Weg oder Patch |

---

## References

- `references/ssh-escape-hell.md` — SSH-Escape-Patterns für Testing über Proxmox → LXC 107 (MCPHub)

- `devops/all-inkl` — All-Inkl MCP Server (nutzt Weg 3)
- `mcp/native-mcp` — Hermes Native MCP Client (nöd deploye, sondern benutze)
- `mcp/mcphub-gateway` — MCPHub Gateway Betrieb

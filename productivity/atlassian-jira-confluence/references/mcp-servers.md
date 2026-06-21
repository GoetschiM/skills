# MCP Server — Stdio-Strategie (07.06.2026)

## Warum keine npm/OpenAPI/SSE MCPs?

Alle öffentlichen MCP-Pakete für Goetschi Labs Services existieren **nicht auf npm**:
- `@kovi/mcp-confluence`, `@kovi/mcp-jira`, `@kovi/jira-mcp-server` → 404
- `qdrant-mcp`, `atlassian-mcp`, `@anthropic/workspace-mcp-server` → 404
- OpenAPI-MCPs (Home Assistant, Qdrant, Asterisk ARI) scheitern an `$ref`-Auflösung

**Lösung:** Eigene Python stdio-MCP-Server bauen. Reines stdlib, kein `pip install`.

## MCP Protocol Format (hand-crafted)

```python
import sys, json

def send_msg(msg: dict):
    data = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()

def read_msg() -> dict:
    line = sys.stdin.readline()
    if not line:
        return None
    if line.startswith("Content-Length:"):
        cl = int(line.split(":")[1].strip())
        sys.stdin.readline()  # empty line separator
        data = sys.stdin.buffer.read(cl).decode()
        return json.loads(data)
    return None
```

### Initialize Response (MUSS Version 2024-11-05 sein!)

**⚠️ WICHTIG (korrigiert 07.06.2026):** MCPHub v1.29.0 akzeptiert **nur** `protocolVersion: "2024-11-05"`. Nicht `"1.0.0"`, nicht `"0.1.0"`, nicht `"v1"`. Die offizielle Spec von Anthropic verwendet dieses Datum als Version.

```python
def handle_initialize(msg):
    return {
        "jsonrpc": "2.0",
        "id": msg["id"],
        "result": {
            "protocolVersion": "2024-11-05",       # NICHT 1.0.0!
            "serverInfo": {"name": "...", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }
    }
```

**Alte (falsche) Version:** `"1.0.0"` → MCPHub antwortet mit "Server's protocol version is not supported" oder connectet trotzdem aber zeigt keine Tools.

### Tool Definition Format

```python
TOOL_DEFINITIONS = [
    {
        "name": "tool_name",
        "description": "Tool description",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "..."
                }
            },
            "required": ["param1"]
        }
    }
]
```

### Tool Call Handler

```python
def handle_call_tool(msg):
    name = msg["params"]["name"]
    args = msg["params"]["arguments"]
    result = tool_functions[name](**args)
    send_msg({
        "jsonrpc": "2.0",
        "id": msg["id"],
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }
    })
```

## Deployed Servers (12 Stück auf CT107 - Stand 07.06.2026)

Alle auf CT107 im Docker Container unter `/root/mcp-servers/goetschi-*.py`.

### MCPHub Konfiguration

Im MCPHub-Format als `type: "stdio"`:

```json
{
  "mcpServers": {
    "service-name": {
      "type": "stdio",
      "command": "python3",
      "args": ["/root/mcp-servers/goetschi-<name>.py"],
      "env": { "ENV_VAR": "value" },
      "enabled": true
    }
  },
  "bearerKeys": ["hermes-artemis-master-2026"],
  "systemConfig": { "mcpRouter": {} }
}
```

### Service-Übersicht

| Config Key | Tools | Status 07.06 |
|---|---|---|
| `home-assistant` | 8 (lights, sensors, scenes) | ❌ Protocol mismatch |
| `jira-confluence` | 9 (Jira + Confluence) | ❌ Protocol mismatch |
| `qdrant` | 6 (search, scroll, count) | ✅ 6 Tools connected |
| `proxmox` | 7 (LXC ops, node status) | ❌ Protocol mismatch |
| `paperless` | 7 (docs, tags, correspondents) | ❌ Auth/Protocol |
| `asterisk-ari` | 7 (channels, endpoints, originate) | ❌ Protocol mismatch |
| `postgres-pgvector` | 7 (DBs, tables, vectors, query) | ✅ 7 Tools connected |
| `unifi` | 6 (devices, networks, health) | ❌ Protocol mismatch |
| `minio` | 6 (buckets, files, CRUD) | ✅ 6 Tools connected |
| `google-workspace` | 5 (email, calendar) | ❌ No token/Protocol |
| `goetschi-gmail` | 6 (gmail_search, get_message, list_labels, send, modify_labels, trash) | ✅ aktiv (enabled: false — nur via N8N) |
| `notion` (npx) | 22 | ✅ 22 Tools connected |

**Connected = 4 Server + Google Gmail (stdio), 52 Tools total.**

## Deployment in Docker Container

```bash
cat /root/mcp-servers/goetschi-home-assistant.py | \
  docker exec -i mcphub bash -c "cat > /root/mcp-servers/goetschi-home-assistant.py"
```

## Bekannte Probleme

### 1. Protocol Version 0.1.0
**Problem:** Einige Server senden `protocolVersion: "0.1.0"` → MCPHub erwartet `"1.0.0"`.
**Fix:** In `handle_initialize()` auf `"1.0.0"` ändern.

### 2. MCPHub Auth broken
- Login gibt "Internal server error" — bcrypt-Hash mismatch
- Bearer-Keys werden ignoriert — "No token, authorization denied"
- Config `oauthServer.enabled: false` hilft nicht
- **Verdacht:** Bug in MCPHub Auth-Logik

### 3. Connection closed (Prozess stirbt sofort)
Diagnose:
```bash
docker exec mcphub python3 /root/mcp-servers/goetschi-<name>.py <<< '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"1.0.0"}}'
```

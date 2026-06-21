# Fast-Startup MCP Pattern

Verhindert Race-Condition bei MCP-Servern mit schweren Imports.

## Problem

MCPHub schickt `initialize` sofort nach dem Spawn des child-Prozesses. Wenn der stdio MCP-Server erst `requests`, `hashlib`, `hmac`, `xml.etree.ElementTree` oder andere schwere Libraries importieren muss, bevor er in die stdin-readloop kommt, dauert das 500-1500ms. MCPHub schliesst die Verbindung nach ~1s Timeout → Server als "disconnected" markiert.

## Pattern

```python
#!/usr/bin/env python3
"""Fast-startup MCP — keine schweren Imports beim Start"""
import sys, json  # ONLY stdlib basics at module level

TOOLS_DATA = [
    # Tool definitions here — strings only, no API calls
]

def ok(rid, result):
    return {"jsonrpc":"2.0","result":result,"id":rid}

def _ensure_loaded():
    global _loaded, hashlib, hmac, ET, requests  # ← KRITISCH: global deklarieren!
    if _loaded:
        return
    import hashlib, hmac
    import xml.etree.ElementTree as ET
    import requests
    _loaded = True

_loaded = False  # module-level flag, updated by global declaration in function

def handle(req):
    rid, m, p = req.get("id"), req.get("method",""), req.get("params",{})
    if m == "initialize":
        # ANTWORTE SOFORT — keine API calls, keine schweren imports
        return ok(rid, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name":"goetschi-xxx","version":"1.0.0"},
            "capabilities": {"tools":{}}
        })
    elif m == "notifications/initialized":
        return None  # ← Ignorieren, kein response nötig
    elif m == "tools/list":
        _ensure_loaded()  # ← Jetzt erst imports laden
        return ok(rid, {"tools": TOOLS_DATA})
    elif m == "tools/call":
        _ensure_loaded()
        return handle_tool_call(rid, p.get("name",""), p.get("arguments",{}))
    ...

def main():
    while True:
        line = sys.stdin.readline()
        if not line: break
        line = line.strip()
        if not line: continue
        try: resp = handle(json.loads(line))
        except: continue
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
```

## Critical Details

### 1. `global` declarations MUST include ALL names assigned in the function

```python
def _ensure_loaded():
    global _loaded, hashlib, hmac, ET, requests, tooldata  # ALLES!
```

If `tooldata = TOOLS_DATA` appears in the function, `tooldata` must be in the `global` declaration. Otherwise Python creates a **local** `tooldata`, the module-level variable stays empty, and tools/list returns `[]`.

### 2. `initialize` must be IMPOSSIBLE to slow down

No imports, no API tests, no credential verification. Return the protocol version and capabilities dict **instantly**.

### 3. `notifications/initialized` returns `None` (no response)

Some MCP servers return errors for this notification. That's fine — MCPHub only cares about the `tools/list` response.

### 4. Differentiate from the HTTP proxy pattern

For **remote HTTP MCP servers** (like the Atlassian Rovo MCP), use the Python HTTP proxy pattern instead (see `atlassian-http-mcp-proxy.md`). The fast-startup pattern is for **stdio** MCP servers that happen to have heavy imports.

## Affected Servers

- MinIO MCP (goetschi-minio.py) — rewritten as minimal server (Jun 2026)
- UniFi MCP (goetschi-unifi.py) — also prone to race on first startup
- Any MCP using `requests`, `google-api-python-client`, or `xml.etree.ElementTree`

# Google MCP Server Architecture

## Overview

Reiner Starlette-HTTP-Server (KEIN FastMCP) — manuell JSON-RPC 2.0 Dispatch.
Läuft in Docker, Port 8002, single-process uvicorn.

```
client → curl/HTTP POST → Starlette Route("/mcp") → dispatch(method) → response
```

## Tool Registration Pattern

Tools sind als **Python-Funktionen** definiert, über e **Decorator** registriert:

### 1. TOOLS-Liste (für tools/list)

```python
TOOLS = []

def tool(name: str, description: str, input_schema: dict = None):
    """Decorator: registriert Tool in TOOLS-Liste"""
    def decorator(func):
        TOOLS.append(Tool(
            name=name,
            description=description,
            inputSchema=input_schema or {"type": "object", "properties": {}},
        ))
        return func
    return decorator

# Verwendung:
@tool("gmail_trash", "Verschiebe Mail in Papierkorb",
      {"type": "object", "properties": {
          "message_id": {"type": "string"}
      }, "required": ["message_id"]})
def gmail_trash(message_id: str) -> str:
    ...
```

**Wichtig:** Der `tool()`-Decorator MUSS direkt uf d'Funktion folge (nid überspringe).
D'Funktion wird trotzdem normal definiert — der Decorator git sie unveränderet zrugg.

### 2. TOOL_MAP-Dict (für tools/call)

```python
TOOL_MAP = {
    "google_auth_url": auth_url,
    "gmail_trash": gmail_trash,
    "gmail_modify": gmail_modify,
    ...
}
```

Wird im HTTP-Handler für s'Lookup bruucht: `TOOL_MAP[tool_name](**arguments)`.

### 3. HTTP-Handler (Kern-Logik)

```python
async def handle_mcp_post(request):
    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {})
    req_id = body.get("id", 1)

    if method == "tools/list":
        tools_list = [t.model_dump(by_alias=True, exclude_none=True) for t in TOOLS]
        return Response(json.dumps({"jsonrpc":"2.0","id":req_id,"result":{"tools":tools_list}}))

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = TOOL_MAP[tool_name](**arguments)
        except Exception as e:
            return Response(json.dumps({"jsonrpc":"2.0","id":req_id,
                "result":{"content":[{"type":"text","text":str(e)}],"isError":true}}))
        return Response(json.dumps({"jsonrpc":"2.0","id":req_id,
            "result":{"content":[{"type":"text","text":str(result)}]}}))
```

## OAuth PKCE Flow

**Zentrali Challenge:** De `google_auth_url` und `google_auth_exchange`-Tool müend  
**d'selbig** `InstalledAppFlow`-Instanz teile, will PKCE (seit 2024 Pflicht bi Google)
en zuefallige `code_verifier` pro Flow generiert.

### Lösung: Global State (Single-Process)

```python
_AUTH_FLOW = None  # Module-level variable

def auth_url():
    global _AUTH_FLOW
    _AUTH_FLOW = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    url, _ = _AUTH_FLOW.authorization_url(...)
    return url

def auth_exchange(code):
    global _AUTH_FLOW
    _AUTH_FLOW.fetch_token(code=code)
    _save_credentials(_AUTH_FLOW.credentials)
    _AUTH_FLOW = None
```

**Warum das funktioniert:** Uvicorn läuft defaultmässig mit 1 Worker in 1 Prozess.  
Alli HTTP-Requests gönnd durch de gliich Prozess → alli gsehnd di gliich global Variable.

**Bei Multi-Worker:** Müsst mer e Shared Storage (Redis, File) für de Flow-State bruuche.

## Server-Start

```python
app = Starlette(routes=[Route("/mcp", handle_mcp_post, methods=["POST"])])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
```

## Response-Format

Immer JSON-RPC 2.0:
- Erfolg: `{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"..."}]}}`
- Fehler: `{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"Error: ..."}],"isError":true}}`

## Key Constraints

- `Accept: application/json` Header isch PFLICHT (suscht 406)
- Kei Sessions, kei Caching, kei SSE — pure HTTP POST/JSON-RPC
- Tool-Funktione sind SYNCHRON (kei async) — Google API-Calls blockiere de Handler
- Gmail-Prefix: `gmail_*`, Calendar: `calendar_*`, Drive: `drive_*`, etc.
- `google_health` isch immer s'letschte Tool (alphabetisch)

# Google MCP Server — Deployment Reference

## MCP SDK Versions & API Surface

Built and tested with **MCP SDK 1.26.0 / 1.27.1**.

### FastMCP Constructor — Gotcha

**Do NOT pass `settings=` — pass everything as direct kwargs:**

```python
# WRONG — TypeError: unexpected keyword argument 'settings'
mcp = FastMCP("X", settings=Settings(host="0.0.0.0"))

# RIGHT — direct kwargs
mcp = FastMCP("X", host="0.0.0.0", port=8002, json_response=True)
```

Full FastMCP constructor signature (MCP SDK ≤1.27.x):

```python
FastMCP.__init__(
    name, instructions=None, website_url=None, icons=None,
    auth_server_provider=None, token_verifier=None, event_store=None,
    retry_interval=None, tools=None,
    debug=False, log_level='INFO',
    host='127.0.0.1', port=8000,
    mount_path='/', sse_path='/sse', message_path='/messages/',
    streamable_http_path='/mcp',
    json_response=False, stateless_http=False,
    warn_on_duplicate_resources=True, warn_on_duplicate_tools=True,
    warn_on_duplicate_prompts=True,
    dependencies=(), lifespan=None, auth=None,
    transport_security=None,
)
```

### Running the Server

Use `run_streamable_http_async()`, NOT `.run()`:

```python
import asyncio
asyncio.run(mcp.run_streamable_http_async())
```

The `.run()` method only accepts `transport` and `mount_path` — host/port are read from constructor kwargs. `run_http_async()` is also fine for SSE transport but StreamableHTTP is simpler for headless/stateless use.

### DNS Rebinding Protection (421 Error)

**Symptom:** curl returns HTTP 421 "Misdirected Request" with "Invalid Host header".
**Cause:** Default `transport_security` only allows `127.0.0.1`, `localhost`, `[::1]`.
**Fix:**
```python
FastMCP("X", host="0.0.0.0",
    transport_security={"enable_dns_rebinding_protection": False})
```

### Accept Header Requirement

Hermes StreamableHTTP client and even curl **must** send `Accept: application/json`. Without it:
```
{"error": {"code": -32600, "message": "Not Acceptable: Client must accept application/json"}}
```

Fix in Hermes config:
```yaml
mcp_servers:
  google:
    url: "http://10.0.60.121:8002/mcp"
    headers:
      Accept: "application/json"
```

### Stateless Mode Required

Set `stateless_http=True` to avoid session tracking issues:
```python
FastMCP("X", stateless_http=True, json_response=True)
```

Without it, Hermes' independent requests (no prior session init JSON-RPC call) get rejected with "Missing session ID".

## OAuth Token Exchange via MCP Tool

The OOB flow (`urn:ietf:wg:oauth:2.0:oob`) works well for headless servers:

```python
flow = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, SCOPES)
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
# → user visits auth_url on their own machine, gets code
flow.fetch_token(code=user_code)
_save_credentials(flow.credentials)
```

The user visits the auth URL on their own machine (same LAN), gets a code, sends it back. The server exchanges the code for tokens. This avoids needing a callback URL.

## Docker Deployment

### Build on target host (no registry needed — transfer source files)

```bash
# Transfer source to target
scp -r /tmp/google-mcp-server/ root@10.0.60.121:/opt/google-mcp-server/

# On the LXC:
docker build -t google-mcp-server:latest /opt/google-mcp-server/
```

### Run

```bash
docker run -d --restart unless-stopped \
  --name google-mcp-server \
  -p 8002:8002 \
  -v /data:/data \
  -e GOOGLE_CLIENT_SECRET=/data/client_secret.json \
  -e GOOGLE_TOKEN_FILE=/data/token.json \
  google-mcp-server:latest
```

On Prod LXC (10.0.60.121) the host path `/data` already exists (shared with other services). The client_secret.json must be copied in separately — it's not in the image.

### Building across LXC boundary (via Proxmox host)

When building on a LXC that isn't directly reachable:

1. `pct push <CT_ID> <source> <dest>` — copy source files into the LXC
2. `pct exec <CT_ID> -- docker build ...` — build inside LXC
3. If source files are on Proxmox host, first copy via Proxmox tools

### Client secret placement

The Google Cloud Console **client_secret.json** must be placed on the Docker volume BEFORE starting the container. It is NOT included in the image (security). The server checks for it on startup and returns a clear error if missing.

## Token Lifecycle

Stored in `/data/token.json` on Docker volume. Auto-refreshed by `google-auth` library when expired:

```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    _save_credentials(creds)
```

The refresh-token was obtained by passing `access_type="offline"` and `prompt="consent"` during the initial auth. If a re-auth is ever needed:

1. Call `google_auth_url()` server tool → user visits link → gets code
2. Call `google_auth_exchange(code="4/xxx...")` → server exchanges code and stores new token

## Health Check

```bash
# Quick health endpoint (GET /health)
curl -s http://10.0.60.121:8002/health
# Response: {"status": "ok", "version": "1.0.0", ...}

# Tool discovery check
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq '.result.tools | length'
# Expect: 14

# Auth status check
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_auth_status","arguments":{}}}'

# Gmail test
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gmail_search","arguments":{"query":"is:unread","max_results":3}}}' \
  | jq '.result.content[0].text'
```

# Atlassian HTTP MCP Proxy Deployment

Deployed 08.06.2026 — Python stdio-to-HTTP proxy for the official Atlassian Rovo MCP Server.

## Architecture

```
MCPHub (CT107:3000)  ←stdio→  atlassian-proxy.py  ←HTTPS+API-Key→  https://mcp.atlassian.com/v1/mcp
```

## Deployment Details

### File Location

- Container: `/root/mcp-servers/atlassian-proxy.py` (inside `mcphub` Docker on CT107)
- mcp_settings.json entry under `mcpServers.atlassian`
- Config: `command: /usr/bin/python3`, `args: [/root/mcp-servers/atlassian-proxy.py]`, `transport: stdio`

### Auth Mechanism

**API Token** (not OAuth!) passed as Bearer token in Authorization header. This bypasses the need for `mcp-remote` OAuth 3LO flow.

Token: The Atlassian API token set during this session. Requires Jira permissions.

### Critical Implementation Details

1. **User-Agent required**: Cloudflare (mcp.atlassian.com) blocks Python/urllib default UA. Must set a Chrome browser UA string.

2. **Accept header**: Must include BOTH `application/json` AND `text/event-stream` — otherwise HTTP 406.

3. **SSE Session management**: `initialize` returns a `Mcp-Session-Id` response header. This must be captured and sent back on ALL subsequent requests (as `Mcp-Session-Id` request header). Without it, each request after initialize fails with `"Request must be an initialize request if no session ID is provided."`

4. **notifications/initialized fails silently**: The server returns `{"error": {"code": -32601, "message": "Method not found"}}` for this notification. This is harmless — the server still processes the next request correctly. MCPHub only tracks connection state, not per-method errors.

5. **Tools available** (as of June 2026):
   - `getTeamworkGraphContext` — Fetch connected context/relationships for Atlassian entities (issues, pages, users, teams, PRs, etc.)
   - `getTeamworkGraphObject` — Get full details for objects by ARI or URL

   Note: These are **Rovo Teamwork Graph** tools, not CRUD tools for issues/pages. For CRUD operations, use the separate `jira-confluence` MCP (self-built).

6. **Env Vars from `command` ARE passed**: Unlike the `env` key in `mcp_settings.json` (which the current MCPHub version does NOT pass to child processes), when the server is configured as `command: /usr/bin/python3` + `args: [...]`, the script inherits the container's full environment. This confirms the bug is specifically in the `env` key passthrough, not in general environment inheritance. **Recommendation**: Continue hardcoding tokens in scripts.

7. **Transport: line-delimited JSON, not Content-Length**: MCPHub sends JSON-RPC requests to a stdio server using the official Content-Length line protocol internally, but when piped through `docker exec -i container python3 proxy.py`, the pipe delivers one complete JSON message per `readline()`. The proxy's `sys.stdin.readline()` loop works reliably. No Content-Length parsing needed in the proxy script.

### OAuth (mcp-remote) Alternative

The official `mcp-remote` proxy approach was abandoned because:
- Requires browser-based OAuth 3LO flow on first run (impossible headless)
- `--token` flag is ignored (always falls back to browser OAuth)
- Callback port (localhost:3736) unreachable from Docker into user's browser
- Node v20+ required (container has v18)

Keep the Python proxy as the primary approach.

## Verification

```bash
# Quick test
docker exec -i mcphub timeout 15 python3 /root/mcp-servers/atlassian-proxy.py << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
```

Expected: initialize succeeds with `protocolVersion: 2024-11-05`, tools/list returns tool definitions.

# MCPHub Initial Status (05.06.2026)

## Discovery von MCPHub

Nach Docker-Start uf LXC 107 war de MCPHub-Container bereits laufend (`Up 9 minutes`). LXC 107: 10.0.60.170, Container: `mcphub`.

## Authentifizierung

MCPHub verwendet **X-Auth-Token** Header (NICHT Authorization: Bearer):

```bash
# Login
POST /api/auth/login
Body: {"username":"admin","password":"Admin_2026!"}
Response: {"success":true,"token":"eyJ...","user":{"username":"admin","isAdmin":true}}

# API
GET /api/servers
Header: X-Auth-Token: eyJ...
```

## Connected MCPs (6/15)

### ✅ Playwright (23 Tools)
- Playwright-browser tools: close, resize, navigate, click, type, snapshot, scroll, console, vision, etc.

### ✅ Fetch (1 Tool)
- Einfach HTTP fetch tool

### ✅ GitHub (26 Tools)
- Full GitHub API: issues, PRs, repos, search, files, etc.

### ✅ Filesystem (14 Tools)
- Read, write, search, patch files

### ✅ MinIO (7 Tools)
- S3 object storage operations

### ✅ UniFi (3 Tools)
- UniFi network controller

## Disconnected MCPs (9/15)

### ❌ Proxmox — Timeout
- McpError: Request timed out
- Config issue: URL/IP or credentials need checking

### ❌ Home Assistant — Connection closed
- McpError: Connection closed
- HA token might be wrong or expired

### ❌ Jira — Connection closed
- McpError: Connection closed
- Atlassian token or URL issue

### ❌ Notion — Timeout
- McpError: Request timed out
- API key might be invalid

### ❌ Obsidian — Timeout
- McpError: Request timed out
- Vault path `/vault` is a placeholder — needs real path

### ❌ Google Workspace — Timeout
- McpError: Request timed out
- Uses `npx google-workspace-mcp` which doesn't exist
- **Fix:** Deploy separate Google MCP Server on LXC 107, use as URL-MCP

### ❌ WhatsApp — Timeout
- McpError: Request timed out
- No WhatsApp Business API account
- **Fix:** Needs alternative integration

### ❌ Dokploy Production — Connection closed
- McpError: Connection closed
- URL/port unclear (10.0.60.121:3000 returns no HTTP response)

### ❌ Dokploy Sandbox — Connection closed
- McpError: Connection closed
- Sandbox is 10.0.60.136:3000, login works but no API key generated

## User Decisions

1. **ALL MCPs on LXC 107** — Kei MCPs via Dokploy. LXC 107 is the central MCP hub.
2. **Google MCP as separate service** — Deploy Google MCP Server on LXC 107 as Docker container, connect via URL-MCP pattern.
3. **Same for WhatsApp/Telegram** — If implemented, run as separate services on LXC 107, not via Dokploy or npx subprocess.
4. **URL-MCP pattern preferred** over npx subprocess for non-trivial MCPs — easier to maintain, restart independently, re-authenticate.

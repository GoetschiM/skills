---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP) + build custom MCP servers."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation
- **Build custom MCP servers** that Hermes connects to (see Building Custom MCP Servers section)

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

**⚠️ User-Preference: KEIN Gateway-Restart!** (Michel, 23.05.2026)
Das isch e **No-Go** — nie de Gateway neustarte nume für MCP-Tools z'aktiviere!
Stattdessen: MCP-Server **direkt via JSON-RPC/CLI ufruefe** (ohni Gateway-Config):
```bash
KAS_LOGIN="w019000a" KAS_PASSWORD="***" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_mail","arguments":{"action":"list"}}}
EOF
```
Siehe `devops/all-inkl` Skill für de vollständig Bash-Wrapper (`scripts/hermes-all-inkl.sh`).

D'Gateway-Config chasch **trotzdem** i d'`mcp_servers`-Sektion schriibe (für spötere Neustart), aber niemals restartä für en sofortige Integrationstest. Nutz immer de direkti CLI-Wäg.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` -> `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` -> `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` -> `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

### Gateway restart required

Adding or removing MCP servers in config.yaml requires restarting the agent (no hot-reload). If restart is not possible (e.g. during a live session), use **Direct JSON-RPC Calls** instead:

```bash
# Example: call an MCP server directly via heredoc (no gateway restart needed)
KAS_LOGIN="w019000a" KAS_PASSWORD="***" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_domain","arguments":{"action":"list"}}}
EOF
```

See `devops/all-inkl` skill for the complete wrapper script (`scripts/hermes-all-inkl.sh`) that provides this pattern for all tools without any gateway config at all.

## MCPHub as Central Gateway (Enterprise Pattern)

**Architecture pattern:** Instead of configuring multiple individual MCP servers in Hermes config.yaml, configure **a single MCPHub** server that itself orchestrates all MCP backends. Hermes connects to MCPHub via HTTP, and MCPHub routes tool calls to the appropriate backend (npx subprocess or URL-MCP).

```yaml
mcp_servers:
  mcphub:
    url: "http://10.0.60.170:3000/mcp"
    headers:
      Accept: "application/json"
      Authorization: "Bearer ${MCPHUB_API_KEY}"
    timeout: 30
    connect_timeout: 15
```

⚠️ **MCPHub v1.0.11 uses dual auth:** a Session Token (for Web-UI + REST API) and a separate API Key (for the `/mcp` endpoint). The API Key must be created in Settings → Keys. The session token from login does NOT work for /mcp. See the `mcphub-gateway` skill for full details.

### Why MCPHub?

| Feature | Individual MCPs | MCPHub Gateway |
|---------|----------------|----------------|
| Config files | 10+ entries in Hermes config | 1 entry in Hermes config |
| Credentials | Scattered in .env per MCP | Centralized on MCPHub |
| Credential-rotation scope | Every Hermes restart | Single point on MCPHub |
| Troubleshooting | Hermes logs only | MCPHub health-check + per-server status |
| Per-MCP access control | Bash or none | MCPHub: X-Auth-Token per user |
| Multiple agent access | N/A (Hermes-only) | Nova, Apollo share same MCPHub |

### Credential Migration Pattern

When moving credentials OUT of Hermes and INTO MCPHub:

```text
1. 🔍 Inventar — List ALL credentials in Hermes config.yaml + .env
2. 📝 MCPHub Config — Add each as an MCP entry in MCPHub's mcp_settings.json
3. 🔄 MCPHub Restart — `docker restart mcphub` (on MCPHub host)
4. ✅ Verify — MCPHub health check shows "connected"
5. 🗑️ Hermes Cleanup — Remove credential from Hermes config.yaml / .env
6. 🔗 1x MCPHub entry — Add the single MCPHub HTTP entry to hermes mcp_servers
7. 🧪 Test — Call a tool that was previously configured locally
```

**Migration sequence matters:** Verify the MCPHub side FIRST before removing local credentials. That way if MCPHub connection fails, the local fallback still works.

### Authentication — API Key

MCPHub's MCP endpoint uses **Bearer token authentication** (Authorization header):

```yaml
mcp_servers:
  mcphub:
    url: "http://10.0.60.170:3000/mcp"
    headers:
      Accept: "application/json"
      Authorization: "Bearer ${MCPHUB_API_KEY}"
```

**To create an API Key:**
1. Open `http://10.0.60.170:3000/` in browser
2. Login with Hermes / Louis_one_13
3. Go to Settings → Keys
4. Click "Add key" — generate and label it
5. The key is used as `Authorization: Bearer <key>`...tant distinction:**
- `POST /api/auth/login` returns a **Session Token** (JWT, for Web-UI + REST API, stored in localStorage)
- The **/mcp endpoint** requires a separate **API Key** (created in Settings → Keys)
- The session token does NOT work for the MCP endpoint ("Invalid bearer token")

### When MCPHub is not reachable / Gateway restart not possible

If Hermes cannot reach MCPHub (network issue, LXC down) OR you cannot restart the gateway to pick up new `mcp_servers` config:

**Option A — Direct SSH to MCPHub:** If you have LXC access, run the tool directly on MCPHub via `lxc-attach`:
```bash
lxc-attach -n 107 -- curl -s http://localhost:3000/health
```

**Option B — Direct npx call (no MCPHub):** Skip MCPHub entirely for one-off tool calls:
```bash
KAS_LOGIN="w019000a" KAS_PASSWORD="***" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "kas_domain", "arguments": {"action": "list"}}}
EOF
```

**Option C — Direct API call to the underlying service:** If the MCP tool wraps an API you know:
```bash
curl -s -X POST "http://service-host:port/api/endpoint" -H "Accept: application/json" ...
```

### Connection via Hermes Native MCP Client

Hermes connects to MCPHub as a single remote MCP server. Once configured in `mcp_servers`, Hermes auto-discovers all tools on the next restart and prefixes them `mcp_mcphub_*`.

**Tool naming:** `mcp_mcphub_{tool_name}` — e.g. `mcp_mcphub_kas_domain`, `mcp_mcphub_git_list_issues`.

**No restart workaround:** If the user won't allow a restart, use direct CLI (Option B above) or proxy tool calls through `terminal()`. Configure the `mcp_servers` entry so it's ready for the next restart, but don't force one.

### MCPHub Status & Debugging

```bash
# From anywhere with network access to MCPHub
curl -s http://10.0.60.107:3000/health
# → {"status": "healthy|degraded", "servers": {"total": N, "connected": N, "disconnected": N}}

# With auth token — full server list
curl -s http://10.0.60.107:3000/api/servers -H "X-Auth-Token: $TOKEN"
```

Common status values:
- `healthy` — all MCP backends connected
- `degraded` — some backends disconnected (most common, e.g. 6/15 connected)
- `unhealthy` — nothing connected

### Pitfalls

- **MCPHub uses X-Auth-Token, not Authorization: Bearer.** Wrong header = "No token, authorization denied".
- **Gateway restart required** to pick up new `mcp_servers` config in Hermes. Configure it anyway but don't restart unprompted — use direct calls until the next restart.
- **MCPHub container name is `mcphub`, not `mcphub-gateway`** — `lxc-attach -n 107 -- docker restart mcphub`
- **Config is READ-ONLY mounted** (`mcp_settings.json:ro`) — only `docker restart` reloads it. No hot-reload.
- **Can't test without restarting:** Unlike stdio MCPs, you can't call `npx` directly as a workaround — the MCPHub client connection only starts at Hermes bootstrap.
- **Per-MCP failures** show as disconnected in the MCPHub health response, not as Hermes errors. Check `/health` first, then `/api/servers`.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### All-Inkl Hosting Admin (SUP-33)

Live-Deployment auf Hermes (23.05.2026). Siehe `references/all-inkl-setup.md` für Credentials, getesteti Domains, Pitfalls und SLA-Regle.

```yaml
mcp_servers:
  all-inkl:
    command: "npx"
    args: ["-y", "mcp-all-inkl"]
    env:
      KAS_LOGIN: "w019000a"
      KAS_PASSWORD: "***"  # im .env oder via env-Variable
    timeout: 30
    connect_timeout: 15
```

**9 Tools, 53 Aktionen:** DNS, Domains, Subdomains, MySQL, Email, Cronjobs, SSL, Account, System.
**Zugriff:** READ-ONLY (usser E-Mail) wäge SLA-Vertrag.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Building Custom MCP Servers for Hermes

When building a custom Python MCP server that Hermes connects to via StreamableHTTP, use `FastMCP` from the `mcp` package.

### FastMCP Constructor (MCP SDK 1.27.x)

**Pitfall:** `FastMCP.__init__()` takes ALL settings as direct keyword arguments, NOT a `settings=` object:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "My MCP Server",
    host="0.0.0.0",         # default: 127.0.0.1
    port=8000,               # default: 8000
    log_level="INFO",
    json_response=True,      # Hermes needs JSON responses
    stateless_http=True,     # no session management needed
)
```

### Required Settings for Hermes Compatibility

| Setting | Value | Why |
|---------|-------|-----|
| `host` | `"0.0.0.0"` | Accept connections from other hosts |
| `stateless_http` | `True` | Hermes sends independent requests (no session init) |
| `json_response` | `True` | Responses are JSON, not SSE-streamed |
| `transport_security` | `{"enable_dns_rebinding_protection": False}` | Disable host validation for LAN access |

**DNS Rebinding Protection blocks LAN connections by default.** Default `allowed_hosts` only includes `127.0.0.1`, `localhost`. When Hermes connects from another host, the server returns **421 Misdirected Request** with `Invalid Host header`. Fix:

```python
mcp = FastMCP("My Server", host="0.0.0.0",
    transport_security={"enable_dns_rebinding_protection": False})
```

### Defining Tools

Use `@mcp.tool()` decorator. Type hints auto-generate JSON schema:

```python
@mcp.tool(name="my_search", description="Search my data source")
def my_search(query: str, max_results: int = 10) -> str:
    """Tool description shown to the agent."""
    return result
```

### Running the Server

```python
import asyncio
if __name__ == "__main__":
    asyncio.run(mcp.run_streamable_http_async())
```

Endpoint defaults to `http://HOST:PORT/mcp` (configurable via `streamable_http_path`).

### Hermes Client Config

Needs `Accept: application/json` header:

```yaml
mcp_servers:
  my_server:
    url: "http://10.0.60.121:8002/mcp"
    headers:
      Accept: "application/json"
    timeout: 30
    connect_timeout: 15
```

Without it: `{"error": {"message": "Not Acceptable: Client must accept application/json"}}`.

### Testing with curl

```bash
# List tools
curl -s -X POST http://HOST:PORT/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call a tool
curl -s -X POST http://HOST:PORT/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"my_tool","arguments":{}}}'
```

### Common Pitfalls

1. **FastMCP `.run()` only accepts `transport` and `mount_path`** — no host/port. Always use `asyncio.run(mcp.run_streamable_http_async())` for HTTP.
2. **421 Misdirected Request** = DNS rebinding protection. Disable with `transport_security={"enable_dns_rebinding_protection": False}`.
3. **"Not Acceptable" error** = missing `Accept: application/json` header in Hermes config.
4. **"Missing session ID" error** = set `stateless_http=True` in constructor.
5. **`TypeError: got an unexpected keyword argument 'settings'`** = pass settings directly as kwargs, not via a `settings=` parameter.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)

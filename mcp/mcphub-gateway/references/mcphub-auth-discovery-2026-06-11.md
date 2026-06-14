# MCPHub Auth Discovery — June 11, 2026

## What changed

- Old admin/Admin_2026! credentials no longer valid
- New credentials: **Hermes / Louis_one_13** (set 11.06.2026)
- The old skill assumed "X-Auth-Token only" — WRONG for v1.0.11

## Dual Auth System discovered

MCPHub v1.0.11 has **two completely separate auth systems**:

### 1. Session Token (for Web-UI + REST API)

```
POST /api/auth/login  →  returns JWT token
```

- Token stored in browser's **localStorage** as key `mcphub_token`
- Token is a JWT containing: username, isAdmin, permissions, iat, exp
- Login sets NO cookie — only localStorage
- Token expiry: 24h (JWT `exp` claim)
- Works with `Authorization: Bearer *** for REST endpoints
- **Does NOT work** for `/mcp` endpoint → 401 "Invalid bearer token"

Used for:
- `/api/servers` — list all MCP servers with status
- `/api/users` — user management
- `/` — Web-UI Dashboard
- Settings pages

### 2. API Key (for MCP endpoint)

```
Settings → Keys → Add key
```

- Requires separate API key created in Web-UI
- Works with `Authorization: Bearer *** on `/mcp`
- "No keys configured yet" → /mcp returns 401
- Bearer Auth switch is ON in Settings, but no keys exist

Used for:
- `/mcp` — generic MCP JSON-RPC
- `/mcp/{server_name}` — per-server smart routing

## Key Discovery Process

1. Login in browser worked (Hermes/Louis_one_13)
2. Dashboard loaded: 19 servers, 16 online
3. `document.cookie` → only `i18next=en` — no auth cookie
4. `JSON.stringify(localStorage)` → `"mcphub_token": "eyJhbG..."` (JWT)
5. Using JWT as Bearer on `/mcp` → 401 "Invalid bearer token"
6. Using JWT as Bearer on `/api/servers` → **works!**
7. Browser → Settings → Keys → "Enable Bearer Authentication" = ON
8. "No keys configured yet" — 0 keys exist
9. Conclusion: Two separate auth systems

## Next Steps

1. Create API Key via Settings → Keys → "Add key"
2. Add MCPHub as `mcp_servers` in Hermes config.yaml:
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
3. Restart Hermes gateway to pick up new MCP tools
4. Remove individual MCP credentials from Hermes config

---
name: vaultwarden-deployment
description: Deploy, configure, and manage Vaultwarden (password manager) with HTTPS, OAuth2, and MCP integration. Covers Docker/Swarm deployment, self-signed or Let's Encrypt TLS, credential bulk-import, and Hermes MCP server registration.
domain: infrastructure
tags:
  - vaultwarden
  - bitwarden
  - password-management
  - docker
  - nginx
  - mcp
  - credentials
triggers:
  - user asks to deploy a password manager
  - user asks to migrate credentials to a vault
  - user asks for Vaultwarden setup or config
  - user needs an MCP server to access credentials
  - task involves bulk-importing passwords from memory/env into Vaultwarden
---

# Vaultwarden Deployment

## Overview
Vaultwarden (Bitwarden-compatible password manager) deployed via Docker on a server. This skill covers the full lifecycle: initial deployment, HTTPS setup, OAuth2 credential bulk-import, and MCP server integration for Hermes agents.

## Prerequisites
- Docker on the target host
- SSH access to the host (use `sshpass` for password-based auth)
- A domain or IP for HTTPS (self-signed cert is sufficient for internal use)
- For OAuth2 import: the user must generate a **Personal API Key** from Settings → Vaultwarden API Key (client_id + client_secret)

## Step 1: Deploy Vaultwarden Container

Pull and run Vaultwarden in Docker on port 80 (internal):

```bash
docker run -d \
  --name vaultwarden \
  --restart unless-stopped \
  -e SIGNUPS_ALLOWED=true \
  -e DOMAIN=https://<your-domain-or-ip> \
  -e ADMIN_TOKEN=<your-admin-token> \
  -v vaultwarden-data:/data \
  vaultwarden/server:latest
```

**Parameters:**
- `SIGNUPS_ALLOWED`: `true` initially so the user can register. Set to `false` after registration.
- `DOMAIN`: Must match the HTTPS domain/IP used by clients (controls CORS/WebAuthn).
- `ADMIN_TOKEN`: Plain text token for `/admin` panel. For production, use `vaultwarden hash` to generate an Argon2 PHC string instead.
- Volume `vaultwarden-data`: Persists SQLite database, attachments, etc.

## Step 2: Set Up HTTPS (Self-Signed)

Create a TLS certificate valid for 10 years:

```bash
mkdir -p /etc/ssl/vaultwarden
openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
  -keyout /etc/ssl/vaultwarden/vaultwarden.key \
  -out /etc/ssl/vaultwarden/vaultwarden.crt \
  -subj "/C=CH/ST=<state>/L=<city>/O=<org>/CN=<domain>" \
  -addext "subjectAltName=DNS:<domain>,DNS:localhost,IP:<ip>"
```

Run an Nginx reverse proxy in front of Vaultwarden:

```bash
docker run -d --name vaultwarden-ssl \
  --restart unless-stopped \
  -p 443:443 \
  -p 8100:80 \
  -v /etc/ssl/vaultwarden:/etc/ssl/vaultwarden:ro \
  --network <docker-network> \
  nginx:alpine
```

Nginx config (mount to `/etc/nginx/conf.d/default.conf`):

```nginx
upstream vaultwarden_backend {
    server vaultwarden:80;
}

server {
    listen 80;
    server_name <domain> <ip>;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name <domain> <ip>;
    ssl_certificate /etc/ssl/vaultwarden/vaultwarden.crt;
    ssl_certificate_key /etc/ssl/vaultwarden/vaultwarden.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Forward requests to Vaultwarden
    location / {
        proxy_pass http://vaultwarden_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Pitfall:** After restarting the Vaultwarden container (due to env changes), Nginx may cache the old upstream IP and return 502. Fix: `docker exec vaultwarden-ssl nginx -s reload`.

## Step 3: Register User + Lock Signups

1. User visits `https://<ip>` and clicks **Create Account**
2. After registration, the user generates a **Personal API Key**: Settings → Vaultwarden API Key → View API Key → copy `client_id` and `client_secret`
3. Restart Vaultwarden with `SIGNUPS_ALLOWED=false`

## Step 4: Bulk-Import Credentials via OAuth2 API

Use the **OAuth2 Client Credentials** flow to programmatically import credentials.

### OAuth2 Token Request

```python
import urllib.request, urllib.parse, json

data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": "<client_id>",
    "client_secret": "<client_secret>",
    "scope": "api",
    "device_identifier": "<unique-device-id>",  # REQUIRED by Vaultwarden
    "device_name": "<descriptive-name>",
    "device_type": "2",
}).encode()

req = urllib.request.Request("http://vaultwarden:80/identity/connect/token", data=data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]
```

**PITFALL:** Vaultwarden's OAuth2 endpoint **requires** `device_identifier` in the body — without it you get HTTP 400 `"device_identifier cannot be blank"`. Also use `scope=api` (not `scope=api offline_access`).

### Create Ciphers (Login Entries)

```python
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

payload = {
    "type": 1,  # Login cipher
    "name": "My Service",
    "login": {
        "uris": [{"uri": "https://example.com", "match": None}],
        "username": "user",
        "password": "secret",
    },
    "notes": "Optional notes",
    "folderId": None,
    "favorite": False,
}

req = urllib.request.Request("http://vaultwarden:80/api/ciphers", data=json.dumps(payload).encode(), headers=headers, method="POST")
resp = urllib.request.urlopen(req)
```

**PITFALLS:**
- Rate limiting: Vaultwarden applies rate limits after multiple failed login attempts. Pace API calls with `time.sleep(0.3)` between creates.
- `POST /api/ciphers` returns 409 if a cipher with same URI+username already exists. Check `POST /api/ciphers?uri=<encoded_uri>` first, or catch 409 and skip.
- The Vaultwarden identity server validates `device_type` as integer. Use `"2"` (desktop browser) — other values may be silently rejected.
- When running the script **inside the Vaultwarden container**, use `http://127.0.0.1:80`. When running from another host/Docker container, use the Docker DNS name (`http://vaultwarden:80` if on same network) or external HTTPS (`https://<ip>` with `--insecure`).

### Credential Dictionary Shape

```python
CREDENTIALS = [
    {
        "name": "Service Name (for search)",
        "uri": "https://service-url",
        "username": "username_or_email",
        "password": "the_password_or_token",
        "notes": "Optional context (SA-token, Bearer, etc.)",
    },
]
```

### Script Location

Save the sync script at `/opt/vaultwarden-mcp/sync_credentials.py` on the host. Make it idempotent (skip existing entries).

## Step 5: MCP Server for Hermes Agents

Create an MCP stdio protocol server in Python that wraps the Vaultwarden API. The server provides two tools:
- `vaultwarden_list_ciphers`: lists all credentials (name, username, URI)
- `vaultwarden_get_credential`: detail search by name (including password)

Protocol: **JSON-RPC 2.0** with HTTP chunked transfer (`Content-Length` headers), protocol version `2024-11-05`.

Register on **MCPHub** (which manages MCP servers centrally). The MCPHub runs on a separate CT/LXC. Config file: `/app/mcp_settings.json` inside the MCPHub container.

Add entry:

```json
{
    "description": "Vaultwarden Credential Store",
    "transport": "stdio",
    "command": "/usr/bin/python3",
    "args": ["/root/mcp-servers/goetschi-vaultwarden.py"],
    "env": {
        "VAULTWARDEN_URL": "https://<vaultwarden-ip>",
        "VAULTWARDEN_INSECURE": "true"
    },
    "enabled": true
}
```

**PITFALL:** The MCP script runs on the MCPHub CT, NOT on the Vaultwarden host. So use the **external HTTPS URL** (with `VERIFY=false`/`--insecure` for self-signed certs). Do NOT use Docker internal DNS names (`http://vaultwarden:80`) from MCPHub — they won't resolve.

**PITFALL:** MCPHub restart (`docker restart mcphub`) can take ~10-15 seconds. All MCPs show as "disconnected" initially. After restart, check `/health` endpoint — `total` should include the new server.

## Verification

1. `curl -sk https://<ip>/` → returns Vaultwarden HTML (login page)
2. `curl -sk https://<ip>/alive` → returns JSON timestamp
3. `curl -sk https://<ip>/admin` → Admin panel (requires token)
4. MCPHub health: `curl http://<mcphub-ip>:3000/health` → shows vaultwarden in `servers`

## References

- [Vaultwarden Wiki](https://github.com/dani-garcia/vaultwarden/wiki)
- [Vaultwarden Admin Page](https://github.com/dani-garcia/vaultwarden/wiki/Enabling-admin-page)
- [Bitwarden API Reference](https://bitwarden.com/help/api/)

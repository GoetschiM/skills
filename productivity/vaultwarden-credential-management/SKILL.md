---
name: vaultwarden-credential-management
description: "Deploy and manage Vaultwarden (Bitwarden-compatible) password manager — Docker-Compose setup, MCP server integration, credential migration from Hermes memory, and agent prompt for secure credential access."
version: 1.0.0
author: Hermes Agent
tags: [vaultwarden, password-manager, credentials, security, bitwarden, mcp]
---

# Vaultwarden Credential Management

Self-hosted password manager using Vaultwarden (Bitwarden-compatible, Rust-based, lightweight). Deploy on Docker, access via MCP from any AI agent.

## Architecture

```
User Browser ──HTTPS──► Vaultwarden (:8100) ──SQLite──► /data/
                             │
Agent (Hermes) ──MCP──► vaultwarden-mcp-server ──API──► Vaultwarden
```

## Deployment

### Docker-Compose

When deploying on a host WITHOUT Dokploy/Traefik exposing ports 80/443 (e.g., Dokploy v0.29.2 embedded Traefik — see `references/dokploy-https-proxy.md`), use a standalone nginx SSL proxy container instead of relying on the platform's reverse proxy.

```yaml
version: '3.8'
services:
  vaultwarden:
    image: vaultwarden/server:latest
    container_name: vaultwarden
    restart: unless-stopped
    ports:
      - "8100:80"
    volumes:
      - vaultwarden-data:/data
    environment:
      - SIGNUPS_ALLOWED=false       # Disable after first user
      - DOMAIN=https://vault.example.com  # Your domain or IP
      - ADMIN_TOKEN_FILE=/data/admin_token  # Admin panel token
      - LOGIN_RATELIMIT_MAX_BURST=10
      - LOGIN_RATELIMIT_SECONDS=60
      - SHOW_PASSWORD_HINT=false
volumes:
  vaultwarden-data:
    driver: local
```

### First-Time Setup

1. Deploy compose, access `http://host:8100`
2. Create the **first** account — this becomes admin
3. Set `SIGNUPS_ALLOWED=false` after creation
4. Access `/admin` page with ADMIN_TOKEN to manage users/configuration
5. **Personal API Key** path: Login → Account Settings (top right avatar) → scroll all the way down → "Vaultwarden API Key" section → "View API Key"
   - This key has format `user_<id>_<secret>` and is used for PERSONAL access (single user)
6. **Organization API Key** (for team/multi-user automation): First create an Organization via WebUI (Settings → Organizations → [+ New Organization]), then in the org settings → Settings → API Key → "View API Key"
   - This key has format `organization_<id>_<secret>` and is needed for headless automation across users

**⚠️ Important**: The Organization API Key is different from the Personal API Key. For Hermes agent automation, you WANT the Organization Owner Access Token. The Personal API Key only gives access to ONE user's vault items.

### API Authentication Methods

| Method | Format | Required For | URL |
|--------|--------|-------------|-----|
| Password auth | Email + Master Password | First login, WebUI | `/identity/connect/token` |
| API Key (Personal) | `user_<id>_<secret>` | Single-user script access | `/identity/connect/token` |
| API Key (Org) | `organization_<id>_<secret>` | Multi-user/agent automation | `/identity/connect/token` |
| Admin Token | Plaintext env var | `/admin` panel access | `/admin` (cookie-based) |

For API Key auth, use `grant_type=client_credentials` with `client_id=<key_type>&client_secret=<secret>&scope=api`.
For password auth, use `grant_type=password` with `username=email&password=master_pw&scope=api+offline_access`.

## MCP Server Integration

### Architecture

A pure-Python MCP server that proxies Vaultwarden's REST API as stdio JSON-RPC 2.0 for MCPHub or Hermes.

### Implementation Pattern (stdlib only)

```python
import sys, json, os, urllib.request, urllib.parse, base64

VAULTWARDEN_URL = os.getenv("VAULTWARDEN_URL", "http://10.0.60.121:8100")
VAULTWARDEN_EMAIL = os.getenv("VAULTWARDEN_EMAIL", "hermes@example.com")
VAULTWARDEN_API_KEY = os.getenv("VAULTWARDEN_API_KEY", "")

class VaultwardenClient:
    def __init__(self):
        self.token = None
        self._authenticate()

    def _authenticate(self):
        """API Key auth (preferred) or password auth"""
        if ":" in VAULTWARDEN_API_KEY:
            client_id, client_secret = VAULTWARDEN_API_KEY.split(":", 1)
            data = {"grant_type": "client_credentials",
                    "client_id": client_id, "client_secret": client_secret, "scope": "api"}
            req = urllib.request.Request(
                f"{VAULTWARDEN_URL}/identity/connect/token",
                data=urllib.parse.urlencode(data).encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"})
        else:
            # Password fallback
            data = {"grant_type": "password", "username": VAULTWARDEN_EMAIL,
                    "password": VAULTWARDEN_MASTER_PW, "scope": "api offline_access",
                    "client_id": "web", "deviceType": 10,
                    "deviceName": "Hermes MCP", "deviceIdentifier": "hermes-vaultwarden-mcp"}
            req = urllib.request.Request(
                f"{VAULTWARDEN_URL}/identity/connect/token",
                data=urllib.parse.urlencode(data).encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"})

        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        self.token = result.get("access_token", "")

    def list_items(self):
        return self._api_call("GET", "/ciphers")

    def get_item(self, name):
        """Search by name, return first match"""
        items = self.list_items()
        for item in items:
            cipher = self._parse_cipher(item)
            if name.lower() in cipher["name"].lower():
                return cipher
        return {"error": f"Not found: {name}"}

    def search(self, query):
        q = query.lower()
        items = self.list_items()
        results = []
        for item in items:
            cipher = self._parse_cipher(item)
            if (q in cipher["name"].lower() or q in cipher.get("username","").lower()):
                results.append(cipher)
        return results

    def add_item(self, name, username, password, uri="", fields=None):
        data = {
            "type": 1, "name": name,
            "login": {"username": username, "password": password,
                      "uris": [{"uri": uri}] if uri else []},
            "fields": [{"type": 0, "name": k, "value": str(v)} for k,v in (fields or {}).items()]
        }
        return self._api_call("POST", "/ciphers", data)

    def _api_call(self, method, path, data=None):
        url = f"{VAULTWARDEN_URL}/api{path}"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        import urllib.error
        req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                     headers=headers, method=method)
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            return json.loads(resp.read()) if resp.status != 204 else {"success": True}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.read().decode()[:200]}"}

    def _parse_cipher(self, cipher):
        login = cipher.get("login", {})
        fields = {f["name"]: f["value"] for f in cipher.get("fields", [])}
        return {
            "id": cipher["id"], "name": cipher["name"],
            "username": login.get("username", ""),
            "password": login.get("password", ""),
            "uri": login.get("uris", [{}])[0].get("uri", "") if login.get("uris") else "",
            "fields": fields,
        }
```

### MCP Tool Definition

```python
VAULTWARDEN_TOOL = {
    "name": "vaultwarden_get",
    "description": "Ruft gespeicherte Credentials aus Vaultwarden ab.",
    "parameters": {"type": "object", "properties": {
        "query": {"type": "string", "description": "Suchbegriff (z.B. 'Proxmox', 'Grafana')"}
    }, "required": ["query"]}
}

def handle_vaultwarden_call(arguments):
    query = arguments.get("query", "")
    client = VaultwardenClient()
    item = client.get_item(query)
    if "error" not in item:
        # Strip password for security, just confirm existence
        result = {k: v for k, v in item.items() if k != "password"}
        result["password_available"] = bool(item.get("password"))
        return result
    results = client.search(query)
    if results:
        safe = [{k: v for k, v in r.items() if k != "password"} for r in results]
        for r in safe: r["password_available"] = True
        return {"results": safe, "count": len(safe)}
    return {"error": f"Keine Credentials gefunden für: {query}"}
```

## Agent Prompt Template

This prompt should be embedded in skills or loaded at session start so agents know to use Vaultwarden instead of hardcoding:

```markdown
## Credential-Management

ALL credentials are centrally stored in Vaultwarden at https://vault.rebelone.ch (via nginx SSL Proxy), intern http://vaultwarden:80 im Docker-Netzwerk.

WHEN you need a password, API key, or login:
  Call vaultwarden_get(query="search term").
  Search by: system name, service, or hostname.

EXAMPLES:
  vaultwarden_get(query="Dokploy")
  vaultwarden_get(query="Proxmox")
  vaultwarden_get(query="Grafana")

RULES:
1. NEVER hardcode credentials in conversation or files
2. NEVER display credentials in plaintext
3. Always retrieve via vaultwarden_get
4. If not found → ask the user, then store in Vaultwarden

NEW CREDENTIALS:
When user gives you a new password:
  1. Store it in Vaultwarden (via add tool)
  2. Remove it from your memory
  3. Confirm to user it's saved
```

## Credential Migration Workflow

When migrating from Hermes memory/Config/skills to Vaultwarden:

1. Run a migration script that reads all known credentials from memory
2. For each credential: check if already in Vaultwarden (by name), skip if yes
3. If not: add via `add_item` with `name`, `username`, `password`, `uri`, `fields` (tags, host, notes)
4. After migration: store the Vaultwarden API key in a secure env var (NOT in memory)
5. Update skills to use `vaultwarden_get` pattern instead of hardcoded values

## Direkte API Credential-Insertion (Vaultwarden Container)

Wenn du ein neues Credential via Vaultwarden REST API speichern willst (z.B. einen neuen Token aus einer Session), geht das am zuverlässigsten via **Python-Script im Vaultwarden Docker Container**:

### Vorgehen

```bash
# 1. CLIENT_SECRET aus dem MCP-Script extrahieren (via base64, da grep/terminal die Zeile truncatet)
sshpass -p "${PM_PASS}" ssh root@10.0.60.10 \
  "pct exec 107 -- docker exec mcphub grep 'CLIENT_SECRET' /root/mcp-servers/goetschi-vaultwarden.py | base64"
# → decode locally, z.B. base64.b64decode(...)

# 2. Python-Script auf dem Agent-Host schreiben (write_file)
#    Inhalt: CLIENT_ID/CLIENT_SECRET rein, dann per VC REST API einen Cipher anlegen

# 3. Script auf pve01 kopieren
cat /tmp/vw_add_credential.py | sshpass -p "${PM_PASS}" ssh root@10.0.60.10 'cat > /tmp/vw_add_credential.py'

# 4. Script im vaultwarden Container ausführen (wo "vaultwarden:80" aufgelöst wird)
sshpass -p "${PM_PASS}" ssh root@10.0.60.10 \
  'pct exec 100 -- docker exec -i vaultwarden python3' < /tmp/vw_add_credential.py
```

**Wichtig**: Das Script muss `http://vaultwarden:80` als URL verwenden — das ist der Docker-Compose interne Hostname. Port 8100 ist der nginx-SSL-Proxy (301 Redirect).

### CLIENT_SECRET korrekt auslesen

`grep` durch den terminal-Output truncated. **Immer base64 verwenden**:
```bash
pct exec 107 -- docker exec mcphub grep 'CLIENT_SECRET' /root/mcp-servers/goetschi-vaultwarden.py | base64
```

## Pitfalls

1. **SIGNUPS_ALLOWED must be disabled after first user** — otherwise anyone can register
2. **ADMIN_TOKEN is separate from user password** — set via env var or file, used for `/admin` page
3. **API Key vs Password auth** — API Key (client_id:client_secret) is preferred for headless access
4. **Container restart loses nothing** — data is in persistent Docker volume
5. **Browser Extension needs HTTPS** — use a reverse proxy (Caddy/Traefik/nginx) for production
6. **Agent must NEVER display passwords in output** — always strip before returning to user
7. **Rate-limiting affects everything** — Vaultwarden applies rate limits (`LOGIN_RATELIMIT_MAX_BURST`, default 10) to ALL login attempts INCLUDING API key auth. After too many wrong attempts (even via Admin API), you get HTTP 429 for the configured `LOGIN_RATELIMIT_SECONDS` (default 60). To avoid this during setup: increase limits temporarily, or wait for cooldown.
8. **User registration via API is not possible without proper key derivation** — The `/identity/accounts/register` endpoint requires a client-side derived master password hash and key pair (PBKDF2/Argon2). You cannot create users programmatically with a simple `curl -X POST`. Always create the first user via WebUI, then use Org API Key for subsequent automation.
9. **Dokploy Traefik is embedded but doesn't expose ports 80/443** — Dokploy v0.29.2 runs Traefik inside its container for internal routing. It does NOT bind 80/443 to the host. If you need external HTTPS access to services deployed alongside Dokploy, use a standalone nginx reverse proxy container. See `docker-ssl-proxy` skill for the pattern.

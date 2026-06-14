# Third-Party App Deployment via Docker Compose (Sandbox LXC 110)

Whenever the user wants to deploy a random open-source project on the Sandbox LXC 110 (10.0.60.136), follow this deployment pattern:

## Pattern

1. **Read the project's README** — look for the Docker Compose deployment command. Usually:
   ```bash
   curl -o docker-compose.yaml https://raw.githubusercontent.com/.../docker-compose.yaml
   docker compose up -d
   ```

2. **Check required environment variables** — the compose file won't start if vars are missing. Common ones:
   - `OSS_JWT_SECRET` (auth secrets, generate with `openssl rand -hex 32`)
   - `ENABLE_TELEMETRY` (set to `false`)
   - `PUBLIC_HOST`, `PUBLIC_BASE_URL`, `SERVER_IP` (for web apps)
   - `POSTGRES_PASSWORD`, `REDIS_PASSWORD` (database credentials)
   
   Create a `.env` file in the project directory:
   ```bash
   echo "OSS_JWT_SECRET=$(openssl rand -hex 32)" > .env
   echo "ENABLE_TELEMETRY=false" >> .env
   ```

3. **Check for port conflicts** — existing services on LXC 110 commonly use:
   - 3000 (Dokploy UI)
   - 3001 (moto-poschung chat)
   - 3010 (Dograh UI)
   - 3033 (moto-poschung web)
   - 8080 (talk-gateway)
   - 8081 (hermes-mt5-dashboard)
   - 3007 (wine-mt5)
   - 5432 (Postgres)
   - 6379 (Redis)
   - 9000-9001 (MinIO)
   
   Use: `ss -tlnp | grep <PORT>` or `docker ps --format "table {{.Names}}\t{{.Ports}}"`

4. **Pull before up** — compose pulls sequentially and can take 2-5 min for large images:
   ```bash
   docker compose pull 2>&1  # First, to download images
   docker compose up -d 2>&1 # Then, to start
   ```

5. **Handle container name conflicts** — if a container name already exists from a previous attempt:
   ```bash
   docker rm -f <container-name>  # Remove old, then retry compose
   docker compose up -d
   ```

6. **Verify** — check all relevant services are up:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ss -tlnp | grep -E "3010|8000|PORT"  # For specific app ports
   curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:<PORT>
   ```

## Access via LXC-attach from pve01

Since the LXC only accepts SSH with password (not key-based), use `lxc-attach` for all commands:

```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "lxc-attach -n 110 -- bash -c '<command>'"
```

For long-running commands like `docker compose pull` (3-5 min), use one of these approaches:

**Option A — Background script:**
```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "lxc-attach -n 110 -- bash -c '
    cat > /opt/app/start.sh << \"SCRIPT\"
#!/bin/bash
cd /opt/app
docker compose pull 2>&1
echo \"---\"
docker compose up -d 2>&1
echo DONE > /tmp/deploy_done
SCRIPT
    chmod +x /opt/app/start.sh
    nohup /opt/app/start.sh > /tmp/deploy.log 2>&1 &
    echo Started
  '"
```

Then poll progress with:
```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "lxc-attach -n 110 -- bash -c 'tail -10 /tmp/deploy.log; cat /tmp/deploy_done 2>/dev/null || echo \"running\"'"
```

**Option B — High timeout** (risks terminal timeout):
```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=300 root@10.0.60.10 \
  "lxc-attach -n 110 -- timeout 300 bash -c 'cd /opt/app && docker compose up -d 2>&1'"
```

## Example: Dograh AI deployment

Dograh (https://github.com/dograh-hq/dograh) is an open-source voice AI platform, self-hosted Vapi/Retell alternative with telephony support (Asterisk ARI, Pipecat).

**Deployment:**
```bash
# 1. Files
mkdir -p /opt/dograh && cd /opt/dograh
curl -sS -o docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml

# 2. Env
echo "OSS_JWT_SECRET=$(openssl rand -hex 32)" > .env
echo "ENVIRONMENT=local" >> .env
echo "ENABLE_TELEMETRY=false" >> .env

# 3. Pull + start (background, ~3-5 min for ~4GB images)
REGISTRY=ghcr.io/dograh-hq docker compose up --pull always -d

# 4. Fix container name conflicts if needed
docker rm -f dograh-ui-1 dograh-api-1 2>/dev/null
docker compose up -d

# 5. Verify
docker ps --format "table {{.Names}}\t{{.Status}}" | grep dograh
```

**Resulting services:**
| Service | Port | Description |
|---------|------|-------------|
| dograh-ui-1 | 3010 | Web UI for building voice agents |
| dograh-api-1 | 8000 | API backend (REST) |
| dograh-postgres-1 | 5432 | Database (used by same stack) |
| dograh-redis-1 | 6379 | Cache (used by same stack) |
| cloudflared-tunnel | 2000 | Cloudflare tunnel (if exposed) |
| minio | 9000 | Object storage (internal, localhost-bind) |

**Access:** `http://10.0.60.136:3010`

**Note:** Dograh ships with auto-generated API keys and its own LLM/STT/TTS stack — no API keys needed for first test.

## First-Time Auth Setup (most compose apps need this)

Many Docker Compose apps require creating the first user via API before the UI is usable.

### Auth discovery pattern

```bash
# 1. Check health endpoint (find auth_provider + version)
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
# → {"status":"ok","version":"1.32.0","auth_provider":"local","deployment_mode":"oss",...}

# 2. Check the OpenAPI spec for all available auth endpoints
curl -s http://localhost:8000/api/v1/openapi.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for path, methods in d.get('paths', {}).items():
    if 'auth' in path or 'sign' in path or 'login' in path:
        for method, info in methods.items():
            print(f'{method.upper()} {path}  — {info.get(\"summary\",\"\")}')"

# 3. Common auth endpoints:
#    POST /api/v1/auth/signup  — Create account (first user = admin)
#    POST /api/v1/auth/login   — Login, returns JWT token
#    GET  /api/v1/auth/me      — Get current user info
```

### Signup: first user becomes admin

The FIRST user to sign up gets `organization_id=1` and admin privileges.
If the email is already registered, use a different email:

```bash
# Sign up as first admin
echo '{"email":"admin@example.com","password":"YourPassword123!","name":"Admin"}' > /tmp/signup.json
curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d @/tmp/signup.json

# On success → {"token":"eyJ...","user":{"id":1,"email":"admin@example.com",...}}
# On dupe   → {"detail":"Email already registered"}
```

### Login (get JWT token for API use)

```bash
echo '{"email":"admin@example.com","password":"YourPassword123!"}' > /tmp/login.json
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d @/tmp/login.json
```

### Pitfall: JSON quoting in remote shells

When running curl inside lxc-attach (ssh → pve01 → lxc-attach), inline JSON with `-d '{"key":"val"}'` often breaks due to nested quoting. **Always write JSON to a temp file first:**

```bash
# CORRECT — write JSON to file, then use @/tmp/file.json
echo '{"email":"x@y.com","password":"pw"}' > /tmp/signup.json
curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d @/tmp/signup.json

# WRONG — inline JSON gets shell-quote mangled:
curl -s -X POST ... -d '{"email":"x@y.com","password":"pw"}'  # ← breaks in nested ssh
```

### Pitfall: Next.js UI → API communication (BACKEND_URL)

**Wichtigste Bug bi Docker Compose mit Next.js Frontend + Backend:**

D'Next.js UI chunt mit `BACKEND_URL=http://api:8000` (Docker-interner Service-Name) use. De Browser chan "api" nöd auflöse!

**Fix:** D'UI mitem korrekte Host-IP starte:
```bash
cd /opt/app
BACKEND_URL=http://<LXC-IP>:<API-PORT> docker compose up -d ui
```
Oder im `.env` File setze:
```
BACKEND_URL=http://10.0.60.136:8000
```

**Alternative:** S'Ganze Stack neu starte mitem Korrekte Backend:
```bash
cd /opt/app
BACKEND_URL=http://<LXC-IP>:<API-PORT> docker compose up -d
```

**Symptom:** s'UI ladt (Spinner/Login-Form), aber Login schlaht fähl mit "network error" im Browser. D'API isch aber erreichbar via curl.

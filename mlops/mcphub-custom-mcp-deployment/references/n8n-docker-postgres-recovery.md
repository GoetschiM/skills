# N8N Docker Postgres Recovery (Dokploy/Compose)

## Symptom: N8N fails to start with `ECONNREFUSED` on Postgres

**Error:** `connect ECONNREFUSED 172.21.0.3:5432`  
**Environment:** Dokploy-managed Docker stack on CT100 (10.0.60.121)

## Root Cause

The N8N Docker stack (`homelab-n8nwithpostgres-pzbt9a`) has two containers:
- `n8n-1` (n8nio/n8n:latest)
- `postgres-1` (postgres:17-alpine)

The Postgres container was **exited with code 137** (OOM-killed or manually stopped).  
On restart, Postgres got a **new Docker internal IP** (172.21.0.x → different IP).  
N8N's `DB_POSTGRESDB_HOST=postgres` uses the **Docker DNS alias**, but if Postgres was down when N8N started, N8N cached the failed DNS resolution to the old IP.

## Fix

```bash
# 1. Restart the Postgres container first
docker start homelab-n8nwithpostgres-pzbt9a-postgres-1

# 2. Wait for Postgres to be healthy
sleep 15

# 3. Then restart N8N (the DNS alias postgres will resolve to the new IP)
docker restart homelab-n8nwithpostgres-pzbt9a-n8n-1
```

## Verification

```bash
# Check both containers are running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep n8n

# Check N8N logs for DB connection
docker logs homelab-n8nwithpostgres-pzbt9a-n8n-1 --tail 5
```

Expected: `n8n` WebUI responds with HTTP 200 on Port 5678.

## Prevention

The `DB_POSTGRESDB_HOST=postgres` env var is **correct** (uses Docker DNS, not hardcoded IP).  
The failure only occurs when Postgres is down during N8N startup.  
For Dokploy stacks, ensure Postgres has `restart: always` or add `depends_on` with `condition: service_healthy`.

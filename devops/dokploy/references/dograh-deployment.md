# Deploying Dograh AI on Sandbox LXC

Dograh AI (voice AI platform, Vapi/Retell alternative) was deployed on Sandbox LXC 110 (10.0.60.136).

## Deployment Steps

```bash
mkdir -p /opt/dograh && cd /opt/dograh
curl -sL "https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml" -o docker-compose.yaml

# Create .env
cat > .env << 'EOF'
OSS_JWT_SECRET=$(openssl rand -hex 32)
ENVIRONMENT=local
ENABLE_TELEMETRY=false
EOF

# Pull images (large — 3-5 min on 100Mbps)
docker compose pull

# Start
docker compose up -d
```

## Critical Fix: UI BACKEND_URL

After initial `docker compose up -d`, the UI container has `BACKEND_URL=http://api:8000` (Docker internal). **The browser cannot resolve `api:8000`** — login will fail with silent errors.

Fix: Restart UI with the correct public IP:
```bash
docker stop dograh-ui-1
docker rm dograh-ui-1
BACKEND_URL=http://10.0.60.136:8000 docker compose up -d ui
```

## Services

| Container | Port | Notes |
|-----------|------|-------|
| dograh-ui-1 | 3010 | Next.js UI |
| dograh-api-1 | 8000 | FastAPI backend |
| dograh-postgres-1 | (internal) | PostgreSQL with pgvector |
| dograh-redis-1 | (internal) | Redis for channel mapping |
| cloudflared-tunnel | — | Optional external access |

## Common Pitfalls

1. **BACKEND_URL must be the LXC IP**, not Docker internal hostname
2. **Docker pull is slow** — run in background with nohup
3. **Container name conflicts** from previous attempts — `docker rm -f` old containers
4. **Login fails silently** — check UI logs for backend connectivity errors

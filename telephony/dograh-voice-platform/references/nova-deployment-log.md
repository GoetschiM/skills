# Dograh Nova Deployment — Setup Log (30.05.2026)

## Host

| | |
|---|---|
| **Hostname** | Nova |
| **IP** | 10.0.60.167 |
| **SSH** | `ssh root@10.0.60.167` (Passwort: `Louis_one_13`) |
| **RAM** | 14 GB (12 GB frei nach Setup) |
| **Disk** | 120 GB (48 GB frei nach Setup) |
| **CPU** | 4 Cores Intel i5-6500T |
| **Existing services** | Asterisk (18.10.0), Whisper STT, edge-tts, Nova Agent, Server-Monitoring |

## Deployment Steps

```bash
# 1. Docker install (use docker-compose-v2, NOT docker-compose v1!)
apt-get update && apt-get install -y docker.io docker-compose-v2

# 2. Dograh compose
mkdir -p /opt/dograh && cd /opt/dograh
curl -sL "https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml" -o docker-compose.yaml

# 3. .env
echo "OSS_JWT_SECRET=$(openssl rand -hex 32)" > .env
echo "ENVIRONMENT=local" >> .env
echo "ENABLE_TELEMETRY=false" >> .env

# 4. Pull + start (images ~2GB total)
docker compose pull --quiet && docker compose up -d

# 5. Fix BACKEND_URL — CRITICAL!
docker stop dograh-ui-1 && docker rm dograh-ui-1
BACKEND_URL=http://10.0.60.167:8000 docker compose up -d ui
```

## ARI Configuration

```bash
# Insert ARI config into Dograh's Postgres
docker compose exec -T postgres psql -U postgres -d postgres << 'SQL'
INSERT INTO telephony_configurations (id, organization_id, name, provider, credentials, is_default_outbound, created_at, updated_at)
VALUES (gen_random_uuid()::text, 1, 'Nova Asterisk ARI', 'ari',
  '{"ari_endpoint":"http://10.0.60.167:8088","app_name":"callbot","app_password":"HermesVB2026","ws_client_name":"dograh","from_numbers":["0796459743"]}',
  false, NOW(), NOW())
ON CONFLICT (organization_id, name) DO NOTHING;
SQL

# Create ARI user on Asterisk (if not exists)
ssh root@10.0.60.167 "echo -e '\n[callbot]\ntype = user\nread_only = no\npassword = HermesVB2026\n' >> /etc/asterisk/ari.conf && asterisk -rx 'module reload res_ari'"

# Start ARI Manager
cd /opt/dograh && docker compose exec -d api python3 /app/api/services/telephony/ari_manager.py

# Verify
sleep 5 && docker compose logs api | grep -i 'WebSocket connected'
```

## User Account

```bash
curl -s -X POST http://10.0.60.167:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"michel@besorgsdir.ch","password":"Dograh2026!","name":"Michel Goetschi"}'
```

## Verification

```bash
# UI
curl -s -o /dev/null -w 'UI: %{http_code}\n' http://10.0.60.167:3010/auth/login
# API
curl -s http://10.0.60.167:8000/api/v1/health | grep -o '"version":"[^"]*"'
# ARI from host
curl -s -u callbot:HermesVB2026 http://10.0.60.167:8088/ari/endpoints
# Containers
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

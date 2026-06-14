# Dokploy Maintenance & Operations Reference

## Prerequisites

All commands run from the Proxmox host (pve01, 10.0.60.10).
SSH with: `sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10`

**IMPORTANT:** For complex/nested docker commands (especially with heredoc stdin like psql), prefer `lxc-attach` over `pct exec` — it's more reliable and avoids quoting/parsing issues:

```bash
# Statt pct exec, verwende lxc-attach:
sshpass -p 'PASSWORT' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  'lxc-attach -n <LXC> -- docker exec -i <container> <command>'

# Für psql mit heredoc stdin:
sshpass -p 'PASSWORT' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "lxc-attach -n <LXC> -- docker exec -i <container> psql -U <user> -d <db>" << 'SQL'
SELECT ...;
SQL
```

## 1. Listing All Dokploy Projects & Applications

Dokploy stores all data in an internal PostgreSQL. Container naming differs between new setup (Compose) and production (Swarm):

### New / Sandbox Setup (Compose-based)
```bash
# Postgres container is directly accessible
pct exec <LXC_ID> -- docker exec dokploy-postgres psql -U dokploy -d dokploy \
  -c "SELECT id, name FROM organization;"
pct exec <LXC_ID> -- docker exec dokploy-postgres psql -U dokploy -d dokploy \
  -c "SELECT \"projectId\", name, description FROM project;"
```

### Production (Swarm-based, container has task suffix)
```bash
# Container name is like: dokploy-postgres.1.4tk5h9wbgaow1mjnjsw2chzh0
# Use a variable to get the container ID dynamically:
pct exec <LXC_ID> -- bash -c '
CID=$(docker ps -q -f name=dokploy-postgres | head -1)
echo "=== Projects ==="
docker exec $CID psql -U dokploy -d dokploy \
  -c "SELECT \"projectId\", name FROM project;"
echo "=== Apps (Application) ==="
docker exec $CID psql -U dokploy -d dokploy \
  -c "SELECT \"appName\", name FROM application;"
echo "=== Apps (Compose) ==="
docker exec $CID psql -U dokploy -d dokploy \
  -c "SELECT \"appName\", name FROM compose;"
'
```

### Getting App Source Info (GitHub repo / branch)
```bash
pct exec <LXC_ID> -- bash -c '
CID=$(docker ps -q -f name=dokploy-postgres | head -1)
docker exec $CID psql -U dokploy -d dokploy \
  -c "SELECT \"appName\", repository, owner, branch FROM application;"
'
```

## 2. Stopping Dokploy Services

NEVER delete containers you're unsure about — scale to 0 instead (reversible).

### Scale service to 0
```bash
pct exec <LXC_ID> -- docker service scale <service-name>=0
# Example:
pct exec 100 -- docker service scale homelab-nei-pur7xq=0
```

Verify: `docker service ls` shows `0/0` replicas.
To restart later: `docker service scale <service-name>=1`

### Remove orphaned/unknown containers (Docker-run, not Swarm-managed)
```bash
pct exec <LXC_ID> -- docker rm -f <container_name>
# For multiple:
pct exec 100 -- docker rm -f admiring_chebyshev dreamy_raman
```

## 3. Copying Docker Images Between LXCs

### Step 1: Export on source LXC → Proxmox host
```bash
pct exec <SRC_LXC> -- docker save <image>:latest -o /tmp/<name>.tar
pct pull <SRC_LXC> /tmp/<name>.tar /tmp/<name>.tar
```

### Step 2: Push to target LXC → Import
```bash
pct push <TGT_LXC> /tmp/<name>.tar /tmp/<name>.tar
pct exec <TGT_LXC> -- docker load -i /tmp/<name>.tar
```

### Step 3: Run container on target (standalone, not Dokploy-managed)
```bash
pct exec <TGT_LXC> -- docker run -d --restart unless-stopped \
  --name <friendly-name> \
  -p <host_port>:<container_port> \
  <image>:latest
```

## 4. S3 Backup Configuration via Direct DB Insert

When Dokploy UI combobox refuses to select provider (React listing issue):

```bash
pct exec <LXC_ID> -- docker exec -i dokploy-postgres psql -U dokploy -d dokploy << "EOF"
INSERT INTO destination ("destinationId", name, "accessKey", "secretAccessKey", bucket, region, endpoint, provider, "organizationId", "createdAt")
VALUES (
  gen_random_uuid()::text,
  'MinIO Homelab',
  'admin',
  '<secret>',
  '<bucket>',
  'us-east-1',
  'http://10.0.60.106:9000',
  'minio',
  (SELECT id FROM organization LIMIT 1),
  NOW()
);
EOF
```

Verify: `SELECT * FROM destination;`

## 5. Common Production Tasks

### If Docker daemon hangs
```bash
pct exec <LXC_ID> -- bash -c '
systemctl stop docker
rm -rf /var/lib/docker/swarm
systemctl start docker
'
```

### If Dokploy health check stays "starting" (Postgres not initialized)
```bash
pct exec <LXC_ID> -- bash -c '
cd /opt/dokploy && docker compose down -v && docker compose up -d
'
```

### Check disk usage
```bash
pct exec <LXC_ID> -- df -h /
pct exec <LXC_ID> -- docker system df
```

## 6. Architecture Overview

Production (LXC 100, 10.0.60.121):
- Docker Swarm (Dokploy's default install)
- 112GB disk, 10GB RAM
- v0.29.2

Sandbox (LXC 110, 10.0.60.136):
- Docker Compose (manual setup for LXC stability)
- 30GB disk, 8GB RAM
- v0.29.5

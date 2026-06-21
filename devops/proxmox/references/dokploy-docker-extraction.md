# Extracting Docker Configs from a Stuck Dokploy LXC

When a Dokploy-managed LXC has a stuck Docker daemon (e.g., disk near full, daemon crashed) and you need to migrate containers to another host (like Coolify).

## The Problem

`docker ps`, `docker compose`, and `docker inspect` all hang or timeout. You can't export images or read compose configs through the normal path.

## Approach: Mount LXC Rootfs from Proxmox Host

```bash
# On the Proxmox host (pve01):
pct mount <VMID>   # Mounts to /var/lib/lxc/<VMID>/rootfs/

# Now read everything directly from disk without Docker
ls /var/lib/lxc/<VMID>/rootfs/
```

## What to Extract

### 1. Config Files in /opt
Dokploy stores standalone docker-compose files under `/opt/<stack-name>/docker-compose.yml`:
- `/opt/obsidian-sync/docker-compose.yml`
- `/opt/paperless/docker-compose.yml`
- `/opt/sd15/Dockerfile`
- `/opt/google-mcp-server/Dockerfile + server.py`
- `/opt/nginx-ssl/nginx.conf`
- `/opt/caddy/Caddyfile`

### 2. Dokploy Compose Files
Dokploy stores its own compose projects at:
```
/etc/dokploy/compose/<project-name>/code/docker-compose.yml
```

These contain the Dokploy-deployed apps (n8n, LiteLLM, MT5, moto-poschung, etc.). Extract via:
```bash
find /var/lib/lxc/<VMID>/rootfs/etc/dokploy -name "docker-compose*" 2>/dev/null
```

### 3. Docker Volumes with Meaningful Names
Look for named volumes (not hex hashes):
```bash
ls /var/lib/lxc/<VMID>/rootfs/var/lib/docker/volumes/
```
Named volumes like `actual-budget-code_actual-data` contain actual app data.

### 4. Environment Variables (.env files)
```bash
find /var/lib/lxc/<VMID>/rootfs -name ".env" 2>/dev/null
```

## Custom Image Handling

Custom images (built by Dokploy, not from registries) have tags like `development-moto-poschung-m7ojyp:latest`. These are stored locally on the source LXC but cannot be exported if Docker daemon is down.

**Solutions:**
1. Try `docker save <image> | gzip > /tmp/image.tar.gz` — may work if daemon responds
2. Rebuild from Dockerfile on the target host (if Dockerfile is extractable)
3. For simple apps (Flask APIs, simple Python services), create a fresh Dockerfile on the target

**PITFALL**: `docker save` also hangs if Docker daemon is stuck. In that case, examine the Dockerfile and source from the LXC rootfs, then rebuild on the target.

## Image Transfer via Rootfs

For small volumes or configs, copy directly from mounted rootfs to target:

```bash
# From Proxmox host:
cp /var/lib/lxc/<VMID>/rootfs/opt/<stack>/* /var/lib/lxc/<TARGET_VMID>/rootfs/opt/<stack>/
```

**PITFALL 1**: Files written via host rootfs have uid 100000 (unprivileged LXC mapping). Use `chown -R 100000:100000` or `pct push <VMID>` instead.

**PITFALL 2**: `pct push` (or `pct exec` cp) is preferred — it handles uid mapping correctly.
```bash
pct push <VMID> /host/path/file /container/path/file
```

## Port Conflict Checking

When moving services to a new LXC, check for port conflicts:

```bash
# On target host:
ss -tlnp | grep -E '<PORT>'
# Or via docker ps
docker ps --format '{{.Ports}}' | grep <PORT>
```

Common reserved ports on Coolify CT118:
- 8000: Coolify Web UI (traefik proxy)
- 8080: Coolify internal proxy
- 6001-6002: Coolify Realtime

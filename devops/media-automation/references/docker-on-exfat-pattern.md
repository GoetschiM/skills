# Docker on exFAT — Deployment Pattern

## The Problem

exFAT filesystems (used on external USB drives for cross-platform compatibility) **do not support Unix file permissions**. Docker container entrypoints that call `chown` on bind-mounted directories **fail immediately** with `Operation not permitted`. This affects:

- **MariaDB/MySQL** — `chown: changing ownership of '/var/lib/mysql/': Operation not permitted` → container enters crash loop, never initializes
- **PostgreSQL** — same pattern, entrypoint tries to chown `/var/lib/postgresql/data/`
- **Redis** — `chown: .: Operation not permitted` → container crash loop
- **NextCloud** — rsync chown errors (non-fatal, but mask real issues)

## The Fix: Docker Named Volumes

**Never bind-mount writable container data directories to exFAT.** Use Docker named volumes instead — they live in `/var/lib/docker/volumes/` on the host's **ext4** system partition.

### Before (broken on exFAT):
```yaml
services:
  db:
    image: mariadb:10.11
    volumes:
      - ./db:/var/lib/mysql        # ❌ Bind mount → exFAT → chown fails
```

### After (working):
```yaml
services:
  db:
    image: mariadb:10.11
    volumes:
      - nextcloud-db:/var/lib/mysql  # ✅ Docker volume → ext4 → chown OK

volumes:
  nextcloud-db:
    driver: local
```

### What you CAN bind-mount from exFAT:

Only **read-only** data that doesn't need chown:
```yaml
services:
  app:
    volumes:
      - /media/exfat/Dokumente:/mnt/Dokumente:ro  # ✅ Read-only exFAT bind mount
```

## Docker Volume Internals

Docker named volumes are stored on the host's ext4 filesystem at:
```
/var/lib/docker/volumes/<project>_<volume-name>/_data/
```

They are managed by Docker's volume subsystem — `docker volume ls`, `docker volume inspect`, `docker compose down -v` (⚠️ removes data).

## Key Differences: Bind Mount vs Named Volume

| Aspect | Bind Mount | Named Volume |
|--------|-----------|-------------|
| Storage location | Host path (any fs) | `/var/lib/docker/volumes/` (ext4) |
| chown support | ❌ on exFAT | ✅ on ext4 |
| Backup | Direct file copy | `docker run --rm -v volume:/data -v $(pwd):/backup alpine tar czf /backup/volume.tar.gz -C /data .` |
| Cleanup | Manual `rm -rf` | `docker compose down -v` or `docker volume rm` |
| Permission control | Via mount options (uid/gid) | Full Unix permissions |

## When to Still Use exFAT Bind Mounts

- **Media files** (movies, TV shows) that need to be accessible to Plex AND accessible via SMB/USB direct
- **Backup targets** that need to be readable from Windows
- **Read-only document shares** mounted into containers just for serving

## MariaDB Version Compatibility

On this infra, **MariaDB 10.11 (LTS)** is proven stable. MariaDB 11.4 had issues:

| Version | Status | Notes |
|---------|--------|-------|
| `mariadb:10.11` | ✅ Working | Uses `MARIADB_*` env vars (also accepts `MYSQL_*`) |
| `mariadb:11.4` | ❌ Failed | `MARIADB_*` env vars parsed but entrypoint still claimed "password not specified" |

**Always use `mariadb:10.11`** for new NextCloud or Wordpress deployments unless a specific feature requires 11.x.

## Redis Command Syntax in Docker Compose

When passing Redis CLI arguments with `--requirepass`, use **YAML block scalar** (`>` with folded lines) or **array** format, NOT a flat string with braces:

```yaml
# ✅ Working — block scalar (folded)
command: >
  redis-server --requirepass MyPassword! --appendonly yes

# ✅ Working — array
command: ["redis-server", "--requirepass", "MyPassword!", "--appendonly", "yes"]

# ❌ Broken (parses --appendonly as argument to --requirepass)
command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
```

## `.env` File with Docker Compose

**Known issue (Docker Compose v2.29.7 on Ubuntu 24.04):** `.env` files in the compose directory may not be loaded when running via SSH. The variables resolve to empty strings even though the `.env` file has correct content (ASCII, Unix line endings, valid KEY=VALUE format).

**Workaround: Inline credentials** in the compose file's `environment:` block. For production, use Docker secrets or a vault system instead.

**Diagnosis:**
```bash
# Check if .env is loaded (shows empty = not loaded)
docker compose config | grep PASSWORD

# Force with --env-file (may also fail)
docker compose --env-file .env config | grep PASSWORD
```

## Verification Script

After deploying a stack on exFAT:

```bash
# 1. Check all containers are running (not in crash loop)
docker ps --format 'table {{.Names}}\t{{.Status}}'

# 2. Check for chown errors specifically
for c in $(docker ps -a --format '{{.Names}}'); do
  err=$(docker logs "$c" 2>&1 | grep -i "operation not permitted\|chown.*failed" | head -1)
  [ -n "$err" ] && echo "❌ $c: $err"
done

# 3. Verify named volumes are used (not bind mounts from exFAT)
for c in $(docker ps --format '{{.Names}}'); do
  echo "=== $c ===" 
  docker inspect "$c" --format '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
done | grep -E '^===|bind.*exfat|exfat|/media/'
```

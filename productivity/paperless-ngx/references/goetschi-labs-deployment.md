# Goetschi Labs Paperless Deployment

## Hosts

| Host | Role | IP |
|------|------|-----|
| **CT103** | Paperless LXC (bare-metal, no Docker) | 10.0.40.30 |
| **CT201** | CasaOS VM (Nextcloud + Samba) | 10.0.60.201 |
| **pve01** | Proxmox Host (bind mount + cron) | 10.0.60.10 |

## Access

- **CT103 SSH**: `root@10.0.60.10 → pct exec 103` (no direct SSH)
- **CT201 SSH**: `michel@10.0.60.201 / Louis_one_14` (SSH key from pve01)
  - Root user has no SSH access; only `michel` user can SSH
  - sudo works via: `echo <pw> | sudo -S <cmd>`
  - Password resets (e.g. `Louis_one_13 → 14`) require re-pushing SSH key
- **CT201 WebUI (CasaOS)**: `http://10.0.60.201:80`
- **Nextcloud**: `http://10.0.60.201:10081` or `https://nextcloud.rebelone.ch`
  - User: `michel` / `Louis_one_14`
  - DB: mariadb, DB User: `nextcloud`, DB Pass: `NextCloudDB2026!`

## Paperless Config

Config file: `/opt/paperless/paperless.conf`

Key settings:
- `PAPERLESS_CONSUMPTION_DIR=/opt/paperless/consume` (bind-mounted from pve01)
- `PAPERLESS_DATA_DIR=/opt/paperless/data`
- `PAPERLESS_MEDIA_ROOT=/opt/paperless/media`
- `PAPERLESS_URL=https://paper.rebelone.ch`
- `PAPERLESS_DBHOST=localhost`, DB: `paperlessdb`, User: `paperless`, Pass: `H9Yp4dz8bPT3v`
- `PAPERLESS_CONSUMER_ENABLE_BARCODES=true`, `PAPERLESS_CONSUMER_BARCODE_STRING=PATCHT`

Logs: `/opt/paperless/data/log/paperless.log`

Services: `paperless-webserver.service`, `paperless-consumer.service`, `paperless-scheduler.service`, `paperless-task-queue.service`

## Workflow: Nextcloud → Paperless

```
Michel uploads PDF to Nextcloud /Scanner/
 → External Storage mount maps to /media/NAS/Paperless-Consume
  → pve01 cron mounts CIFS share every 2 minutes (sync-paperless-consume.sh)
    → copies .pdf files to /var/tmp/paperless-consume/
      → Bind-mounted to CT103:/opt/paperless/consume/
        → Paperless consumer picks up + OCRs
```

### CIFS mount (on pve01)

```bash
mount -t cifs //10.0.60.201/Paperless-Consume /mnt/paperless-share -o guest,vers=3.0
```

### Bind mount to CT103

```bash
pct set 103 -mp0 /var/tmp/paperless-consume,mp=/opt/paperless/consume
```

### Cron job (pve01, every 2 min)

Script: `/root/sync-paperless-consume.sh`

```bash
#!/bin/bash
mount -t cifs //10.0.60.201/Paperless-Consume /mnt/paperless-share -o guest,vers=3.0 2>/dev/null || true
cp -n /mnt/paperless-share/*.pdf /var/tmp/paperless-consume/ 2>/dev/null || true
umount /mnt/paperless-share 2>/dev/null || true
```

Cron: `*/2 * * * * /root/sync-paperless-consume.sh >/dev/null 2>&1`

### Samba config (on CT201)

```ini
[Paperless-Consume]
   path = /media/NAS/Paperless-Consume
   browseable = yes
   read only = no
   guest ok = yes
   create mask = 0777
   directory mask = 0777
```

Available SMB shares on CT201: `NAS`, `Media`, `Paperless-Consume`, `IPC$`.

### Nextcloud External Storage

The /Scanner folder is configured as a Nextcloud Local External Storage:

1. **Docker compose volume mount** (added via SMB to `/media/NAS/Container/Nextcloud/docker-compose.yml`):
   ```yaml
   - /media/NAS/Paperless-Consume:/mnt/Scanner:rw
   ```
2. **OCC command** (needs `-e REDIS_HOST_PASSWORD=***`):
   ```bash
   docker exec -u www-data -e REDIS_HOST_PASSWORD=*** \
     nextcloud php occ files_external:create /Scanner local null::null \
     --config "datadir=/mnt/Scanner"
   ```
3. The `/mnt/Dokumente` volume was changed from `:ro` to `:rw` to allow editing in Nextcloud.

### CasaOS Docker compose location

All CasaOS app configs are on the data disk: `/media/NAS/Container/<app-name>/docker-compose.yml`

Accessed via SMB share `NAS`: `mount -t cifs //10.0.60.201/NAS /mnt/nas-share -o guest,vers=3.0`

## Nextcloud Docker compose (CT201)

```yaml
services:
  db:
    image: mariadb:10.11
    container_name: nextcloud-db
    volumes: [nextcloud-db:/var/lib/mysql]
    environment:
      MARIADB_ROOT_PASSWORD: ***
      MARIADB_PASSWORD: NextCloudDB2026!
      MARIADB_DATABASE: nextcloud
      MARIADB_USER: nextcloud

  redis:
    image: redis:7-alpine
    container_name: nextcloud-redis
    command: redis-server --requirepass RedisSecure2026! --appendonly yes
    volumes: [nextcloud-redis:/data]

  app:
    image: nextcloud:32.0
    container_name: nextcloud
    ports: [10081:80]
    depends_on: [db, redis]
    volumes:
      - nextcloud-app:/var/www/html
      - /media/NAS/Movie:/mnt/Movie:ro
      - /media/NAS/Container/Dokumente:/mnt/Dokumente:rw
      - /media/NAS/Paperless-Consume:/mnt/Scanner:rw
    environment:
      MYSQL_HOST: db
      MYSQL_DATABASE: nextcloud
      MYSQL_USER: nextcloud
      MYSQL_PASSWORD: NextCloudDB2026!
      REDIS_HOST: redis
      REDIS_HOST_PASSWORD: RedisSecure2026!
      NEXTCLOUD_ADMIN_USER: michel
      NEXTCLOUD_ADMIN_PASSWORD: Louis_one_14
      NEXTCLOUD_TRUSTED_DOMAINS: localhost,nextcloud.rebelone.ch,10.0.60.201
      OVERWRITECLIURL: https://nextcloud.rebelone.ch
      OVERWRITEPROTOCOL: https
      PHP_MEMORY_LIMIT: 512M
      PHP_UPLOAD_LIMIT: 2G
      PHP_MAX_FILE_UPLOADS: 50

volumes:
  nextcloud-db: {driver: local}
  nextcloud-redis: {driver: local}
  nextcloud-app: {driver: local}

networks:
  nextcloud-net: {driver: bridge}
```

## Pitfalls (from actual deployment)

- **LXC cannot mount NFS/CIFS** — must use pve01 bind mount
- **`!` in passwords breaks shell heredocs** — use sshpass with array syntax
- **CIFS vers=3.0 required** — newer Samba doesn't do SMB1
- **Paperless only accepts .pdf and .PDF** — text files are queued but fail
- **OCC needs Redis password** as `-e REDIS_HOST_PASSWORD=***` or `NOAUTH Authentication required`
- **Nextcloud External Storage is correct, not symlinks** — symlinks are read-only
- **Nextcloud volume mounts must be `:rw`** — `:ro` prevents all file operations
- **`files_external:create` without `--config` creates a broken entry** — always set datadir
- **`files_external:delete` prompts for confirmation** — pipe `y` via stdin
- **Firewall on VM** (`firewall=1`) blocks cross-VM traffic — use host as intermediary
- **No `qemu-guest-agent`** on CT201 — can't use `qm guest exec`; use SSH or SMB instead
- **Password resets remove SSH authorized_keys** — re-push SSH key after changes
- **rsync script must copy from share root, not subdir** — the SMB share IS the consume folder
- **CT201 has only `michel` user for SSH** — root SSH is disabled; use `sudo -S` with michel

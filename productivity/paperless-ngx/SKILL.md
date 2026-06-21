---
name: paperless-ngx
description: "Deploy, configure, and integrate Paperless-ngx on LXC. Covers consume workflows (Nextcloud/CIFS/Samba), MinIO backup, cross-LXC data sync, and database maintenance."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Paperless, Documents, NAS, Nextcloud, Samba, Backup, LXC, Proxmox]
    related_skills: [ocr-and-documents, minio-mc]
---

# Paperless-ngx

Paperless-ngx is a document management system that automatically OCRs, tags, and archives PDFs.

## Architecture Pattern (Goetschi Labs)

Paperless runs on a **dedicated LXC** (CT103). The integration with Nextcloud has **two directions** — consume (Nextcloud → Paperless) and live document view (Paperless → Nextcloud).

### Direction 1: Nextcloud → Paperless (Consume)

Users upload PDFs in Nextcloud → they appear in Paperless's consume directory automatically.

```
Michel uploads PDF in Nextcloud /Scanner/
  → Nextcloud External Storage (Local, datadir=/mnt/Scanner)
    → /media/NAS/Paperless-Consume/ (Samba share on CT201)
      → pve01 mounts via CIFS (fstab, auto at boot)
        → lsyncd watches for new files → syncs live (5s delay)
          → bind mount to CT103:/opt/paperless/consume/
            → Paperless consumer picks up + OCRs + archives
```

**lsyncd** (replaces old cron-based rsync pattern):
```bash
# Proxmox host (pve01) — no config file needed
lsyncd -delay 5 -insist -rsync /mnt/paperless-share /var/tmp/paperless-consume/
```

lsyncd 2.2.3 does NOT support `delay` in its Lua config file — use CLI flags instead. The `-insist` flag keeps it running even if the source is temporarily unavailable.

### Direction 2: Paperless → Nextcloud (Live Document View)

All Paperless documents are visible in Nextcloud as a read-only folder — instant, no manual sync.

```
Paperless (CT103, /opt/paperless/media/documents/)
  → Samba share "Paperless-Media" (read-only, guest access)
    → pve01 mounts via CIFS: /mnt/paperless-media/
      → lsyncd live-syncs to /media/NAS/Paperless-Dokumente/
        → NAS SMB share on CT201 (guest, browseable)
          → Docker volume mount into Nextcloud: /mnt/Paperless:ro
            → Nextcloud External Storage /Paperless-Dokumente (read-only)
```

This gives a live view of **every archived document** in Nextcloud, organised by year/person.

### Full Data Flow

```
                    +-----------------------+          +----------------------+
                    |  Nextcloud (CT201)    |          |  Paperless (CT103)   |
                    |                       |          |                      |
 User uploads ─────>│ /Scanner (RW ext.     |──SMB──>  │ /opt/paperless/      |
                    |  storage)             |  CIFS    │   consume/ (bind     |
                    |                       |  lsyncd  │   mount from pve01)  │
                    |                       |          │                      |
                    | /Paperless-Dokumente  |<──SMB──  │ /opt/paperless/      |
                    |  (RO ext. storage)    |  CIFS    │   media/documents/   |
                    |                       |  lsyncd  │   1,491+ PDFs        |
                    +-----------------------+          +----------------------+
                                        ▲                      │
                                        │                      │
                                   pve01 (Proxmox Host) ──────┤
                                   - 2× CIFS mounts (fstab + _netdev,nofail)
                                   - 2× lsyncd daemons (systemd services)
                                   - Bind mount to CT103 consume dir
                                   - SMB/CIFS bridge between VLANs (10.0.40/10.0.60)

## Key Constraints (LXC)

**LXC containers CANNOT mount NFS or CIFS** — they lack `CAP_SYS_ADMIN` by default in Proxmox. Workaround: use bind mounts from the Proxmox host.

### CIFS Bridge Pattern (Proxmox Host as Intermediary)

When the NAS/VM with the Samba share is in a **different VLAN** than the LXC (e.g. CT103 is 10.0.40.0/24, CT201 is 10.0.60.0/24), and the VM has `firewall=1` enabled:

```
LXC (CT103, 10.0.40.x) ── bind mount ──> pve01 ── CIFS mount ──> VM (CT201, 10.0.60.x)
```

The Proxmox host bridges both VLANs and has sufficient privileges.

### fstab for CIFS Durability

Add CIFS mounts to `/etc/fstab` so they survive reboots:
```bash
# Paperless-Media (from CT103 Samba)
//10.0.40.30/Paperless-Media /mnt/paperless-media cifs guest,vers=3.0,_netdev,nofail 0 0

# NAS share (from CT201 CasaOS)
//10.0.60.201/NAS /mnt/nas-share cifs guest,vers=3.0,_netdev,nofail 0 0

# Consume share (from CT201 Paperless-Consume)
//10.0.60.201/Paperless-Consume /mnt/paperless-share cifs guest,vers=3.0,_netdev,nofail 0 0
```

**Flags explained:**
- `_netdev` — wait for network before mounting
- `nofail` — don't block boot if the share is unavailable
- `vers=3.0` — explicit SMB protocol version (newer Samba drops SMB1)

### lsyncd for Live Sync (Replaces Cron)

Instead of polling every 2 minutes via cron, use **lsyncd** with inotify for near-instant file propagation:

```bash
# Install
apt-get install -y lsyncd

# Start (no config file — CLI mode for v2.2.3+)
lsyncd -delay 5 -insist -rsync /mnt/paperless-media/documents /mnt/nas-share/Paperless-Dokumente
```

**Pitfall:** lsyncd 2.2.3 does not support `delay` inside its Lua config file (`settings { delay = 5 }` fails with "setting 'delay' unknown"). Always use the CLI `-delay N` flag.

### systemd Service for lsyncd (Boot-Safe)

```ini
# /etc/systemd/system/lsyncd-paperless.service
[Unit]
Description=lsyncd - Live sync Paperless Media to NAS
After=network.target remote-fs.target
Wants=remote-fs.target

[Service]
Type=simple
ExecStart=/usr/bin/lsyncd -delay 5 -insist -rsync /mnt/paperless-media/documents /mnt/nas-share/Paperless-Dokumente
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now lsyncd-paperless.service
```

### Old Pattern (Cron-based — Kept for Simpler Setups)

For simpler setups where live sync is not needed, the cron approach still works:

## Setup Checklist

### 1. Paperless on LXC (Bare-metal, not Docker)

Paperless runs as native systemd services (not Docker) on CT103:

| Service | Status |
|---------|--------|
| `paperless-webserver.service` | Gunicorn ASGI server |
| `paperless-consumer.service` | File watcher + OCR worker |
| `paperless-scheduler.service` | Celery beat (mail fetching, retention) |
| `paperless-task-queue.service` | Celery workers |

Check logs: `tail -f /opt/paperless/data/log/paperless.log`

Config: `/opt/paperless/paperless.conf`
```ini
PAPERLESS_CONSUMPTION_DIR=/opt/paperless/consume
PAPERLESS_DATA_DIR=/opt/paperless/data
PAPERLESS_MEDIA_ROOT=/opt/paperless/media
PAPERLESS_DBHOST=localhost
PAPERLESS_DBNAME=paperlessdb
PAPERLESS_DBUSER=paperless
PAPERLESS_DBPASS=<secret>
PAPERLESS_REDIS=redis://localhost:6379
PAPERLESS_URL=https://paper.rebelone.ch
PAPERLESS_SECRET_KEY=<secret>
```

### 2. Samba Share on Source (e.g. CasaOS/CT201)

```bash
# Add to /etc/samba/smb.conf
[Paperless-Consume]
   path = /media/NAS/Paperless-Consume
   browseable = yes
   read only = no
   guest ok = yes
   create mask = 0777
   directory mask = 0777

systemctl restart smbd
```

### 3. CIFS Mount + Cron on Proxmox Host

Sync script (`/root/sync-paperless-consume.sh`):
```bash
#!/bin/bash
mount -t cifs //10.0.60.201/Paperless-Consume /mnt/paperless-share -o guest,vers=3.0 2>/dev/null || true
cp -n /mnt/paperless-share/*.pdf /var/tmp/paperless-consume/ 2>/dev/null || true
umount /mnt/paperless-share 2>/dev/null || true
```

Cron: `*/2 * * * * /root/sync-paperless-consume.sh >/dev/null 2>&1`

### 4. Bind Mount to LXC

```bash
pct set 103 -mp0 /var/tmp/paperless-consume,mp=/opt/paperless/consume
```

### 5. Test

Drop a `.pdf` file into `/opt/paperless/consume/` on the LXC and check logs:
```
tail -f /opt/paperless/data/log/paperless.log
# Should show: "Adding /opt/paperless/consume/test.pdf to the task queue."
```

## Nextcloud Integration

### Option A: Symlink (Simple, but Read-Only in Nextcloud UI)

On CasaOS/Nextcloud VM (CT201):
1. Nextcloud runs as Docker with binds:
   - `/media/NAS/Container/Dokumente` → `/mnt/Dokumente`
2. Create symlink: `ln -sf /media/NAS/Paperless-Consume /media/NAS/Container/Dokumente/Scanner`
3. Michel uploads PDFs to `Dokumente / Scanner` in Nextcloud
4. CIFS cron syncs → Paperless consumes

**⚠️ Pitfall:** Symlinks in Nextcloud are read-only — users **cannot move, copy, or rename files** inside them. The container volume must be mounted `:rw` (not `:ro`) for write access, but Nextcloud still treats symlinked directories as immutable. Use Option B instead.

### Option C: Live Paperless → Nextcloud Mount (Read-Only, All Documents)

This makes **every archived Paperless document** visible in Nextcloud instantly, without any user action. Uses lsyncd for live sync + Docker volume mount + Nextcloud External Storage.

**1. On the Paperless LXC (CT103):** Create a Samba share for the media directory

```bash
# /etc/samba/smb.conf (on CT103)
[Paperless-Media]
   path = /opt/paperless/media
   browseable = yes
   read only = yes
   guest ok = yes
   force user = nobody
   force group = nogroup

service smbd restart
```

**2. On the Proxmox host (pve01):** Mount the share and set up lsyncd

```bash
# Mount both source and target
mkdir -p /mnt/paperless-media /mnt/nas-share
mount -t cifs //10.0.40.30/Paperless-Media /mnt/paperless-media -o guest,vers=3.0
mount -t cifs //10.0.60.201/NAS /mnt/nas-share -o guest,vers=3.0

# Create target directory on NAS
mkdir -p /mnt/nas-share/Paperless-Dokumente

# Initial copy (first time only)
cp -rn /mnt/paperless-media/documents/* /mnt/nas-share/Paperless-Dokumente/

# Start lsyncd for live sync
lsyncd -delay 5 -insist -rsync /mnt/paperless-media/documents /mnt/nas-share/Paperless-Dokumente
```

**3. Add fstab entries** (survive reboot):

```bash
cat >> /etc/fstab << 'EOF'
//10.0.40.30/Paperless-Media /mnt/paperless-media cifs guest,vers=3.0,_netdev,nofail 0 0
//10.0.60.201/NAS /mnt/nas-share cifs guest,vers=3.0,_netdev,nofail 0 0
EOF
```

**4. Create systemd service** for the lsyncd daemon:

```bash
cat > /etc/systemd/system/lsyncd-paperless.service << 'UNIT'
[Unit]
Description=lsyncd - Live sync Paperless documents to NAS
After=network.target remote-fs.target
Wants=remote-fs.target

[Service]
Type=simple
ExecStart=/usr/bin/lsyncd -delay 5 -insist -rsync /mnt/paperless-media/documents /mnt/nas-share/Paperless-Dokumente
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload && systemctl enable --now lsyncd-paperless.service
```

**5. On the Nextcloud VM (CT201):** Add Docker volume mount

Edit `/media/NAS/Container/Nextcloud/docker-compose.yml` (accessible via SMB share `NAS`):

```yaml
volumes:
  - /media/NAS/Paperless-Dokumente:/mnt/Paperless:ro   # Add this line
```

Then restart the container:
```bash
docker compose -f /media/NAS/Container/Nextcloud/docker-compose.yml up -d
```

**6. Create Nextcloud External Storage** via OCC:

```bash
export REDIS_HOST_PASSWORD=***
docker exec -u www-data -e REDIS_HOST_PASSWORD=$*** \
  nextcloud php occ files_external:create /Paperless-Dokumente local null::null \
  -c datadir=/mnt/Paperless
```

**⚠️ Pitfall:** `REDIS_HOST_PASSWORD` must be passed as `-e` env var to `docker exec -u www-data`, not as shell export — the variable must be available inside the container for OCC to authenticate with Redis.

**7. Verify:**

```bash
# Check files landed on NAS
find /mnt/nas-share/Paperless-Dokumente/ -type f | wc -l
# Should match Paperless document count

# Check External Storage in Nextcloud
docker exec -u www-data -e REDIS_HOST_PASSWORD=$*** \
  nextcloud php occ files_external:list
# Expected: /Paperless-Dokumente, Local, datadir=/mnt/Paperless
```

## Managing External Storage Duplicates

When creating External Storages multiple times (e.g. first attempt without `--config`, second with), you get duplicate entries:

```bash
# List all
docker exec -u www-data -e REDIS_HOST_PASSWORD=$*** \
  nextcloud php occ files_external:list

# Delete stale entry (ID from list)
echo y | docker exec -u www-data -e REDIS_HOST_PASSWORD=$*** \
  nextcloud php occ files_external:delete <ID>
```

The `echo y` pattern is necessary because `files_external:delete` prompts interactively and won't read `-y` flag correctly in some versions.



### Accessing Nextcloud Internals Without SSH

When SSH is not available on the Nextcloud VM, use the **SMB share** to edit the Docker compose:

1. Mount the NAS share that contains the docker-compose.yml:
   ```bash
   mount -t cifs //VM_IP/NAS /mnt/nas-share -o guest,vers=3.0
   ```
2. Edit the compose file directly:
   ```bash
   cp /mnt/nas-share/Container/Nextcloud/docker-compose.yml /mnt/nas-share/Container/Nextcloud/docker-compose.yml.bak
   # Edit compose, add volume mount, then restart container via SSH or CasaOS UI
   ```
3. CasaOS stores Docker compose files under `/media/NAS/Container/<app-name>/docker-compose.yml`.
4. Check available SMB shares first: `smbclient -L VM_IP -N`

## Troubleshooting: Paperless WebUI (Port 8010) Down / Mobile App Login Fails

### Symptom

- WebUI at `http://<host>:8010` returns **Connection Refused**
- Mobile app (Android/iOS) finds the server but **authentication fails** or **cannot connect**
- `curl http://localhost:8010` times out on the Paperless server itself
- But `ping` and `smbclient` (Samba) still work — the host is alive

### Step 1: Check Process

```bash
ss -tlnp | grep 8010
# If empty → Gunicorn isn't listening
systemctl status paperless-webserver  # Check if running
journalctl -u paperless-webserver --no-pager -n 30 | grep -iE "(oom|killed|error|fail)"
```

### Step 2: Check for OOM-Kill (Most Common Cause on 512MB LXCs)

Look for this in the journal:
```
A process of this unit has been killed by the OOM killer.
Worker (pid:182317) was sent SIGKILL! Perhaps out of memory?
```

**Fix:** Increase LXC memory:

```bash
# Proxmox host: set memory to 2GB (up from 512MB)
pct set <VMID> -memory 2048

# Then restart Paperless services
pct exec <VMID> -- systemctl restart paperless-webserver paperless-consumer paperless-scheduler paperless-task-queue

# Verify
pct exec <VMID> -- free -m   # Should show ~2048 total
pct exec <VMID> -- ss -tlnp | grep 8010  # Should show gunicorn listening
pct exec <VMID> -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/
# Expected: 302 (redirect to login page)
```

**Paperless memory baseline (after fix):**
| Component | RAM (after OOM fix) |
|-----------|--------------------|
| Gunicorn (1 master + 1 worker) | ~140 MB |
| PostgreSQL (Paperless DB) | ~40 MB |
| Celery workers | ~80 MB |
| System overhead | ~300 MB |
| **Total comfortable** | **≥ 1 GB** |

LXC with 512MB is **too tight** — Paperless consistently triggers OOM on startup + consumer processing. Minimum recommended: **1.5 GB**, ideal: **2 GB**.

### Step 3: Fix Missing EnvironmentFile in systemd Units

If the service restarts but still binds to default port 8000 (not 8010) or fails to connect to Redis/PostgreSQL:

```bash
# Check if PAPERLESS_PORT from paperless.conf is being read
pct exec <VMID> -- env | grep PAPERLESS_PORT
# If empty → EnvironmentFile is missing in the systemd unit

# The problem: paperless-webserver.service has NO EnvironmentFile directive
# paperless.conf sets PAPERLESS_PORT=8010 but the file is never sourced

# Fix EVERY Paperless systemd unit (4 services):
for svc in paperless-webserver paperless-consumer paperless-scheduler paperless-task-queue; do
  unit_file="/etc/systemd/system/${svc}.service"
  # Check if EnvironmentFile already present
  if pct exec <VMID> -- grep -q "EnvironmentFile" "$unit_file" 2>/dev/null; then
    echo "Already fixed: $svc"
  else
    pct exec <VMID> -- sed -i 's|^ExecStart=|EnvironmentFile=/opt/paperless/paperless.conf\nExecStart=|' "$unit_file"
    echo "Fixed: $svc"
  fi
done

pct exec <VMID> -- systemctl daemon-reload
pct exec <VMID> -- systemctl restart paperless-webserver paperless-consumer paperless-scheduler paperless-task-queue
```

### Step 4: Manual Start (When systemd Hangs)

If `systemctl restart` hangs (common when systemd inside the LXC is slow or the container is under memory pressure):

```bash
# Start Gunicorn directly with explicit port, bypassing systemd
pct exec <VMID> -- bash -c 'cd /opt/paperless/src && PAPERLESS_PORT=8010 /usr/local/bin/gunicorn -b 0.0.0.0:8010 -c /opt/paperless/gunicorn.conf.py paperless.asgi:application > /dev/null 2>&1 &'

# Wait and verify
sleep 5
pct exec <VMID> -- ss -tlnp | grep 8010
```

**⚠️ Pitfall:** The `pct exec` foreground guard may block this. Use a script pushed to the PVE host and run there.

### Step 5: Verify Consumer Pipeline

Even after WebUI is restored, the consumer may still be down:

```bash
pct exec <VMID> -- systemctl is-active paperless-consumer paperless-scheduler paperless-task-queue
# All 3 should show "active"

# Test consumer:
pct exec <VMID> -- touch /opt/paperless/consume/test_$(date +%s).pdf
pct exec <VMID> -- timeout 10 tail -f /opt/paperless/data/log/paperless.log
```

## API-Token Authentication for Mobile Apps

Paperless-ngx 2.20+ uses Django REST Framework's Token Authentication. The standard user/password login may fail in the mobile app due to the upgraded Django-allauth version. Always prefer **API-Token authentication** in the mobile app.

### Generate Token

```bash
pct exec <VMID> -- bash -c 'cd /opt/paperless/src && python3 manage.py shell -c "
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
user = get_user_model().objects.get(username=\"michel\")
token, _ = Token.objects.get_or_create(user=user)
print(\"API-Token:\", token.key)
"' 2>&1 | grep "API-Token:"
```

**Pitfall:** Nested quotes in `pct exec` with `bash -c` are fragile. Use `echo 'python code' | python3 manage.py shell` as a more reliable pattern:
```bash
echo 'from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
user = get_user_model().objects.get(username="michel")
token, _ = Token.objects.get_or_create(user=user)
print("Status:", user.username)
print("API-Token:", token.key)' | pct exec <VMID> -- python3 /opt/paperless/src/manage.py shell 2>&1 | tail -3
```

### Configure Mobile App

1. Server URL: `http://<host>:8010` (use **http**, not https, unless TLS is configured)
2. Login method: **API-Token**
3. Token: paste the generated token exactly (case-sensitive)

**⚠️ Common pitfall:** The token is valid even if the app says "invalid token". Check connectivity first — the Paperless server may not be reachable via Tailscale/remote network (see Remote Access section below).

## Remote Access via Tailscale Subnet Routing

When Michel needs Paperless/Nextcloud from mobile (LTE/5G, different WiFi), he uses Tailscale. But Paperless runs on **10.0.40.30** (internal VLAN) — not directly routable via Tailscale unless the Proxmox host advertises subnet routes.

### Setup Subnet Router on Proxmox Host

```bash
sshpass -p '<PVE_PASS>' ssh -o StrictHostKeyChecking=no root@<PVE_HOST> \
  'tailscale up --accept-routes --advertise-routes=10.40.30.0/24,10.60.0.0/24 --accept-dns=false'
```

The routes **must be approved** in the Tailscale Admin Console:
1. Open https://login.tailscale.com/admin/machines
2. Find the PVE host (e.g. `pve01`)
3. Click **Approve** next to the advertised subnet routes

### Client Side

- **Android/iOS**: Enable "Use Tailscale DNS" + route acceptance in the Tailscale app settings
- **Windows/Mac**: The Tailscale client automatically accepts advertised routes
- Verify: `tailscale status` should show the PVE host's allowed IPs include `10.40.30.0/24`

### Test

```bash
# From a machine connected to Tailscale (not on local network)
curl -s -o /dev/null -w "%{http_code}" http://10.0.40.30:8010/
# Expected: 302
```

### If Subnets Don't Work (No Approval)

#### Option A: socat Proxy on the Proxmox Host (PROVEN)

Create a systemd service on the Proxmox host that forwards a port on the host's Tailscale IP to the Paperless LXC:

```bash
# /etc/systemd/system/paperless-proxy.service
[Unit]
Description=Paperless Proxy - Tailscale Access
After=network.target

[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:8010,reuseaddr,fork TCP:10.40.30.8010:8010
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

systemctl daemon-reload && systemctl enable --now paperless-proxy
```

Then connect from the Tailscale client using the **Proxmox host's Tailscale IP** rather than the LXC's internal IP:
- Server URL: `http://<pve-tailscale-ip>:8010`
- Same API-Token as usual

**Requires:** `socat` installed on the Proxmox host (`apt-get install -y socat`).

#### Option B: SSH tunnel from the Proxmox host

```bash
ssh -L 8010:10.0.40.30:8010 -N -f root@10.0.60.10
```

**Pitfall:** After `tailscale serve` setup, the tailscale serve port shows on the Tailscale IP but may not survive container/tailscaled restarts. The socat approach (`paperless-proxy.service`) is **more reliable** for persistent port forwarding.

#### Option C: `tailscale serve` (requires serve to be enabled in the tailnet first)

```bash
tailscale serve --bg --https 8010 http://10.0.40.30:8010
```

## Pitfalls / Lessons Learned

- **No CIFS/NFS from LXC**: Use host bind mount or rsync instead
- **`!` in passwords breaks shell** — use sshpass with array syntax or env vars, not shell heredocs
- **CIFS vers=3.0** often needed for newer Samba servers (default might try SMB1)
- **SSH key survives password changes** on the remote machine — the key persists in `authorized_keys`
- **Bind mounts persist after LXC restart** but not after `pct restore` — re-attach if container is recreated
- **Paperless rejects non-PDFs** in consume — only `.pdf` and `.PDF` files are processed (`.txt` files are queued but fail)
- **Firewall on Proxmox VM** (`firewall=1`) blocks LXC → VM traffic — use the Proxmox host as intermediary or add rules
- **Nextcloud OCC needs Redis password** as env var when Redis auth is configured — without `-e REDIS_HOST_PASSWORD=<secret>` OCC fails with `NOAUTH`
- **Nextcloud External Storage** is the correct approach, not symlinks (symlinks are read-only in Nextcloud)
- **No `qemu-guest-agent`** on VMs without guest tools → can't use `qm guest exec`; use SSH, Samba, or host-as-intermediary patterns
- **SMB to edit config files** opens the full filesystem — use the NAS share to modify Docker compose files, configs, and scripts directly
- **Nextcloud volume mounts must be `:rw`** — the default `:ro` prevents creating/moving/copying files in Nextcloud UI
- **`files_external:create` without `--config` creates a broken entry** — always specify `--config "datadir=/mnt/Scanner"`
- **`files_external:delete` prompts for `y/N`** — pipe `y` via `echo y | ...` for headless execution
- **lsyncd 2.2.3 doesn't support `delay` in Lua config** — use `-delay SECS` CLI flag instead
- **lsyncd `-insist` flag** keeps it running even if source/target is temporarily unavailable
- **CIFS mount is slow for first copy** — 929MB/1,491 files took ~60 seconds; set generous timeouts
- **Multiple External Storage entries accumulate** — check `files_external:list` before creating new ones
- **`docker exec -u www-data -e REDIS_HOST_PASSWORD=<secret>` is the correct invocation**; the env var MUST be on the docker exec command line, not in the shell that calls docker
- **Paperless has separate originals vs archives** — `documents/originals/` = uploaded PDF, `documents/archive/` = OCR-processed version with embedded text. Archive is what users typically want to see in Nextcloud.
- **Proxmox VM root SSH may be disabled** — only non-root users can SSH; use `echo <pw> | sudo -S <cmd>` pattern, with single-quote password to avoid `!` expansion
- **SSH key may be wiped on password reset** — re-push public key to `~/.ssh/authorized_keys2` after any credential rotation on the target machine

## Reference Files

- `references/goetschi-labs-deployment.md` — Concrete host IPs, access credentials, exact command sequences, and pitfalls from the actual Goetschi Labs Paperless + Nextcloud + CasaOS deployment.
- `references/troubleshooting.md` — Diagnostic procedures and recovery steps for common Paperless failures (Port 8010 down, mobile app login, consumer pipeline stalled, Samba unreachable, Docker Compose Postgres IP shift).

## Related Skills

- **`proxmox`** (mlops) — LXC lifecycle, SSH bootstrap, bind mounts, `pct exec` investigation patterns
- **`ocr-and-documents`** (productivity) — local PDF text extraction (pymupdf, marker-pdf)

## MinIO Backup Setup

TBD — establish a cron that:
1. Dumps Paperless PostgreSQL DB: `pg_dump -U paperless paperlessdb > /tmp/paperless-db.sql`
2. Rsyncs `/opt/paperless/data/` and `/opt/paperless/media/` to MinIO
3. Use `mc` CLI (MinIO client) or `s3cmd` for cloud storage push

## Upgrading Paperless-ngx (Non-Docker Native Install)

When upgrading from an older version (e.g. 2.12.x) to a modern release (2.20.x), the procedure differs significantly from Docker-based installs. This covers the **native systemd** setup pattern used on Goetschi Labs CT103.

### Breaking Changes between 2.12 and 2.20

| Area | 2.12.x | 2.20.x | Impact |
|------|--------|--------|--------|
| **ASGI Server** | Gunicorn (`paperless.workers.ConfigurableWorker`) | **Granian** (native ASGI) | `gunicorn.conf.py` with `ConfigurableWorker` fails — class removed |
| **Django** | 4.2.x | 5.2.x | ~27 DB migrations required |
| **Python** | 3.11 compatible | 3.11+ compatible | Same |
| **Frontend** | Bundled | Newer React build | Must replace `static/` |

**⚠️ Granian is mandatory in 2.20**: Gunicorn's sync worker is WSGI-only — Paperless 2.20 uses Channels `ProtocolTypeRouter` (ASGI). Trying `worker_class = "sync"` gives `TypeError: ProtocolTypeRouter.__call__() missing 1 required positional argument: 'send'`. Switch to Granian.

### Step-by-Step Upgrade (Proven: 2.12.1 → 2.20.15)

#### Step 1: Backup Everything

```bash
# Database
pct exec <VMID> -- bash -c 'PGPASSWORD=<secret> pg_dump -U paperless -h localhost paperlessdb > /tmp/paperless_backup.sql'

# Verify backup
pct exec <VMID> -- wc -c /tmp/paperless_backup.sql
```

#### Step 2: Download Release Tarball

Paperless-ngx is **not on PyPI** — pip can't find it. Download from GitHub:

```bash
# Find asset name
curl -s "https://api.github.com/repos/paperless-ngx/paperless-ngx/releases/tags/v2.20.15" | \
  python3 -c "import sys,json; [print(a['name']) for a in json.load(sys.stdin).get('assets',[])]"

# Download (~82 MB)
wget -q "https://github.com/paperless-ngx/paperless-ngx/releases/download/v2.20.15/paperless-ngx-v2.20.15.tar.xz" \
  -O /tmp/paperless-ngx.tar.xz
```

#### Step 3: Extract and Replace Source

```bash
# Extract (creates paperless-ngx/ subdirectory)
tar xf /tmp/paperless-ngx.tar.xz -C /opt/paperless/

# Backup old source
mv /opt/paperless/src /opt/paperless/src_v2.12.1.bak

# Copy new source
cp -r /opt/paperless/paperless-ngx/src /opt/paperless/src

# Replace frontend static assets
rm -rf /opt/paperless/static
cp -r /opt/paperless/paperless-ngx/static /opt/paperless/static
```

#### Step 4: Install Dependencies

The tarball includes `requirements.txt` with exact pinned versions (~186 packages):

```bash
# PEP 668 (Debian 12+): --break-system-packages required
pip install --break-system-packages -r /opt/paperless/paperless-ngx/requirements.txt 2>&1 | tail -5
# Expects ~3-4 minutes. Installs granian, django-5.2.x, celery-5.5.x, etc.
```

#### Step 5: Switch to Granian (Breaking Change)

Replace the systemd service — the old `gunicorn.conf.py` with `ConfigurableWorker` is dead:

```bash
cat > /etc/systemd/system/paperless-webserver.service << 'UNIT'
[Unit]
Description=Paperless webserver (Granian ASGI)
After=network.target
Wants=network.target
Requires=redis.service

[Service]
WorkingDirectory=/opt/paperless/src
EnvironmentFile=/opt/paperless/paperless.conf
ExecStart=/usr/local/bin/granian --interface asgi --host 0.0.0.0 --port 8010 --workers 2 --log-level info paperless.asgi:application

# ⚠️ NOTE: systemd does NOT expand shell variables like ${PAPERLESS_PORT:-8010} in ExecStart.
# PAPERLESS_PORT from paperless.conf is sourced via EnvironmentFile and works as env var,
# but for the Granian binary we hardcode 8010 because the config file also uses 8010.
# If you need to change the port, edit both paperless.conf AND this unit file.

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
```

**Granian vs Gunicorn comparison:**
| Feature | Gunicorn | Granian |
|---------|----------|---------|
| ASGI support | Needs uvicorn worker | Native |
| Port syntax | `-b 0.0.0.0:8010` | `--host 0.0.0.0 --port 8010` |
| Workers syslog | Standard | Info level with PID |
| Interface arg | N/A | `--interface asgi` |
| App reference | `paperless.asgi:application` | Same |

#### Step 6: Fix systemd PATH for Celery

After upgrade, scheduler/consumer/task-queue may fail with "celery: command not found". systemd's PATH may not include `/usr/local/bin`. Fix all 4 units:

```bash
# Check and fix each unit
for unit in paperless-webserver paperless-consumer paperless-scheduler paperless-task-queue; do
  unit_file="/etc/systemd/system/${unit}.service"
  # Fix absent full paths in ExecStart
  sed -i 's|^ExecStart=celery\b|ExecStart=/usr/local/bin/celery|' "$unit_file"
  # Ensure EnvironmentFile is present
  if ! grep -q "EnvironmentFile" "$unit_file"; then
    sed -i 's|^ExecStart=|EnvironmentFile=/opt/paperless/paperless.conf\nExecStart=|' "$unit_file"
  fi
done

systemctl daemon-reload
```

#### Step 7: Run Database Migrations

```bash
pct exec <VMID> -- bash -c 'cd /opt/paperless/src && python3 manage.py migrate 2>&1 | tail -5'
# Expected: ~27 migrations including documents.1067-1075, mfa, paperless.0004
```

#### Step 8: Collect Static Files

```bash
pct exec <VMID> -- bash -c 'cd /opt/paperless/src && timeout 120 python3 manage.py collectstatic --noinput 2>&1'
```

**⚠️ Pitfall:** `collectstatic` may **timeout** on low-RAM LXCs or when the Django static finder takes too long. The tarball already ships with a pre-built `static/` directory at `/opt/paperless/paperless-ngx/static/`. If `collectstatic` fails or times out, copy it manually:
```bash
rm -rf /opt/paperless/static   # remove empty/incomplete static
cp -r /opt/paperless/paperless-ngx/static /opt/paperless/static
```

#### Step 9: Restart & Verify

```bash
pct exec <VMID> -- systemctl restart paperless-webserver paperless-consumer paperless-scheduler paperless-task-queue
sleep 8

# Verify port
pct exec <VMID> -- ss -tlnp | grep 8010
# Should show granian

# Verify HTTP
pct exec <VMID> -- curl -s -o /dev/null -w "%{http_code}" -m 5 http://localhost:8010/
# Expected: 302

# Verify all services active
pct exec <VMID> -- systemctl is-active paperless-webserver paperless-consumer paperless-scheduler paperless-task-queue
# All 4 must show "active"
```

### Troubleshooting: Common Upgrade Failures

#### OOM Killer (512MB RAM LXCs)

**Symptom:** `journalctl -u paperless-webserver` shows:
```
A process of this unit has been killed by the OOM killer.
```

**Fix:**
```bash
# Increase from 512MB → 2GB
pct set <VMID> -memory 2048
systemctl restart paperless-webserver
```

**Memory baseline (2.20 + Granian + 2 workers):** ~620 MB baseline, ~1 GB under load. **Minimum safe: 1.5 GB. Recommended: 2 GB.**

#### ModuleNotFoundError: paperless.workers

**Symptom:** Gunicorn fails with `class uri 'paperless.workers.ConfigurableWorker' invalid or not found`.

**Fix:** Switch to Granian (Step 5). The `paperless.workers` module was removed in 2.20.

#### systemctl restart Hangs

**Symptom:** `systemctl restart paperless-webserver` never returns (60+ second timeout).

**Fix:** Bypass systemd — start Granian directly:
```bash
pct exec <VMID> -- bash -c 'cd /opt/paperless/src && nohup /usr/local/bin/granian --interface asgi --host 0.0.0.0 --port 8010 paperless.asgi:application > /var/log/granian.log 2>&1 &'
```

Better yet: write a script locally, `scp` to PVE host, push into LXC, then `pct exec` the script.

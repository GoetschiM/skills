---
name: proxmox
description: Manage Proxmox VE — create/start/stop/destroy LXCs, SSH bootstrap, disk cleanup, API auth. Covers pve01 (Goetschi Labs) and generic Proxmox operations.
tags:
  - proxmox
  - lxc
  - pve
  - virtualization
  - goetschi-labs
triggers:
  - user says "erstell einen LXC" / "neuen Container" / "lxc erstellen"
  - user asks to manage Proxmox containers
  - LXC destroy is stuck (mounted/locked disk)
---

# Proxmox LXC Management

## API Auth

Proxmox API base: `https://<host>:8006/api2/json`

```python
import requests, urllib3
urllib3.disable_warnings()
session = requests.Session()
session.verify = False

r = session.post(f"https://{HOST}:8006/api2/json/access/ticket",
                 data={"username": "root@pam", "password": PASSWORD}, timeout=15)
data = r.json().get('data', {})
session.headers.update({"CSRFPreventionToken": data.get('CSRFPreventionToken', '')})
session.cookies.set("PVEAuthCookie", data.get('ticket', ''))
```

After login, all subsequent API calls have auth.

## List LXCs

```python
r = session.get(f"https://{HOST}:8006/api2/json/nodes/{NODE}/lxc", timeout=15)
lxcs = r.json().get('data', [])
```

## Create LXC

```python
r = session.post(f"https://{HOST}:8006/api2/json/nodes/{NODE}/lxc", json={
    "vmid": VMID,
    "ostemplate": "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst",
    "hostname": "coolify",
    "rootfs": {"size": "32G", "storage": "Disk"},
    "memory": 2048,
    "cores": 2,
    "net0": "name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,tag=VLANID",
    "password": "ROOT_PASSWORD",
    "features": "keyctl=1,nesting=1",
    "unprivileged": 1,
}, timeout=120)
```

**PITFALL**: The create task returns UPID immediately. Wait a few seconds before checking status. First boot takes ~30s.

## SSH Bootstrap (Ubuntu LXC)

Fresh Ubuntu LXCs have `PermitRootLogin prohibit-password` in sshd_config. Enable password auth via **pct exec** on the Proxmox host:

```bash
pct exec <VMID> -- bash -c 'echo PermitRootLogin yes >> /etc/ssh/sshd_config && echo PasswordAuthentication yes >> /etc/ssh/sshd_config && systemctl restart sshd'
```

**PITFALL**: pct exec needs SSH on the Proxmox host itself, not via API (API `/nodes/{node}/lxc/{vmid}/exec` returns 501 for LXCs).

**PITFALL: pct exec can timeout on long-running commands.** When running `systemctl restart` or `apt-get install` inside an LXC via `pct exec`, the SSH connection may hang if the command triggers systemd operations that take longer than the SSH timeout. Workarounds:
  1. Keep commands short — no chains of 3+ commands in one `pct exec`
  2. Use `timeout N` inside the container: `pct exec <VMID> -- timeout 30 systemctl restart paperless-webserver`
  3. When `systemctl restart` hangs silently, start the process directly (bypassing systemd): `pct exec <VMID> -- bash -c 'cd /path && PAPERLESS_PORT=8010 /usr/local/bin/gunicorn ... &'`
  4. Push a script to the PVE host and run it there rather than inline pct exec chains

## SSH Access Pattern (sshpass)

When the PVE host uses password-auth SSH (not key-only from this host):

```bash
# Install sshpass if needed
apt-get install -y sshpass

# Single command
sshpass -p '<PASSWORD>' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@<PVE_HOST> '<command>'

# Multiple commands — use script on PVE host
sshpass -p '<PASSWORD>' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@<PVE_HOST> 'cat > /tmp/script.sh << SCRIPTEOF
#!/bin/bash
pct exec 103 -- echo "step1"
pct exec 103 -- echo "step2"
SCRIPTEOF
chmod +x /tmp/script.sh && bash /tmp/script.sh'
```

**PITFALL:** Heredocs inside SSH + pct exec nesting create shell escape problems. For anything beyond 2-3 lines, write the script locally, `scp` it to the PVE host, then SSH-execute it.

**PITFALL: SSH may be public-key only.** If `sshpass` fails silently (exit code 5, no auth method tried), check SSH debug output:
```bash
sshpass -p '<PASSWORD>' ssh -v -o StrictHostKeyChecking=no root@<HOST> 'hostname' 2>&1 | tail -10
```
If the server only offers `publickey,keyboard-interactive` and `keyboard-interactive` is actually a second publickey attempt, password auth is blocked. **The password itself may be correct** but Proxmox VE's SSH is configured to refuse password-based logins. Workaround: use an authorized key.

## Destroy LXC

```python
# 1. Stop
session.post(f"https://{HOST}:8006/api2/json/nodes/{NODE}/lxc/{VMID}/status/stop", timeout=30)
time.sleep(3)

# 2. Check if still running
r = session.get(f"https://{HOST}:8006/api2/json/nodes/{NODE}/lxc/{VMID}/status/current", timeout=15)
status = r.json().get('data', {}).get('status', '?')

# 3. Delete via API
r = session.delete(f"https://{HOST}:8006/api2/json/nodes/{NODE}/lxc/{VMID}", timeout=60)
```

### Stuck Disk Cleanup

If the LXC was mounted (`pct mount <ID>`), the logical volume stays locked:

```
lvremove 'Disk/vm-<ID>-disk-0' error: Logical volume contains a filesystem in use.
```

**Fix chain:**

```bash
pct unmount <ID>              # Unmount if mounted
rm -f /etc/pve/lxc/<ID>.conf  # Delete config
lvchange -an Disk/vm-<ID>-disk-0   # Deactivate LV
lvremove -f Disk/vm-<ID>-disk-0    # Force delete
```

If `dmsetup info Disk-vm--<ID>--disk--0` shows `Open count: 1`, find the holder:

```bash
lsof /dev/Disk/vm-<ID>-disk-0  # Slow — skip if timeout risk
# Alternative: check mounts
cat /proc/mounts | grep vm-<ID>
```

Forced approach when nothing works:
```bash
dmsetup remove Disk-vm--<ID>--disk--0
lvremove -f Disk/vm-<ID>-disk-0
```

The freed disk space becomes available to the thin pool automatically. No reboot needed for config removal — space reclaims on next thin pool operation.

#### PITFALL: pve2 unreachable → `pct list` hangs → blocks all LVM ops

When pve02 is offline (returns 500/connection refused), `pct list` hangs trying to query the offline node. This prevents **all** LXC operations that depend on the node list:

```bash
# This will hang forever:
pct list
pct destroy 110 --force   # hangs if pct list is called internally

# Workaround: skip the node list and manipulate directly
umount -l /var/lib/lxc/<VMID>/rootfs   # lazy unmount if mount is hanging
dmsetup remove Disk-vm--<VMID>--disk--0   # force-remove the device mapper entry
lvchange -an Disk/vm-<VMID>-disk-0
lvremove -f Disk/vm-<VMID>-disk-0
```

**Proxmox CLI** commands that require `pve02` to be up: `pct list`, `pct destroy` (implicitly), `pct migrate`. For emergency operations when pve02 is down, go directly to LVM/dmsetup.

## Find Free VMID

Ping IDs to find free ones. Avoid `101` (often on pve02 or a VM). Common free range on pve01: 115-140.

```python
r = session.get(f"https://{HOST}:8006/api2/json/nodes/{NODE}/lxc", timeout=15)
used = {l['vmid'] for l in r.json().get('data', []) if l['vmid'] != 0}
# Gap: 110 is Dokploy-Sandbox (old), replaced by 118 Coolify
```

## SSH Key Deploy (Alternative to Password)

When pct exec is not available, deploy SSH public key to LXC via config hook or by mounting rootfs and writing `authorized_keys` directly:

```bash
# Via host rootfs access
mkdir -p /var/lib/lxc/<VMID>/rootfs/root/.ssh/
cat /root/.ssh/id_rsa.pub >> /var/lib/lxc/<VMID>/rootfs/root/.ssh/authorized_keys
chmod 600 /var/lib/lxc/<VMID>/rootfs/root/.ssh/authorized_keys
```

This only works if the container is **unprivileged** (mapped user). For privileged containers, UIDs match and this works directly.

## Docker Deployment on Non-PVE Hosts via sshpass

When you need to deploy a Docker container on a host that isn't pve01 (e.g., Dokploy host at 10.0.60.121, or any LXC with Docker):

### Quick Container Deploy

```bash
sshpass -p '<PASS>' ssh -o StrictHostKeyChecking=no root@<HOST> 'docker run -d \
  --name container_name \
  --restart unless-stopped \
  -p HOST_PORT:CONTAINER_PORT \
  -v volume_name:/data \
  -e ENV_VAR=value \
  image:tag'
```

### Check Status

```bash
sshpass -p '<PASS>' ssh -o StrictHostKeyChecking=no root@<HOST> 'docker ps --filter name=NAME --format "{{.Names}} {{.Status}} {{.Ports}}"'
```

### Update Running Container (env vars, restart policy)

```bash
sshpass -p '<PASS>' ssh -o StrictHostKeyChecking=no root@<HOST> '
docker stop container_name
docker rm container_name
docker run -d --name container_name ...same params with changes...
'
```

**Use case**: Deploying helper services (Vaultwarden, monitoring agents) alongside existing infrastructure without going through Coolify/Dokploy.

**PITFALL**: If the host runs Coolify/Dokploy, Docker containers deployed via `docker run` directly will appear in Coolify's Docker view but won't be managed by Coolify. Use Coolify projects for long-lived services.

When you're on an LXC that can SSH to the PVE host, and you need to investigate **other LXCs**:

### Pattern: Write Script → scp → pct push → pct exec

Deeply nested SSH quoting (`ssh user@host "bash -c 'su - postgres -c \"psql -c \\\"...\\\"\"'"`) breaks fast. **Never inline complex scripts in SSH args.**

**Correct approach:**

1. Write a script locally
2. `scp` it to the PVE host
3. `pct push` it into the target container
4. `pct exec` to run it inside

```bash
# 1. Write script locally
cat > /tmp/check_db.sh << 'SCRIPTEOF'
#!/bin/bash
echo "=== PSQL Check ==="
su - postgres -c "psql -c 'SELECT datname FROM pg_database WHERE datistemplate = false;'"
SCRIPTEOF

# 2. scp to PVE host
sshpass -p "$PVE_PASS" scp -o StrictHostKeyChecking=no /tmp/check_db.sh root@$PVE_HOST:/tmp/

# 3. + 4. pct push + exec in one SSH call
sshpass -p "$PVE_PASS" ssh -o StrictHostKeyChecking=no root@$PVE_HOST \
  "pct push 105 /tmp/check_db.sh /tmp/check_db.sh 2>/dev/null; \
   pct exec 105 -- timeout 30 bash /tmp/check_db.sh"
```

**PITFALL**: `pct push` may warn on first call if target dir doesn't exist — that's non-fatal. Run both commands in sequence with `;`, not `&&`, so the exec runs regardless.

### Pitfall: su - postgres fails with "Peer authentication"

When using `pct exec` to run psql, you're root, not the postgres system user. The `local all postgres peer` rule in pg_hba.conf blocks direct `psql -U postgres`. Always use:

```bash
pct exec <VMID> -- timeout 15 su - postgres -c "psql -c '...'"
```

### Mini Reference: Common Diagnostic One-Liners

```bash
# List databases (via proxmox host)
pct exec <VMID> -- timeout 10 su - postgres -c "psql -c 'SELECT datname FROM pg_database WHERE datistemplate = false;'"

# List tables in a specific database
pct exec <VMID> -- timeout 10 su - postgres -c "psql -d <dbname> -c 'SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('\"'\"'pg_catalog'\"'\"', '\"'\"'information_schema'\"'\"');'"

# Check active connections
pct exec <VMID> -- timeout 10 su - postgres -c "psql -c 'SELECT state, application_name, client_addr FROM pg_stat_activity WHERE pid <> pg_backend_pid();'"

# DB sizes
pct exec <VMID> -- timeout 10 su - postgres -c "psql -d postgres -c 'SELECT d.datname, pg_size_pretty(pg_database_size(d.datname)) FROM pg_database d WHERE d.datistemplate = false ORDER BY d.datname;'"

# Docker containers on a CT
pct exec <VMID> -- timeout 15 docker ps --format "{{.Names}}	{{.Image}}	{{.Ports}}"

# Docker container env vars (DB-related)
pct exec <VMID> -- timeout 10 bash -c 'docker inspect <container> 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin)[0]; [print(e) for e in d.get('\"'\"'Config'\"'\"',{}).get('\"'\"'Env'\"'\"',[]) if any(x in e.lower() for x in ['\"'\"'db_'\"'\"','\"'\"'database'\"'\"','\"'\"'postgres'\"'\"','\"'\"'host'\"'\"'])]"'
```

### How to Identify a Verwaiste (Orphaned) PostgreSQL Database

When checking if a PG database is still in use:

1. **Active connections**: Is anyone connected? `pg_stat_activity.backend_start` older than days = dead.
2. **Which services reference it?**: Check Docker env vars on ALL containers in all LXCs (CT100, CT118, etc.) for `DB_POSTGRESDB_HOST` / `POSTGRES_HOST` pointers.
3. **Docker-internal vs external**: If a service uses `DB_HOST=postgres` (not an IP), it's using a linked Docker container, not an external PG server.
4. **No connections + no configs pointing to it + old data = safe to drop**.

## Reference Files

- `references/proxmox-monitoring.md` — Deploy Prometheus/Loki/Grafana monitoring stack across LXC fleet (node_exporter, promtail, Grafana datasource/dashboard provisioning)
- `references/pgvector-proxmox-investigation.md` — Detailed investigation of abandoned PostgreSQL databases across Goetschi Labs LXCs
- `references/dokploy-docker-extraction.md` — Docker env extraction from Dokploy to find DB connections
- `references/vaultwarden-credential-mcp.md` — Vaultwarden deployment + credential management MCP (on mcphub-custom-mcp-deployment skill)
- `references/lxc-bind-mounts.md` — Bind-mounting host directories into LXC containers (workaround for missing NFS/CIFS capabilities)
- `references/infrastructure-scan-workflow.md` — Parallel 3-agent scan workflow + Michel's preferred format for container documentation (7 categories, key:value per line, emoji status)
- `references/goetschi-infrastruktur.md` — **Vollständiger Infrastruktur-Scan von pve01** (Stand 07.06.2026). Alle 18 Container/2 VMs mit IPs, Ports, Diensten, Docker-Containern, Datenbanken, URLs, Beschreibungen, Passwörtern. 7 Kategorien. Enthält auch offene Punkte/TODOs.

## Goetschi Labs Specifics

- **pve01**: 10.0.60.10 (NOT 10.0.60.1!). Port 8006 = WebUI, port 22 = SSH. Root password `Riotstar_PROXMOX_13` works for both SSH (`sshpass`) and Proxmox API. The 10.0.60.1 address is the **gateway** (UniFi), not pve01 — try that first when SSH fails silently.
- **pve02**: 10.0.60.x (other node), often offline
- **Dokploy Host** (CT100): SSH root@10.0.60.121 with password `Louis_one_13`. Hosts Dokploy WebUI on :3000 and direct Docker containers (Vaultwarden on :8100, etc.).
- **Coolify Host** (CT118): 10.0.60.139 (NOT 10.0.60.118). WebUI on :8000.
- **Storage**: `Disk` pool, thin provisioning
- **VLANs**: 60 (service/IoT), 10 (client), 20 (IoT old)

### Quick Access via sshpass

Once you confirm pve01 is at 10.0.60.10 (not 10.0.60.1):

```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh -o StrictHostKeyChecking=no root@10.0.60.10 'pct list'
```

**PITFALL**: Getting the wrong IP (10.0.60.1 instead of 10.0.60.10) will make you think the password is wrong. Always `pct list` immediately after a successful SSH to confirm you're on the right host.

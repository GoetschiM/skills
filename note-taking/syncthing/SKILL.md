---
name: syncthing
description: Deploy and configure Syncthing as a Docker container for file synchronization — Obsidian vault sync, cross-device file sharing, and multi-agent note synchronization
tags: [syncthing, obsidian, sync, vault]
---

# Syncthing — File Synchronization Server

## When to Use
- User wants a central Obsidian vault that syncs across PC, Android, and agent machines
- Cross-device file synchronization needed (general purpose)
- Multi-agent note-taking infrastructure (Hermes/Apollo/Nova sharing a vault)

## Safety Rules
- **NEVER** deploy on a production LXC with <5% free disk space — check `df -h /` first
- Prefer non-production hosts (Apollo, Nova) over production hosts (LXC 100)
- When deploying on production: deploy ONE container only, touch NO existing containers/configs
- Always verify available disk BEFORE deciding where to host — a full disk can crash production services
- **Notify user BEFORE deploying** if they actively use Syncthing on their phone/PC — the container appears instantly in their client and they'll see an unknown device asking to connect

## Step-by-Step

### 1. Host Selection
```bash
# Check free space on candidate hosts
df -h /
```
- Prefer host with >20GB free and Docker installed
- For Obsidian vaults: deploy on the host where a vault already exists (to seed it)
- Never deploy to a host running production Dokploy if disk is >95% full

### 2. Directory Setup
```bash
mkdir -p /opt/syncthing/config
mkdir -p /opt/syncthing/vault

# Create vault folder structure
for folder in "1-Tagebuch" "2-Kontakte" "2-Notizen" "3-Infrastruktur" "4-Projekte"; do
    mkdir -p "/opt/syncthing/vault/$folder"
done

# Create marker file (required by Syncthing)
touch /opt/syncthing/vault/.stfolder
```

### 3. Seed Existing Vault (optional but recommended)
```bash
# If a vault exists elsewhere, copy existing notes so the user has a starting point
cp -r /path/to/existing/vault/*.md /opt/syncthing/vault/
cp -r /path/to/existing/vault/*/ /opt/syncthing/vault/
```

### 4. Docker Deploy

First check if Docker Compose (V2 plugin) is available:
```bash
docker compose version 2>&1 || echo "compose not available"
```

If available, use `docker compose -f /opt/syncthing/docker-compose.yml up -d` (after creating the compose file in step 8). Otherwise, use `docker run`:

```bash
docker run -d \
  --name syncthing \
  --hostname syncthing-obsidian \
  -e PUID=0 \
  -e PGID=0 \
  -p 8384:8384 \
  -p 22000:22000/tcp \
  -p 22000:22000/udp \
  -p 21027:21027/udp \
  -v /opt/syncthing/config:/var/syncthing/config \
  -v /opt/syncthing/vault:/var/syncthing/vault \
  --restart unless-stopped \
  syncthing/syncthing:latest
```

### 5. Configure Folder in config.xml
Wait for the container to generate the default config (~5 seconds), then stop it:
```bash
docker stop syncthing
```

Edit `/opt/syncthing/config/config.xml` — add a `<folder>` element after the `</device>` section:

```xml
    <folder id="obsidian-vault" label="Obsidian Vault" path="/var/syncthing/vault" type="sendreceive" rescanIntervalS="60" fsWatcherEnabled="true" fsWatcherDelayS="10" ignorePerms="false" autoNormalize="true">
        <filesystemType>basic</filesystemType>
        <device id="DEVICE_ID" introducedBy=""></device>
        <minDiskFree unit="%">1</minDiskFree>
        <versioning></versioning>
        <copiers>0</copiers>
        <pullerMaxPendingKiB>0</pullerMaxPendingKiB>
        <hashers>0</hashers>
        <order>random</order>
        <ignoreDelete>false</ignoreDelete>
        <scanProgressIntervalS>0</scanProgressIntervalS>
        <pullerPauseS>0</pullerPauseS>
        <pullerDelayS>1</pullerDelayS>
        <maxConflicts>10</maxConflicts>
        <disableSparseFiles>false</disableSparseFiles>
        <paused>false</paused>
        <markerName>.stfolder</markerName>
        <copyOwnershipFromParent>false</copyOwnershipFromParent>
        <modTimeWindowS>0</modTimeWindowS>
        <maxConcurrentWrites>16</maxConcurrentWrites>
        <disableFsync>false</disableFsync>
        <blockPullOrder>standard</blockPullOrder>
        <copyRangeMethod>standard</copyRangeMethod>
        <caseSensitiveFS>false</caseSensitiveFS>
        <junctionsAsDirs>false</junctionsAsDirs>
        <syncOwnership>false</syncOwnership>
        <sendOwnership>false</sendOwnership>
        <syncXattrs>false</syncXattrs>
        <sendXattrs>false</sendXattrs>
        <blockIndexing>true</blockIndexing>
    </folder>
```

The device ID is in the container's startup log:
```bash
docker logs syncthing 2>&1 | grep "device ID"
```

### 6. Start Container
```bash
docker start syncthing
```

Wait for initial scan to complete:
```bash
sleep 8
docker logs syncthing 2>&1 | grep "Completed initial scan"
```

### 7. Verify
- Web UI: `http://HOST_IP:8384/` (should return HTTP 200)
- Initial folder scan: check logs for "Completed initial scan"
- Vault files visible in `/opt/syncthing/vault/`

### 8. Client Setup
Give the user:
- **Device ID** (from step 5 logs)
- **Web UI URL**: `http://<host-ip>:8384`
- Instructions:
  - PC: Install Syncthing → Add Remote Device → enter ID
  - Android: Install Syncthing-Fork → same process
  - Accept the "Obsidian Vault" folder share → choose local path

### 9. Optional: Docker Compose
For long-term management, create `/opt/syncthing/docker-compose.yml`:
```yaml
version: '3'
services:
  syncthing:
    image: syncthing/syncthing:latest
    container_name: syncthing
    hostname: syncthing-obsidian
    environment:
      - PUID=0
      - PGID=0
    volumes:
      - /opt/syncthing/config:/var/syncthing/config
      - /opt/syncthing/vault:/var/syncthing/vault
    ports:
      - 8384:8384
      - 22000:22000/tcp
      - 22000:22000/udp
      - 21027:21027/udp
    restart: unless-stopped
```

## Pitfalls
- **LXC containers** may have small UDP buffer sizes — the Syncthing warning about `failed to sufficiently increase receive buffer size` is benign
- **Root warning**: Syncthing warns about running as root/privileged user — acceptable in LXC context since the container runs as UID 0 anyway
- **First run**: the container generates a default config with NO folders configured — you must add the `<folder>` element manually
- **Firewall**: Port 8384 (Web UI), 22000 (sync), 21027 (discovery) must be reachable by clients
- **WAN sync**: Syncthing relays work out of the box, but Tailscale is recommended for performance over WAN
- **Don't forget the marker file**: Syncthing needs `/.stfolder` in each shared directory
- **Auto-accept folders**: Set `autoAcceptFolders="true"` on the local device in config.xml to auto-accept incoming folder shares from remote devices

## Ports
| Port | Protocol | Purpose |
|------|----------|---------|
| 8384 | TCP | Web UI (HTTP) |
| 22000 | TCP+UDP | Sync data transfer |
| 21027 | UDP | Local discovery (broadcast) |

## References
- `references/obsidian-vault-sync-2026-05-31.md` — Real deployment: Apollo host, vault seeding, client connection details for Goetschi Labs

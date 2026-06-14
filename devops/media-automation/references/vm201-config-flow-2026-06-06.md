# VM 201 Config Flow — 06.06.2026

## Context

Complete first-time configuration of the ArrStack on VM 201 (10.0.60.201) after Docker containers were deployed. All services were running but not configured — no root folders, no download clients, no indexers, no media.

## SSH Key Injection (no SSH password)

SSH as root failed with `Permission denied (publickey,password)`. Solution: use CasaOS File API to inject SSH key.

```bash
# CasaOS login
RESPONSE=$(curl -s 'http://10.0.60.201/v1/users/login' -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"Michel","password":"Louis_one_13"}')

# Token extraction (JWT in data.token)
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# Inject SSH public key
curl -s -X PUT "http://10.0.60.201/v1/file" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"path\":\"/root/.ssh/authorized_keys\",\"content\":\"$(cat ~/.ssh/id_rsa.pub)\\n\"}"

# Test SSH
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@10.0.60.201 "hostname"
```

## exFAT Mount Fix

The 7.4TB USB disk is exFAT. Container user `abc` (uid 1000) couldn't write because mount was `uid=300,gid=1001,dmask=0022`.

**Fix:** Update fstab + reboot (mount -o remount ignored uid/gid on exFAT):

```bash
# Check current mount
mount | grep /media/NAS

# Update fstab
# UUID=481C-5B3E /media/NAS exfat defaults,nofail,uid=1000,gid=1000,umask=000 0 0

# Reboot
reboot

# Verify after reboot
mount | grep /media/NAS
# Expected: uid=1000,gid=1000,dmask=000,fmask=000

# Test write as abc
docker exec -u abc radarr touch /movies/test.txt && echo ABC_WRITE_OK
```

## qBittorrent Password Fix

Initial password had PBKDF2 hash in config. After Docker restart (config change), password reverted. Fix: recreate container with `WEBUI_PASSWORD` env var.

## Docker Networking: qBittorrent HTTP Body Bug

**The critical finding:** Docker's userland proxy (`docker-proxy`) corrupts HTTP POST bodies for qBittorrent 5.2.1's Qt HTTP server. Login from `-p 8082:8080` always returns 401, but `docker exec ... 127.0.0.1:8080` works.

**Fix:** Use `--network host` with `WEBUI_PORT=8082`:

```bash
docker rm -f qbittorrent
docker run -d \
  --name=qbittorrent \
  --network host \
  -e PUID=1000 -e PGID=1000 -e TZ=Etc/UTC \
  -e WEBUI_PORT=8082 -e WEBUI_PASSWORD=Louis_one_13 \
  --restart unless-stopped \
  -v /DATA/AppData/qbittorrent/config:/config \
  -v /media/NAS/Downloads:/downloads \
  lscr.io/linuxserver/qbittorrent:latest
```

**Downside:** `--network host` containers can't connect to custom Docker networks. Radarr/Sonarr reach qBittorrent at the Docker gateway IP instead:

```bash
# Update Radarr download client host from 172.18.0.5 to 172.18.0.1
```

## Radarr Configuration Sequence

### 1. Root Folder
```python
POST /api/v3/rootfolder
{"path": "/movies"}  # container path, NOT host path
```

### 2. Download Client (qBittorrent)
```python
# After --network host fix, use:
{"host": "172.18.0.1", "port": 8082, "username": "admin", "password": "Louis_one_13"}
```

### 3. Indexer via Prowlarr
YTS.mx is DEAD (NXDOMAIN). Added The Pirate Bay via Cardigann:
```python
{"definitionFile": "piratebay", "baseUrl": "https://apibay.org"}
```

### 4. Add Movies
```python
# Lookup by TMDB ID, then POST with qualityProfileId=5, searchForMovie=True
```

## Authentication Setup (User Preference)

User set Forms authentication with `michel` / `Louis_one_13` on all services:

```python
# For Radarr + Sonarr:
PUT /api/v3/config/host
{"authenticationMethod": "forms", "authenticationRequired": "enabled", 
 "username": "michel", "password": "Louis_one_13"}

# For Prowlarr:
PUT /api/v1/config/host  # same payload
```

## Language Setup (User Preference: German)

```python
# Radarr + Sonarr: uiLanguage = 1 (integer; 0=English, 1=German)
UI.put("/api/v3/config/ui", {"uiLanguage": 1})

# Prowlarr: uiLanguage = "de" (string locale code)
UI.put("/api/v1/config/ui", {"uiLanguage": "de"})

# qBittorrent: API setPreferences
POST /api/v2/app/setPreferences {"locale": "de"}
```

All required container restart (Radarr, Sonarr) or page refresh (Prowlarr, qBittorrent).

## Final Credentials

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Radarr | http://10.0.60.201:7878 | michel | Louis_one_13 |
| Sonarr | http://10.0.60.201:8989 | michel | Louis_one_13 |
| Prowlarr | http://10.0.60.201:9696 | michel | Louis_one_13 |
| qBittorrent | http://10.0.60.201:8082 | admin | Louis_one_13 |

## Results

- **The Dark Knight** (1.7GB YIFY) — ✅ Imported
- **Star Wars** (7.2GB) — ✅ Imported
- **Inception** (30.7GB REMUX) — Downloaded, awaiting import
- **Interstellar** (4.5GB) — Downloaded, awaiting import
- **The Last of Us S01** — ⬇️ Downloading (via Sonarr)
- **The Last of Us S02** — ⬇️ Downloading (via Sonarr)

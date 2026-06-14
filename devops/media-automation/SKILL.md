---
name: media-automation
description: "Deploy and configure the ArrStack — qBittorrent, Prowlarr, Sonarr, Radarr, and Plex — for automated media downloads with German content prioritization. Covers Docker Compose setup, indexer configuration, quality profiles, and integration patterns."
tags: [arrstack, sonarr, radarr, prowlarr, qbittorrent, plex, media, docker-compose]
category: devops
---

# Media Automation Stack — ArrStack

The "ArrStack" is the standard open-source media automation pipeline. Five components work together to automatically download, organize, and stream movies and TV shows — with full German content support.

## Trigger

- User mentions "ArrStack", "Sonarr", "Radarr", "Prowlarr", "media stack"
- User says "Filme/Serien automatisch lade", "Plex", "Torrent-Automatisierung"
- User wants to deploy a media automation stack on Dokploy or Docker host

## Architecture

```
User adds show/movie
    ↓ Sonarr (series) / Radarr (movies)
    ↓ Prowlarr (searches indexers for torrents)
    ↓ qBittorrent (downloads the file)
    ↓ Sonarr/Radarr (renames & moves to media folder)
    ↓ Plex (scans & serves the file)
```

## ⚠️ User Expectation: Full End-to-End Execution

**User will NOT do any manual setup steps.** When deploying or migrating the media stack, the agent must execute ALL work — folder creation, file transfer, container deployment, configuration — not just prepare files and wait.

Specifically:
- Write docker-compose.yml to the target host (via CasaOS file API or SSH)
- Create SMB shares if needed (via CasaOS Samba API)
- Deploy containers (docker compose up -d or via CasaOS container/compose API)
- Copy media files from the source to the target
- Do NOT leave steps for the user to do themselves

## Infra (Stand 06.06.2026)

**Media-Stack + Plex → VM 201 (CasaOS) auf Proxmox 01 | 10.0.60.201**
- Prowlarr (9696) ✅ — Meta-Indexer
- Sonarr (8989) ✅ — Serien-Management
- Radarr (7878) ✅ — Film-Management (Container: linuxserver, restart=unless-stopped)
- qBittorrent (8082) ✅ — Torrent-Client (⚠️ `--network host` mode, nicht via `-p` port mapping)
- Plex (32400, host network) ✅ — Media Server
- MeTube (8081) — YouTube Downloader (separat, läuft parallel)
- 7.4TB WD USB-Platte via Pass-Through: `/media/NAS/` (exFAT, uid=1000,gid=1000,umask=000)

- **NAS Directory Layout (Stand 06.06.2026, nach Plex-Library-Korrektur):**
  - `/media/NAS/Movie/Filme/` — **🎬 Plex "Filme"-Library + Radarr-Zielordner** (Haupt-Movie-Ordner)
  - `/media/NAS/Movie/Serien/` — **📺 Plex "Serien"-Library + Sonarr-Zielordner**
  - `/media/NAS/Movie/Family&Frends/` — Plex "Familie"-Library
  - `/media/NAS/Movie/Kawasaki Ninja Videos/` — Plex "Kawasaki"-Library
  - `/media/NAS/Movie/Music/`, `/media/NAS/Movie/RAW/` — Anderi
  - `/media/NAS/Movies/` — 🏚️ **Alt (nüme bruucht, leer bis auf Testfiles)**
  - `/media/NAS/Downloads/` — ⬇️ Torrent-Downloads (Zwischenspeicher)
  - `/media/NAS/TVShows/` — 📺 Zweit-Serienordner (aktuell leer)
  - `/media/NAS/Bilder/`, `/media/NAS/Container/`, `/media/NAS/Proxmox-Backups/`, `/media/NAS/Frigate/` — Anderi Dienste

- **Plex Library Paths (aktuell):**
  | Library | Plex-Container Pfad | Host-Pfad |
  |---------|-------------------|-----------|
  | Filme | `/movies_old/Filme/` | `/media/NAS/Movie/Filme/` |
  | Serien | `/movies_old/Serien/` | `/media/NAS/Movie/Serien/` |
  | Familiie | `/movies_old/Family&Frends/` | `/media/NAS/Movie/Family&Frends/` |
  | Kawasaki Videos | `/movies_old/Kawasaki Ninja Videos/` | `/media/NAS/Movie/Kawasaki Ninja Videos/` |

  ⚠️ **CRITICAL:** Plex-Library-Pfad nach Migration prüfen! Die Library-Pfade stammen vom alten System (`/HDD/Movies/...`) und wurden NIE aktualisiert. Plex zeigt alte Filme ggf. nur aus Cache. Bei vollständigem Library-Refresh werden sie leer, wenn der Pfad nicht existiert. Korrektur via Plex UI: Bearbeiten → Pfad anpassen.

- **Container-Mounts — Radarr:**
  - `/media/NAS/Movie/Filme/` → `/movies` (Root-Folder)
  - `/media/NAS/Downloads/` → `/downloads`
  - `/DATA/AppData/radarr/config/` → `/config`

- **Container-Mounts — Plex:**
  - `/media/NAS/Movie/` → `/movies_old`
  - `/media/NAS/Movies/` → `/movies` (nicht als Library registriert)
  - `/media/NAS/TVShows/` → `/tvshows`
  - `/DATA/AppData/plex/config/` → `/config`

- **Container-Mounts — Sonarr:**
  - `/media/NAS/Movie/Serien/` → `/tv` (Root-Folder)
  - `/media/NAS/Downloads/` → `/downloads`
  - `/DATA/AppData/sonarr/config/` → `/config`

- Configs: `/DATA/AppData/<service>/config/`
- GitHub: https://github.com/GoetschiM/gl-stack/blob/dev/media-stack/

**Sandbox LXC 110 (10.0.60.136)**
- Media-Container abgebaut (disk I/O errors, nur noch Dev: Dokploy, Talk-Gateway)
- **Kein aktueller SSH-Zugriff** — Port 22 offen, aber Passwort «Louis_one_13» funktioniert nicht
- Media-Dateien müssen von hier auf VM 201 kopiert werden — momentan blockiert

## Cloud Upload (Feature Request)

**User wants finished movies auto-uploaded to Nextcloud after Radarr imports them.** Not yet implemented — idea notes:

## ⚠️ First-Time Setup Checklist

**Critical:** Deploying the containers is NOT enough. The stack does nothing until configured.
Before assuming the stack works, verify ALL of these:

```bash
# 1. Root folders MUST exist + configured in Radarr/Sonarr
curl -s 'http://localhost:7878/api/v3/rootfolder?apikey=RADARR_KEY'   # → should NOT be []
curl -s 'http://localhost:8989/api/v3/rootfolder?apikey=SONARR_KEY'   # → should NOT be []

# 2. Radarr/Sonarr MUST have movies/series added
curl -s 'http://localhost:7878/api/v3/movie?apikey=RADARR_KEY'       # → length > 0
curl -s 'http://localhost:8989/api/v3/series?apikey=SONARR_KEY'      # → length > 0

# 3. Download client (qBittorrent) MUST be configured in Radarr/Sonarr
curl -s 'http://localhost:7878/api/v3/downloadclient?apikey=RADARR_KEY'  # → has entry
curl -s 'http://localhost:8989/api/v3/downloadclient?apikey=SONARR_KEY'  # → has entry

# 4. Prowlarr apps MUST be linked
curl -s 'http://localhost:9696/api/v1/applications?apikey=PROW_KEY'  # → has Radarr + Sonarr entries

# 5. Queue should be accessible (no auth errors)
curl -s 'http://localhost:7878/api/v3/queue?apikey=RADARR_KEY'       # → 200, not auth error

# 6. Downloads directory must exist and be writable
docker exec qbittorrent ls -la /downloads/                            # → not error
```

**Common failure mode (real-world scenario 05.06.2026):**
- Stack deployed clean, all 5+ containers "Up" for 34+ hours, but **nothing happening** = 0 movies in Radarr, no root folder set
- User assumes "it's running" → but no movies were ever added → empty queue, no activity
- **Fix:** Add root folders → set qBittorrent as download client → link Prowlarr → add media
- **Verify after config:** Queue shows items / "grabbed" events in History

- **Radarr Connect → Custom Script** triggers on import/upgrade. Script runs `rclone copy` to Nextcloud WebDAV or Google Drive.
- **Challenges:** 4K movies are 30-80GB; upload bandwidth; Nextcloud on LXC 100 is 89% full.
- **Simpler alternative:** Serve `/movies` via nginx file browser or Nextcloud External Storage mount instead of uploading.

## API Configuration Pattern (Post-Deploy)

After all containers are running, configure via API (not just UI):

### 1. Add root folders
```bash
curl -s -X POST 'http://localhost:7878/api/v3/rootfolder?apikey=KEY' \
  -H 'Content-Type: application/json' \
  -d '{"path": "/movies"}'
curl -s -X POST 'http://localhost:8989/api/v3/rootfolder?apikey=KEY' \
  -H 'Content-Type: application/json' \
  -d '{"path": "/tv"}'
```

### 2. Link Prowlarr to Radarr/Sonarr
```bash
curl -s -X POST 'http://localhost:9696/api/v1/app?apikey=PROW_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Radarr",
    "implementation": "Radarr",
    "configContract": "RadarrSettings",
    "fields": [
      {"name":"prowlarrUrl","value":"http://localhost:9696"},
      {"name":"baseUrl","value":"http://172.19.0.3:7878"},
      {"name":"apiKey","value":"RADARR_KEY"},
      {"name":"syncCategories","value":[2000,2040,2045,3100000,3101000,3103000]}
    ],
    "syncLevel": "fullSync"
  }'
```
After linking, Prowlarr pushes all configured indexers to Radarr/Sonarr automatically (within ~60s).

### 3. Set quality profile
Change default profile ID for root folder, or set per-movie:
```bash
# List profiles
curl -s 'http://localhost:7878/api/v3/qualityprofile?apikey=KEY'
# Assign profile to root folder
curl -s -X PUT 'http://localhost:7878/api/v3/rootfolder/1?apikey=KEY' \
  -H 'Content-Type: application/json' \
  -d '{"path": "/movies", "defaultQualityProfileId": 5}'  # 5 = "4K+"
```

### 4. Fix permissions for linuxserver images
All `linuxserver/*` containers run as user `abc` (uid 1000). After creating media dirs:
```bash
chown -R 1000:1000 /opt/media-stack/movies /opt/media-stack/tv /opt/media-stack/downloads
```
Without this, Radarr/Sonarr log: `Folder '/movies' is not writable by user 'abc'`.

**⚠️ exFAT exception:** On exFAT filesystems, `chown` fails with `Operation not supported`. Fix via fstab uid/gid options (see exFAT section above).

### 5. Discover container path mappings for root folder setup

**Before adding root folders in Radarr/Sonarr, check what the container actually sees as mount paths.** Docker maps host paths to container-internal paths — Radarr's root folder must use the **container path**, not the host path:

```bash
docker inspect radarr | python3 -c "
import sys, json
d = json.load(sys.stdin)
for m in d[0].get('Mounts', []):
    print(f\"  {m.get('Source','?')} -> {m.get('Destination','?')}\")
"
```

**Example output (VM 201):**
```
/media/NAS/Movies -> /movies
/media/NAS/Downloads -> /downloads
```

So the root folder path in Radarr must be **`/movies`**, NOT `/media/NAS/Movies`.

### 6. Add public indexers to Prowlarr via Cardigann API

**Public indexers like YTS and 1337x use Prowlarr's `Cardigann` implementation.** The API requires `definitionFile` set to a lowercase name matching Prowlarr's built-in definition. Do NOT use the uppercase implementation name directly:

```python
import json, urllib.request

PK = "PROWLARR_API_KEY"
H = "http://localhost:9696"

# Add YTS via Cardigann
idx = {
    "name": "YTS",
    "implementation": "Cardigann",
    "configContract": "CardigannSettings",
    "fields": [
        {"name": "definitionFile", "value": "yts"},   # lowercase!
        {"name": "baseUrl", "value": "https://yts.mx"}
    ],
    "enable": True,
    "priority": 25,
    "appProfileId": 1      # "Standard" profile (ID=1)
}

url = f"{H}/api/v1/indexer?apikey={PK}"
req = urllib.request.Request(url, method="POST",
    data=json.dumps(idx).encode(),
    headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=15)
result = json.loads(resp.read().decode())
print(f"Created: {result['name']} (ID {result['id']})")
```

**List available definition files** by querying the schema:
```python
s, data = api("GET", "/api/v1/indexer/schema")
for d in data:
    if d.get("implementation") == "Cardigann":
        name = d.get("name")
        for f in d.get("fields", []):
            if f.get("name") == "definitionFile":
                print(f"  {name:30s} → definitionFile = {f.get('value')}")
```

**Known definitions (from 630+ Cardigann implementations):**
- `yts` → YTS (movies, works without login)
- `1337x` → 1337x (often **Cloudflare-blocked** — FlareSolverr needed)
- `knaben` → Knaben (requires credentials)

**Finding the right definitionFile value:** Query the schema and look for `"name": "definitionFile"` with `"value": "<name>"` in the Cardigann entries.

### 7. Quality Profile API format (cutoff must be object)

**When creating or updating quality profiles via API, the `cutoff` field must be an object `{"id": N}`, NOT a plain integer:**

```python
# CORRECT:
profile = {
    "name": "4K+1080p",
    "cutoff": {"id": 31},      # object format!
    "items": [
        {"quality": {"id": 26}, "allowed": True},  # HDTV-2160p
        {"quality": {"id": 27}, "allowed": True},  # WEB 2160p
        {"quality": {"id": 30}, "allowed": True},  # Bluray-2160p
        {"quality": {"id": 18}, "allowed": True},  # HDTV-1080p
        {"quality": {"id": 19}, "allowed": True},  # WEB 1080p
    ]
}
# WRONG (gives validation error):
# "cutoff": 31   ← causes 400 error
```

**Key quality IDs for movie profile:**
| ID | Name | Resolution |
|----|------|-----------|
| 16 | HDTV-720p | 720p |
| 18 | HDTV-1080p | 1080p |
| 19 | WEB 1080p | 1080p |
| 20 | Bluray-1080p | 1080p |
| 26 | HDTV-2160p | 4K |
| 27 | WEB 2160p | 4K |
| 30 | Bluray-2160p | 4K |
| 31 | Remux-2160p | 4K |

**If adding 1080p to an existing profile fails (ERR 400: "Qualities can only be used once"):**
- The profile may already contain the qualities but nested under a group item (quality ID 0 = "Unknown" = group placeholder)
- Read the profile first, inspect the `items` array, then modify in-place via PUT
- Safer approach: create a **new** profile instead of modifying the existing one

### 5. Find API keys
Generated on first launch. Location:
```bash
grep -oP '<ApiKey>\K[^<]+' /opt/media-stack/radarr/config/config.xml
grep -oP '<ApiKey>\K[^<]+' /opt/media-stack/sonarr/config/config.xml
grep -oP '<ApiKey>\K[^<]+' /opt/media-stack/prowlarr/config/config.xml
```

## Components

| Component | Docker Image | Purpose | Internal Port |
|-----------|-------------|---------|---------------|
| qBittorrent | `linuxserver/qbittorrent` | Torrent client | 8080 (WebUI) + 6881 (DHT) |
| Prowlarr | `linuxserver/prowlarr` | Meta-indexer connecting Sonarr/Radarr to torrent sites | 9696 |
| Sonarr | `linuxserver/sonarr` | Automated TV show management | 8989 |
| Radarr | `linuxserver/radarr` | Automated movie management | 7878 |
| Plex | `plexinc/pms-docker` | Media server streaming | 32400 |

## Quality Profiles (Goetschi Labs Preference)

**User specification for this infra:** "4K minimum / Full HD" — movies should be found in **4K (2160p)** first, falling back to **1080p** only when 4K isn't available. NO SD/720p content.

Configure Radarr quality profile as follows:
- **Primary:** 4K+ (HDTV-2160p, WEB 2160p, Bluray-2160p, Remux-2160p) — cutoff at Remux-2160p
- **Fallback:** If movies aren't found, create a "4K+1080p" profile that includes 4K + 1080p WEB/Bluray with cutoff at Bluray-2160p
- **Language:** Original (not German-specific) — Swiss user, multi-language content fine
- **NO:** SD, 720p, CAM, Telesync, BR-DISK

## Indexer Policy

**This infra operates WITHOUT VPN** (user explicit: "kein VPN"). Only **public indexers** are used:
- The Pirate Bay (general) ✅ **Works reliably** — uses `apibay.org` API, no Cloudflare
- 1337x (general) — wide coverage, but **Cloudflare-blocked** (even with FlareSolverr)
- YTS (movies) — ❌ **DEAD as of June 2026** (`yts.mx` returns NXDOMAIN). Do NOT add YTS; it no longer resolves.
- Knaben (DE meta-search) — requires credentials
- LimeTorrents — redirects to `.fun` domain, connection test fails
- Torrent9 — redirect issue, connection test fails
- EZTV — Cloudflare-blocked
- **NOT:** Private trackers (no VPN, no invite management)

## Docker Compose (Full Stack)

Definitive compose file with all services, volume mounts, and network config:

See `references/arrstack-compose.md` for the complete YAML and configuration guide.

For the Sandbox-specific compose (with 8081 port mapping and absolute paths), see `templates/sandbox-arrstack-compose.yml`.

## External NAS / SMB Storage Backend

Containers run directly on **VM 201 (NAS-Backup, CasaOS)** with 7.4TB WD USB disk. See `references/casaos-smb-storage-arch.md` for architecture, API endpoints, and deployment via CasaOS API.

Key ports on VM 201 (10.0.60.201):
- Port 80 — CasaOS Web UI (Vue.js SPA, API via /v1/*)
- Port 445 — SMB/CIFS share (guest ok, anonymous)
- Port 8081 — MeTube (YouTube downloader, nicht Teil vom Stack)
- Port 8082 — qBittorrent WebUI (wg. MeTube-Konflikt, alternativ 8081 falls frei)

**Deployment ohne SSH — über CasaOS REST API:**
1. POST /v1/users/login → get JWT token (Michel / Louis_one_13)
2. PUT /v1/file → write docker-compose.yml to /DATA/MediaStack/
3. POST /v1/folder → create directories
4. POST /v1/samba/shares → manage SMB shares

**SSH-Zugriff via SSH-Key-Injection (wenn SSH-Passwort nicht funktioniert):**
Wenn das SSH-Passwort für root auf VM 201 nicht bekannt ist oder sshpass fehlschlägt, kann SSH-Zugriff via CasaOS File-API hergestellt werden:

```bash
# 1. CasaOS Login
TOKEN=$(curl -s "http://10.0.60.201/v1/users/login" -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"Michel","password":"Louis_one_13"}' | jq -r '.data.token')

# 2. Eigenen SSH-Public-Key in authorized_keys schreiben
curl -s -X PUT "http://10.0.60.201/v1/file" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"path\":\"/root/.ssh/authorized_keys\",\"content\":\"$(cat ~/.ssh/id_rsa.pub)\"}"

# 3. Test SSH
ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no root@10.0.60.201 "hostname"
```

⚠️ **CasaOS läuft als Docker-Container mit root-Rechten** — der File-API-Endpoint `PUT /v1/file` schreibt Dateien absolut von innerhalb des Containers aus, d.h. `/root/.ssh/authorized_keys` wird auf dem **Host** (VM 201) geschrieben. Der Container hat vollen Dateisystem-Zugriff über bind-mounts, inkl. `/root/` des Hosts.

**Plex deployen mit Claim-Token:**
Siehe `templates/vm201-plex-compose.yml`. Token von https://plex.tv/claim holen, in `PLEX_CLAIM` einsetzen und deployen:
```bash
docker compose -f /DATA/MediaStack/plex-compose.yml up -d
# Oder manuell via SSH auf VM 201
```

**Port-Konflikte beachten:**
- MeTube läuft auf Port 8081 → qBittorrent muss extern auf 8082 gemappt werden
- Bei Compose-Deployment: einzeln deployen, wenn Port-Konflikt auftritt:
  ```bash
  docker compose -f /PATH/docker-compose.yml up -d # schlägt feil für qB
  docker run -d --name qbittorrent -e WEBUI_PASSWORD=xxx -p 8082:8080 ... linuxserver/qbittorrent
  ```

## Confluence Documentation

A fully-written guide (without VPN references) exists on Confluence:
- **Title:** "Media Automation Stack — ArrStack (Sonarr / Radarr / Prowlarr / qBittorrent / Plex)"
- **Parent:** 🔧 Infrastruktur (ID: 17530881)
- **URL:** https://goetschi.atlassian.net/wiki/spaces/~goe/pages/40271874/

## Status Verification

Quick health check of a running ArrStack deployment — run from the LXC or remotely via sshpass:

```bash
# Local (inside the LXC)
bash /root/.hermes/skills/devops/media-automation/scripts/arrstack-status.sh local /opt/media-stack

# Remote (from another host)
SSHPASS='Dokploy_Sandbox_24' \
  bash /root/.hermes/skills/devops/media-automation/scripts/arrstack-status.sh 10.0.60.136 /opt/media-stack
```

The script checks all 4 services via their API keys (extracted from config.xml), reports torrent count, indexers, series/movies, download clients, and disk usage.

## Common Tasks

### Add a service to an existing stack
- Go to Dokploy project → Add Service
- Use Docker image `linuxserver/<component>`
- Map volumes (config, media, downloads) and required ports
- In Sonarr/Radarr Settings → Download Clients → add qBittorrent
- In Sonarr/Radarr Settings → Indexers → add Prowlarr

### Configure for 4K content (post-deploy)
1. Radarr → Settings → Profiles → Use/Edit "4K+" profile
2. Quality: 4K (2160p) cutoff, with 1080p fallback only
3. Radarr → Settings → Indexers → enable "Automatic Search"
4. Radarr → Settings → General → enable "Download Propers and Repacks"
5. Sonarr → Settings → Profiles → Create "Full HD+" profile (1080p minimum)

### Troubleshooting
- **"No results found" in Sonarr/Radarr** → Check Prowlarr indexer connections (test button); verify indexers are not Cloudflare-blocked
- **qBittorrent not downloading** → Verify download directory writable; check qBittorrent temp password status
- **"Folder not writable by user 'abc'"** → `chown -R 1000:1000` on media directories
### Plex not showing new files → Check library path alignment first
**Häufigster Grund für "Filme fehlen in Plex":** Radarr schreibt in `/movies` (Container-Pfad für Host-Ordner A), Plex scannt aber einen anderen Pfad (Host-Ordner B oder alten Pfad). Prüfe:

```bash
# 1. Plex-Library-Pfade auslesen (via API)
curl -s 'http://127.0.0.1:32400/library/sections?X-Plex-Token=TOKEN' | grep -oP 'path="[^"]+"'

# 2. Radarr/Plex Mounts vergleichen
docker inspect radarr --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
docker inspect plex --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

# 3. Korrektur: Entweder Radarr-Mount ändern (Container neu) oder Plex-Library-Pfad anpassen
```
Siehe ausführlichen Fix unten im Pitfall "Plex Library Path Alignment".

- **qBittorrent not downloading** → Verify download directory writable; check qBittorrent temp password status
- **Compose deployment hangs** → Use `background=true` + `notify_on_complete=true` in terminal()
- **Docker DB corruption after LXC stop** → Remove `/var/lib/docker/volumes/metadata.db` and restart Docker

## Pitfalls

### Documentation Locations (User Expectation)

**User expects ALL ArrStack documentation in 3 places at minimum:**
1. **Confluence** — structured wiki page under "Infrastruktur" (parent ID: 17530881)
2. **Obsidian** — note in the vault under `3-Infrastruktur/`
3. **Skill** — this file (SKILL.md) must contain all credentials, URLs, and recovery procedures

When setting up or making changes to the ArrStack, **always document in all three places**.

Current documentation links:
- Confluence: https://goetschi.atlassian.net/wiki/spaces/~goe/pages/40992769
- Obsidian: `/opt/data/home/Documents/Obsidian Vault/3-Infrastruktur/Media Automation Stack (ArrStack).md`
- Skill: `/root/.hermes/skills/devops/media-automation/SKILL.md`

### qBittorrent Docker Networking: `--network host` REQUIRED (not `-p`)

**CRITICAL: Docker userland proxy corrupts qBittorrent HTTP requests.** When qBittorrent runs with `-p 8082:8080` (default Docker port mapping), the `docker-proxy` userland process interferes with HTTP request body parsing. Symptoms:

- Login via API (`POST /api/v2/auth/login`) returns **HTTP 401** from all external connections
- Same credentials work perfectly when called **from inside the container** (`127.0.0.1:8080`)
- Root URL `/` returns `"Unauthorized"` text instead of the WebUI login form
- Docker logs show: `Http::RequestParser::ParseResult ... body parsing error`

**🔧 Fix — use `--network host` instead of `-p`:**

```bash
# WRONG — Docker proxy breaks HTTP body parsing:
docker run -d \
  -p 8082:8080 \
  -e WEBUI_PORT=8080 \
  -e WEBUI_PASSWORD=Louis_one_13 \
  lscr.io/linuxserver/qbittorrent:latest

# CORRECT — host networking bypasses the proxy:
docker run -d \
  --name=qbittorrent \
  --network host \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e WEBUI_PORT=8082 \
  -e WEBUI_PASSWORD=Louis_one_13 \
  -e TORRENTING_PORT=6881 \
  --restart unless-stopped \
  -v /DATA/AppData/qbittorrent/config:/config \
  -v /media/NAS/Downloads:/downloads \
  lscr.io/linuxserver/qbittorrent:latest
```

**Key differences:**
- `WEBUI_PORT=8082` (not 8080) — because `--network host` shares the host's port namespace. Since MeTube uses 8081, use 8082 directly.
- No `-p` flag — qBittorrent binds directly to `*:8082`
- Torrenting port 6881 is exposed directly without port mapping
- After starting, verify: `ss -tlnp | grep 8082` should show `qbittorrent-nox` listening

**⚠️ Trade-off with `--network host`:**
- The container CANNOT be connected to custom Docker networks (e.g., `mediastack_media_net`)
- Radarr/Sonarr reach qBittorrent via the host's Docker gateway IP (`172.18.0.1` or `172.17.0.1`)
- Update Radarr/Sonarr download client host to `172.18.0.1` (the gateway of the shared network)
- Add `--restart unless-stopped` to ensure auto-restart after reboot

**⚠️ Fallback if `--network host` can't be used:** Only iptables DNAT without Docker proxy. But the `--network host` approach is simpler and more reliable.

**Verification that login works from outside:**
```bash
curl -s -w '\nHTTP: %{http_code}' -X POST \
  -d 'username=admin&password=Louis_one_13' \
  'http://10.0.60.201:8082/api/v2/auth/login'
# Expected: HTTP 204 (empty body = success)
```

**Verification that WebUI login form loads:**
```bash
curl -s 'http://10.0.60.201:8082/' | head -c 100
# Expected: '<!DOCTYPE html>' — the login page HTML
```

**linuxserver/qbittorrent generates a temporary password on first boot (or after config reset).** The default `admin/adminadmin` credentials fail via API login. To find the real password:

```bash
docker logs qbittorrent 2>&1 | grep -i "temporary password"
```

The temp password changes **every time the container is restarted** if the config volume is empty/reset. **Always check docker logs** after first boot before trying to configure download clients.

### qBittorrent: temp password from logs doesn't work (PBKDF2 hash stored)

**If qBittorrent was started before and has a config file with a PBKDF2 password hash, the temp password shown in `docker logs` will NOT work for API login** — qBittorrent uses the stored hash instead of the temp password for API auth. The API returns `401 Unauthorized` even with the correct temp password.

**Fix — reset the entire config:**
```bash
# 1. Stop qBittorrent
docker stop qbittorrent

# 2. Delete the entire config directory (not just the conf file)
rm -rf /opt/media-stack/qbittorrent/config/

# 3. Start fresh — this forces a new temp password
docker start qbittorrent
sleep 8

# 4. Get the fresh temp password
docker logs qbittorrent 2>&1 | grep -i "temporary password"
```

⚠️ **Gotcha: `docker logs` shows ALL temp passwords since container creation.** If the container has been restarted multiple times, `tail -1` gives the CURRENT session's password, but earlier ones also appear in the log. Even the last temp password from logs can give `401 Unauthorized` if qBittorrent has a stored config hash. Reset the config entirely in that case.

**Alternative — hardcode password via Docker env var (PREFERRED):**
Add `WEBUI_PASSWORD=<fixedpassword>` as environment variable in the docker-compose.yml. After restart, that fixed password works for both WebUI and API login. **This is the more reliable approach** — no config reset needed, and the password survives restarts.

**Alternative — set password via API (no restart needed):**
If you already have a working temp password and want to set a fixed one without restarting:

```bash
# 1. Login with temp password
SID=$(curl -s -c /tmp/qb.cookies "http://127.0.0.1:8080/api/v2/auth/login" \
  -d "username=admin&password=TEMP_PW")

# 2. Set new password via Preferences API
curl -s "http://127.0.0.1:8080/api/v2/app/setPreferences" \
  -b /tmp/qb.cookies \
  -d 'json={"web_ui_password":"radarrpass2026"}'

# 3. Verify — HTTP 200 = success
curl -s -c /tmp/qb2.cookies "http://127.0.0.1:8080/api/v2/auth/login" \
  -d "username=admin&password=radarrpass2026"
# Expected: raw HTTP response 204 No Content (empty body = success)

# 4. The config file now has Password_PBKDF2 hash saved
cat /config/qBittorrent/qBittorrent.conf | grep Password
```

⚠️ **Note:** The API returns HTTP 204 with empty body on success — NOT "Ok." as documented. An empty response does NOT mean failure.

### LXC disk full: 4K REMUX files fill 110G fast — fstrim recovery

**Disk constraint:** LXC 110 (sandbox) has a 110G thin-provisioned LVM disk. 4K REMUX movies are 30-80GB each, so just 2-3 concurrently downloading REMUX files can fill the disk completely. Once 100% full, ALL container operations fail (docker exec, file writes, docker start).

**Symptoms of a full disk:**
```bash
df -h /                         # Shows 100% use
docker exec qbittorrent ...     # "no space left on device"
docker logs qbittorrent ...     # Works (log is on overlay)
pct exec <LXC> -- lsof +L1      # Shows deleted files still held open by processes
```

**Recovery procedure when disk is 100% full:**

1. **Pause/stop qBittorrent** — torrent download files are held open by qBittorrent's PID. Even after `rm -f`, the space is not freed until the process closes the file descriptor.
```bash
pct exec <LXC> -- docker stop qbittorrent
```

2. **Delete incomplete/complete torrent data** from the downloads directory:
```bash
pct exec <LXC> -- rm -rf /opt/media-stack/downloads/*
```

3. **Verify with lsof** that no processes still hold deleted files:
```bash
pct exec <LXC> -- lsof +L1 | grep deleted
```

4. **Trim the LVM thin volume** from the Proxmox HOST (cannot be done from inside unprivileged LXC — `fstrim` gives "Operation not permitted"):
```bash
# On Proxmox host:
pct fstrim <LXC>
```

5. **Verify freed space** from both host and container:
```bash
pct exec <LXC> -- df -h /
# Host:
lvs | grep vm-<LXC>            # Should show lower data_percent
```

**Why this works:** LVM thin-provisioned volumes report 100% usage even after files are deleted, because the thin pool still has the blocks allocated. `pct fstrim` sends the SCSI UNMAP/DISCARD command down to the thin pool, which releases the blocks. Without it, the LXC stays at 100% forever.

**Prevention — avoid REMUX quality on 110G disk:**
- REMUX 4K = 30-80GB per movie (fits 1-3 movies on 110G)
- x265/AV1 4K = 5-15GB per movie (fits 7-15 movies on 110G)
- WEB 2160p = 4-10GB per movie (fits 10-20 movies on 110G)
- **Set quality profile to exclude REMUX** for this LXC — use "4K x265" or "WEB 2160p" cutoff

### Simultaneous SQLite "disk I/O error" in Radarr + Sonarr → disk full

**When Radarr AND Sonarr both show identical SQLite `disk I/O error` responses from their APIs, the root cause is almost certainly a full LXC disk, not individual DB corruption.** Both apps use SQLite databases on the same volume, so a filesystem-level failure affects them identically.

**API symptom:**
```json
{"message": "disk I/O error", "description": "System.Data.SQLite.SQLiteException: disk I/O error"}
```

**Diagnosis — check disk usage (inside LXC):**
```bash
df -h /
# If 100%, follow the fstrim recovery procedure above
```

**Why both fail simultaneously:** Radarr and Sonarr DBs are separate files but share the same ext4 filesystem on the same thin-provisioned LVM volume. When the LVM pool is overcommitted or the disk fills to 100%, SQLite cannot allocate new pages in any DB on that filesystem, producing the same error for all SQLite-based services.

**Prevention:** Monitor disk usage on the media LXC weekly. The 110G thin disk can hold ~2-3 4K REMUX files.

### Using Prowlarr health API as stack-wide status

When Radarr/Sonarr are down, Prowlarr's health API still works and reports all application failures:

```bash
curl -s "http://10.0.60.136:9696/api/v1/health?apikey=PROW_KEY"
```

Response format:
```json
[{
    "source": "ApplicationLongTermStatusCheck",
    "type": "error",
    "message": "All applications are unavailable due to failures for more than 6 hours"
}]
```

This is useful for remote diagnostics when you can't access the LXC directly.

### Real-world recovery transcript (2026-06-02)

For a detailed step-by-step transcript of recovering from 100% disk on LXC 110 (sandbox-dokploy), see `references/disk-full-recovery-2025-06-02.md`.

### qBittorrent Radarr download client: broken config recovery

**After Docker corruption / restart, the qBittorrent client in Radarr may have the wrong IP or password.** The Radarr download client config stores the old Docker IP and password hash, which breaks the chain.

**Step-by-step recovery:**

```python
import json, urllib.request

K = "RADARR_API_KEY"

# 1. GET current download clients
clients = json.load(urllib.request.urlopen(
    f"http://localhost:7878/api/v3/downloadclient?apikey={K}"))

# 2. DELETE the old broken client
cid = clients[0]["id"]
del_req = urllib.request.Request(
    f"http://localhost:7878/api/v3/downloadclient/{cid}?apikey={K}",
    method="DELETE")
urllib.request.urlopen(del_req)

# 3. CREATE new client with current IP + temp password
client = {
    "enable": True,
    "name": "qBittorrent",
    "implementation": "QBittorrent",
    "configContract": "QBittorrentSettings",
    "fields": [
        {"name": "host", "value": "172.19.0.2"},     # Check current IP!
        {"name": "port", "value": 8080},
        {"name": "username", "value": "admin"},
        {"name": "password", "value": "CURRENT_TEMP_PW"},
    ],
    "priority": 1     # REQUIRED: must be 1-50, 0 causes 400 error
}
payload = json.dumps(client).encode()
create_req = urllib.request.Request(
    f"http://localhost:7878/api/v3/downloadclient?apikey={K}",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST")
result = json.load(urllib.request.urlopen(create_req))
print(f"Created client: {result['name']} ID={result['id']}")
```

⚠️ **`priority` field MUST be 1-50.** Setting 0 or omitting it gives `'Priority' must be between 1 and 50. You entered 0.` error.

### Radarr: trigger search after fixing download client

**`MoviesSearch` with empty `movieIds: []` searches ZERO movies.** The Radarr log shows `"Performing search for 0 movies"` — all movies silently skipped. Must pass explicit movie IDs:

```python
# WRONG — searches 0 movies:
{"name": "MoviesSearch", "movieIds": []}

# CORRECT — searches movies with IDs 1,2,3,4:
{"name": "MoviesSearch", "movieIds": [1, 2, 3, 4]}

# Or use MovieEditor-style command:
# POST /api/v3/movie/editor with {"movieIds":[...], "monitored":true} first
```

**After recreating the qBittorrent client, Radarr won't automatically re-search movies.** You must trigger a search on all movies:

```python
import json, urllib.request

K = "RADARR_API_KEY"
movies = json.load(urllib.request.urlopen(
    f"http://localhost:7878/api/v3/movie?apikey={K}"))

for m in movies:
    mid = m["id"]
    cmd = json.dumps({"name": "MoviesSearch", "movieIds": [mid]}).encode()
    req = urllib.request.Request(
        f"http://localhost:7878/api/v3/command?apikey={K}",
        data=cmd,
        headers={"Content-Type": "application/json"},
        method="POST")
    urllib.request.urlopen(req, timeout=10)

# Then check queue
queue = json.load(urllib.request.urlopen(
    f"http://localhost:7878/api/v3/queue?apikey={K}"))
for q in (queue.get("records", []) if isinstance(queue, dict) else queue):
    print(f"{q.get('status','?')} | {q.get('title','?')}")
```

**History check** to verify actual downloads started:
```python
hist = json.load(urllib.request.urlopen(
    f"http://localhost:7878/api/v3/history?page=1&pageSize=20&apikey={K}"))
for r in hist.get("records", []):
    if r.get("eventType") == "grabbed":
        print(f"GRABBED: {r.get('sourceTitle','?')}")
```

### FlareSolverr Proxy Configuration in Prowlarr

FlareSolverr is configured as an **IndexerProxy** (NOT a setting in `/api/v1/config`). The API endpoint is `/api/v1/indexerproxy`:

```python
# POST /api/v1/indexerproxy
{
    "name": "FlareSolverr",
    "implementation": "FlareSolverr",       # Must match schema
    "configContract": "FlareSolverrSettings",
    "fields": [
        {"name": "host", "value": "http://172.18.0.6:8191"},   # ⚠️ field is 'host', NOT 'flareSolverrUrl'!
        {"name": "requestTimeout", "value": 60}
    ],
    "tags": []
}
```

**Key schema details (from `/api/v1/indexerproxy/schema`):**
```json
{
    "implementation": "FlareSolverr",
    "fields": [
        {"name": "host", "default": "http://localhost:8191/"},
        {"name": "requestTimeout", "default": 60, "advanced": true}
    ]
}
```

**Validation:** Prowlarr validates the proxy immediately on POST — returns 400 if unreachable from inside the container. Ensure FlareSolverr is on the same Docker network.

**After adding the proxy, restart Prowlarr:** `docker restart prowlarr`

**Limitation on this infra (VM 2025):** Even with FlareSolverr, most Cloudflare challenges time out after 15s (default). 1337x, EZTV, and LimeTorrents remain blocked. The Pirate Bay works without FlareSolverr (uses `apibay.org` API).

### Setting German Language via API

**Radarr + Sonarr** (`/api/v3/config/ui`):
```python
ui = api_get("/api/v3/config/ui")
ui["uiLanguage"] = 1   # integer: 0=English, 1=German
api_put("/api/v3/config/ui", ui)
# Requires container restart to take effect
docker restart radarr  # or sonarr
```

**Prowlarr** (`/api/v1/config/ui`):
```python
ui = api_get("/api/v1/config/ui")
ui["uiLanguage"] = "de"   # string locale code
api_put("/api/v1/config/ui", ui)
# Takes effect on next page load (no restart needed)
```

**qBittorrent** (`/api/v2/app/setPreferences`):
```python
# Set locale
data = b"json={\"locale\":\"de\"}"
# Set password
data = b"json={\"web_ui_password\":\"Louis_one_13\"}"
# Both return HTTP 200 with empty body on success
```

### qBittorrent: Known-Working Login at VM 201

After user set Forms authentication on all services (05.06.2026):

| Service | URL | Login |
|---------|-----|-------|
| Radarr | http://10.0.60.201:7878 | michel / Louis_one_13 |
| Sonarr | http://10.0.60.201:8989 | michel / Louis_one_13 |
| Prowlarr | http://10.0.60.201:9696 | michel / Louis_one_13 |
| qBittorrent | http://10.0.60.201:8082 | **admin** / Louis_one_13 |

**Note:** qBittorrent username is always `admin` (cannot be changed). Only the password can be set via API or env var.

### Setting Up Forms Authentication via API (Radarr/Sonarr/Prowlarr)

**When the user wants to set a WebUI login password (not just API keys), use the `config/host` API endpoint with `authenticationMethod: forms`:**

```python
import json, urllib.request

svc = {"host": "http://localhost:7878", "key": "RADARR_KEY"}  # or sonarr/prowlarr

# 1. Read current host config
url = f"{svc['host']}/api/v3/config/host?apikey={svc['key']}"
config = json.loads(urllib.request.urlopen(url, timeout=10).read())

# 2. Set forms auth
config["authenticationMethod"] = "forms"
config["authenticationRequired"] = "enabled"
config["username"] = "michel"
config["password"] = "Louis_one_13"

# 3. Write back
body = json.dumps(config).encode()
req = urllib.request.Request(
    f"{svc['host']}/api/v3/config/host?apikey={svc['key']}",
    method="PUT", data=body,
    headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=10)
print(f"Auth set: {resp.status}")
```

**API endpoint differences by service:**
- **Radarr + Sonarr:** `/api/v3/config/host`
- **Prowlarr:** `/api/v1/config/host`

**⚠️ Password stored as PBKDF2 hash** — the API response shows `"password": "..."` as a hash string, not the plaintext. This is normal and expected.

**⚠️ After setting auth, the next API calls must include `?apikey=...`** — the auth is additive, not replacing API key access.

### Docker-on-exFAT Deployment Pattern (General)

For a comprehensive guide covering Docker volumes vs bind mounts on exFAT, MariaDB version compatibility, Redis command syntax, and `.env` file issues, see `references/docker-on-exfat-pattern.md`.

### exFAT NAS-Disk: kein chown/chmod möglich — Fix via fstab + Reboot

Die 7.4TB WD USB-Platte auf VM 201 ist mit **exFAT** formatiert. exFAT unterstützt **keine Unix-Permissions oder Ownership** (`chown`/`chmod` funktionieren nicht). Das hat Konsequenzen:

- **Der "Folder not writable"-Fix** (`chown -R 1000:1000`) **funktioniert nicht** auf exFAT — der Befehl endet mit `Operation not supported`.
- **Problem:** Alle linuxserver-Container laufen als `abc` (uid 1000). Wenn der exFAT-Mount mit falschem `uid=` gemounted ist (z.B. `uid=300`), können die Container **nicht schreiben** — Radarr gibt `"Folder '/movies' is not writable by user 'abc'"`.
- **Prüfen:** `mount | grep /media/NAS` — die mount-Optionen müssen `uid=1000,gid=1000` und `dmask=000,fmask=000` enthalten.

**🔧 Fix — fstab anpassen + reboot (PREFERRED, persistent):**

Das System verwendet einen systemd-Mount-Unit aus `/etc/fstab`. Ein `mount -o remount` **ignoriert** die uid/gid/dmask-Änderungen auf exFAT — nur ein **Reboot** aktiviert die korrekten Optionen:

```bash
# 1. fstab mit korrekten Optionen (uid=1000,gid=1000,umask=000)
UUID=481C-5B3E /media/NAS exfat defaults,nofail,uid=1000,gid=1000,umask=000 0 0

# 2. Verify fstab
cat /etc/fstab | grep /media/NAS

# 3. Reboot (Container starten via restart=unless-stopped automatisch neu)
reboot

# 4. After reboot: verify
mount | grep /media/NAS
# Erwartet: uid=1000,gid=1000,dmask=000,fmask=000

# 5. Test write inside container
docker exec -u abc radarr touch /movies/test.txt && echo ABC_WRITE_OK
```

**⚠️ Wichtige Nuancen:**
- `umask=000` in fstab ist equivalent zu `fmask=000,dmask=000` → 777 Permissions
- Der exFAT-Kernel-Treiber **ignoriert** `mount -o remount` für uid/gid/dmask — selbst nach erfolgreichem unmount/mount bleibt der alte Wert
- Systemd-Mount-Units (`media-NAS.mount`) werden automatisch aus fstab generiert
- **Ohne Reboot:** Die einzige Alternative ist, die Dateien nicht auf exFAT zu schreiben, sondern auf einem ext4-Dateisystem

**Erkennung:** `df -T /media/NAS/` zeigt `Filesystem type: exfat`.

**Alternativ — manueller Mount (temporär, falls Reboot nicht möglich):**
```bash
# Stop all containers that access the mount
docker stop radarr sonarr prowlarr qbittorrent

# Force unmount
umount -f /media/NAS

# Mount with correct options
mount -t exfat -o uid=1000,gid=1000,dmask=000,fmask=000 /dev/sdc1 /media/NAS
```

**Hinweis zur Systemd-Mount-Unit-Prüfung:**
```bash
# Prüfen, ob eine systemd mount unit existiert
systemctl list-units --type=mount | grep -i nas

# Aktuelle Unit-Optionen anzeigen
systemctl cat media-NAS.mount
```

All linuxserver/* images run as **user `abc` with uid 1000** (mapped via `PUID=1000 PGID=1000`). If media dirs (`/movies`, `/tv`, `/downloads`) are owned by `root`, the containers can't write:

```bash
chown -R 1000:1000 /opt/media-stack/movies /opt/media-stack/tv /opt/media-stack/downloads
```

### Radarr/Sonarr: SQLite "disk I/O error" after LXC disk fills up

**Symptom:**
- Radarr/Sonarr API returns HTTP 200 but body is `{"message": "disk I/O error", "description": "System.Data.SQLite.SQLiteException: disk I/O error..."}`
- Web UI shows error or fails to load
- Other Docker containers on the same LXC work fine (qBittorrent, Prowlarr)
- `curl -v http://<host>:7878/` returns 200 (Kestrel running) but `/api/v3/movie?apikey=KEY` returns the I/O error

**Cause:**
- LXC thin-provisioned disk fills to 100% (e.g., large REMUX downloads)
- SQLite database on the container gets corrupted during a write operation that fails due to no space
- Alternatively: unclean LXC shutdown (`pct stop --skiplock`) corrupts the SQLite file

**Fix — recover from backup:**

1. If disk is full, free space first (see "LXC disk full: 4K REMUX files fill 110G fast — fstrim recovery" above):
   ```bash
   # Stop Radarr/Sonarr first
   docker stop radarr
   # Clean up completed downloads or old torrents
   rm -rf /opt/media-stack/downloads/*
   docker start radarr
   pct fstrim <LXC>     # From Proxmox host — required for LVM thin
   ```

2. If DB is still corrupt after freeing space, restore from automatic SQLite backup:
   ```bash
   # Radarr creates .db-backup files automatically after migration
   ls -la /opt/media-stack/radarr/config/radarr.db*
   # Expected files: radarr.db, radarr.db-backup, radarr.db-shm, radarr.db-wal
   
   # Restore from backup:
   docker stop radarr
   cp /opt/media-stack/radarr/config/radarr.db-backup \
      /opt/media-stack/radarr/config/radarr.db
   rm -f /opt/media-stack/radarr/config/radarr.db-shm \
         /opt/media-stack/radarr/config/radarr.db-wal
   docker start radarr
   ```

3. If no `.db-backup` exists, Radarr creates a `radarr.db.backup` on first migration. Use that.

**Prevention:**
- Set Radarr quality profile to **exclude REMUX** on small LXC disks (<200G) — REMUX 4K = 30-80GB per movie
- Configure Radarr auto-backup: Settings → General → "Backup interval" (default 7 days)
- Monitor LXC disk usage and alert before full
- After any `pct stop --skiplock`, verify Radarr/Sonarr APIs respond correctly

### Docker DB corruption after unclean LXC shutdown

If the LXC is forcefully stopped (`pct stop --skiplock`), Docker's volume metadata database can corrupt with `error while opening volume store metadata database (/var/lib/docker/volumes/metadata.db): timeout`.

**Fix:**
```bash
# 1. Kill all stale processes
pkill -9 dockerd; pkill -9 containerd

# 2. Remove stale PID file + corrupted DB
rm -f /var/run/docker.pid /run/docker.pid /run/docker.sock
rm -f /var/lib/docker/volumes/metadata.db

# 3. Start via socket activation (NOT direct service start)
#    systemctl start docker often times out after corruption.
#    Socket activation triggers dockerd automatically:
systemctl start docker.socket

# 4. Verify
ss -xlp | grep docker.sock   # Should show dockerd PID listening
docker ps                     # Should work now
```

**Socket activation vs direct start:** After metadata.db corruption, `systemctl start docker` frequently hangs (15s+ timeout) because the daemon gets stuck on volume store initialization. `systemctl start docker.socket` avoids this — the socket listens immediately, and when the first client (`docker ps`) connects, systemd lazily starts dockerd. This bypasses the corrupt-volume-store deadlock.

### Docker network IP reassignment after restart

**Every time Docker restarts (especially after corruption recovery), container IPs on the bridge network are reassigned.** This breaks Prowlarr app configs because they store raw Docker IPs (e.g. `172.19.0.3:7878` for Radarr).

**After any Docker restart, always check IPs before assuming the stack works:**

```bash
# Get current IPs
for c in radarr sonarr prowlarr qbittorrent; do
  ip=$(docker inspect "$c" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
  echo "$c: $ip"
done
```

### Cross-Container Networking: Same-Network Required

**All containers must be on the SAME Docker network for inter-service communication.** If one container (e.g. qBittorrent) was started standalone and the others via compose (custom network), they can't reach each other:

```bash
# 1. Check which networks each container is on
for c in radarr sonarr prowlarr qbittorrent; do
  echo "=== $c ==="
  docker inspect "$c" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}|{{end}}'
done

# 2. If mismatch, connect the isolated container to the stack's network
docker network connect <stack_network> qbittorrent

# 3. Verify all are now on the same subnet
# All IPs should be in the same /16 range (e.g. 172.18.0.x)
docker network inspect <stack_network> | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d[0].get('Containers', {}).values():
    print(f\"{c.get('Name','?')}: {c.get('IPv4Address','?')}\")
"

# 4. Update app configs with the correct IPs
# On the shared network, use 172.18.0.x addresses
```

**Common scenario on VM 201 (CasaOS):**
- Radarr, Sonarr, Prowlarr are deployed via CasaOS and share a custom network (e.g. `mediastack_media_net`, subnet `172.18.0.0/16`)
- qBittorrent is deployed separately via `docker run` and lands on default `bridge` network (`172.17.0.0/16`)
- **Fix:** `docker network connect mediastack_media_net qbittorrent` — then qBittorrent gets an IP on BOTH networks
- **Resulting IPs on VM 201:** Radarr `172.18.0.3`, Prowlarr `172.18.0.2`, Sonarr `172.18.0.4`, qBittorrent `172.18.0.5`

Then update Prowlarr applications API:

```bash
# Check current app configs
curl -s 'http://localhost:9696/api/v1/applications?apikey=PROW_KEY'

# Update Radarr app (ID=1) with correct IP
curl -s -X PUT 'http://localhost:9696/api/v1/applications/1?apikey=PROW_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"id":1,"enable":true,"syncLevel":"fullSync","name":"Radarr","implementation":"Radarr","configContract":"RadarrSettings","fields":[{"name":"prowlarrUrl","value":"http://172.19.0.X:9696"},{"name":"baseUrl","value":"http://172.19.0.Y:7878"},{"name":"apiKey","value":"RADARR_KEY"},{"name":"syncCategories","value":[2000,2040,2045,3100000,3101000,3103000]}]}'

# Sonarr similarly (ID=2)
```

⚠️ **Prowlarr app API endpoint is `/api/v1/applications` (plural), NOT `/api/v1/app`.** The singular form returns 404.

### Python urllib.request vs curl for API config

**When running API commands inside an LXC via `pct exec` or `lxc-attach` + SSH, complex JSON payloads suffer from quoting hell.** Bash's single-quote nesting, `&` sign interpretation in URLs, and JSON-within-strings create fragile commands.

**Reliable alternative — write a Python script directly on the LXC and execute it:**

```bash
cat > /tmp/config_arrstack.py << 'PYEOF'
import json, urllib.request

KEY = "..."
RADARR = "http://localhost:7878/api/v3"

# Lookup a movie
req = urllib.request.Request(f"{RADARR}/movie/lookup?term=tmdb:157336&apikey={KEY}")
data = json.load(urllib.request.urlopen(req))

# Add a movie with full config
m = data[0]
m["qualityProfileId"] = 5  # 4K+
m["rootFolderPath"] = "/movies"
m["monitored"] = True
m["addOptions"] = {"searchForMovie": True}
m.pop("id", None)

payload = json.dumps(m).encode()
req2 = urllib.request.Request(f"{RADARR}/movie?apikey={KEY}",
    data=payload, headers={"Content-Type": "application/json"}, method="POST")
result = json.load(urllib.request.urlopen(req2))
print(f"Added: {result['title']} ({result['year']})")
PYEOF

# Then execute it inside the LXC
pct exec <LXC> -- python3 /tmp/config_arrstack.py
```

This avoids all shell quoting issues and works reliably. Use whenever the payload has complex JSON or `&` characters in URLs.

### Port conflicts (Sandbox LXC 110)

qBittorrent uses port 8080 (WebUI). On **Sandbox LXC 110 (10.0.60.136):** port 8080 is occupied by `talk-gateway`. Map externally to 8081:
```yaml
ports:
  - "8081:8080"
  - "6881:6881"
  - "6881:6881/udp"
```
- **Docker-in-LXC:** Ensure `features: nesting=1` in Proxmox LXC config or `security.nesting=true` in Docker compose
- **VPN is optional** — the stack works without one; user preference is no VPN on Goetschi Labs infra
- **Sonarr/Radarr API keys** — generated on first launch in Settings → General; needed in Prowlarr Apps config
- **No Dokploy API access yet** — for sandbox deployment, use Dokploy Web UI or direct Docker Compose on the host

### Port-Konflikte erkennen und lösen

qBittorrent verwendet Port 8080 (WebUI) und 6881 (DHT/TCP+UDP). **Prüfe vor Deployment, ob die Ports frei sind:**

```bash
# Alle Ports des Stacks checken
ss -tlnp | grep -E '8080|9696|8989|7878'
# Oder via Docker
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

**Bekannte Konflikte auf Sandbox LXC 110 (10.0.60.136):**
- Port 8080 wird vom `talk-gateway` Container belegt
- **Lösung:** qBittorrent extern auf 8081 mappen (intern bleibt 8080):
  ```yaml
  ports:
    - "8081:8080"   # extern 8081 → intern 8080
    - "6881:6881"
    - "6881:6881/udp"
  ```

### Sonarr/Radarr erster Start: DB-Migrationen (30-60s)

Beim **ersten Start** führen Sonarr und Radarr umfangreiche SQLite-DB-Migrationen durch (50–200+ Schritte). Während dieser Zeit antwortet der HTTP-Endpoint mit **000 (Connection refused/geschlossen)**.

**Das ist normal!** Warte nicht nur auf HTTP-Code, sondern prüfe die Logs:

```bash
# Warte auf Fertigstellung
docker logs sonarr --tail 2   # Erwartet: "Hosting environment: Production"
docker logs radarr --tail 2   # Erwartet: "Content root path: /app/sonarr/bin"

# Dann HTTP-Check
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8989   # Soll 200 sein
```

Wenn der Container läuft (`docker ps` zeigt "Up X minutes") aber HTTP 000 zurückkommt → Logs checken, ob noch Migrationen laufen.

### Dokploy Compose UI "Raw" Tab funktioniert nicht (Dokploy v0.29.5)

Beim Erstellen eines Compose-Service in der Dokploy UI **wechselt der "Raw"-Tab nicht von "GitHub"** — das UI bleibt auf "GitHub" kleben und der Raw-Editor wird nie angezeigt. Dokploy hat keine öffentliche REST API (alle API-Endpoints geben 401/404 ohne gültiges Session-Cookie).

**Workaround A — Direkt per Docker Compose auf dem LXC deployen:**
```bash
pct exec <LXC> -- mkdir -p /opt/<project>/ && cat > /opt/<project>/docker-compose.yml << 'EOF'
# ... compose content ...
EOF
pct exec <LXC> -- bash -c "cd /opt/<project> && docker compose up -d"
```

**Workaround B — Compose-Content direkt in die Dokploy-Postgres-DB schreiben:**
```bash
# 1. Compose-ID finden
pct exec <LXC> -- docker exec dokploy-postgres psql -U dokploy -d dokploy \
  -c 'SELECT "composeId", name, "sourceType" FROM compose;'

# 2. sourceType auf 'raw' setzen + ComposeFile befüllen (Single Quotes escapen!)
pct exec <LXC> -- docker exec -i dokploy-postgres psql -U dokploy -d dokploy << EOF
UPDATE compose SET
  "sourceType" = 'raw',
  "composeFile" = '$(cat /opt/<project>/docker-compose.yml | sed "s/'/''/g")',
  branch = 'dev'
WHERE "composeId" = 'ID_FROM_STEP_1';
EOF
```
Danach deployed der Dokploy Background-Job automatisch innert Sekunden (kein manueller API-Call nötig).

### qBittorrent IP-Ban Prevention — zu viele Fehlversuche

**Symptom:** qBittorrent WebUI zeigt nur "Unauthorized" als Text an, kein Login-Formular. Auch mit korrektem Passwort kommt man nicht rein.

**Ursache:** qBittorrent banned IPs nach 5 fehlgeschlagenen Login-Versuchen (Standard). Der Ban dauert standardmässig 1 Stunde.

**Fix — Config anpassen + Container neustarten:**
```bash
# 1. Ban-Limit erhöhen und Ban-Dauer verkürzen
echo -e "\n[WebUI]\nMaxAuthenticationFailCount=100\nBanDuration=60" >> /DATA/AppData/qbittorrent/config/qBittorrent/qBittorrent.conf

# 2. Container neustarten (löscht in-memory Ban-Liste + aktiviert neue Config)
docker restart qbittorrent

# 3. Nach Restart prüfen: Login funktioniert wieder
curl -s -X POST 'http://10.0.60.201:8082/api/v2/auth/login' \
  -d 'username=admin&password=Louis_one_13' -w ' HTTP:%{http_code}'
# Erwartet: HTTP:204 (leer = Erfolg)
```

**Prävention:** Bei jedem neuen qBittorrent-Deployment sofort die Config mit hohem MaxAuthenticationFailCount versehen.

### Plex Library Path Alignment — Radarr-Importe unsichtbar in Plex

**Symptom:** Radarr importiert Filme erfolgreich (hasFile=true, Dateien im Ordner), aber Plex zeigt sie nicht an. Die alten Filme sind sichtbar, neue fehlen.

**Ursache:** Radarrs Root-Folder und Plex' Library-Pfad zeigen auf verschiedene Host-Ordner. Auf VM 201 typisches Szenario:
- Plex Library "Filme" hat historischen Pfad `/HDD/Movies/Filme` (vom alten System, existiert nicht mehr)
- Radarr schreibt in `/movies` -> `/media/NAS/Movies/` (neu, Plex-sichtbar aber nicht registriert)
- Korrekte Daten liegen in `/media/NAS/Movie/Filme/` (Plex-Container sieht als `/movies_old/Filme/`)

**Diagnose:**
```bash
# Plex Library-Pfade
TOKEN=$(grep -oP 'PlexOnlineToken="\K[^"]+' /DATA/AppData/plex/config/Library/Application\ Support/Plex\ Media\ Server/Preferences.xml)
curl -s "http://127.0.0.1:32400/library/sections?X-Plex-Token=$TOKEN" | grep -oP 'path="[^"]+"'

# Mounts vergleichen
echo "=== Radarr ===" && docker inspect radarr --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
echo "=== Plex ===" && docker inspect plex --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

**Fix Option A — Radarr-Mount ändern (Container neuerstellen, empfohlen):**
```bash
docker stop radarr && docker rm radarr
docker run -d --name=radarr --network=mediastack_media_net \
  -p 7878:7878 \
  -e PUID=1000 -e PGID=1000 -e TZ=Europe/Zurich \
  --restart=unless-stopped \
  -v /DATA/AppData/radarr/config:/config \
  -v /media/NAS/Movie/Filme:/movies \
  -v /media/NAS/Downloads:/downloads \
  lscr.io/linuxserver/radarr:latest

# Danach RefreshMovie für alle Filme triggern
curl -s -X POST 'http://127.0.0.1:7878/api/v3/command?apikey=KEY' \
  -H 'Content-Type: application/json' \
  -d '{"name":"RefreshMovie","movieIds":[1,2,3,4]}'  # explizite IDs!
```

**Fix Option B — Plex Library-Pfad korrigieren (via UI):**
1. http://10.0.60.201:32400/web -> Library "Filme" -> Bearbeiten
2. Pfad von `/HDD/Movies/Filme` auf `/movies_old/Filme/` ändern
3. "Bibliothek scannen" triggern

**Wichtig:** Der korrekte Plex-Pfad ist der Container-Pfad (`/movies_old/Filme/`), NICHT der Host-Pfad (`/media/NAS/Movie/Filme/`).

### Radarr-Container neuerstellen bei Mount-Änderungen

Wenn der Root-Folder von Radarr geändert werden muss, reicht ein API-Update nicht — der Docker-Mount muss neu gesetzt werden. Wichtigste Punkte:

1. **Config bleibt erhalten** — `/DATA/AppData/radarr/config/` ist ein separates Volume, alle Einstellungen bleiben
2. **Port-Mapping nicht vergessen** — bei Bridge-Netzwerk zwingend `-p 7878:7878`, sonst von aussen nicht erreichbar
3. **Nach Neustart:** Radarr braucht 10-30s für DB-Migrationen, erst dann API-ready
4. **Root-Folder via API prüfen:** `curl -s 'http://127.0.0.1:7878/api/v3/rootfolder?apikey=KEY'`
5. **RefreshMovie triggern:** Sonst erkennt Radarr existierende Dateien nicht

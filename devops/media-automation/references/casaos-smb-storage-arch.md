# CasaOS VM 201 — Media Storage & API Access

> Architecture: VM 201 (NAS-Backup) running CasaOS with 7.4TB WD USB disk as both media storage AND Docker host for the ArrStack. Plex runs separately on Proxmox 02.

## Current Architecture (Stand 03.06.2026)

```\nVM 201 (10.0.60.201) — CasaOS + Docker Host\n┌─────────────────────────────────────────┐\n│  CasaOS WebUI (Port 80)                 │\n│  SMB Shares (Port 445):                 │\n│    [NAS]   → /media/NAS                 │\n│    [Media] → /media/NAS                 │\n│  Docker Containers:                      │\n│    qBittorrent (8082) → /media/NAS/Downloads │\n│    Sonarr      (8989) → /media/NAS/TVShows   │\n│    Radarr      (7878) → /media/NAS/Movies    │\n│    Prowlarr    (9696)                      │\n│  ┌─────────────────────────────────────┐ │\n│  │ 7.4TB WD (sdc1, exFAT)             │ │\n│  │ /media/NAS/Movies     (Radarr)      │ │\n│  │ /media/NAS/Movie      (⚠️ manuell!)  │ │\n│  │ /media/NAS/TVShows    (Sonarr)      │ │\n│  │ /media/NAS/Downloads  (qBit)        │ │\n│  │ /media/NAS/Bilder                   │ │\n│  │ /media/NAS/Container                │ │\n│  │ /media/NAS/Proxmox-Backups          │ │\n│  │ /media/NAS/Frigate                  │ │\n│  └─────────────────────────────────────┘ │\n└─────────────────────────────────────────┘

Proxmox 02 (10.0.60.11)
┌─────────────────────────────┐
│  Plex (Docker, Port 32400)  │
│  → mounts SMB from VM 201   │
└─────────────────────────────┘
```

## Deploy via CasaOS API (alternative to SSH)

When SSH access isn't available, use CasaOS's internal REST API endpoints found by reverse-engineering the Web UI's JavaScript bundles.

### 1. Authentication

```bash
# Login — returns JWT access_token
curl -X POST "http://VM_IP/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"Michel","password":"PASSWORD"}'

# Save token
TOKEN=$(cat /tmp/token)
```

The API uses a `testVisionNum` mechanism: paths without `/v[2-9]` prefix get `/v1` auto-prepended. So `POST /users/login` becomes `POST /v1/users/login`.

All authenticated requests need header: `Authorization: $TOKEN`

### 2. Key API Endpoints

| Endpoint | Method | Purpose | Body/Params |
|----------|--------|---------|-------------|
| `/v1/users/login` | POST | Login | `{username, password}` |
| `/v1/users/refresh` | POST | Refresh token | `{refresh_token}` |
| `/v1/file` | PUT | Write file content | `{path, content}` |
| `/v1/file` | POST | Create empty file | `{path}` |
| `/v1/file/content` | GET | Read file content | `?path=...` |
| `/v1/folder` | POST | Create folder | `{path}` |
| `/v1/folder` | GET | List folder contents | `?path=...` |
| `/v1/storage` | GET | List mounts | — |
| `/v1/disks` | GET | List disks | — |
| `/v1/sys/utilization` | GET | CPU/RAM/net stats | — |
| `/v1/samba/shares` | GET | List SMB shares | — |
| `/v1/samba/shares` | POST | Create SMB share | `{path, anonymous}` |
| `/v1/samba/shares/{id}` | DELETE | Delete SMB share | — |
| `/v2/app_management/compose` | GET | List compose apps | — |
| `/v1/sys/ssh-login` | POST | Test SSH credentials | `{username, password, port}` |

### 3. Reverse-engineering API from JS bundles

When encountering an unknown CasaOS instance:

1. Fetch the main JS bundle from the web UI:
   ```bash
   # Get all JS file references from HTML
   curl -s http://VM_IP/ | grep -oP 'src="[^"]+\.js"' | sort -u
   
   # Main bundle usually named app.<hash>.js
   # Vendors bundle contains OpenAPI definitions
   ```

2. Extract API path patterns:
   ```bash
   # Find all API paths
   grep -oP '/v\d+/[^"'"'"'\s,)]+' app.js | sort -u
   
   # Find service definitions (PREFIX constants)
   grep -oP 'const PREFIX = "[^"]+"' app.js | sort -u
   ```

3. The `service.js` bundle section contains the axios client config:
   - `baseURL` is usually empty (same origin)
   - `testVisionNum` auto-prepends `/v1` unless path starts with `http` or `/v[2-9]`
   - Token is sent as `Authorization` header (stored in localStorage as `access_token`)
   - On 401, auto-tries `POST /v1/users/refresh` with refresh_token

4. Auth flow: Login → get `access_token` + `refresh_token` → store → send `Authorization: <token>` on all requests.

### 4. Write Docker Compose via API

```bash
# Write compose file to VM
curl -X PUT "http://VM_IP/v1/file" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"path":"/DATA/MediaStack/docker-compose.yml","content":"services:\n  ..."}'

# Read back to verify
curl -s "http://VM_IP/v1/file/content?path=/DATA/MediaStack/docker-compose.yml" \
  -H "Authorization: $TOKEN"
```

### 5. Manage SMB Shares via API

```bash
# List current shares
curl -s "http://VM_IP/v1/samba/shares" -H "Authorization: $TOKEN"

# Delete broken/old shares
curl -X DELETE "http://VM_IP/v1/samba/shares/ID" -H "Authorization: $TOKEN"

# Create new share (anonymous, writable)
curl -X POST "http://VM_IP/v1/samba/shares" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"path":"/media/NAS/Movies","anonymous":true}'

# Verify: check smb.conf
curl -s "http://VM_IP/v1/file/content?path=/etc/samba/smb.conf" \
  -H "Authorization: $TOKEN"
```

## SMB Share Configuration

Current smb.conf (auto-managed by CasaOS):
```
[global]
   workgroup = WORKGROUP
   server string = NAS-Backup
   security = user
   map to guest = bad user
   dns proxy = no

[NAS]
   path = /media/NAS
   browseable = yes
   writable = yes
   guest ok = yes
   create mask = 0777
   directory mask = 0777

[Media]
   path = /media/NAS
   comment = Movies, TVShows, Downloads
   browseable = yes
   writable = yes
   guest ok = yes
   create mask = 0777
   directory mask = 0777
```

Accessible from any host on the same network: `\\10.0.60.201\Media` or `\\10.0.60.201\NAS`

## Related

- Obsidian: `3-Infrastruktur/Media Automation Stack (ArrStack).md`
- SKILL.md: `devops/media-automation/SKILL.md`

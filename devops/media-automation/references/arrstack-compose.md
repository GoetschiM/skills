# ArrStack — Vollständige Docker Compose + Konfiguration

## Docker Compose (Full Stack)

> **⚠️ Pfad-Hinweis:** Relative Pfade (`./config/`, `./downloads/`) funktionieren nur vom Compose-Verzeichnis aus. Bei Deployment auf LXC via Dokploy absolute Pfade verwenden (z. B. `/opt/media-stack/qbittorrent/config:/config`). Siehe `templates/sandbox-arrstack-compose.yml` für ein konkretes Beispiel mit absoluten Pfaden.

```yaml
services:
  qbittorrent:
    image: linuxserver/qbittorrent:latest
    container_name: qbittorrent
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Zurich
      - WEBUI_PORT=8080
    volumes:
      - ./config/qbittorrent:/config
      - ./downloads:/downloads
    ports:
      - 8080:8080
      - 6881:6881
      - 6881:6881/udp
    restart: unless-stopped
    networks:
      - arrnet

  prowlarr:
    image: linuxserver/prowlarr:latest
    container_name: prowlarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Zurich
    volumes:
      - ./config/prowlarr:/config
    ports:
      - 9696:9696
    restart: unless-stopped
    networks:
      - arrnet

  sonarr:
    image: linuxserver/sonarr:latest
    container_name: sonarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Zurich
    volumes:
      - ./config/sonarr:/config
      - ./media/tv:/tv
      - ./downloads:/downloads
    ports:
      - 8989:8989
    restart: unless-stopped
    networks:
      - arrnet

  radarr:
    image: linuxserver/radarr:latest
    container_name: radarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Zurich
    volumes:
      - ./config/radarr:/config
      - ./media/movies:/movies
      - ./downloads:/downloads
    ports:
      - 7878:7878
    restart: unless-stopped
    networks:
      - arrnet

  plex:
    image: plexinc/pms-docker:latest
    container_name: plex
    environment:
      - TZ=Europe/Zurich
      - PLEX_CLAIM=      # Optional: Claim-Token von plex.tv/claim
    volumes:
      - ./config/plex:/config
      - ./media/tv:/tv:ro
      - ./media/movies:/movies:ro
      - ./transcode:/transcode
    ports:
      - 32400:32400
    restart: unless-stopped
    networks:
      - arrnet

networks:
  arrnet:
    driver: bridge
```

## Empfohlene Ordnerstruktur

```
/media/
├── downloads/           # qBittorrent download directory
│   ├── sonarr/          # Category for TV show downloads
│   └── radarr/          # Category for movie downloads
├── media/
│   ├── tv/              # Sonarr → organized TV shows
│   └── movies/          # Radarr → organized movies
└── config/
    ├── qbittorrent/
    ├── prowlarr/
    ├── sonarr/
    ├── radarr/
    └── plex/
```

## Ersteinrichtung (nach Docker Compose up -d)

### 1. qBittorrent WebUI
- URL: `http://<HOST>:8080`
- Login: `admin` / `adminadmin`
- **Kategorien anlegen:**
  - Tools → Options → Downloads → Categories
  - `sonarr` (Save Path: `/downloads/sonarr`)
  - `radarr` (Save Path: `/downloads/radarr`)

### 2. Prowlarr
- URL: `http://<HOST>:9696`
- Settings → Indexers → + Add:
  - **1337x** (Public, kein API-Key)
  - **The Pirate Bay** (Public)
  - **RARBG** (falls erreichbar)
  - **Torrentz2** (Meta-Search)
  - **IPTorrent** / **FileList** (Private → API-Key nötig)
- Settings → Apps → + Add:
  - **Sonarr:** Prowlarr URL: `http://sonarr:8989` + API-Key (aus Sonarr Settings → General)
  - **Radarr:** Prowlarr URL: `http://radarr:7878` + API-Key (aus Radarr Settings → General)

### 3. Sonarr
- URL: `http://<HOST>:8989`
- Settings → Media Management:
  - Root Folder: `/tv`
  - Season Folders: ON
- Settings → Download Clients:
  - Type: qBittorrent
  - Host: `qbittorrent`
  - Port: `8080`
  - Username: `admin`, Password: `adminadmin`
  - Category: `sonarr`
- Settings → Indexers → Prowlarr (wird via Prowlarr Apps automatisch gesynct)
- Settings → Profiles → + Add "German HD":
  - Qualities: 1080p, 720p (preferred order)
  - Language: **German** (crucial — prevents English downloads!)

### 4. Radarr
- URL: `http://<HOST>:7878`
- Gleiche Konfiguration wie Sonarr, aber:
  - Root Folder: `/movies`
  - Download Client Category: `radarr`
  - Quality Profile: "German BluRay" (1080p, BluRay, H.264/H.265)

### 5. Plex
- URL: `http://<HOST>:32400/web`
- Setup-Assistent durchlaufen
- Libraries:
  - **TV Shows** → Folder: `/tv`
  - **Movies** → Folder: `/movies`
- Language: Deutsch (for metadata)

## Empfohlene Indexer für deutsche Inhalte

| Indexer | Typ | URL | API-Key | Deutsche Releases |
|---------|-----|-----|---------|-------------------|
| 1337x | Public | 1337x.to | Nein | Gut — aktiv deutsch filtrerbar |
| The Pirate Bay | Public | thepiratebay.org | Nein | Oft geblockt, ggf. Mirror nötig |
| RARBG | Public | rarbg.to | Nein | Oft offline, gute Qualität |
| IPTorrent | Private | iptorrents.com | Ja | Beste Qualität, Invite nötig |
| FileList | Private | filelist.io | Ja | Sehr gute deutsche Inhalte |
| Torrentz2 | Meta | torrentz2.nz | Nein | Aggregiert andere Indexer |

## German Quality Profile (Detail)

For Sonarr/Radarr: Settings → Profiles → Create new profile:

**Name:** German HD
- **Items** (in order, drag to arrange):
  - Anime 1080p
  - HDTV 1080p
  - WEBDL 1080p
  - BluRay 1080p
  - HDTV 720p
  - WEBDL 720p
  - BluRay 720p
- **Language:** German (mandatory!)
- **Cutoff:** BluRay 1080p
- **Upgrades Allowed:** Yes, Up Until: BluRay 1080p

## Fehlerbehebung

### "No results found" — Indexer Problem
```bash
# In Prowlarr prüfen:
curl -s http://<HOST>:9696/api/v1/indexer | python3 -c "import sys,json; [print(f'{i[\"name\"]}: {i[\"enableRss\"]}/{i[\"enableSearch\"]}') for i in json.load(sys.stdin)]"
```

### qBittorrent lädt nicht
```bash
# Download-Ordner schreibbar?
ls -la /downloads  # muss PUID 1000 (oder dein PGID) gehören
# Torrent manuell testen
curl -Lo /downloads/test.torrent https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso.torrent
```

### Plex aktualisiert nicht
```bash
# Plex-Container neustarten
docker compose restart plex
# Oder Library-Scan triggern:
curl -X POST "http://<HOST>:32400/library/sections/all/refresh" -H "X-Plex-Token: <TOKEN>"
```

### Container IPs (für interne Kommunikation via Docker-Netzwerk)
| Service | Hostname (Docker intern) |
|---------|-------------------------|
| qBittorrent | `qbittorrent` |
| Prowlarr | `prowlarr` |
| Sonarr | `sonarr` |
| Radarr | `radarr` |
| Plex | `plex` |

# NextCloud Deployment — CasaOS VM 201 (PRIMARY)

## Host

**VM 201** (CasaOS, 10.0.60.201) — primäri NextCloud-Instanz (seit 06.06.2026). Ersetzt di alti LXC 100 Instanz.

**Docker Compose Pfad:** `/media/NAS/Container/Nextcloud/docker-compose.yml`

## Docker Compose Setup

### Services

| Service | Image | Internal Port | Notes |
|---------|-------|---------------|-------|
| nextcloud | `nextcloud:32.0.11` | 80 → 10081 | Apache + PHP |
| nextcloud-db | `mariadb:10.11` | 3306 | **NICHT 11.4** (Env-Var Kompatibilität) |
| nextcloud-redis | `redis:7-alpine` | 6379 | Für File Locking + Caching |

### exFAT → Docker Volumes

Die 8TB-Platte (`/dev/sdc1`) isch exFAT formatiert und uf `/media/NAS` gmounted. Alli **schriibende** Container-Dateie müend uf Docker Named Volumes (ext4) loufe:

```yaml
volumes:
  - nextcloud_db:/var/lib/mysql       # Docker volume (ext4) — MariaDB Data
  - nextcloud_redis:/data             # Docker volume (ext4) — Redis Persistenz
  - nextcloud_data:/var/www/html      # Docker volume (ext4) — Nextcloud App

volumes:
  nextcloud_db:
  nextcloud_redis:
  nextcloud_data:
```

Nume **Lese-Shares** chömed vo exFAT (schriibgschützt via Read-only Bind-Mount):

```yaml
volumes:
  - /media/NAS/Container/Dokumente:/mnt/Dokumente:ro   # Dokumänt
  - /media/NAS/Movie:/mnt/Movie:ro                      # Movies + Serien
```

### MariaDB 10.11 (NICHT 11.4!)

```yaml
services:
  nextcloud-db:
    image: mariadb:10.11
    environment:
      MYSQL_ROOT_PASSWORD: ...   # Works mit 10.11
      MYSQL_DATABASE: nextcloud
      MYSQL_USER: nextcloud
      MYSQL_PASSWORD: ...
```

**Warum nid 11.4:** MariaDB 11.4+ akzeptiert nur `MARIADB_ROOT_PASSWORD`/`MARIADB_*`. Nextcloud-Custom-Apps und `occ` bruched aber `MYSQL_*`-Vars. 10.11 isch LTS und akzeptiert beides.

### Redis Command — YAML-Block-Scalar verwende

```yaml
services:
  nextcloud-redis:
    image: redis:7-alpine
    command: >
      redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
```

**YAML-Array-Form (`command: ["redis-server", ...]`)** führt zu Parsing-Fehler. Block-Scalar `>` isch sicher.

## External Storage (8TB Shares in NextCloud)

Nach dem Deployment: Movie-Folder + Dokumente-Folder via OCC als External Storage verbinde.

```bash
# 1. App enable
docker exec nextcloud php occ app:enable files_external

# 2. Movie-Ordner verbinde (zeigt ganzi /mnt/Movie inkl. Filme/, Serien/, Music/)
docker exec nextcloud php occ files_external:create \
  /Movie local null::null \
  --config datadir=/mnt/Movie

# 3. Dokumente-Ordner verbinde
docker exec nextcloud php occ files_external:create \
  /Dokumente local null::null \
  --config datadir=/mnt/Dokumente

# 4. Verifiziere
docker exec nextcloud php occ files_external:list
```

**Wichtig:** `null::null` = kä Authentication (lokale Dateizuegriff). D'Mounts sind defaultmässig für **alli** Benutzer sichtbar.

## Cloudflare Tunnel

### Config (`/root/.cloudflared/config.yml` auf LXC 100)

```yaml
ingress:
  - hostname: nextcloud.rebelone.ch
    service: http://10.0.60.201:10081    # VM 201, HTTP (Cloudflare macht HTTPS)
  - service: http_status:404
```

### Nextcloud Config (`config.php`)

```php
'overwriteprotocol' => 'https',
'overwrite.cli.url' => 'https://nextcloud.rebelone.ch',
'overwritehost' => 'nextcloud.rebelone.ch',
```

Setze via OCC:
```bash
docker exec nextcloud php occ config:system:set overwriteprotocol --value https
docker exec nextcloud php occ config:system:set overwrite.cli.url --value "https://nextcloud.rebelone.ch"
docker exec nextcloud php occ config:system:set overwritehost --value "nextcloud.rebelone.ch"
```

**🔴 trusted_domains "Comma-String" Bug — Diagnose:** Wänn d'Domain-Fehler chunnt, `docker exec nextcloud php occ config:system:get trusted_domains --output=json` laufe. Zeigts `"localhost,nextcloud.rebelone.ch,10.0.60.201"` (alli in eim Eintrag), isches de Comma-String Bug.

**Korrekt — jede Domain separat:**

```bash
docker exec nextcloud php occ config:system:set trusted_domains 0 --value localhost
docker exec nextcloud php occ config:system:set trusted_domains 1 --value nextcloud.rebelone.ch
docker exec nextcloud php occ config:system:set trusted_domains 2 --value 10.0.60.201
```

## Verification

```bash
curl -s http://10.0.60.201:10081/status.php
# {"installed":true,"maintenance":false,"needsDbUpgrade":false,"version":"32.0.11.1"}

# Cloudflare-Zugriff:
curl -s https://nextcloud.rebelone.ch/status.php
# Söllte gliich usgseh

# External Storage:
docker exec nextcloud php occ files_external:list
# Söll Movie (Mount ID 1) + Dokumente (Mount ID 2) zeige
```

## Confluence-Doku aktualisiere

Nach Änderige am NextCloud-Setup **immer** d'Confluence-Seite "NextCloud — Datei-Sync & Dokument-Pipeline" (ID 35880981) aktualisiere.

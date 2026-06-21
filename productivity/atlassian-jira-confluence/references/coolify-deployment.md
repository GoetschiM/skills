# Coolify Deployment — Migration von Dokploy (Goetschi Labs)

## Sandbox → Coolify Migration

### CT 118 (Coolify LXC) — Infos

| Eigenschaft | Wert |
|-------------|------|
| VMID | 118 |
| IP | 10.0.60.139 |
| Coolify URL | http://10.0.60.139:8000 |
| SSH Zugang | `root@10.0.60.139` / Passwort: `Louis_one_13` |
| Host | pve01 |
| Template | Ubuntu 24.04 LTS |
| RAM | 2GB (Disk 32GB) |
| Docker | 29.5.3 |

### Quick-Install Coolify

```bash
# Auf frischem Ubuntu LXC (24.04):
curl -fsSL https://cdn.coollabs.io/coolify/install.sh -o /tmp/install.sh
bash /tmp/install.sh
# Fertig in ~2 Minuten, läuft auf Port 8000
```

### SSH in frischen LXC aktivieren (Ubuntu default: kein Root-PW-Login)

Frische Ubuntu-LXCs haben `PermitRootLogin prohibit-password`. SSH von NOVA aus blockt:

```bash
# Schritt 1: Über pve01 ins LXC und SSH konfigurieren
sshpass -p "Riotstar_PROXMOX_13" ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "pct exec <VMID> -- bash -c '
    echo PermitRootLogin yes >> /etc/ssh/sshd_config
    echo PasswordAuthentication yes >> /etc/ssh/sshd_config
    systemctl restart sshd
    echo SSH fertig'"

# Schritt 2: Von NOVA aus per sshpass in den Container
sshpass -p "Louis_one_13" ssh -o StrictHostKeyChecking=no root@<LXC_IP> "hostname"
```

**IP des neuen LXCs finden:** Über UniFi API (aktive Clients), nicht Proxmox API — keine Guest Agent Support für LXCs.

### Deployment-Strategie: Docker Compose direkt (nicht Coolify API!)

Die Coolify API benötigt ein API-Token das man im Coolify UI generieren muss. In der Praxis ist es einfacher, Docker Compose direkt via SSH auf dem LXC zu deployen und dann via Coolify UI zu verwalten:

```bash
# 1. Docker Compose auf CT118 deployen
sshpass -p "Louis_one_13" ssh root@10.0.60.139 "
  mkdir -p /opt/<stack>
  cat > /opt/<stack>/docker-compose.yml << 'YAML'
services:
  <service>:
    image: <image>:<tag>
    ...
YAML
  cd /opt/<stack>
  docker compose pull
  docker compose up -d
"

# 2. In Coolify UI (http://10.0.60.139:8000) anmelden
#    Account: michel / Riotstar_MICHEL_13
# 3. Projekte manuell anlegen (oder später per API-Token)
```

### Wichtige Stacks und ihre docker-compose.yml

**besorgsdir** (WordPress + MariaDB + Chat)
- Ports: 3034 (WP), 3035 (Chat)
- Credentials: MYSQL_ROOT_PASSWORD=besorgsdir_root_2026, WORDPRESS_DB_PASSWORD=besorgsdir_pass_2026

**dograh** (Postgres(pgvector) + Redis + MinIO)
- Ports: 5432 (PG), 6379 (Redis), 9001 (MinIO)
- Credentials: POSTGRES_PASSWORD=postgres, Redis PW=redissecret, MinIO=minioadmin/minioadmin

**Besonderheit pgvector/pgvector:pg17:** Das ist kein Standard-Postgres. Die Umgebungsvariablen sind `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — wie Standard-Postgres. Port 5432 wird intern exponiert.

### Pitfall: Custom Dockerfiles überleben keine Sandbox-Löschung

Docker-Container die **lokal gebaut** werden (Custom Dockerfiles aus Dokploy) haben ihre Build-Kontexte **nicht** in Docker Volumes — sie liegen im Verzeichnis des Projekts auf dem LXC (z.B. `/opt/moto-poschung/`). Die Images sind lokal `docker images` aber nicht in einer Registry.

**Bei Migration:**
1. Dockerfile und Build-Kontexte aus dem LXC rootfs kopieren (via `pct mount`)
2. `docker build -t <name> .` auf dem neuen LXC ausführen
3. Danach `docker compose up -d` mit dem gebauten Image

Ohne die originalen Dockerfiles + Kontexte (`Dockerfile.*`, `start.sh`, `package.json`) können Custom-Images nicht rebuildet werden.

### Pitfall: Docker auf alter Sandbox läuft nicht mehr (Disk/Timeout)

Wenn der Docker daemon auf einem alten LXC hängt (timeout bei `pct exec`), direkt die **rootfs mounten** statt `pct exec`:

```bash
pct mount 110   # mountet nach /var/lib/lxc/110/rootfs
# Dann direkter cp auf dem Host:
cp /var/lib/lxc/110/rootfs/opt/besorgsdir/docker-compose.yml /var/lib/lxc/118/rootfs/opt/
# Fertig?
pct unmount 110   # WICHTIG: vor erneutem pct mount!
```

**Achtung pct mount bleibt hängen:** `pct unmount` vor erneutem `pct mount` ausführen, sonst timeout und LVM-Lock (`Open count: 1`). Bei hängendem LVM:

```bash
rm -f /etc/pve/lxc/<VMID>.conf
umount -l /var/lib/lxc/<VMID>/rootfs 2>/dev/null
lvchange -an Disk/vm-<VMID>-disk-0 2>/dev/null  # geht oft trotzdem nicht
dmsetup remove Disk-vm--<VMID>--disk--0 2>/dev/null
lvremove -f Disk/vm-<VMID>-disk-0 2>/dev/null   # blockt bis Reboot
```
In der Regel blockt `lvremove` wegen `Open count: 1` bis zum nächsten pve01 Reboot. Der LXC ist trotzdem weg (gestoppt + Config gelöscht).

### LXC Transfer ohne SSH (wenn pct mount verfügbar)

```bash
# Auf pve01:
pct mount 110   # Sandbox (Quelle)
pct mount 118   # Coolify (Ziel)

# Configs kopieren (docker-compose.yml, .env, Dockerfile)
cp -r /var/lib/lxc/110/rootfs/opt/besorgsdir /var/lib/lxc/118/rootfs/opt/

# Achtung: Bei unprivilegierten LXCs haben Dateien mapped UIDs (100000+)
# Das stört bei cp - aber Inhalte bleiben korrekt.

pct unmount 110
pct unmount 118
```

### Post-Migration: Sandbox löschen (CT 110)

```python
session.delete("https://10.0.60.10:8006/api2/json/nodes/pve01/lxc/110", timeout=30)
```

**Pitfall: LVM-Disk hängt nach Löschung**

Der API delete gibt 200 zurück, aber der LVM-Layer kann hängen bleiben:

```
lvremove 'Disk/vm-110-disk-0' error: Logical volume contains a filesystem in use.
```

Weil vorher `pct mount 110` aufgerufen wurde. Nach dem Delete:
```bash
pct unmount 110                       # mount lösen
rm -f /etc/pve/lxc/110.conf          # Config löschen
dmsetup remove Disk-vm--110--disk--0 # force remove
lvremove -f Disk/vm-110-disk-0       # fails oft trotzdem
```

Wenn `dmsetup info` zeigt `Open count: 1`, blockt es bis zum nächsten pve01 Neustart. Der LXC ist trotzdem weg — die 110G werden beim nächsten Reboot freigegeben.

### Running Containers on Coolify (CT118) — Gesamtliste (2026-06-06)

Nach der vollständigen Produktionsmigration laufen diese Container auf CT118 (10.0.60.139):

| Container | Image | Port | Status |
|-----------|-------|------|--------|
| besorgsdir-wp | wordpress:latest | 3034 | ✅ |
| besorgsdir-db | mariadb:11 | - | ✅ |
| dograh-postgres | pgvector/pgvector:pg17 | 5432 | ✅ |
| dograh-redis | redis:7 | 6379 | ✅ |
| dograh-minio | minio/minio | 9001 | ✅ |
| n8n | n8nio/n8n:latest | 5678 | ✅ |
| n8n-postgres | postgres:17-alpine | - | ✅ |
| obsidian-couchdb | couchdb:3.4.1 | 5984 | ✅ |
| mt5-trading | goetschi-labs-mt5-tradingbot:latest (lokal built) | 3007 | ✅ |
| actual-budget | actualbudget/actual-server:latest | 5006 | ✅ |
| nextcloud | nextcloud:latest | 8090 | ✅ (8080 belegt durch Coolify) |
| nextcloud-db | postgres:16-alpine | - | ✅ |
| portainer | portainer/portainer-ce:latest | 9443 | ✅ |
| coolify | coollabsio/coolify:4.1.2 | 8000 | ✅ |

**RAM usage:** ~1GB total (bei 2GB Limit) — Nextcloud braucht 150MB+.

### What was on the old Sandbox (CT110) and not migrated

These stacks had Custom Dockerfiles that need manual rebuild:
- **moto-poschung** — Dockerfile gesichert, muss auf CT118 gebaut werden
- **nei-v2** — Dockerfile gesichert, muss auf CT118 gebaut werden
- **mt5-sandbox** — hermes-dashboard + wine-mt5, braucht Dockerfile (nicht in Registry)
- **nei-app** — Node.js PM2 App, Configs gesichert (package.json, ecosystem.config.js)

Media-stack wurde gelöscht (qBittorrent, Prowlarr, Sonarr, etc.) — vom User angefordert.

## Produktionsmigration (CT100 → CT118) — Zweite Welle

Nach der Sandbox-Migration folgte die Produktion (CT100 → CT118). Anders als bei der Sandbox wurden hier keine Stacks via pct mount kopiert, sondern **neu aufgesetzt mit public Docker Images**.

### Neue Services auf CT118 (zweite Welle)

| Service | Bild | Port | Type |
|---------|------|------|------|
| n8n + Postgres | n8nio/n8n:latest, postgres:17-alpine | 5678 | Automatisierung |
| Obsidian CouchDB | couchdb:3.4.1 | 5984 | Notizen-Sync |
| MT5 Trading Bot | Flask API, lokal gebaut | 3007 | Trading |
| Actual Budget | actualbudget/actual-server:latest | 5006 | Finanzen |
| Nextcloud + Postgres | nextcloud:latest, postgres:16-alpine | 8090 | Filesharing |
| Portainer | portainer/portainer-ce:latest | 9443 | Docker UI |

**Total Container auf CT118:** 18 (davon 5 Coolify-Infrastruktur)

### Port-Konflikte erkennen und lösen

Auf CT118 ist **Port 8000** durch Coolify belegt. Der nächste Konflikt:

- **Port 8080** — belegt durch `coolify-proxy` (Traefik) das selbst auf 8080 lauscht
  - Nextcloud musste auf `8090:80` gelegt werden
- **Coolify UI Port 8000** — nicht mit Portainer 8000 kombinierbar → Portainer nur auf 9443
- Vor dem Deploy: `docker ps --format 'table {{.Names}}\t{{.Ports}}'` um free Ports zu checken

### Pro-Tipp: Reihenfolge der Public-Image Migration

Nicht alle Images müssen gleichzeitig. Die **empfohlene Reihenfolge** basierend auf Komplexität:

1. Portainer (1 Container, keine DB, minimal Config) → **5 Sekunden**
2. MT5 Trading Bot (1 Container, kein externer Service) → **30 Sekunden** (local build)
3. Actual Budget (1 Container, kein externer Service) → **Pull + 2 Sekunden**
4. Obsidian CouchDB (1 Container, simple Config) → **5 Sekunden**
5. n8n + Postgres (2 Container, healthcheck) → **2 Minuten**
6. Nextcloud + Postgres (2 Container, DB healthcheck) → **5 Minuten** (grosses Pull)
7. **Nicht deployen: SD15 API** (PyTorch + Modelle ~8-10GB zu gross für 32GB Disk)

### Nicht migriert (auf CT100 belassen)

Diese Services blieben auf CT100, da sie auf dedizierten LXCs laufen oder Custom Images brauchen:

- **LiteLLM** — läuft auf CT116 + Apollo CT108, unabhängig
- **Paperless-ngx** — läuft auf CT103, unabhängig
- **SD15 API** — zu gross für CT118 (8-10GB PyTorch + Modelle)
- **moto-poschung** — Next.js Custom App, Source auf CT100 (package.json + Dockerfile bekannt, Image zu gross zum Export)
- **Google MCP** — sollte auf MCPHub laufen, nicht auf Coolify
- **Caddy + nginx-ssl** — SSL Proxy, falls HTTPS gebraucht wird

### Coolify Idle Container Stop aktivieren

Coolify **unterstützt kein Auto-Stop direkt** (es ist kein Serverless-Anbieter). Stattdessen:

**Docker Compose restart policies** setzen:
```yaml
services:
  my-service:
    restart: unless-stopped
```

**Praktischer Workaround für Goetschi Labs:** Ein cronjob der idle Container per `docker inspect` prüft und stoppt:
```bash
for c in $(docker ps --format '{{.Names}}'); do
  uptime=$(docker inspect $c --format '{{.State.StartedAt}}')
  # Rechne: wenn > 2h her und kein aktiver Port? stop
done
```

### Proxmox LXC Verwaltung nach Migration

Siehe `proxmox` Skill für komplette LXC-Lifecycle-Doku.

**Wichtige Änderungen am Infrastruktur-Status:**
- CT110 (Dokploy-Sandbox) → ❌ gelöscht
- CT118 (Coolify-Sandbox) → ✅ aktiv, 10.0.60.139:8000
- CT100 (Dokploy-Produktion) → läuft noch, teilweise migriert

## Migrations-Workflow: Von Dokploy Docker Swarm zu docker-compose

Dokploy deployed Docker-Container als **Swarm Services**. Diese Images existieren nur lokal im Docker-Daemon — keine Registry, kein Git-Backend.

### Herausforderungen bei Export

**Problem: Docker Image Export blockt**
```bash
# Versuch 1: docker save via pct exec → timeout (Next.js/node_modules ~500MB+)
pct exec 100 -- docker save my-app:latest | gzip > /tmp/app.tar.gz
# → Hängt nach 60s+

# Versuch 2: docker cp vom LXC rootfs in den Host → timeout bei Node_modules
pct mount 100
cp -r /var/lib/lxc/100/rootfs/path/...
# → OK für Configs, aber node_modules/ und .next/ sind zu gross
```

**Lösung: package.json rekonstruieren, dann lokal neu bauen**

1. Lese `docker exec <container> cat /app/package.json` (geht immer)
2. Kopiere nur Source-Verzeichnisse ohne `node_modules`, `.next`, `yarn-v*`
3. Baue auf dem neuen LXC: `npm install && npm run build`
4. Dockerfile aus dem Container lesen und anpassen

**Typisches moto-poschung Dockerfile:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Wenn kein Git → Source aus Container extrahieren

```bash
# Auf pve01:
docker cp <container>:/app/package.json /tmp/moto-package.json
docker cp <container>:/app/next.config.ts /tmp/moto-next.config.ts
docker cp <container>:/app/Dockerfile /tmp/moto-Dockerfile
docker cp <container>:/app/src /tmp/moto-src
docker cp <container>:/app/prisma /tmp/moto-prisma
docker cp <container>:/app/public /tmp/moto-public
docker cp <container>:/app/scripts /tmp/moto-scripts

# Transfer zu neuem LXC:
sshpass -p "Louis_one_13" ssh root@10.0.60.139 "mkdir -p /opt/moto-poschung"
tar czf - -C /tmp moto-package.json moto-next.config.ts moto-src moto-prisma ... | \
  sshpass -p "Louis_one_13" ssh root@10.0.60.139 "tar xzf - -C /opt/moto-poschung"
```

### cURL-Transfer zwischen LXCs (via pve01 HTTP Server)

```bash
# Auf pve01:
cd /tmp && python3 -m http.server 8888 &
# Von CT118:
curl -sL 'http://10.0.60.10:8888/moto-source.tar.gz' -o /tmp/moto-source.tar.gz
```

⚠️ **Achtung:** pve01's Disk wird voll wenn das image gross ist (500MB+ tarball). Lieber Source nur via dependency-freien Weg kopieren.

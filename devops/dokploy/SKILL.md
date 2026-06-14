---
name: dokploy
description: "Manage Dokploy-deployed Docker services — SSH host access, compose file editing, port publishing, service redeploy, health verification."
tags: [dokploy, docker-compose, docker-swarm, traefik, infrastructure]
related_skills: [dokploy-lxc-setup, proxmox-lxc]
---

# Dokploy — Docker Services verwalten

Dokploy ist ein Docker-Compose/Swarm Deployment-Manager. Services werden als Docker Compose Stacks deployed, mit Traefik als Reverse Proxy.

**🔴 User-Preference (26.05.2026): Dokploy hat ein MCP/REST-API. Neuen Service deployen / verwalten → ZUERST via Dokploy MCP/API versuchen, NICHT direkt SSH+paramiko.** Der User hat mich explizit korrigiert, dass das Deployment (z.B. Actual Budget) über Dokploy's MCP-Endpoint hätte laufen sollen. SSH+paramiko ist nur Fallback wenn die API nicht verfügbar oder unzureichend ist.

## Trigger

- User sagt "änder Port bei Service X", "mach Container Y erreichbar", "schau Docker-Konfiguration"
- User sagt "neuen Service deployen" → **zuerst Dokploy API/MCP versuchen, nicht direkt SSH+paramiko**
- User fragt nach Host-IP, Ports, Container-Status
- SharedArrayBuffer-Fehler bei interner Web-App → nginx-Proxy mit mkcert nötig

## Preferred: Dokploy API/MCP (empfohlen)

Dokploy stellt ein MCP/API bereit — das ist der bevorzugte Weg. SSH+paramiko nur als Fallback.

| Aspekt | Details |
|--------|---------|
| Host Production | `10.0.60.121` (❌ Port 3000 down) |
| Host Sandbox | `10.0.60.136:3000` (✅ erreichbar, Login erforderlich) |
| MCP | `@dokploy/mcp` npm package → `npx @dokploy/mcp --stdio` |
| Auth | **DOKPLOY_API_KEY** env var — Key nur via WebUI generierbar (Settings → API Keys) |
| Status | Erkundet (06.06.2026) — siehe `references/dokploy-api-notes.md` |
| REST API | **Nicht öffentlich** — alle Endpoints (`/api/*`) geben 401/404 ohne Session-Cookie |

**⚠️ Lehre (26.05.):** Beim Deploy per SSH+paramiko wurden Nextcloud-Container gelöscht (Namenskonflikt). Dokploy-API hätte Kollisionen verhindert. **⚠️ Stand 06.06.:** @dokploy/mcp benötigt einen API-Key, der nur im WebUI unter Settings → API Keys generiert werden kann — solange das Sandbox-Passwort nicht bekannt ist, bleibt nur SSH/Docker Compose als Workaround.

## Fallback: SSH+paramiko

Nur wenn Dokploy API nicht erreichbar ist.

| Property | Wert |
|----------|------|
| Host | `10.0.60.121` |
| User | `root` |
| Pass | `Louis_one_13` |
| SSH | Via **paramiko** (nicht native ssh — Password-Auth wird vom Terminal-Tool blockiert) |

**NICHT** `ssh` direkt im Terminal — das scheitert an Password-Auth. Immer `python3 -c "import paramiko; ..."` via `terminal()`.

## Compose File Struktur

```
/etc/dokploy/compose/<project-name>/code/docker-compose.yml
```

Projektname = `goetschi-labs-<service>-<random>` (z.B. `goetschi-labs-browserless-lelgmv`).

## Sandbox/Production GitOps — Goetschi Labs Stack (28.05.2026)

### 🆕 Sandbox Deployment Pattern (31.05.2026)

**Sandbox Dokploy:** `10.0.60.136:3000` (LXC 110)

Wenn der User sagt "mach Stack X auf sandbox-dokploy":

1. **Access:** Dokploy Web UI at `http://10.0.60.136:3000`
   - Login: `hermes@radislione.net` (Passwort beim User erfragen falls nicht gespeichert)
2. **SSH to LXC 110:** Via Proxmox host (`pve01`, `pct enter 110`) — direkte SSH geht nicht (Passwort unbekannt)
3. **Deployment options:**
   - **Via Dokploy UI:** Create Project → Add Services per Docker image (slow for multi-service stacks)
   - **Via direct Docker Compose on LXC:** Faster for multi-service stacks (arr-stack, etc.) — use `pct enter 110` then `docker compose up -d`
4. **Volumes:** Ensure storage directories exist before deploying (`/media/downloads`, `/media/tv`, `/media/movies`, `/config/{service}`)

**⚠️ Dokploy UI vs Docker Compose:** For stacks with 3+ interdependent services (Sonarr+Radarr+Prowlarr+qBittorrent), Docker Compose on the LXC host is faster and more reliable than creating 4 separate Dokploy services. Dokploy can still manage the stack after deployment if the compose file lives in `/opt/dokploy/stacks/<name>/`.

### Architektur

Dokploy lauft als **LXC 100** uf **pve01 (10.0.60.10)** — Proxmox VE. Apollow (Hermes, LXC 108), MinIO (505), Qdrant (506), InfluxDB (109) und andere LXCs sind auf demselben Host. Docker-in-LXC funktioniert via `features: nesting=1` in der LXC-Config.

Bei Dokploy-Crash vs. stürzt der Container ab → ALLE darauf hosted Dienste (n8n, Backups etc.) sind weg. Das hat Michel mehrmals erlebt.

### Lösung: Sandbox + GitOps

**Git-Repo:** `GoetschiM/gl-stack` (privat) — github.com/GoetschiM/gl-stack

**Branch-Strategie:**
| Branch | Zweck | Deploy auf |
|--------|-------|------------|
| `main` | Production | Dokploy LXC 100 (10.0.60.121) |
| `dev` | Sandbox/Testing | Neuer LXC (z.B. 101 oder 110) |
| `feature/*` | Neue Features | Von `dev` abzweigen |

**Workflow:**
1. Neue Docker-Compose / Config im `dev`-Branch
2. Auf Sandbox-LXC testen
3. PR `dev` → `main`
4. Production deployt vom `main`-Branch

**Repo-Struktur:**
```
gl-stack/
├── n8n/
│   ├── docker-compose.yml     # n8n + WebDAV Proxy als separated Service
│   ├── webdav_proxy.js        # Node.js Proxy für Nextcloud WebDAV
│   └── workflows/             # n8n Workflow-Exporte als JSON (aus n8n-UI exportieren)
├── litellm/
│   └── docker-compose.yml
├── .gitignore                  # .env, secrets/, credentials/
└── README.md                   # Branch-Strategie + Setup
```

**Repo-Naming-Konvention:**
- **NICHT** generisch wie "bots", "dokploy-infra" — Michel hat "hunderte Bots"
- **Präzis & repräsentativ** — z.B. `gl-stack` (Goetschi Labs Stack)
- **Privat** — immer `private: True`, nie öffentlich

### Sandbox-LXC erstellen (pve01)

```bash
# Proxmox SSH (10.0.60.10, root:<PASSWORT>)
# Template: ubuntu-24.04-standard (135MB, verfügbar auf pve01)
pct create <ID> local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname gl-sandbox \
  --memory 8192 \
  --swap 2048 \
  --cores 2 \
  --rootfs Disk:8 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1,keyctl=1 \
  --unprivileged 1 \
  --onboot 1

pct start <ID>
pct exec <ID> -- apt update && apt install -y curl docker.io docker-compose-v2
# Dokploy installieren (curl -fsSL https://dokploy.com/install.sh | sh)
# Git-Config aus gl-stack pullen
```

**Freii LXC IDs:** 101, 102, 104, 106, 110, 111, 113-119, 123-299, 302-503

**Gesamtablauf** (alle Schritte, inkl. aller Pitfalls):

### 1. Compose File mit Nginx-Proxy
Siehe `references/sharedarraybuffer-nginx-proxy.md` für vollständige Configs.

Wichtigste Punkte:
- Nginx als Reverse Proxy vorschalten (Traefik kann kein COOP/COEP)
- `proxy_hide_header` für COOP/COEP wenn Upstream bereits sendet
- COEP: `credentialless` statt `require-corp`
- HTTPS + mkcert (self-signed scheitert auf iOS)

### 2. HTTPS via mkcert (nicht Self-Signed)
```bash
mkcert -install
mkcert -cert-file /etc/ssl/<service>/fullchain.pem \
       -key-file /etc/ssl/<service>/privkey.pem \
       10.0.60.121 localhost 127.0.0.1
```

**User muss Root-CA einmalig installieren** (siehe `references/sharedarraybuffer-nginx-proxy.md`).

### 3. Deploy
```bash
cd /etc/dokploy/compose/<project>/code
docker compose up -d --remove-orphans
```

### 4. Verifizieren
```bash
curl -skI https://10.0.60.121:<PORT>/ | grep -i cross-origin
# Erwartet: same-origin + credentialless (einmal, kein Duplikat)
```

## Standard-Workflow: Port publizieren

Dokploy verwendet standardmässig **Traefik** + `expose:` — kein Host-Port. Wenn ein direkter Port gebraucht wird:

1. **SSH zum Host** via paramiko
2. **Compose File lesen**: `/etc/dokploy/compose/<project>/code/docker-compose.yml`
3. **`ports:` Sektion hinzufügen** unter dem Service:
   ```yaml
   ports:
     - "3005:3000"
   ```
   Freien Port prüfen via `ss -tlnp | grep <PORT>`.
4. **Redeployen**: `docker compose up -d --remove-orphans` im Code-Verzeichnis
5. **Verifizieren**:
   - `docker ps` → Port sollte sichtbar sein: `0.0.0.0:3005->3000/tcp`
   - `ss -tlnp` → Port sollte LISTEN zeigen
   - `curl -s http://<host>:<port>/` → Service antwortet

## Redeploy via paramiko

```python
import paramiko
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', 'Louis_one_13', timeout=10)

# Compose File per SFTP schreiben
sftp = s.open_sftp()
with sftp.open(path, 'w') as f:
    f.write(new_content)
sftp.close()

# Redeploy
i,o,e = s.exec_command(
    'cd <project-dir>/code && docker compose up -d --remove-orphans 2>&1',
    timeout=30
)
print(o.read().decode())
s.close()
```

Das `terminal()`-Tool erkennt `docker compose up` fälschlich als "long-running process". Verwende entweder `background=true` oder verpacke es in ein Python-Script via `terminal()`.

## Health-Verifikation

Nach dem Redeploy:
```python
i,o,_ = s.exec_command("docker ps --filter 'name=<service>' --format '{{.Names}} | {{.Status}} | {{.Ports}}'")
print(o.read().decode())
```

Service antwortet? Vom Hermes-Container aus via:
```bash
curl -s -o /dev/null -w "%{http_code}" http://10.0.60.121:<PORT>/<endpoint>
```

Browserless spezifisch: `/docs` gibt 301 (redirect), `/` gibt 404.

## Port Allocation Table (Stand: Letzte Aktualisierung)

```text
3000 → Dokploy WebUI
3001 → moto-poschung
3002 → tonio
3004 → familie-markt
3005 → Browserless
3006 → portfolio-michel
3011 → NEI
3013 → Worldmonitor
3014 → Nanoclaw
3023 → MCP Dokploy
3110 → Paperclip
4000 → LiteLLM
6333-6334 → Qdrant
8000 → Portainer
8015 → Paperless
9000 → MinIO
9119 → Hermes Dashboard
9443 → Portainer
```

## LXC Setup: New Dokploy Instance from Scratch

When setting up a fresh Dokploy instance on a new Proxmox LXC (sandbox/dev), follow this end-to-end flow rather than Dokploy's official install script (which uses Docker Swarm — unreliable in LXC):

### 1. LXC Create (on Proxmox pve01, 10.0.60.10)

```bash
# Template: ubuntu-24.04-standard
pct create <ID> local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname sandbox-dokploy \
  --cores 2 \
  --memory 8192 \
  --rootfs Disk:<SIZE> \
  --net0 name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,ip6=dhcp,type=veth \
  --features nesting=1 \
  --unprivileged 1 \
  --ostype ubuntu \
  --storage Disk \
  --password "<PASS>"
```

**Quorum fix** if pve02 is offline: start `pmxcfs -l -f` before pct create, then `killall pmxcfs` after.

### 2. Install Docker

```bash
apt-get update && apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo 'deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable' > /etc/apt/sources.list.d/docker.list
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose-v2
```

**Critical:** Use `docker compose` v2, NOT `docker-compose` v1 (Python). v1 fails in LXC with `"Not supported URL scheme http+docker"`.

### 3. Remove Swarm Residue (if exists)

```bash
docker rm -f $(docker ps -aq) 2>/dev/null
docker swarm leave --force 2>/dev/null
rm -rf /var/lib/docker/swarm 2>/dev/null
systemctl restart docker
```

### 4. Deploy Dokploy via Docker Compose

```yaml
services:
  postgres:
    image: postgres:16
    container_name: dokploy-postgres
    environment:
      POSTGRES_USER: dokploy
      POSTGRES_PASSWORD: <SECURE_PASS>
      POSTGRES_DB: dokploy
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - dokploy_net
    restart: unless-stopped
  redis:
    image: redis:7
    container_name: dokploy-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - dokploy_net
    restart: unless-stopped
  dokploy:
    image: dokploy/dokploy:v0.29.5
    container_name: dokploy
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://dokploy:<SECURE_PASS>@postgres:5432/dokploy
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - dokploy_net
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
```

`docker compose up -d` → wait 30s for Postgres init.

### 5. MinIO S3 Backup for Dokploy

Create bucket: `mc mb homelab/sandbox-dokploy-backup`

In Dokploy UI: Settings → Backup → S3 Compatible → endpoint `http://10.0.60.106:9000`, bucket `sandbox-dokploy-backup`.

### 6. Verification

```bash
curl -s -o /dev/null -w "%{http_code}" http://10.0.60.136:3000  # 200/307
```

See `references/dokploy-lxc-setup-ops.md` for maintenance commands, app listing, container image copying, and post-migration verification.

## 🔴 Dokploy in LXC — Docker Swarm fails, Docker Compose stattdessen

**Problem:** Der offizielle Install-Script (`curl -fsSL https://dokploy.com/install.sh | sh`) erkennt Proxmox LXC-Container und setzt `--endpoint-mode dnsrr` für Docker Swarm Services. Trotzdem schlagen **host-mode Ports** (3000, 80, 443) fehl — die Swarm-Tasks bleiben in `Preparing` oder kriegen `no suitable node (host-mode port already in use)`.

**Grund:** Docker Swarm mit host-mode Ports ist in LXC-Containern nicht zuverlässig (kein eigener Netzwerk-Stack, iptables-Einschränkungen).

**Lösung:** Dokploy per Docker Compose statt Docker Swarm betreiben (siehe `proxmox-lxc` Skill für LXC-Erstellung):

```bash
# 1. Cleanup falls Swarm-Install bereits versucht
docker swarm leave --force 2>/dev/null
docker system prune -af
docker rm -f $(docker ps -aq) 2>/dev/null

# 2. Docker Compose Setup
mkdir -p /opt/dokploy
cat > /opt/dokploy/docker-compose.yml << 'COMPOSE'
services:
  postgres:
    image: postgres:16
    container_name: dokploy-postgres
    environment:
      POSTGRES_USER: dokploy
      POSTGRES_PASSWORD: <SECURE_PASSWORD>
      POSTGRES_DB: dokploy
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - dokploy_net
    restart: unless-stopped

  redis:
    image: redis:7
    container_name: dokploy-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - dokploy_net
    restart: unless-stopped

  dokploy:
    image: dokploy/dokploy:v0.29.5
    container_name: dokploy
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://dokploy:<SECURE_PASSWORD>@postgres:5432/dokploy
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - dokploy_net
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  dokploy_net:
    driver: bridge
COMPOSE

docker compose -f /opt/dokploy/docker-compose.yml up -d
```

**Verifikation in LXC:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

## 💾 MinIO S3 Backup — Dokploy vorkonfigurieren

MinIO (10.0.60.106:9000) ist der lokale S3-kompatible Storage für Backups.

**Bei Erst-Einrichtung (Dokploy WebUI nach Setup):**
1. Dokploy unter `http://<LXC-IP>:3000` öffnen
2. Settings → Backup → S3 Compatible
3. Werte: Endpoint `http://10.0.60.106:9000`, Bucket `sandbox-dokploy-backup`, Region `us-east-1`, Access+Secret Keys

**Bucket vorher via MC-CLI erstellen:**
```bash
mc alias set homelab http://10.0.60.106:9000 <ACCESS> <SECRET>
mc mb homelab/sandbox-dokploy-backup
```

## Häufige Probleme

### 🔴 Single Point of Failure — Produktiv-Dienste nicht isolieren

**Gelernt Mai 2026:** Dokploy-Host crashes → ALLE Docker-Container auf derselbe Box sind down. Betroffen:
- **n8n** (Workflow-Automatisierung)
- Backups, Asterisk, etc.

**User-Problem:** Wennd Dokploy mehrmals abstürzt, lit nöd nur n8n flach.

**Lösig (drei Strategie):**
1. **Sandbox/Dokploy-Kopie** → Separate Dokploy-Instanz für Dev/Testing (siehe Abschnitt "Sandbox-Architektur")
2. **Kritische Dienste isoliere** → n8n in eigenem Dienst (Container oder separater Dokploy-Service)
3. **Dokploy-Stabilität verbessere** → Logs prüfe, warum Dokploy crasht (Memory-Limit? Disk-Full? Docker-Daemon-Problem?)

### 🔴 Container-interni Prozesse überleben Dokploy-Neustart NICHT (28.05.2026)

**Klassen-Level-Pattern:** Dokploy managed nur den Container-Lifecycle (start/stop/restart). Prozesse die manuell **innerhalb** des Containers gestartet werden (z.B. per `docker exec` oder im Container per Shell) gehen verloren, sobald Dokploy den Container neustartet.

**Betroffen:** Jeder Service der einen Hilfsprozess im selben Container braucht:
- **WebDAV Proxy** (Node.js, Port 9876, in n8n Container) für Nextcloud-PROPFIND/MOVE
- Ähnliche Sidecar-Prozesse in anderen Containern

**Symptom:** Nach Dokploy-Crash oder -Restart schlagen Workflows fehl die den internen Prozess ansprechen. Z.B. n8n "Doc Pipeline" → `ECONNREFUSED` auf `localhost:9876`.

**Lösung (drei Optionen):**

**Option A — Guard-Prozess (einfach, sie repariert sich selbst):**
```bash
# Einmalig im Container ausführen (via Dokploy Web Terminal oder `docker exec`):
# Erstellt Proxy-Script + Guard-Loop der alle 30s prüft und bei Crash neustartet
curl -s http://10.0.60.156:9877/install_webdav_proxy.sh | sh
```
Details: `n8n-api-automation` Skill → `scripts/install_webdav_proxy.sh`.

**Option B — Eigner Docker-Container für Hilfsprozess:**
Den Sidecar (z.B. WebDAV Proxy) als separaten Docker-Container deployen, mit eigenem Port-Mapping. Dokploy managed den Lifecycle. Der Hauptcontainer spricht ihn über den internen Docker-Netzwerknamen an.

**Option C — Embedded Entrypoint (permanent):**
Das Hilfs-Script in den Container per Dokploy-Command oder eigenem Dockerfile integrieren, sodass es beim Container-Start automatisch mitläuft.

**Diagnose:** Prüfe ob interner Prozess lebt:
```bash
# Im Container:
curl -sf http://127.0.0.1:<PORT>/health
# Von aussen (wenn kein Port-Mapping): Guck in Dokploy Console / docker exec
```
```
erzeugt beim ersten Start automatisch ALLE Zwischenverzeichnisse des Zielpfads (`data/user/files/`) als **root:root**. Der Container-Init versucht danach, das `data/` -Verzeichnis mit dem richtigen User (z.B. `www-data`) zu initialisieren, scheitert aber weil root die Dateien besitzt.

**Lösung (zwei Optionen):**

**Option A — Bind-Mount temporär entfernen (empfohlen bei Erstinstallation):**

1. Bind-Mount aus compose entfernen
2. `docker compose down -v` (löscht ALLE named volumes — Container + DB + Data)
3. `docker compose up -d` (frische Init ohne Bind-Mount)
4. Warten bis der Init abgeschlossen ist (30-60s für rsync + OCC)
5. Bind-Mount wieder ins compose einfügen
6. `docker compose up -d` (Container wird recreiert — kurzzeitige Downtime)

**Option B — Permissions manuell fixen (bei laufendem Container):**
```bash
docker exec <container> sh -c 'mkdir -p /var/www/html/data && chown -R www-data:www-data /var/www/html/data'
```
Funktioniert nur wenn die Init bereits komplett durchgelaufen ist (rsync + app files vorhanden).

**Wichtig:** Ein `docker restart` reicht NICHT — der Bind-Mount bleibt bestehen und erzeugt jedes Mal die root-Ornder neu. Das Volume muss komplett zerstört werden (`down -v`).

### 🔴 Docker compose build benötigt >180s timeout + Background Pattern (13.06.2026)

Bei grossen Builds (React + Three.js Abhängigkeiten) kann `docker compose build` über 180s dauern. Der Build hat 6 Stages:
- `builder 3/6`: COPY package*.json (5s)
- `builder 4/6`: RUN npm install (60-105s — Three.js heavy!)  
- `builder 5/6`: COPY . . (ab 58s)
- `builder 6/6`: RUN npm run build (ab 18s — tsc + vite)

### 🔴 nginx:alpine pre-pull workaround (13.06.2026)

Wenn der Docker Build mit `TLS handshake timeout` für nginx:alpine scheitert, obwohl Internet grundsätzlich funktioniert:

1. **Zuerst nginx:alpine einzeln pullen:** `docker pull nginx:alpine`
2. **Dann Build starten:** `docker compose build`

Das Problem war ein **TLS-Handshake-Timeout beim auth.docker.io Token-Fetch** während des Multi-Stage Builds. Interessanterweise funktioniert `curl -I registry-1.docker.io` (HTTP 401, erwartet), aber der Build-Process kriegt sporadisch Timeouts. Ein vorgeschaltetes `docker pull nginx:alpine` löst das — entweder weil das Image im lokalen Cache landet oder der Docker-Daemon den Auth-Token vorab cached.

**Diagnose:**
```bash
# Prüfe ob Registry erreichbar
curl -sI --connect-timeout 10 https://registry-1.docker.io/v2/ 2>&1 | head -5
# → HTTP/2 401 = OK (authentication required but reachable)

# Prüfe ob nginx:alpine lokal vorhanden
docker images nginx:alpine --format "{{.Repository}}:{{.Tag}}"


**Empfohlenes Pattern für lange Builds auf 10.0.60.121:**

```python
import paramiko
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', 'Louis_one_13', timeout=30)

i, o, e = s.exec_command('cd /opt/... && docker compose build 2>&1', timeout=600)
output = o.read().decode()
print(output[-3000:])

# Prüfe Ergebnis
if 'FINISHED' in output or 'successfully built' in output.lower():
    s.exec_command('cd /opt/... && docker compose up -d --remove-orphans 2>&1', timeout=30)
```

Alternativ via background+notify_on_complete:
```bash
docker compose build 2>&1 > /tmp/build-output.txt
```
Dann auf `notify_on_complete` warten und `cat /tmp/build-output.txt | tail -20` lesen.

**🔴 Vermeide `exec_command(timeout=180)` — das timet den Build mitten im npm install!**
Das Tool-Timeout von `terminal()` kann `docker compose up -d` killen. Workaround:
- `background=true` setzen + `notify_on_complete=true`
- Oder in Python via paramiko.exec_command(timeout=30) verpacken

### "Permission denied" bei SSH
SSH mit Password klappt nur via paramiko. `ssh root@host` direkt gibt Permission denied.

### Compose File existiert nicht
Dokploy legt Projekte dynamisch an. Der Pfad `/etc/dokploy/compose/<name>/code/docker-compose.yml` ist konsistent. Use `find` to locate it:
```bash
find /etc/dokploy/compose -maxdepth 4 -name "docker-compose.yml"
```

## Pitfalls

- **SharedArrayBuffer-fähige Apps (Actual Budget etc.)** benötigen einen Nginx-Proxy mit COOP/COEP Headern via HTTPS. Traefik kann das nicht. Siehe `references/sharedarraybuffer-nginx-proxy.md`.
- **HTTPS ist zwingend** — COOP/COEP allein reicht nicht. SharedArrayBuffer erfordert `secureContext=true` (HTTPS oder localhost). Self-Signed-Certs werden auf mobilen Geräten oft blockiert → **mkcert** verwenden für lokal vertrauenswürdige Certs.
### 🔴 SharedArrayBuffer: Drei Bedingungen für den Fix (gelernt 26.05.2026)

SharedArrayBuffer benötigt **alle drei**:
1. **Secure Context** → HTTPS (HTTP reicht nicht — `isSecureContext` ist `false`)
2. **COOP: same-origin** → korrekter Header
3. **COEP: require-corp** oder **credentialless** → korrekter Header

**Chronologische Fehleranalyse (Actual Budget):**

**Phase 1 — Headers fehlten komplett:** Traefik/Docker liefert keine COOP/COEP → Browser blockiert SAB.  
**Phase 2 — Duplicate Headers:** nginx-Proxy mit `add_header` eingebaut, aber `actual-server` sendet **selber** schon COOP/COEP → `require-corp, require-corp` (Duplikat) → Browser ignoriert.  
**Phase 3 — Credentialless:** COEP auf `credentialless` umgestellt (weniger streng, SAB funktioniert trotzdem ab Chrome 110+).  
**Phase 4 — HTTPS fehlt:** Sogar mit korrekten Headern: HTTP → `secureContext: false` → `crossOriginIsolated: false`. HTTPS zwingend nötig.  
**Phase 5 — mkcert:** Self-Signed Cert reicht nicht auf iOS (kein "Proceed anyway"). **mkcert** installiert lokal vertrauenswürdige Root-CA.

**Lösung nginx (vollständig):**
```nginx
proxy_hide_header Cross-Origin-Opener-Policy;
proxy_hide_header Cross-Origin-Embedder-Policy;
add_header Cross-Origin-Opener-Policy 'same-origin' always;
add_header Cross-Origin-Embedder-Policy 'credentialless' always;
```

Siehe komplettes Dossier in `references/sharedarraybuffer-nginx-proxy.md` (inkl. mkcert-Setup, User-Anleitung für Root-CA-Installation, Diagnose-Toolkit).

### User-Preference: Nie öffentlich machen

Bei SharedArrayBuffer-Fixes: User lehnt öffentliche DNS + Let's Encrypt ab. Interne HTTPS-Lösung via mkcert bevorzugen, nie öffentliche Ports/Domains vorschlagen.

### 🔴 User korrigierte mich (26.05.): Neuen Service deployen → zuerst Dokploy API/MCP versuchen

Ich habe Actual Budget per SSH+paramiko deployed und dabei Nextcloud-Container gelöscht (Namenskonflikt). Der User sagte explizit: "über Dokploy auch nur bei MCP, das Ganze über Dokploy deployen". Das API hat vermutlich Sicherungen gegen solche Kollisionen.

- Hermes läuft selbst in einem Docker-Container
- Hermes läuft selbst in einem Docker-Container — `docker` CLI und `/var/run/docker.sock` sind von innen NICHT erreichbar
- Die Container-IDs (Hostname `4729b9e53591`) ändern sich bei Neustarts
- Traefik-Labels bleiben erhalten — Port-Publishing ist ZUSÄTZLICH, nicht alternativ
- `expose:` in docker-compose.yml ist nur deklarativ; ohne `ports:` kein Host-Zugriff
- Nach Port-Änderung: Container wird **recreated** (nicht nur gestartet) — kurzzeitige Downtime
- `docker compose up -d --remove-orphans` entfernt alte Container-Versionen sauber

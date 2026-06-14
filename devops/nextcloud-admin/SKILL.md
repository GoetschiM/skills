---
name: nextcloud-admin
description: "Nextcloud administration via direct database & occ access — password recovery, app management, user creation, Talk setup — when the web UI is slow or unreachable."
version: 1.0.0
author: Hermes Agent
license: MIT
category: devops
tags: [nextcloud, admin, talk, postgresql, occ, recovery]
related_skills: [proxmox-lxc, dokploy, dokploy-lxc-setup]
---

# Nextcloud Admin — Direct DB & OCC Operations

## Overview

Nextcloud 33 (und neuere) laufen uf PHP 8.4 mit PostgreSQL. Wenn d'Web-UI z'langsam isch oder nöd erreichbar, cha mer alles via direkti DB-Zuegriff + `occ` erledige. Diesi Skill deckt di wichtigste Admin-Operatione ab.

## Instanz (Stand Juni 2026)

| Instanz | Host | Port | Image | DB | Admin |
|---------|------|------|-------|----|-------|
| **Production (VM 201)** | 10.0.60.201 | 10081 | nextcloud:32 (Docker) | MariaDB 10.11 + Redis | michel |

🔴 **LXC 100 NextCloud (10.0.60.121:8080) isch decommissioned (06.06.2026)** — migriert uf VM 201. D'Instanz uf LXC 100 isch nüm aktiv. Es läuft aber no anderi Docker-Container (NEI, MT5, Mind, Obsidian LiveSync) dört.

D'CasaOS/VM 201-Instanz isch jetzt **primär** — Cloudflare-Tunnel (`nextcloud.rebelone.ch`) zeigt uf 10.0.60.201:10081.

Für Deployment-Details lueg `references/deployment-casaos-vm.md`.

## Zugriff via Docker Container (VM 201)

Nextcloud läuft uf **CasaOS VM 201 (10.0.60.201)**. Instanz-Name: `nextcloud`, DB: `nextcloud-db`, Redis: `nextcloud-redis`.

```bash
# SSH direkt, oder via Proxmox Host (10.0.60.10)
ssh root@10.0.60.201

# OCC usführe:
docker exec -w /var/www/html nextcloud php occ <command>

# SQL direkt über DB-Container:
docker exec -i nextcloud-db mysql -u nextcloud -p'PASSWORT' nextcloud << 'SQL'
SELECT * FROM oc_users;
SQL

# Redis Cli:
docker exec -i nextcloud-redis redis-cli -a 'PASSWORT' KEYS '*'
```

## Credentials finden / Admin-Passwort zurücksetze

### 0. Credentials via Docker inspect uslese (schnellschti Methode)

Wänn Nextcloud im Docker lauft (VM 201, 10.0.60.201):

```bash
# SSH uf de Host und Nextcloud-Env uslese
ssh root@10.0.60.201 docker inspect nextcloud --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -iE 'NEXTCLOUD_ADMIN|MYSQL|MARIADB|PASSWORD'

# Zeigt: NEXTCLOUD_ADMIN_USER, NEXTCLOUD_ADMIN_PASSWORD, MYSQL_PASSWORD, REDIS_HOST_PASSWORD
```

**Alternative (wenn `docker inspect` redacted ist):** Via `systemctl` oder Docker Compose .env uslese:

```bash
# Docker Compose .env (CasaOS: /media/NAS/Container/Nextcloud/.env o.ä.)
cat /etc/dokploy/compose/*/code/.env 2>/dev/null | grep -iE 'NEXTCLOUD_ADMIN|MYSQL|PASSWORD'

# systemd service env
systemctl cat nextcloud 2>/dev/null | grep EnvironmentFile
```

### 1. Admin User + ENV finden

```bash
# Admin User aus env:
lxc-attach -n 100 -- docker exec code-nextcloud-1 env | grep NEXTCLOUD_ADMIN
# NEXTCLOUD_ADMIN_USER=michel
# NEXTCLOUD_ADMIN_PASSWORD=***  (wird gredacted — via docker inspect use)

# Alternativ: docker inspect
docker inspect code-nextcloud-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep NEXTCLOUD_ADMIN_PASSWORD
# Gitt de volle Password-Wert (Docker zeigt *** bim env, aber inspect zeigt's)
```

### 2. Config.php usläse (DB Credentials)

```bash
lxc-attach -n 100 -- docker exec code-nextcloud-1 cat /var/www/html/config/config.php
```

Wichtigi Felder: `dbuser`, `dbpassword`, `dbhost`, `dbname`, `passwordsalt`, `secret`.

### 3. Admin-Passwort per `occ user:resetpassword` (Empfohlen — einfacher)

Sofern de Docker-Nextcloud noch lauft (Standardfall VM 201), isch `occ user:resetpassword` de schnellschti Weg. D'Herausforderig: s'Passwort wird interaktiv 2x abgfrogt.

**Funktioniert — Heredoc im SSH-Call:**

```bash
ssh root@10.0.60.201 '
docker exec -i -w /var/www/html nextcloud \
  php occ user:resetpassword michel << '\''EOF'\''
Michel_NC_Admin_2026!
Michel_NC_Admin_2026!
EOF
echo "Exit: $?"
'
```

Erwarteti Antwort: `Successfully reset password for michel`

**Pitfall:** De verschachtleti Heredoc (`<< '\\''EOF'\\''` im SSH-String) isch nötig will de Docker-Container s'Password-Prompt via stdin erwartet (nöd über Argumente). Einfache Heredoc (`<< EOF`) ohni SSH-Apostroph-Escaping führt zu `Password cannot be empty!`.

**🔴 Pitfall: "Password is in compromised password list"** — Nextcloud prüeft s'Passwort über Have I Been Pwned (api.pwnedpasswords.com). Wenn Nextcloud meint, de Password isch inere Leak-Datenbank, chunnt: `The password is in a compromised password list. Please choose a different one.`
**Fix:** Eifach en andere Password probiere — z.B. statt `Louis_one_13` → `Louis_one_14`. Falls das au blockiert wird, chasch du s'Password-Policy-Check milder stelle:
```bash
docker exec nextcloud php occ config:system:set auth.password_policy.bypass_password_history_check --value true --type boolean
```

**Verifikation:**

```bash
# Login testen
curl -s --max-time 15 -u "michel:Michel_NC_Admin_2026!" \
  -H "OCS-APIRequest: true" \
  "http://10.0.60.201:10081/ocs/v2.php/cloud/user" | grep '<status>ok</status>' || echo "FEHLER"
```

### 4. Admin-Passwort zurücksetze (via DB — Argon2id)

Nextcloud 33 brucht **Argon2id** als Password-Default (PHP 8.4). D'Passwort-Hashes hend e Version-Prefix (`3|` für Argon2id, `2|` für bcrypt).

**Zwei Schritte:**
- **Schritt A:** Argon2id-Hash generiere (im Container, wo PHP 8.4 lauft):
```bash
HASH=$(lxc-attach -n 100 -- docker exec code-nextcloud-1 php -r \
  'echo "3|" . password_hash("NEUES_PASSWORT", PASSWORD_ARGON2ID);')
echo "$HASH"
# Output: 3|$argon2id$v=19$m=65536,t=4,p=1$...
```

- **Schritt B:** Hash in DB schribe:
```bash
# Mit heredoc — da d'$ Zeiche susst vom Shell parst werded!
lxc-attach -n 100 -- docker exec -i code-db-1 psql -U oc_admin -d nextcloud << 'SQL'
UPDATE oc_users SET password='3|$argon2id$v=19$m=65536,t=4,p=1$...' WHERE uid='michel';
SQL
```

**🔴 Wichtig: Heredoc mit 'SQL' (einfache Anführigszeichä vom Begrenzer) verwende!** Suscht werded d'`$`-Zeiche im Argon2id-Hash vom Bash interpretiert und s'Passwort wird unbrauchbar.

### 4. Login testen

```bash
curl -s -u "michel:NEUES_PASSWORT" -H "OCS-APIRequest: true" \
  http://10.0.60.121:8080/ocs/v2.php/cloud/user
# Sollt <status>ok</status> und <id>michel</id> zrückgeh
```

## Talk Room + Bot Management

### Talk-Room erstelle + verwalte

```bash
# Room erstelle (type 3 = public group)
curl -s --max-time 60 -u "michel:PASSWORT" \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d 'roomType=3&roomName=Hermes-Lab' \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v4/room"

# User zum Room hinzufüge (via occ — z'verlässlichschti)
lxc-attach -n 100 -- timeout 180 docker exec -i code-nextcloud-1 \
  php occ talk:room:add ROOM_TOKEN --user Hermes --user Nova

# Via API — NUR bi chline Userzahle (langsam!)
curl -s --max-time 60 -u "michel:PASSWORT" \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d 'participant=Hermes' \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v4/room/ROOM_TOKEN/participants"

# Teilnehmer aaluege
curl -s --max-time 30 -u "michel:PASSWORT" \
  -H "OCS-APIRequest: true" \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v4/room/ROOM_TOKEN/participants"

# Falls API zu langsam — direkt via DB:
INSERT INTO oc_talk_attendees (room_id, actor_type, actor_id, display_name, participant_type, state)
VALUES (1, 'users', 'Hermes', 'Hermes Agent', 1, 0)
ON CONFLICT (room_id, actor_type, actor_id) DO NOTHING;
```

### Talk Bot erstelle (Webhook — für Agent-Integration)

```bash
# Bot registriere
lxc-attach -n 100 -- timeout 180 docker exec -i code-nextcloud-1 \
  php occ talk:bot:create "Hermes" "Hermes AI Agent" \
  --secret "mindestens_40_zeichen_langer_secret_key_1234567890"

# Bot in Room installiere (mit Webhook-URL)
# talk:bot:install <name> <secret> <url>
lxc-attach -n 100 -- timeout 180 docker exec -i code-nextcloud-1 \
  php occ talk:bot:install 1 iytt2n7g

# Bot-Liste
lxc-attach -n 100 -- timeout 180 docker exec -i code-nextcloud-1 \
  php occ talk:bot:list
```

### Talk API — Nachrichte sende/empfange

**🔴 API Version beachte!** Chat-Endpoints sind NUR under `api/v1/` verfüegbar. Room-Endpoints under `api/v4/`.

```bash
# Nachricht sende (v1!)
curl -u "USER:PASS" \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d 'message=Hallo Welt!' \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/chat/ROOM_TOKEN"

# Nöii Nachrichte hole (v1!)
curl -u "USER:PASS" \
  -H "OCS-APIRequest: true" \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/chat/ROOM_TOKEN?lookIntoFuture=1&limit=100"
```

**🔴 Fix: uid_lower-Spalte in oc_users**

Wänn mer User direkt via SQL (`INSERT INTO oc_users`) aagleit, isch d'Spalte `uid_lower` leer — Nextcloud cha de User denn nöd finde (Login 401, "User does not exist"). `occ user:add` setzt das automatisch.

```sql
-- Falls du doch per SQL muesch: uid_lower isch PFLICHT!
UPDATE oc_users SET uid_lower=LOWER(uid) WHERE uid_lower='' OR uid_lower IS NULL;
```

### Talk App installiere + enable

**Wichtig: Version check!** Talk brucht e spezifischi Version für jedes Nextcloud-Release.

```bash
# 1. Neuesti release finde (für NC 33: stable33 branch)
curl -sL https://api.github.com/repos/nextcloud-releases/spreed/releases/latest \
  | grep -E '"tag_name"|"name"' | head -2
# Output: v23.0.5 (für NC 33 min-version=33 max-version=33)

# 2. Falschi Version lösche + richtegi installiere
lxc-attach -n 100 -- docker exec code-nextcloud-1 sh -c '
rm -rf /var/www/html/custom_apps/spreed
cd /tmp
curl -sL -o spreed.tar.gz https://github.com/nextcloud-releases/spreed/releases/download/v23.0.5/spreed-v23.0.5.tar.gz
tar xzf spreed.tar.gz -C /var/www/html/custom_apps/
chown -R www-data:www-data /var/www/html/custom_apps/spreed
rm spreed.tar.gz
'

# 3. App enable (langsam — bis zu 180s!)
lxc-attach -n 100 -- timeout 180 docker exec -w /var/www/html \
  code-nextcloud-1 php occ app:enable spreed --no-warnings

# 4. Verify: Tables created?
lxc-attach -n 100 -- docker exec -i code-db-1 psql -U oc_admin -d nextcloud -c "\dt oc_spreed*"

# 5. Falls Tables nöd erstellt: disable + re-enable
lxc-attach -n 100 -- timeout 180 docker exec -w /var/www/html \
  code-nextcloud-1 php occ app:disable spreed --no-warnings
lxc-attach -n 100 -- timeout 180 docker exec -w /var/www/html \
  code-nextcloud-1 php occ app:enable spreed --no-warnings
```

**🔴 Fallstrick:** Wird `app:enable` gstoppt bevor d'Migrations dure sind, bliibed d'App-Tables unvollständig und es chönd PHP-Fehler uufträtte (wie `relation "oc_talk_attendees" does not exist`). Im Zweifel immer disable + re-enable.

### Verfüegbari Apps prüefe (Liste alle enabled)

```bash
lxc-attach -n 100 -- docker exec -i code-db-1 psql -U oc_admin -d nextcloud \
  -c "SELECT appid, configkey, configvalue FROM oc_appconfig WHERE configkey='enabled' ORDER BY appid;"
```

## Benutzer verwalte

### User via occ erstelle (empfohlen)

```bash
# Password wird zweimal abgfrogt — dusse mit heredoc pipe:
lxc-attach -n 100 -- timeout 180 docker exec -i code-nextcloud-1 \
  php occ user:add <username> --display-name "Display Name" << 'PWD'
Passwort123!
Passwort123!
PWD
```

### 🔴 User via DB erstelle — NUR mit oc_accounts-Eintrag!

User über direkti SQL-Inserts (`INSERT INTO oc_users`) werded vo Nextcloud nöd erkannt — `occ user:list` / `occ user:add` / `occ user:resetpassword` meldet denn "User does not exist", obwohl de DB-Eintrag vorhande isch.

**Ursache:** Nextcloud 33 bruucht en **zusätzliche Iitrag i de `oc_accounts`-Tabelle** für d'User-Metadate. Ohne dä wird de User vo de Auth-Backend nöd gfunde.

**Richtiger Weg:** Immer `occ user:add` verwende, oder falls das nöd möglich isch (z.B. API zu langsam):

```bash
# 1. Hash generiere (via PHP im Container)
HASH=$(lxc-attach -n 100 -- docker exec code-nextcloud-1 php -r \
  'echo "3|" . password_hash("Passwort123!", PASSWORD_ARGON2ID);')

# 2. User + Account in DB erstelle
lxc-attach -n 100 -- docker exec -i code-db-1 psql -U oc_admin -d nextcloud << SQL
INSERT INTO oc_users (uid, displayname, password) VALUES ('$USER', '$DISPLAY', '$HASH')
ON CONFLICT (uid) DO NOTHING;
INSERT INTO oc_group_user (gid, uid) SELECT 'admin', '$USER' WHERE NOT EXISTS (
  SELECT 1 FROM oc_group_user WHERE gid='admin' AND uid='$USER');
-- oc_accounts isch PFLICHT!
INSERT INTO oc_accounts (uid, data) VALUES ('$USER', '{"displayname":{"value":"$DISPLAY","scope":"v2-federated","verified":"0"},"email":{"value":null,"scope":"v2-federated","verified":"0"},"avatar":{"scope":"v2-federated"}}')
ON CONFLICT (uid) DO NOTHING;
SQL
```

## SSL/HTTPS — Nextcloud für externi Proxy konfiguriere

### Übersicht Ports

| Service | Protokoll | Port | Beschrieb |
|---------|-----------|------|-----------|
| Nextcloud HTTP | HTTP | 8080 | Direkt, ohni SSL (für Cloudflare Tunnel / Tailscale intern) |
| SSL-Proxy | HTTPS | 8443 | nginx mit self-signed cert (nur für interni Tests) |
| Cloudflare Tunnel | HTTP → 8080 | — | Extern über Cloudflare-Domain mit echtem SSL |

**Wichtig:** Für Nextcloud Talk Android App isch HTTPS **zwingend** nötig (WebRTC Mikro/Kamera). Über Tailscale-VPN allei reicht nöd — Talk brucht en gültigs SSL-Zertifikat uf App-Ebeni.

### Config.php für SSL/Cloudflare schribe

`occ config:system:set` **funktioniert nöd immer** — reported success aber config.php bliibt unveränderet. Workaround: Diräkt i d'PHP-Config-Datei schribe.

**🔴 Occ Fallback — diräkti Config-Edit (wenn occ versagt):**

```bash
# 1. Config usläse (via base64 — Encoding-Sicherheit)
lxc-attach -n 100 -- docker exec code-nextcloud-1 base64 /var/www/html/config/config.php

# 2. Python: base64 decode -> edit -> encode -> write back
python3 -c "
import base64, subprocess
r = subprocess.run(['sshpass','-p','PASS','ssh','root@10.0.60.10',
  'lxc-attach -n 100 -- docker exec code-nextcloud-1 base64 /var/www/html/config/config.php'],
  capture_output=True,text=True)
config = base64.b64decode(r.stdout.strip()).decode()
config = config.replace(\"'overwriteprotocol' => 'http'\",
                        \"'overwriteprotocol' => 'https'\")
new_b64 = base64.b64encode(config.encode()).decode()
subprocess.run(['sshpass','-p','PASS','ssh','root@10.0.60.10',
  f\"lxc-attach -n 100 -- docker exec -u 0 code-nextcloud-1 sh -c 'echo {new_b64} | base64 -d > /var/www/html/config/config.php'\"])
"
```

### Wichtigi Config-Values für externi Zugriff

```php
'overwriteprotocol' => 'https',                         // Erzwungt HTTPS für alli generierte URLs
'overwrite.cli.url' => 'https://nextcloud.domain.ch',   // Öffentlichi URL (für OCC, Cron, Auth-Redirects)
'overwritehost'     => 'nextcloud.domain.ch',            // Host-Header erzwinge
```

**Cloudflare Tunnel — Yml-Config:**

```yaml
ingress:
  - hostname: nextcloud.rebelone.ch
    service: http://10.0.60.201:10081    # VM 201, immer HTTP (Flexible SSL)
  - service: http_status:404
```

**Cloudflare Dashboard zuesätzlich:**
- Network -> **WebSockets: ON** (Pflicht für Talk!)
- SSL/TLS -> **Flexible** (will Tunnel -> Origin über HTTP lauft)

**Cloudflare-spezifisch:**
- `overwrite.cli.url` = `https://<cloudflare-domain>` (z.B. nextcloud.rebelone.ch)
- `overwriteprotocol` = `https`
- `overwritehost` = `<cloudflare-domain>`
- Tunnel pointet zu **HTTP** `http://localhost:8080` (nöd HTTPS!)

### trusted_proxies setze

Für richtigi X-Forwarded-Proto-Erkennig (verhindert dass Nextcloud HTTP-URLs generiert):

```bash
# Docker-Netzwerk-IP vom Proxy/nginx finde
lxc-attach -n 100 -- docker inspect nextcloud-ssl-proxy --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

# Config setze
lxc-attach -n 100 -- docker exec code-nextcloud-1 php /var/www/html/occ \
  config:system:set trusted_proxies 0 --value "172.23.0.0/16"
lxc-attach -n 100 -- docker exec code-nextcloud-1 php /var/www/html/occ \
  config:system:set trusted_proxies 1 --value "10.0.60.0/24"
```

Ohni `trusted_proxies` ignoriert Nextcloud `X-Forwarded-Proto: https` und generiert HTTP-URLs -> Login-Flow redirectet uf HTTP -> Android App 400 "plain HTTP request sent to HTTPS port".

### Self-Signed Cert (für interni Notfälle)

```bash
# Cert erstelle (10 Jahre)
lxc-attach -n 100 -- sh -c '
mkdir -p /opt/nginx-ssl
openssl req -x509 -newkey rsa:4096 -keyout /opt/nginx-ssl/nextcloud.key \
  -out /opt/nginx-ssl/nextcloud.crt -days 3650 -nodes \
  -subj "/CN=10.0.60.121" \
  -addext "subjectAltName=IP:10.0.60.121"
chmod 600 /opt/nginx-ssl/nextcloud.key
'

# nginx Proxy starte (funktioniert zuverlässig)
docker run -d --name nextcloud-ssl-proxy --restart unless-stopped \
  --network nextcloud-network \
  -v /opt/nginx-ssl/nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro \
  -v /opt/nginx-ssl/nextcloud.crt:/etc/ssl/certs/nextcloud.crt:ro \
  -v /opt/nginx-ssl/nextcloud.key:/etc/ssl/private/nextcloud.key:ro \
  -p 8443:443 nginx:alpine
```

**🔴 Fallstrick:** Caddy mit `tls internal` git TLS internal error (`OpenSSL error:0A000438`) mit self-signed certs -> immer nginx:alpine verwende für self-signed SSL.

## CRITICAL FALLSTRICKE

1. **PHP occ isch extrem langsam** (lädt ganz Nextcloud). Immer `timeout 180` setze, 30s sind nie gnueg. Uf VM 201 (Docker direkt, kei LXC) isches schneller — aber nid under 60s für komplexi Commands.

3. **MariaDB 11.4 vs 10.11 — MYSQL_* vs MARIADB_* Env Vars:** MariaDB 11.4+ akzeptiert KEI `MYSQL_*`-Env-Vars meh (nume `MARIADB_*`). D'nextcloud Docker Images bruched aber `MYSQL_*`. **Fix:** `mariadb:10.11` (LTS) verwende — das akzeptiert beides und isch langfristig stabil.

4. **trusted_domains "Comma-String" Bug:** Wänn `trusted_domains` via `occ config:system:set trusted_domains 1 --value='localhost,nextcloud.rebelone.ch,10.0.60.201'` gsetzt wird, landed ALLI Domain-Näme als EINZEIGNE STRING im Array-Eintrag 1 (`["localhost", "localhost,nextcloud.rebelone.ch,10.0.60.201"]`). Nextcloud zeigt denn "nicht vertrauenswürdige Domain" für alli Domains usser `localhost`.

   **Diagnose:** `docker exec nextcloud php occ config:system:get trusted_domains --output=json`

   **Korrekt:** Jede Domain in eignig Array-Index setze:
   ```bash
   docker exec nextcloud php occ config:system:set trusted_domains 1 --value=nextcloud.rebelone.ch
   docker exec nextcloud php occ config:system:set trusted_domains 2 --value=10.0.60.201
   ```

   **Index lösche:** `docker exec nextcloud php occ config:system:delete trusted_domains 1`

3. **exFAT-Dateisystem — kene Write-Bind-Mount möglich:** exFAT unterstützt keni POSIX-Chown/Chmod. Docker-Volumes uf em ext4-Root-Filesystem erstelle (`docker volume create nextcloud_data`), nur Lese-Shares als Bind-Mount (`:ro`). Nie schriibende Bind-Mount uf exFAT versuche — Nextcloud chunted bi Permission-Probleme.

4. **Redis Command Syntax in Docker Compose:** YAML-Array-Form `command: ["redis-server", "--requirepass", "..."]` führt zu Parsing-Fehler. **Fix:** YAML-Block-Scalar `>` verwende → `command: > redis-server --requirepass ${PASSWORD} --appendonly yes`

5. **External Storage via OCC:** `occ files_external:create` brucht drei Argument: `<mount_name> <backend> <authentication>`. Für en lokale Ordner: `occ files_external:create /Movie local null::null --config datadir=/mnt/Movie`. D'App `files_external` muess vorgängig enabled si: `occ app:enable files_external`.

6. **Cloudflare Flexible SSL + trusted_domains:** Nextcloud Config brucht `'overwriteprotocol' => 'https'`, `'overwrite.cli.url' => 'https://nextcloud.rebelone.ch'`, `'overwritehost' => 'nextcloud.rebelone.ch'`. Ohni `trusted_proxies` ignoriert Nextcloud `X-Forwarded-Proto` und generiert HTTP-URLs → Android App chunted 400er.

2. **Passwort-Hashes:** D'$ im Argon2id-Hash werded vom Shell interpretiert. Verwende **immer** heredoc mit quotetem Begrenzer (`<< 'SQL'`), nie `echo "..." | psql`.

3. **Talk App Version:** Immer `min-version` und `max-version` im `appinfo/info.xml` prüefe. Für NC 33 → Talk v23.x, für NC 31 → Talk v21.x. Falschi Version installiert sich aber schiint enabled → wenn Tables fehled, isches falsch.

4. **Nextcloud-Port am Apache:** Nextcloud lauft uf Port 8080 → 80 (Apache intern). D'API isch unter `/ocs/v2.php/...` erreichbar. `/status.php` gaht am schnellschte (läd nöd ganz Nextcloud).

5. **Auth-Timing:** De erschti curl-Request nach Passwort-Reset cha öppe 10-20s bruuche — PHP kompiliert Caches. Nöd z'früh ufgeh.

6. **occ config:system:set Persistenz-Problem:** Occ reported `set to string https` aber d'config.php bliibt uf em alte Wert. Workaround: Diräkti Config-Edit über base64 + Python (siehe obe).

7. **Cloudflare Tunnel + Talk:** WebSockets MÜEND im Cloudflare Dashboard aktiv si (Network → WebSockets: ON). SSL/TLS uf "Flexible" (Tunnel → origin über HTTP) oder "Full" (Tunnel → origin über HTTPS).

8. **Android Talk App brucht zwingend HTTPS:** Au über Tailscale-VPN verweigeret d'App Mikrofon-Zugriff ohni gültigs SSL. Es langet nid, dass de Transport verschlüsslet isch — d'App prüeft uf HTTPS-Protokoll.

9. **"400 Bad Request — The plain HTTP request was sent to HTTPS port" — Diagnose:**
   - **Symptom:** Android App zeigt Login-Page, aber nach Login chunnt 400er.
   - **Ursache 1 (häufig):** Nextcloud generiert HTTP-URLs im Login-Flow, weil `trusted_proxies` fählt oder `overwriteprotocol` nöd uf 'https' gsetzt isch. D'App folgt em HTTP-Link → 400.
   - **Ursache 2:** D'App schickt HTTP statt HTTPS, wil sie de self-signed Cert nöd akzeptiert het und uf HTTP fallbackt.
   - **Diagnose:** Öber curl prüefe: `curl -sk https://10.0.60.121:8443/status.php` → 200 = SSL funktioniert, Ursache isch Nextcloud-Config.
   - **Fix Ursache 1:** `overwriteprotocol => 'https'`, `overwrite.cli.url => 'https://<domain>'`, `trusted_proxies => [...]` mit Docker-Netzwerk-Subnets setze.
   - **Fix Ursache 2:** Self-signed Cert uf Android installiere (Iistellige → Sicherheit → Zertifikat installiere → CA-Zertifikat) ODER uf Cloudflare Tunnel wächsle (echte SSL-Cert).

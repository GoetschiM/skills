---
name: nextcloud-talk-integration
description: "Nextcloud Talk als Kommunikationsplattform fuer Hermes/Nova/Apollo — Bot-User, Talk-Room, API-Integration"
version: 1.0.0
author: Hermes Agent
tags: [nextcloud, talk, chat, communication, bots, multi-agent]
---

# Nextcloud Talk Integration

## Uebersicht

Hermes, Nova und Apollo sind als eigenstaendige Benutzer in Nextcloud Talk integriert.

## Architektur

- **Nextcloud**: 33.0.3 auf Docker (code-nextcloud-1), LXC 100 (10.0.60.121)
- **Talk App**: v23.0.5 (custom_apps/spreed/)
- **Database**: PostgreSQL (code-db-1)
- **API Base URL**: `http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/`
- **Chat Send**: `POST /api/v1/chat/{token}` — `message=...` + OCS-APIRequest Header
- **Chat Receive**: `GET /api/v1/chat/{token}?lookIntoFuture=1&limit=100`

## Benutzer

| User | Password | Rolle |
|------|----------|-------|
| michel | NextCloud123! | Admin |
| Hermes | Hermes_Talk_2026! | Bot |
| Nova | Nova_Talk_2026! | Bot |
| Apollo | Apollo_Talk_2026! | Bot |

## Talk Room

- **Name**: Hermes-Lab
- **Token**: iytt2n7g
- **Room ID**: 1
- **Type**: 3 (Public Group)
- **Teilnehmer**: michel, Hermes, Nova, Apollo
- **Bot**: Hermes (ID 1, via talk:bot:create)

## API Nutzung

```bash
# Nachricht senden
curl -u "Hermes:Hermes_Talk_2026!" \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d 'message=Hallo!' \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/chat/iytt2n7g"

# Nachrichten empfangen
curl -u "Hermes:Hermes_Talk_2026!" \
  -H "OCS-APIRequest: true" \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/chat/iytt2n7g?lookIntoFuture=1&limit=100"
```

**Wichtig**: Nextcloud PHP ist traege — 30-60s Timeout!

## Gateway Service

Ab Version 1.1.0: Es git en **standalone Gateway-Service** (FastAPI, Docker) wo:
- Talk-Rooms pollt (Default alle 5s)
- @Mentions (@Hermes / @Nova / @Apollo) erkennt (inkl. `{mention-X}` XML-Parsing)
- Nachrichten via HMAC-SHA256 signierte Webhooks an Agent-Endpoints dispatched
- Agent-Antworten via `POST /respond` entgegenimmt und i Talk postet
- Vollständige Kette getestet ✅: Talk → Gateway → Webhook → /respond → Talk

**Deployment (Sandbox):** `docker run -d --name talk-gateway --restart unless-stopped -p 8080:8080 talk-gateway:latest`
**GitHub:** `gl-stack/services/nextcloud-talk-gateway/`

**Agent Webhooks:**
| Agent | Webhook URL |
|-------|-------------|
| Hermes | http://10.0.60.156:9091/talk-webhook |
| Nova | http://10.0.60.136:9092/talk-webhook |
| Apollo | http://10.0.60.136:9093/talk-webhook |

```bash
# Service starten auf Sandbox LXC (10.0.60.136)
cd services/nextcloud-talk-gateway/
docker compose up -d

# Config anpassen in config.yaml
# - talk.*: Nextcloud Credentials
# - agents.*: Agenten + Webhook-URLs + Secrets
# - rooms.*: Talk-Room Token
```

### API Endpoints (Gateway)

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `GET /health` | GET | Health Check |
| `GET /status` | GET | Status (Rooms, Agents, last_message_id) |
| `POST /respond` | POST | Agent-Antwort vom Agent empfange und i Talk poste |

### /respond Schema (WICHTIG — exakte Feldnäme!)

De Agent **mues** zruggposte a `POST /respond` mit em JSON-Schema:

```json
{
  "room_token": "iytt2n7g",
  "text": "Antwort vom Agent",
  "agent_name": "Hermes"
}
```

Nume die 3 Fälder! Falschi Feldnäme (`message` statt `text`, `actor_name` statt `agent_name`) verursache en **422 Unprocessable Entity**.

### Gateway Bugfix-Katalog

Die folgende Bugs sind während Entwicklig gfunde und gfixt worde. Merk si für spöteri Gateway-Projekt oder wenn s'Gateway nomol baut wird:

**Bug 1: `lastKnownMessageId` in Talk API filtert falsch rum**
- Erwartig: `lastKnownMessageId=36` gibt Messages **nach** ID 37 zrugg (nöii Messages)
- Realität: `lastKnownMessageId=36` filtert Messages **bis** ID 36, exkludiert also nöii
- Fix: `lastKnownMessageId` ganz wegla. D'API git ohni Parameter die **letzte Messages** zrugg. Nöii IDs lokal tracke (Intervall-Verglich).

**Bug 2: `{mention-user1}` statt `@AgentName`**
- Talk kodiert @Mentions im XML nöd als Text, sondern als `{mention-user1}` im `<message>` Tag
- Die tatsächliche User-Mapping stot im `<messageParameters>` XML-Block:
  ```xml
  <messageParameters>
    <element>
      <parameterType>user</parameterType>
      <parameterId>Hermes</parameterId>
      <name>Hermes</name>
    </element>
  </messageParameters>
  ```
- Fix: `<messageParameters>` mues extra parsed werde, de `<message>`-Text dörf `{mention-*}` durch `@` + Name ersetze.

**Bug 3: HMAC Signature failt wäge JSON-Key-Ordering**
- Gateway sendet `model_dump_json()` (keys i Felddefinition-Reiefolg)
- Webhook verifiziert mit `json.dumps(body, sort_keys=True)` (alphabetisch)
- Unterschiedlichi JSON-Strings → unterschiedlichi HMACs → 403
- Fix: Webhook mues de **raw request body** näh (`await request.body()`) und dä für HMAC verwende, nid `json.dumps()`.
  ```python
  raw_body = await request.body()
  expected = hmac.new(WEBHOOK_SECRET, raw_body, hashlib.sha256).hexdigest()
  ```

**Bug 4: /respond 422 wäge falsche Feldnäme**
- Gateway erwartet: `room_token`, `text`, `agent_name`
- Webhook sandti: `room_token`, `message`, `actor_name`, `reply_to`
- Fix: Uf exakti Feldnäme achte — kei extra Fälder, kei Aliases.

### Talk API Quirks (gelernt us de Entwicklig)

**Wichtigste API-Besonderheite:**
1. **Timout immer 30-60s setze** — Nextcloud PHP isch träg, vor allem bim erste Poll
2. **`lookIntoFuture=0` für Polling, `lookIntoFuture=1` für langi Verbindige (Long-Poll)**
3. **`lastKnownMessageId` macht nöd das, mes erwartet** — git Messages VOR däm ID zrugg, nid nöieri
4. **User Auth via HTTP Basic** — funktioniert, aber Session-Cookie wird nöd persistiert
5. **`OCS-APIRequest: true` Header isch PFLICHT** — ohni dä git's en 404 statt XML-Response
6. **HTTP 201 bei erfolgreichem Sende** (nöd 200!)
7. **XML-Response** (nöd JSON) — `<ocs><meta><status>ok</status>...</meta></ocs>`
8. **Room-Token statt Room-ID** für chat API — `v1/chat/{token}`, Room-ID für v4 API

### Aktueller Stand

- **Deployed**: Sandbox Dokploy (10.0.60.136:8080)
- **Config**: 1 Room (Hermes-Lab), 3 Agents (Hermes/Nova/Apollo)
- **GitHub**: `services/nextcloud-talk-gateway/` auf gl-stack (dev+main)

## Setup-Schritte

1. **Talk App installieren**:
   ```bash
   curl -sL https://github.com/nextcloud-releases/spreed/archive/refs/tags/v23.0.5.tar.gz
   # Nach /var/www/html/custom_apps/spreed/ entpacken
   occ app:enable spreed
   ```
2. **Benutzer erstellen** (NUR via occ, nicht per SQL!):
   ```bash
   occ user:add Hermes --display-name "Hermes Agent"
   ```
3. **Talk Room erstellen**:
   ```bash
   curl -u "michel:NextCloud123!" -X POST \
     -d 'roomType=3&roomName=Hermes-Lab' \
     "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v4/room"
   ```
4. **User zum Room hinzufuegen**:
   ```bash
   occ talk:room:add iytt2n7g --user Hermes --user Nova --user Apollo
   ```
5. **Bot registrieren**:
   ```bash
   occ talk:bot:create "Hermes" "Hermes AI Bot" --secret "..." 
   occ talk:bot:install 1 iytt2n7g "http://webhook-url"
   ```

## Nextcloud SSL Proxy (für Android App / Audio)

D'Nextcloud Talk Android App bruucht **HTTPS** — au mit self-signed Cert. Dafür git's en nginx-Proxy.

**Standort:** Production LXC 100 (10.0.60.121)
**Container:** `nextcloud-ssl-proxy` (nginx:alpine)
**Port:** 8443 (HTTPS) → code-nextcloud-1:80
**Netz:** nextcloud-network (Bridge)
**Cert:** Self-Signed, 10 Jahr, für IP 10.0.60.121

### Setup

```bash
# 1. Self-Signed Cert erstelle
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /opt/nginx-ssl/nextcloud.key \
  -out /opt/nginx-ssl/nextcloud.crt \
  -subj "/CN=10.0.60.121/O=GoetschiLabs/C=CH" \
  -addext "subjectAltName=IP:10.0.60.121"

# 2. Nginx Config schriebe
cat > /opt/nginx-ssl/nginx.conf << 'EOF'
server {
    listen 443 ssl;
    server_name 10.0.60.121;
    ssl_certificate /etc/ssl/certs/nextcloud.crt;
    ssl_certificate_key /etc/ssl/private/nextcloud.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    location / {
        proxy_pass http://code-nextcloud-1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10G;
        # WebSocket für Talk
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 3. Container starte
docker run -d --name nextcloud-ssl-proxy --restart unless-stopped \
  --network nextcloud-network \
  -v /opt/nginx-ssl/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v /opt/nginx-ssl/nextcloud.crt:/etc/ssl/certs/nextcloud.crt:ro \
  -v /opt/nginx-ssl/nextcloud.key:/etc/ssl/private/nextcloud.key:ro \
  -p 8443:443 \
  nginx:alpine

# 4. Nextcloud konfiguriere
php /var/www/html/occ config:system:set trusted_domains 4 --value="10.0.60.121:8443"
php /var/www/html/occ config:system:set overwrite.cli.url --value="https://10.0.60.121:8443"
php /var/www/html/occ config:system:set overwriteprotocol --value="https"
php /var/www/html/occ config:system:set trusted_proxies 0 --value="172.18.0.0/16"
```
\n**Android App:** `https://10.0.60.121:8443` — Zertifikatswarnig akzeptiere (dis eigete Cert)\n\n**Template:** `templates/nginx-ssl-proxy.conf` — fertigi nginx-Config zum Wiederverwende

**Reference:** `references/ssl-android-troubleshooting.md` — vollständige Debug-Pfad für 400 "plain HTTP request", Android-Cert-Installation, und Edge Cases

## Externer Zugriff via Tailscale Subnet Routing

Für Android-Zugriff (Nextcloud Talk App, Browser) usserem LAN brucht's Tailscale — aber **nid jedes Gerät** im Netz muess einzle Tailscale ha.

### Prinzip: Subnet Routing

Tailscale verbindet Gerät i me Mesh. Mit **Subnet Routing** wird e ganzi IP-Range (z.B. `10.0.60.0/24`) über eis Tailscale-Gerät im LAN erreichbar:

```
Android App ──Tailscale──→ pve01 (10.0.60.10) ──LAN──→ LXC 100:8443
                                ↑
                          Subnet Route
                          10.0.60.0/24
```

Der Android-Michel verbindet sich mit **Tailscale VPN** — de Traffic goht verschlüsslet zu pve01, wo en über LAN zum LXC 100 leitet.

### Setup

```bash
# Nur uf EIMEM Gerät im Subnet (z.B. Proxmox Host pve01):
tailscale up --accept-routes --advertise-routes=10.0.60.0/24 --accept-dns=false

# Denn i de Tailscale Admin Console:
# https://login.tailscale.com/admin/machines
# → pve01 → "Subnet routes" → "Approve" für 10.0.60.0/24
```

### Vorteile gegenüber Tailscale uf jedem Container
- Kei TUN-Device in unprivileged LXCs nötig (geit det nöd)
- Ei Tailscale-Instanz für s'ganze Subnetz
- Android verbindet direkt zu `10.0.60.121:8443` (oder jeder andere IP im 10.0.60.x Range)
- Ende-zu-Ende verschlüsslet: WireGuard (Tailscale) + TLS (SSL-Proxy)

### Wichtig

1. **Route approve**: Nach `tailscale up --advertise-routes=...` muess i de **Admin Console** die Route **approve** werde
2. **Android App URL**: `https://10.0.60.121:8443` (mit `https://`)
3. **Self-Signed Cert**: Android zeigt Warnig — akzeptiere (isch dis eigete Zertifikat)
4. **Kei Ports nach usse offe**: Tailscale isch reine outbound-Tunnel — kei Port-Forwarding nötig

### 🔴 Pitfall: occ config:system:set versagt still

`occ config:system:set` für `overwriteprotocol` und `overwrite.cli.url` **kann still failen** — d'Config wird nöd aktualisiert, obwohl occ "set to string ..." zruggmäldet. Ursache: APCu-Cache oder Permission-Problem im Docker-Container.

**Lösig: Config.php direkt editiere via base64**

Statt `occ config:system:set ...`:

```
# 1. Aktuelle Config.php auslese (base64)
BASE64=$(docker exec code-nextcloud-1 base64 /var/www/html/config/config.php)

# 2. Inhalt decode, replace, encode
echo "$BASE64" | base64 -d > /tmp/nc_config.php
sed -i "s/'overwriteprotocol' => 'http',/'overwriteprotocol' => 'https',/" /tmp/nc_config.php
NEW_BASE64=$(base64 /tmp/nc_config.php | tr -d '\n')

# 3. Zruggschriebe
docker exec -u 0 code-nextcloud-1 sh -c "echo '$NEW_BASE64' | base64 -d > /var/www/html/config/config.php"
```

Die Methode funktioniert **garantiert**, au wenn occ mit APCu-Cache kämpft.

### User direkt via SQL erstellen
Nextcloud braucht 4 Tabellen: oc_users (mit uid_lower!), oc_group_user, oc_accounts (JSON-Profil), data/{uid}/. Immer occ user:add!

### API v1 vs v4
Chat-Nachrichten: **v1/chat/{token}** (nicht v3/v4). Room-Verwaltung: **v4/room**.

### Nextcloud Chat Bot Webhook
talk:bot:install benoetigt eine URL fuer den Webhook-Endpoint. Ohne Webhook kann der Bot nur pullen (polling).

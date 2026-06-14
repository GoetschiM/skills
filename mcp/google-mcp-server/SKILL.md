---
name: google-mcp-server
description: "Zentraler Google MCP Server — alle Bots (Hermes, Nova, Henry) nutzen eine OAuth-Session für Gmail, Calendar, Drive, Sheets, Docs."
version: 2.3.0
author: Hermes Agent
tags: [google, mcp, gmail, calendar, drive, oauth]
related_skills:
  - email-classifier
---

# Google MCP Server

Zentraler MCP Server für Google-Dienste. Läuft auf **Prod LXC 100** (10.0.60.121) als Docker-Container.

## Architektur

```
Google MCP Server (Docker, Port 8002)
├── Low-level Starlette app (KEIN FastMCP — v1.27.2 Bug!)
├── Eine OAuth Session (einmal auth → persistenter Token)
├── Automatischer Token Refresh
└── 16 MCP Tools (manuell via Starlette HTTP Handler)
    ├── google_auth_url / google_auth_exchange / google_auth_status
    ├── gmail_search / gmail_get / gmail_trash / gmail_modify / gmail_send
    ├── calendar_list / calendar_create
    ├── drive_search / drive_get
    ├── sheets_get / sheets_update
    ├── docs_get
    └── google_health
```

## Server Info

- **URL:** `http://10.0.60.121:8002/mcp`
- **Container:** `google-mcp-server` (Docker, restart unless-stopped)
- **Volume (KRITISCH!):** `-v /opt/data/google-mcp-server/data:/data`
- **Source:** `/tmp/google-mcp-server/server.py` (Build-Verzeichnis)
- **Image:** `google-mcp-server:latest` (lokal gebaut)
- **Architektur:** Starlette + low-level HTTP Handler (niä FastMCP verwende! Bug in v1.27.2)

## Tools (16 total)

| Tool | Beschreibung |
|------|-------------|
| `google_auth_url` | OAuth-URL generieren |
| `google_auth_exchange` | Code gegen Token tauschen |
| `google_auth_status` | Token-Status prüfen |
| `gmail_search` | Mails suchen |
| `gmail_get` | Mail-Inhalt holen (vollständigen Body) |
| **`gmail_trash`** | **Mail in Papierkorb + als gelesen markieren** |
| **`gmail_modify`** | **Labels ändern (add/remove z.B. UNREAD, TRASH)** |
| `gmail_send` | Mail senden |
| `calendar_list` | Kalendertermine |
| `calendar_create` | Termin erstellen |
| `drive_search` | Drive durchsuchen |
| `drive_get` | Datei-Metadaten |
| `sheets_get` | Sheet lesen |
| `sheets_update` | Sheet schreiben |
| `docs_get` | Doc lesen |
| `google_health` | Status aller Dienste |

## Deployment

### Architecture Reference
> `references/architecture.md` — tool registration pattern, HTTP handler, OAuth PKCE flow, server startup

```bash
# Source liegt in /tmp/google-mcp-server/server.py
cd /tmp/google-mcp-server

# Container erstelle
docker build --no-cache -t google-mcp-server:latest .

# Container starten (Volume-Pfad KRITISCH für Token-Persistenz!)
docker run -d --name google-mcp-server \
  --restart unless-stopped \
  -p 8002:8002 \
  -v /opt/data/google-mcp-server/data:/data \
  google-mcp-server:latest

# Logs prüfe
docker logs google-mcp-server --tail 5

# Token-Status prüfe
curl -s http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_health","arguments":{}}}'
```

## Verwendung

**Immer `Accept: application/json` Header mitschicke!**
Ohni dä Header schickt de Server 406 Not Acceptable.

```bash
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gmail_search","arguments":{"query":"is:unread","max_results":5}}}'
```

### Wichtigi Befehle

```bash
# Mails löschen (trash + als gelesen)
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gmail_trash","arguments":{"message_id":"MAIL_ID"}}}'

# Als gelesen markiere (ohni löschä)
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gmail_modify","arguments":{"message_id":"MAIL_ID","remove_labels":"UNREAD"}}}'

# Tools-Liste abruefe
curl -s -X POST http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## OAuth Setup (einmalig — Token überläbt Neustarts!)

> **PKCE-Fix (important!):** `auth_url()` und `auth_exchange()` MÜSSEN
> de gliiche PKCE code_verifier teile. Die deployed Version verwendet
> **`global _AUTH_FLOW`** (gleicher `InstalledAppFlow` für beide Calls).
> Details und beide Alternativ-Methoden: `references/pkce-oauth-fix.md`

Falls Token abläuft oder uf em Volume nid existiert:

1. De Auth-URL abruefe:
```bash
curl -s http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_auth_url","arguments":{}}}'
```

2. Link im Browser öffnen → Google Auth → Code kopieren (4/...)

3. Code iitausche:
```bash
curl -s http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_auth_exchange","arguments":{"code":"4/xxx..."}}}'
```

4. **Verifiziere: Token isch im Volume**
```bash
ls -la /opt/data/google-mcp-server/data/token.json
```
Sötti Datei existiere → Token überläbt Container-Neustarts und -Rebuilds.

## Token-Persistenz (KRITISCH!)

De Token wird im Volume `/opt/data/google-mcp-server/data/token.json` gspeichered.
**MUSS** per `-v` gemountet werde, suscht ischer bim nächste docker rm weg.

**Historische Fehler (29.05.2026):**
- Beim erschte Deployment isch de Token im Container-Layer gspeichered worde (nid im Volume)
- Bi Rebuild (docker rm + docker run) isch de Token verlore
- Fix: Volume uf `/opt/data/google-mcp-server/data` mounte — das isch uf em langlebige Proxmox-Datastore
- Container Chache (docker system prune) löscht nüt us Volume

**Prüf-Command:**
```bash
docker exec google-mcp-server ls -la /data/token.json
```

## References

Zu diesem Skill ghörendi Referenz-Dateie:

| Datei | Inhalt |
|-------|--------|
| `references/architecture.md` | Tool registration pattern, HTTP handler, OAuth PKCE flow, server startup |
| `references/pkce-oauth-fix.md` | PKCE Verifier-Problem + beide Fix-Ansätze (global + file-based) |
| `references/client-secrets.md` | **BEIDE** OAuth Clients uf Notion (Client-ID + Secret im Klartext) |
| `references/deployment.md` | Deployment-Workflow, Ports, Volumes |
| `references/deployment-quickref.md` | Kurzreferenz für schnelles Deployen |
| `references/token-persistence.md` | Token-Persistenz via Volume |
| `references/fastmcp-bug-1272.md` | FastMCP v1.27.2 Bug-Doku (warum Starlette verwendet wird) |

## Troubleshooting

### 14 statt 16 Tools (docker-proxy Effekt) ⚠️ UNGELÖST (29.05.2026, bestätigt mehrfach)

D' `tools/list`-Response unterschided sich je nach Zugriffspfad:

| Zugriff | Tools |
|---------|-------|
| Container-intern via localhost | 16 ✅ |
| Container-intern via TestClient (ASGI direkt) | 16 ✅ |
| Container-intern via Bridge-IP (172.17.0.X) | 16 ✅ |
| Von USSE via docker-proxy (10.0.60.121:8002) | 14 ❌ |

Fehlendi Tools: **gmail_trash, gmail_modify**.

**Docker-proxy ist nur TCP** — es sollte HTTP nid modifizieren. Dennoch tritt
der Effekt reproduzierbar auf. Mögliche Ursachen (ungelöst):
- Docker Overlay Network / DNAT vor LXC
- LXC Kernel Namespace Issue
- Starlette/uvicorn Request-Routing für spezifische Source-IPs

**Workaround:** `tools/call` uf gmail_trash/gmail_modify funktioniert vo usse
**PROBLEMLOS** — nume `tools/list` git 14 zrugg. Einfach direkt ufruefe statt
uf d'Liste z'vertraue.

```bash
# Geit immer — au vo usse!
curl -s http://10.0.60.121:8002/mcp \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gmail_trash","arguments":{"message_id":"xxx"}}}'
```

### Wichtigi Pitfalls

#### 🔴 Code-Änderige im Container verifiziere VOR User-Test

**Gfährlichste Fehler (mehrfach passiert am 29.05.2026):** De User (Michel) het 3x en  
Auth-Code gschickt, wo nöd funktioniert het, will d'Server-Änderige nöd aktiv gsy sind  
(`docker exec` het en andere Prozess modifiziert — nid de uvicorn-Prozess).

**Regle — unbedingt befolge:**
1. Code im Source-File ändere (`/tmp/google-mcp-server/server.py`)
2. Container **neubaue** (`docker build`) ODER `docker cp server.py:/app/server.py && docker restart`
3. **Verifiziere** dass d'Änderig aktiv isch:  
   `docker exec google-mcp-server grep "PATTERN" /app/server.py`
4. **Teste** (via curl — nid via `docker exec python3` will das en NEUE Prozess isch!)
5. **Erst DANN** de User bitte, öppis z'tue (Auth-Code schicke, Klick mache, etc.)

Jede Fehlversuch vom User = Vertrauensverlust. Lieber 2x prüefe als 1x z'wenig.

#### 🔴 Embedded Functions statt Imports

Wenn du Code in laufendem Container änderesch (`docker cp` + `docker restart`):
- **NIEMALS** Funktionen us eme separate Modul importiere (`from auth_patch import ...`)
- **IMMER** Funktionen DIREKT in server.py definiere, VOR der TOOL_MAP-Referenz
- Grund: Import-Zeile landet im File nooch de TOOL_MAP und verursacht `NameError`
- **Auch NIEMALS** per `docker exec python3 -c` mit langem Heredoc patchen — wird
  oft als daemon-detected blockiert oder läuft im falschen Prozess-Kontext.
  Verwende stattdessen `docker cp` für Datei-Manipulation.

#### 🔴 Python `true` vs `True` Bug (Line 585)

**Symptom:** `auth_exchange` schlägt fehl mit `Internal error: name 'true' is not defined` — aber nöd bim eigentliche Code, sondern BI der Error-Response-Serialisierung.

**Ursache:** Zeile 585 und 577 in `server.py` verwenden JavaScript `true` statt Python `True` in der Error-Handling-Response:

```python
# ❌ FALSCH — JavaScript-Notation in Python
"isError":true
# ✅ RICHTIG
"isError":True
```

**Fix im laufenden Container:**
```bash
docker exec google-mcp-server sed -i 's/"isError":true/"isError":True/g' /app/server.py
docker restart google-mcp-server
```

**Fix im Build-Verzeichnis:**
```bash
sed -i 's/"isError":true/"isError":True/g' /tmp/google-mcp-server/server.py
docker stop google-mcp-server
docker cp /tmp/google-mcp-server/server.py google-mcp-server:/app/
docker start
```

**Prüf-Command:** `docker exec google-mcp-server grep 'isError.*true' /app/server.py` — sollte leer sein (keine Treffer = gefixt).

#### 🔴 Syntax Error → Restart Loop Recovery

Wenn server.py einen Syntax Error bekommt (z.B. durch falschen Patch), crasht
der Container sofort beim Start. Docker restartet automatisch, aber der
Container ist nur Millisekunden "Up" — zu kurz für `docker exec`.

**Recovery:**
```bash
docker stop google-mcp-server                    # Stoppt sofort (kein Restart-Timeout)
docker cp /tmp/original/server.py google-mcp-server:/app/server.py  # Fix
docker start google-mcp-server                    # Läuft wieder
```

Als Vorsorge: **immer** einen unmodifizierten Stand von server.py parat haben
(z.B. im `/tmp/google-mcp-server/` Build-Verzeichnis).

#### 🔴 Volume mounting vergässe
Volume MUSS bi `docker run` mit `-v /opt/data/google-mcp-server/data:/data` deby si.  
Ohni Volume: Token isch nur im Container-Layer → verlore bim `docker rm`.

#### 🔴 "406 Not Acceptable" / Empty Response
`Accept: application/json` Header fehlt. De Server prüft das zwingend.

#### 🔴 client_secret.json fehlt bei Erst-Einrichtung

Dä **OAuth Client Secret** als JSON-Datei (`client_secret.json`) MUSS im Volume existiere. Ohni schlaht `InstalledAppFlow.from_client_secrets_file()` fähl sofort:

```bash
# Prüfe ob vorhande
ls -la /opt/data/google-mcp-server/data/client_secret.json
```

**Fundort:** De Client Secret JSON liit **NICHT** als reguläre Google-Cloud-Console-Download, sondern isch i **Notion** dokumentiert:

- **Notion-Page:** [OAuth-Client erstellt](https://www.notion.so/OAuth-Client-erstellt-30981c83f6d9804f8a22e84ee0542689)
- **Page-ID:** `30981c83f6d9804f8a22e84ee0542689`
- Döt staht d'**Client-ID** + **Clientschlüssel** im Klartext → us dene isch de JSON manuell z'baue

**Zwei OAuth Clients existiere (Details: `references/client-secrets.md`):**

| Client | Erstellt | Status |
|--------|----------|--------|
| `983053334079-vq4…` | 16.02.2026 | Alt, nid verwändet |
| **`983053334079-9t7…`** | **23.02.2026** | **Aktiv (im Einsatz)** |

**Deployed `client_secret.json` baue (NUR EINMALIG):**
```bash
# Uf Basis vo Notion-Eintrag — Client-ID + Secret direkt us dere Page
# Das File isch im Volume → überläbt Neustarts + Rebuilds
cat > /opt/data/google-mcp-server/data/client_secret.json << 'EOF'
{"installed":{"client_id":"GOOGLE_CLIENT_ID_2","project_id":"meinlokalerbot","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"GOOGLE_CLIENT_SECRET_2","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
EOF
```

#### 🔴 `invalid_grant` in google_api.py — Token Sync Fix (29.05.2026)

**Symptom:** `google_api.py gmail search "is:unread"` gibt:
```
google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.', ...)
```
**Ursache:** `google_api.py` liest Token us `/root/.hermes/google_token.json`, de MCP Server aber schribt sin Token i ds **Volume** unter `/opt/data/google-mcp-server/data/token.json`. Wenn das Volume neu isch oder de Token det aktualisiert wird, bliibt `/root/.hermes/google_token.json` alt.

**Fix (einmalig):** `/root/.hermes/google_token.json` vom MCP-Volume symlinke:
```bash
rm -f /root/.hermes/google_token.json
ln -s /opt/data/google-mcp-server/data/token.json /root/.hermes/google_token.json
```
Ab dem Momänt liest `google_api.py` immer de aktuellste Token us em Volume — au wenn er via MCP Server refreshed wird.

**Wenn de Symlink scho existiert aber de Token abglofe isch:** Eifach neui OAuth Auth via MCP Server mache (google_auth_url → google_auth_exchange), denn isch de Token automatisch au für google_api.py verfüegbar.

### Token verlore nach Rebuild

### MCP Client kann keine Verbindung
- Container läuft? `docker ps --filter name=google-mcp-server`
- Port 8002 öffentlich? `ss -tlnp | grep 8002`
- Vom Host aus testbar? `curl -v http://10.0.60.121:8002/mcp -H "Accept: application/json"`

### Server stürzt beim Start ab (Restart Loop)
Logs prüfe: `docker logs google-mcp-server --tail 20`

Wenn ein **Syntax Error in server.py** die Ursache ist, steckt der Container
in einer Restart-Schleife (zu kurz "Up" für `docker exec`):

```bash
docker stop google-mcp-server                                    # Stoppe
docker cp /tmp/google-mcp-server/server.py google-mcp-server:/app/  # Fixe Datei
docker start google-mcp-server                                    # Start
```

Häufigste Ursachen:
- Syntax-Fehler nach einer `patch`-Operation im laufenden Container
- Import aus einem nicht existierenden Modul
- `_logged_tool` Wrapper mit doppelten Anführungszeichen

**Teste Code-Änderungen NIE per `docker exec python3 -c`** — das erzeugt
einen neuen Python-Prozess und zeigt nicht den uvicorn-Server-Zustand an.
Verwende stattdessen **curl** für echte HTTP-Tests.

### Source Code verwalte
```bash
# Source uf gl-stack repo
cp /tmp/google-mcp-server/server.py /gl-stack/services/google-mcp-server/
cd /gl-stack && git add . && git commit -m "fix: google-mcp-server v2 - Starlette, persistent token, gmail_trash"
```

## Wichtigi Konvention

- **JSON-RPC 2.0** via HTTP POST
- Immer **`Content-Type: application/json`** Header
- Immer **`Accept: application/json`** Header (suscht 406)
- Response-Format: `{"jsonrpc":"2.0","id":<id>,"result":{"content":[{"type":"text","text":"..."}]}}`
- Errors: `{"jsonrpc":"2.0","id":<id>,"result":{"content":[{"type":"text","text":"Error: ..."}],"isError":true}}`
# 🚨 System-Credentials & Endpunkte (ID 35717121) — Update-Reference

## Zweck

Diese Referenz dokumentiert den **kompletten Workflow für Updates** der zentralen Credential-Seite.
Letztes grosses Update: **09.06.2026 → v4** (12 Kategorien statt bisher 6).

## Grundprinzipien

- **ALLES** rein: IPs, Ports, URLs, Username, Passwort-Schema
- **Kritische Credentials** (Proxmox root, SIP-Passwörter, API-Tokens) → `🔒 .env/Qdrant` (nie Klartext auf Confluence!)
- **Normali Credentials** (Admin-User, Mailboxen, Medienstacks) → direkt als Klartext in `<code>`-Tags
- **Seitentitel:** `🚨 System-Credentials & Endpunkte`
- **Parent:** Root-Seite `Goetschi Labs` (ID 163933)
- **Kei Tables auf Confluence?** Telegram hat keine Tables, aber Confluence schon — <table> ist OK im Storage-Format

## Kategorien (vollständige Reihenfolge seit v4)

```
 1. 🏠 Hosts & Infrastruktur      — Proxmox, LXCs, VMs, Docker-Hosts
 2. 🔑 Cloud-Dienste & APIs       — All-Inkl, GitHub, ElevenLabs, Notion, Jira, Telegram
 3. 🤖 AI & LLM Services          — LiteLLM, Ollama, MCPHub, Qdrant
 4. 🌐 Netzwerk & Telefonie       — UniFi, SIP, Asterisk, Dograh, Call-APIs
 5. 🎬 Media-Stack (VM 201)       — qBit, Sonarr, Radarr, Prowlarr, Plex + Storage
 6. 🎙️ Telefonie-Komponenten     — Dograh, Asterisk, Call API, LiteLLM (Voice-spezifisch)
 7. 💾 Storage & Backups          — MinIO, GitHub, NextCloud DB
 8. 🚀 Platform-Orchestratoren    — Coolify, Dokploy Prod, Dokploy Dev/Sandbox
 9. 🛠️ Hermes Agent (lokal)      — Config, Skills, Profile, Model, TTS/STT, Cron, Gateway
10. 📦 Spezielle Systeme          — Kali, Bot04, MT5, TRAD Projekt, n8n
11. 🗝️ Passwort-Schema            — Louis_one_*, Riotstar_*, HermesVB*, Admin_*!, ApolloHermes*!
12. ⚠️ Hinweise                    — Credential-Philosophie, bekannte Fehler
```

**Kritisch:** Bisherigs Update (v3→v4) het Kategorie 8, 9, 10, 11 dezuegno. Bi nöie Updates die vollständig Liste verwende, nie auf Kategorie 1-6 reduziere.

## Update-Prozess — 2 bewährte Wege

### Weg A: curl + JSON-Tempfile (empfohlen, robuster)

```bash
# 1. HTML-Body vorbereite (in /tmp/confluence-body.html)
#    — Emoji-Unicode direkt verwenden (🚨🏠🔑 etc.)
#    — &, <, > escapen: &amp; &lt; &gt;
#    — <strong> für Host-Namen, <code> für Credentials

# 2. Aktuelle Version holen
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"

CURRENT=$(curl -s -u "$AUTH" \
  "$BASE/rest/api/content/35717121?expand=version" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['version']['number'])")
NEXT=$((CURRENT + 1))

# 3. JSON-Payload bauen
python3 -c "
import json
with open('/tmp/confluence-body.html') as f:
    body = f.read()
payload = {
    'id': '35717121',
    'type': 'page',
    'title': '\U0001f6a8 System-Credentials & Endpunkte',
    'space': {'key': '~5a75b5612d61371e861f4dae'},
    'version': {'number': $NEXT},
    'body': {'storage': {'value': body, 'representation': 'storage'}}
}
with open('/tmp/confluence-payload.json', 'w') as f:
    json.dump(payload, f, ensure_ascii=False)
"

# 4. PUT (via -d @file — NIE inline, sonst shell-escape-Chaos!)
curl -s -u "$AUTH" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d @/tmp/confluence-payload.json \
  "$BASE/rest/api/content/35717121" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'✅ v{d.get(\"version\",{}).get(\"number\",\"?\")} — {d.get(\"status\",\"?\")}')
print(f'🌐 https://{DOMAIN}/wiki{d.get(\"_links\",{}).get(\"webui\",\"?\")}'
```
**Wichtig:** Das `***`-Problem — will Confluence-Token oft `***` enthaltet, wird jede Code-Block mit `TOKEN=***` zerschosse. **Immer** curl mit source .env + `$ATLASSIAN_TOKEN` Variable, nie hardcoded ins Script schribe.

### Weg B: Python (via execute_code, bei grossen Bodies)

```python
import json
# Env lese
env = {}
with open("/opt/data/home/.hermes/.env") as f:
    for line in f:
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v

# Config
EMAIL = env["ATLASSIAN_EMAIL"]
TOKEN = env["ATLASSIAN_TOKEN"]
DOMAIN = env["ATLASSIAN_DOMAIN"]
PAGE_ID = "35717121"
BASE = f"https://{DOMAIN}/wiki"

# 1. Aktuelle Version
import urllib.request, base64
auth_h = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
headers = {"Authorization": f"Basic {auth_h}", "Content-Type": "application/json"}
req = urllib.request.Request(f"{BASE}/rest/api/content/{PAGE_ID}?expand=version",
    headers=headers)
data = json.loads(urllib.request.urlopen(req).read())
current_ver = data["version"]["number"]
next_ver = current_ver + 1

# 2. HTML einlesen + Payload
with open("/tmp/confluence-body.html") as f:
    body = f.read()
payload = {
    "id": PAGE_ID,
    "type": "page",
    "title": "🚨 System-Credentials & Endpunkte",
    "space": {"key": "~5a75b5612d61371e861f4dae"},
    "version": {"number": next_ver},
    "body": {"storage": {"value": body, "representation": "storage"}}
}

# 3. PUT
req2 = urllib.request.Request(f"{BASE}/rest/api/content/{PAGE_ID}",
    data=json.dumps(payload).encode(), headers=headers, method="PUT")
resp = json.loads(urllib.request.urlopen(req2).read())
print(f"✅ Version {current_ver} → {resp['version']['number']}")
print(f"🌐 https://{DOMAIN}/wiki{resp['_links']['webui']}")
```

**Bekanntes Problem mit Python:** `urllib.request` hat manchmal base64-Basic-Auth-Probleme (403 Forbidden). Grund ist encoding der Base64. **Fix:** Dann Weg A (curl) verwenden.

## HTML-Struktur für Credential-Seite

Confluence Storage-Format akzeptiert HTML. Template:

```html
<h1>🚨 System-Credentials &amp; Endpunkte</h1>
<p><em>Letztes Update: DD.MM.YYYY</em></p>

<h2>🏠 1. Hosts &amp; Infrastruktur</h2>
<table>
<thead>
<tr><th>System</th><th>Typ</th><th>IP</th><th>Ports</th><th>Zugriff</th><th>Hinweise</th></tr>
</thead>
<tbody>
<tr><td><strong>System-X</strong></td><td>LXC/VM</td><td>10.0.60.X</td><td>22, 8080</td><td>🔒 .env</td><td>Beschreibung</td></tr>
</tbody>
</table>
```

**Wichtige HTML-Regeln:**
- Alle Überschriften als `<h2>` (Confluence ignoriert h1-h6-Defaults, zeigt alles als h2-artig)
- Emojis direkt als Unicode: 🚨🏠🔑🤖🌐🎬🎙️💾🚀🛠️📦🗝️⚠️
- `<strong>` für Host-Namen
- `<code>` für Credentials (nur nicht-kritische)
- `&amp;` und `&lt;`/`&gt;` escaped
- ⚠️ Hinterlege bei Credentials die NUR in .env stönd: `🔒 .env`
- ⚠️ MCPHub-Login-Fail dokumentiere: `admin: Admin_2026! ⚠️ Login nüm gültig`

## Repository-Struktur (GitHub)

Skills leben in: `github.com/GoetschiM/hermes-agent-skills/`
Zugriff: 🔒 privat (User: GoetschiM, Token in .env)

## Bekannte Pitfalls & Learnings (09.06.2026)

### 1. API-Token mit `***` im Value zerstört Shell/Python

Das Confluence-Token (`ATATT3...3BE5`) enthält `***`. Wenn du `export TOKEN=***` schribsch, parsed die Shell * als Glob und du hesch zerschosseni Syntax.

**Lösung:** `source /opt/data/home/.hermes/.env` verwende (Shell liist richtig) oder `with open()` direkt lese (Python). NIE in heredoc oder execute_code inline setze.

### 2. HTML-Body > Shell-Quote-Problem

HTML-Bodies sind gross (>6000 Bytes) mit verschachtelten Quotes. Inline in `curl -d '{...}'` zerschiest Shell.

**Lösung:** Immer JSON via Python `json.dumps()` erstelle → Tempfile → `curl -d @/tmp/payload.json`. Siehe Weg A oben.

### 3. "Password nicht mehr gültig" — verschlüsselte .env-Struktur

.env-Datei kann in versch. Pfaden liige:
- `/root/.hermes/.env` → Hermes Haupt-Config
- `/opt/data/home/.hermes/.env` → Atlassian-Credentials
- `/root/.hermes/config.yaml` → Hermes-Tokens

**Merke:** `ATLASSIAN_EMAIL` und `ATLASSIAN_TOKEN` sind NUR in `/opt/data/home/.hermes/.env`.
`source` braucht `set -a` um die Vars an subprocesses zu exportieren.

### 4. MCPHub-Login invalid → nicht auf Confluence vergessen

MCPHub (10.0.60.170:3000) hat admin/Admin_2026! — aber das Login funktioniert aktuell nicht mehr. Auf der Credential-Seite mit ⚠️ markieren. Fix braucht Docker-Neustart auf LXC 107 via Proxmox 01.

### 5. All-Inkl-Details bei jedem Update prüfen

All-Inkl-Zugang: w019000a.kasserver.com, w019000a / Riotstar_ALLINKL_13
Domain: goetschi-labs.ch
5 Mailboxen (info, hermes, nova, magos, orion) → ApolloHermes2026!
Alte Mail hermes@radislione.net muss gelöscht werden.

### 6. Hermes Agent ist NICHT auf der Credential-Seite vergessen

Seit v4: Hermes Agent hat eigene Sektion (9) mit Config-Pfad, Model, TTS/STT, Cronjobs, Gateway.
Beim nächsten Update prüfen: Hat sich was geändert?
- Ports (Gateway?)
- Model (deepseek-v4-flash)
- TTS-Provider (elevenlabs)
- Skills-Verzeichnis

### 7. Passwort-Schema bei jedem Update aktualisieren

Sektion 11 (🗝️ Passwort-Schema) is kritisch — sie dokumentiert WELCHE Passwort-Formate wo verwendet werden.
- `Louis_one_*` → Apollo/Hermes root, VMs, MinIO, Media → Louis_one_13, Louis_one_14
- `Riotstar_*` → Michel-Schema: Riotstar_MICHEL_13, Riotstar_ALLINKL_13
- `HermesVB*` → Voice: HermesVB2026 (NOVA, ARI)
- `Admin_*!` → MCPs: Admin_2026!
- `ApolloHermes*!` → Agent-Mail: ApolloHermes2026!

### 8. Coolify-Standort nicht sicher — Doku offen lassen

Coolify läuft (wsl.) auf Proxmox 02 (10.0.60.11) unter Docker. Zugriff via Port 3000 (o.ä.)
Kali-Linux-Container läuft in Coolify — nicht in Docker auf Apollo.

## Änderungshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| v1 | 23.05.2026 | Erstellung (Grundstruktur) |
| v2 | 27.05.2026 | Erweitert mit Cloud, Media, MinIO |
| v3 | 09.06.2026 | Vollständige IPs, Ports, Hosts, MCPHub, NextCloud |
| v4 | 09.06.2026 | **Komplett neu**: 12 Kategorien (Coolify, Dokploy, Hermes, Passwörter, Voice, Systeme) |

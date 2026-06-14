---
name: confluence
description: "Confluence Cloud REST API — Spaces, Seiten lesen/erstellen/bearbeiten, Knowledge-Base strukturieren. Goetschi Labs persönlicher Space + Support Onboarding."
tags: [confluence, wiki, documentation, knowledge-base, atlassian]
category: productivity
---

# Confluence Integration — Apollo's Knowledge-Base 📚

Confluence-Cloud: **`goetschi.atlassian.net/wiki`**

## Trigger-Bedingungen

- Dokumentation muss aktualisiert werden (nach Ticket-Abschluss, nach Änderungen)
- User sagt: "Confluence", "Wiki", "Doku-Seite", "Knowledge"
- User will einen strukturierten Wissensbereich aufbauen
- Neue Erkenntnisse/Prozesse die festgehalten werden müssen

## Zugangsdaten

**⚠️ Pfad-Update (05/2026):** `/opt/data/.atlassian.env` git's nümm! Credentials jetzt i `/opt/data/home/.hermes/.env`:

```bash
# Env-Vars setze
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"
```

Oder direkt in Python/execute_code:
```python
with open("/opt/data/home/.hermes/.env") as f:
    env = {}
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v
AUTH = f"{env['ATLASSIAN_EMAIL']}:{env['ATLASSIAN_TOKEN']}"
BASE = f"https://{env['ATLASSIAN_DOMAIN']}/wiki"
```

## Spaces

| Key | Name | Typ | Homepage ID |
|-----|------|-----|-------------|
| `~5a75b5612d61371e861f4dae` | **Goetschi Labs** | Personal (Haupt-Wiki) | 163933 |
| `ITSUPPORT` | **Support** | Onboarding | 164097 |

## Aktuelle Seiten-Struktur (Goetschi Labs)

```\nGrundverständnis Wir sind Goetschi Labs (163933) [Root]\n├── 🔗 Integrationen (17170454)\n│   └── NextCloud — Datei-Sync & Shared Watchfolder (35880981)\n├── 🔧 Infrastruktur (17530881)\n├── 📋 Betrieb & Runbooks (17563649)\n├── 🧪 Experimente & Evaluierungen (17596417)\n│   └── Lokale Mediengenerierung: Erste Evaluation (17629185)\n├── Dokumentation: Asterisk Two-Way Voice Bridge (16941057)\n└── [Goetschi Labs Workspace (17170434) — DELETED 25.05.2026]\n```\n\n**⚠️ Goetschi Labs Workspace (17170434) existiert nümm** — die Seite isch glöscht. Ihri ehemalige Child-Seiten (Integrationen, Infrastruktur, Betrieb, Experimente) sind jetzt direkt under em Root (163933). Neui Seite under em jeweilige direkte Parent (17170454, 17530881, 17563649, 17596417) erstelle, NIE unter 17170434.

## Spezial: Credential-Seite aktualisieren

**Seit 09.06.2026: v4 mit 12 Kategorien live!** Siehe `references/credentials-update.md` für den vollständigen Workflow.

Die Credential-Seite (ID 35717121) hat aktuell folgende Kategorien (Stand v4):
1. 🏠 Hosts & Infrastruktur
2. 🔑 Cloud-Dienste & APIs
3. 🤖 AI & LLM Services
4. 🌐 Netzwerk & Telefonie
5. 🎬 Media-Stack (VM 201)
6. 🎙️ Telefonie-Komponenten
7. 💾 Storage & Backups
8. 🚀 Platform-Orchestratoren ← **NEU v4**
9. 🛠️ Hermes Agent (lokal) ← **NEU v4**
10. 📦 Spezielle Systeme ← **NEU v4**
11. 🗝️ Passwort-Schema ← **NEU v4**
12. ⚠️ Hinweise

**CRITICAL: Bei Updates nie uf Kategorien 1-6 reduziere — ALLI 12 bhalte und ggf. ergänze!**

## API-Operationen

### 1️⃣ Space-Inhalt auflisten (alle Seiten)

```bash
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"

# Alle Seiten in Goetschi Labs Space
curl -s -u "$AUTH" "$BASE/rest/api/content?spaceKey=~5a75b5612d61371e861f4dae&limit=50&expand=ancestors,version" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
for p in d.get('results',[]):
    parent = p.get('ancestors',[])
    parent_info = parent[-1]['title'] if parent else 'ROOT'
    ver = p.get('version',{}).get('number',1)
    print(f'  [{p[\"id\"]:8s}] {p[\"title"]:50s} v{ver} > {parent_info}')
"
```

### 2️⃣ Seite lesen (Inhalt + Details)

```bash
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"

curl -s -u "$AUTH" "$BASE/rest/api/content/163933?expand=body.storage,version,ancestors,space" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Title: {d[\"title\"]}')
print(f'Space: {d[\"space\"][\"name\"]} ({d[\"space\"][\"key\"]})')
print(f'Version: {d[\"version\"][\"number\"]}')
print(f'Body:\\n{d.get(\"body\",{}).get(\"storage\",{}).get(\"value\",\"-\")}')
"
```

### 3️⃣ Seite erstellen (Child-Page)

```bash
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"

# Seite erstellen unter 🔗 Integrationen (17170454) als Parent (aktuell aktivi Seite)
# oder unter Infrastruktur (17530881), Betrieb & Runbooks (17563649), etc.
#
# ⚠️ NIE 17170434 (Goetschi Labs Workspace) — Seite gelöscht!
# Für Integration: Parent=17170454, Infrastruktur: Parent=17530881, etc.

curl -s -X POST -u "$AUTH" \
  -H "Content-Type: application/json" \
  "$BASE/rest/api/content" \
  -d '{
    "type": "page",
    "title": "Seiten-Titel hier",
    "space": {"key": "~5a75b5612d61371e861f4dae"},
    "ancestors": [{"id": "17170434"}],
    "body": {
      "storage": {
        "value": "<p>Inhalt der Seite als HTML...</p>",
        "representation": "storage"
      }
    }
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Erstellt: {d[\"_links\"][\"webui\"]} (ID: {d[\"id\"]})')"
```

**Wichtige Parent-IDs (Stand 06.06.2026):**
| Seite | ID |
|-------|-----|
| 🏠 Goetschi Labs — Übersicht & Regeln (Root) | 163933 |
| 🔗 Integrationen | 17170454 |
| 🔧 Infrastruktur | 17530881 |
| 📋 Betrieb & Runbooks | 17563649 |
| 🧪 Experimente & Evaluierungen | 17596417 |
| 🤖 Agenten & Systeme | 32538626 |
| 📈 Börse & Finanzen | 32571393 |
| 💾 Backups & Datenhaltung | 32604161 |
| 🚨 System-Credentials & Endpunkte | 35717121 |
| 📦 Projekte | 42532865 |
| 🏠 Smart Home & Home Assistant | 42500099 |
| 🌐 Netzwerk & Zugriff | 42926082 |
| 🎙️ Telefonie & Voice | 42958850 |
| 📡 Medien & Automation | 42991617 |

### 4️⃣ Seite updaten (Versionierung!)

```bash
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"

# ERST aktuelle Version holen!
CURRENT=$(curl -s -u "$AUTH" "$BASE/rest/api/content/163933?expand=version" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['version']['number'])")

# DANN mit nächsthöherer Version updaten
NEXT=$((CURRENT + 1))
curl -s -X PUT -u "$AUTH" \
  -H "Content-Type: application/json" \
  "$BASE/rest/api/content/17170434" \
  -d "{
    \"type\": \"page\",
    \"title\": \"Goetschi Labs Workspace\",
    \"space\": {\"key\": \"~5a75b5612d61371e861f4dae\"},
    \"version\": {\"number\": $NEXT},
    \"body\": {
      \"storage\": {
        \"value\": \"<p>Neuer Inhalt...</p>\",
        \"representation\": \"storage\"
      }
    }
  }" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Update v{CURRENT}->v{NEXT}: {d.get(\"status\",\"FAILED\")}')"
```

### 5️⃣ Suchen

```bash
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN/wiki"

curl -s -u "$AUTH" "$BASE/rest/api/search?cql=text~\"Asterisk\"&limit=10" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('results',[]):
    print(f'  [{r[\"content\"][\"id\"]:8s}] {r[\"title\"]:50s} Space: {r[\"resultGlobalContainer\"][\"title\"]}')
"
```

## Dokumentations-Konventionen

**Wohin was kommt:**

- **🔗 Integrationen** (17170454) → Nur externe Anbindungen/SaaS (WhatsApp, Telegram, Jira, Notion, GitHub, Google Workspace, Confluence)
- **🔧 Infrastruktur** (17530881) → Server, Container, Netzwerk, LXCs, Dokploy, Ports (ohne sensitive Werte!)
- **🤖 Agenten & Systeme** (32538626) → Unsere eigenen Agenten (Hermes, Nova, Dograh), Skills, Swarm-Wissen, LLM-Integrationen
- **📈 Börse & Finanzen** (32571393) → Trading-Bots, MT5, NEI, Market-Data, Finanz-Tools
- **📋 Betrieb & Runbooks** (17563649) → Backup/Recovery, Monitoring/Health, Cronjobs, Wartung, Pipeline-Prozesse, E-Mail Dispatch
- **🧪 Experimente & Evaluierungen** (17596417) → Technologie-Evaluierungen, Proof-of-Concepts, GL-Ticket-Experiments
- **💾 Backups & Datenhaltung** (32604161) → Backup-Strategien, MinIO, GitHub-Backups
- **🚨 System-Credentials & Endpunkte** (35717121) → Zentrale Credential-Dokumentation, API-Endpunkte (sensitive!)
- **📦 Projekte** (42532865) → Kundenprojekte, externe Engagements (Moto-Poschung, grow-pro.ch)
- **🏠 Smart Home & Home Assistant** (42500099) → Home Assistant, Shelly, Hue, Smart-Devices
- **🌐 Netzwerk & Zugriff** (42926082) → UniFi, Tailscale, VPN, Netzwerk-Topologie
- **🎙️ Telefonie & Voice** (42958850) → Asterisk-Telefonzentrale, Apollo-Call, Voice-Integration
- **📡 Medien & Automation** (42991617) → ArrStack, Plex, Media-Management

**Nach Ticket-Abschluss:**
1. Wenn neue Infrastruktur/Integration entstanden → Seite unter passendem Parent erstellen (🔧 Infrastruktur / 🔗 Integrationen / 🤖 Agenten & Systeme)
2. Wenn neuer Prozess → Seite unter "📋 Betrieb & Runbooks"
3. Wenn neue Technologie evaluiert → Seite unter "🧪 Experimente & Evaluierungen"
4. Wenn neues externes Projekt → Seite unter "📦 Projekte"
5. Wenn neue Credentials → Seite unter "🚨 System-Credentials & Endpunkte"
6. Im Ticket kommentieren: "Doku aktualisiert in Confluence: [Link zur Seite]"

## HTML-Body für Confluence-Seiten

Confluence Storage-Format verwendet HTML. Wichtige Tags:

```html
<p>Absatz</p>
<h1>Überschrift 1</h1> ... <h6>Überschrift 6</h6>
<ul><li>Punkt 1</li><li>Punkt 2</li></ul>
<ol><li>Nummer 1</li><li>Nummer 2</li></ol>
<code>Inline-Code</code>
<ac:structured-macro ac:name="code">
  <ac:plain-text-body><![CDATA[Code-Block hier]]></ac:plain-text-body>
</ac:structured-macro>
<ac:structured-macro ac:name="info">
  <ac:rich-text-body><p>Info-Box</p></ac:rich-text-body>
</ac:structured-macro>
<ac:structured-macro ac:name="warning">
  <ac:rich-text-body><p>Warnung</p></ac:rich-text-body>
</ac:structured-macro>
<ac:structured-macro ac:name="tip">
  <ac:rich-text-body><p>Tipp</p></ac:rich-text-body>
</ac:structured-macro>
<a href="https://...">Link</a>
<br/> für Zeilenumbruch
<strong>Fett</strong> oder <em>Kursiv</em>
<table><tr><th>Header</th><td>Value</td></tr></table>
```

## Bekannte Probleme & Pitfalls

- ⚠️ **Versionierung:** Confluence erlaubt kein Update ohne korrekte `version.number` — immer erst aktuelle Version holen!
- ⚠️ **Base URL:** Confluence Cloud API ist unter `/wiki/rest/api/` erreichbar, nicht `/rest/api/`. Korrekt: `https://domain.atlassian.net/wiki/rest/api/content/...`
- ⚠️ **Storage-Format:** Body muss `representation: storage` sein, nicht `wiki` oder `editor`
- ⚠️ **IDs:** Content-IDs sind numerisch und Space-Keys können kryptisch sein (`~...` für Personal Spaces)
- ⚠️ **CQL-Suche mit Sonderzeichen schlägt fehl:** Wenn der Seitentitel einen `—` (Em Dash), `–` (En Dash) oder andere Unicode-Sonderzeichen enthält, bricht `/rest/api/search?cql=title~"..."` mit HTTP 400 ab. Fix: Titel-url-codiert direkt via `/rest/api/content?spaceKey=KEY&title=URENCODED_TITLE` suchen (ohne CQL).
- ⚠️ **Große HTML-Bodies in Shell: JSON per Tempfile** — Multi-line Storage-HTML in `curl -d "..."` bricht wägem Shell-Quote'ing. Lösig: JSON-String i Tempfile schribe (`/tmp/body.json`) und via `curl -d @/tmp/body.json` referenze. Python `json.dumps()` isch sicherer als Shell-Escapes. (Gelernt 26.05.2026 bim Erstelle vo Qdrant-Standard-Seite.)
- ⚠️ **Rate Limits:** Bei Batch-Updates 500ms Pause zwischen Requests
- ✅ CQL-Syntax: `text~"suchbegriff"` für Volltextsuche, `space=KEY` für Space-Filter, `type=page` für Seitentyp

## 3-Fach-Sicherung

Bei Änderungen am Workflow oder Credentials:
1. **Skill updaten** → `skill_manage(action='patch', name='confluence', ...)`
2. **Memory updaten** → `memory(action='add', target='memory', ...)`
3. **Notion Knowlage DB** → Eintrag aktualisieren

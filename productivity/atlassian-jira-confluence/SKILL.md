---
name: atlassian-jira-confluence
description: "Goetschi Labs operations umbrella: Atlassian Jira & Confluence, Notion, TTS config, credential hierarchy, infrastructure reference, agent communication rules, UniFi/MCPHub debugging. Use for any Goetschi Labs task."
version: 1.0.0
author: Magos
license: MIT
metadata:
  hermes:
    tags: [atlassian, jira, confluence, goetschi-labs, api]
    related_skills: [hermes-agent]
---

# Atlassian Jira & Confluence (Goetschi Labs)

## Overview

Goetschi Labs nutzt Atlassian Cloud unter goetschi.atlassian.net. Zwei Hauptprojekte:
- **GL**: Goetschi Labs interne Tickets
- **SUP**: Support-Tickets (migriert in GL)

Für Confluence gibt es **3 Spaces**: Goetschi Labs (`~5a75b5612d61371e861f4dae`), Besorgsdir (`BES`), Support (`ITSUPPORT`).

## Setup

⚠️ **Wichtig (Stand 2026):** Atlassian hat die `/rest/api/2/` Endpunkte abgeschaltet. Die Bibliothek `atlassian-python-api` funktioniert für **Jira** nicht mehr (nur Confluence geht noch via `/rest/api/2/`). Für Jira IMMER `requests` mit `/rest/api/3/...` verwenden (siehe Jira-Aufrufe unten).

**Confluence** (funktioniert noch via Library):
```python
from atlassian import Confluence

confluence = Confluence(
    url='https://goetschi.atlassian.net',
    username='michelgoetschi@gmail.com',
    password='<API_TOKEN>',  # Aus Memory/User-Credentials
    timeout=30
)
```

**Jira** (immer REST v3 direkt):
```python
import requests
AUTH = ('michelgoetschi@gmail.com', '<API_TOKEN>')  # Aus Memory/User-Credentials
```

### Installation
```bash
pip3 install atlassian-python-api requests
```

## Confluence – Wichtige Pages

**Goetschi Labs Space** (`~5a75b5612d61371e861f4dae`):
| ID | Title | Beschreibung |
|----|-------|-------------|
| 163933 | Goetschi Labs — Übersicht & Regeln | Onboarding & Mission |
| 17170454 | 🔗 Integrationen | Alle integrierten Dienste |
| 17530881 | 🔧 Infrastruktur | Server, LXC, Docker Swarm |
| 17563649 | 📋 Betrieb & Runbooks | Daily Ops, Cronjobs, Wartung |
| 30343262 | 🤖 Agenten-Profile | Hermes, NOVA, APOLLO |
| 29491264 | 🧠 Schwarmwissen-Architektur | Qdrant + Minio + Skill-Sharing |
| 29491203 | Nova Memory — Qdrant | Semantisches Langzeitgedächtnis |

### Nützliche Confluence-Aufrufe

```python
# Alle Spaces
spaces = confluence.get_all_spaces(limit=50)

# Alle Pages in einem Space
pages = confluence.get_all_pages_from_space('~5a75b5612d61371e861f4dae', limit=50)

# Page-Inhalt lesen
page = confluence.get_page_by_id(163933, expand='body.storage')
body_html = page.get('body',{}).get('storage',{}).get('value','')

# Page suchen
results = confluence.get_all_pages_from_space(space_key, start=0, limit=50)
```

### Confluence Page Body updaten (REST API v2)

**⚠️ Wichtig:** Die `atlassian-python-api` Library bietet keinen einfachen Weg, den Body einer Seite zu ersetzen. Stattdessen direkt REST API v2 via `requests`:

```bash
# 1. Schritt: Aktuellen Content + Version abrufen
curl -s -u "user:API_TOKEN" \
  "https://goetschi.atlassian.net/wiki/api/v2/pages/PAGE_ID?body-format=storage"

# 2. Schritt: PUT mit version.number+1 und body.value
curl -s -u "user:API_TOKEN" \
  -X PUT \
  -H "Content-Type: application/json" \
  "https://goetschi.atlassian.net/wiki/api/v2/pages/PAGE_ID" \
  -d '{
    "id": PAGE_ID,
    "status": "current",
    "title": "Page Title",
    "body": {
      "representation": "storage",
      "value": "<h1>Updated HTML Content</h1>"
    },
    "version": {
      "number": N+1,
      "message": "Update summary"
    }
  }'
```

**Python-Workflow für große HTML-Updates (wie Credentials-Seite):**
```python
import requests, json

AUTH = ('michelgoetschi@gmail.com', '<API_TOKEN>')
BASE = 'https://goetschi.atlassian.net/wiki/api/v2/pages'
PAGE_ID = 35717121

# 1. Aktuelle Daten holen
r = requests.get(f'{BASE}/{PAGE_ID}?body-format=storage', auth=AUTH, timeout=15)
page = r.json()
version = page['version']['number']

# 2. HTML aus Datei laden
with open('/tmp/page_content.html') as f:
    new_body = f.read()

# 3. PUT update
payload = {
    'id': PAGE_ID,
    'status': 'current',
    'title': '🚨 System-Credentials & Endpunkte',  # Muss EXAKT gleich sein
    'body': {'representation': 'storage', 'value': new_body},
    'version': {'number': version + 1, 'message': 'Update: ...'}
}
r2 = requests.put(f'{BASE}/{PAGE_ID}', json=payload, auth=AUTH,
                  headers={'Content-Type': 'application/json'}, timeout=30)
print(r2.json().get('version', {}).get('number', 'ERROR'))
```

**Pitfalls:**
- **`!` im API-Token** bricht Shell heredocs und Python `"""..."""` Strings — immer via `sys.argv` oder Datei übergeben
- **`version.number` muss exakt `aktuell+1`** sein — Confluence lehnt falsche Versionen ab
- **`title` muss exakt mit dem aktuellen Seitentitel übereinstimmen** — inklusive Emojis
- **Timeouts:** Erster Request kann 10-30s dauern (Atlassian Cloud Cold-Start)

## Jira – Wichtige Aufrufe

⚠️ **ACHTUNG (Stand 2026):** `atlassian-python-api` nutzt die alte `/rest/api/2/` API, die Atlassian inzwischen abgeschaltet hat (`"The requested API has been removed. Please migrate to the /rest/api/3/search/jql API"`). **Kein einziger API-Call via Library funktioniert mehr.** Immer direkt REST v3 via `requests` verwenden:

```python
# Tickets abfragen (via REST v3)
import requests
url = 'https://goetschi.atlassian.net/rest/api/3/search/jql'
auth = ('michelgoetschi@gmail.com', '<API_TOKEN>')
r = requests.post(url, json={'jql': 'project = GL ORDER BY created DESC', 'maxResults': 20,
    'fields': ['summary', 'status', 'priority', 'assignee', 'created']},
    auth=auth, headers={'Accept': 'application/json'}, timeout=30)
data = r.json()
for issue in data.get('issues', []):
    key = issue['key']
    summary = issue['fields']['summary']
    status = issue['fields']['status']['name']
    # ...

# Einzelnes Ticket
issue = requests.get('https://goetschi.atlassian.net/rest/api/3/issue/GL-123',
    auth=auth, headers={'Accept': 'application/json'}, timeout=15)

# Projekte abfragen
projects = requests.get('https://goetschi.atlassian.net/rest/api/3/project',
    auth=auth, headers={'Accept': 'application/json'}, timeout=15)

# Ticket erstellen (siehe REST API v3 unten)
```

### REST API v3 direkt (für Issue-Types & ADF-Description)

⚠️ **Wichtig:** Jira Cloud REST API v3 erwartet `description` im **Atlassian Document Format (ADF)** als **Python-dict, nicht als JSON-String**. `requests.post(json=payload)` serialisiert selbst — doppeltes `json.dumps()` führt zu "Der Feldwert ist kein gültiger ADF-Inhalt".

```python
import requests, json

url = 'https://goetschi.atlassian.net/rest/api/3/issue'
auth = ('michelgoetschi@gmail.com', '<API_TOKEN>')

# description MUSS ein dict sein (KEIN json.dumps())
adf = {
    'type': 'doc',
    'version': 1,
    'content': [
        {'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Beschreibungstext'}]},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [{'type': 'text', 'text': 'Überschrift'}]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Punkt 1'}]}]}
        ]},
        {'type': 'orderedList', 'content': [
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Schritt 1'}]}]}
        ]}
    ]
}

payload = {
    'fields': {
        'project': {'key': 'GL'},
        'summary': 'Ticket-Titel',
        'issuetype': {'id': '10045'},  # 'Problem' in GL-Projekt
        'description': adf,            # <- dict, NICHT json.dumps(adf)!
        'priority': {'name': 'High'},
        'labels': ['label1', 'label2']
    }
}

r = requests.post(url, json=payload, auth=auth,
                  headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                  timeout=30)
print(f'Status: {r.status_code}, Key: {r.json().get("key","")}')
```

**GL-Projekt Issue-Types** (Team Managed, KEIN "Task"):
| ID | Name |
|----|------|
| 10045 | Problem |
| 10046 | Suggestion |
| 10047 | Question |

**labels** müssen als Array von Strings (kein Dictionary). **priority** als `{'name': '...'}`.

### Issue-Types eines Projekts abfragen
```python
r = requests.get('https://goetschi.atlassian.net/rest/api/3/project/GL', auth=auth, headers={'Accept': 'application/json'}, timeout=15)
p = r.json()
print('Project:', p.get('id'))
for it in p.get('issueTypes', []):
    print(f'  {it.get("id")}: {it.get("name")}')
```

### Verfügbare Issue-Types systemweit
```python
r = requests.get('https://goetschi.atlassian.net/rest/api/3/issuetype', auth=auth, headers={'Accept': 'application/json'}, timeout=15)
for it in r.json():
    print(f'{it.get("id")}: {it.get("name")}')
```

## Wichtige Credentials

Die API-Token liegen in `~/.hermes/memories/MEMORY.md` und Michel's User-Profil.

## Wichtiger Hinweis

⚠️ Die Confluence-Seite ist **NICHT 100% aktuell**. Die echte Infrastruktur weicht ab (z.B. Proxmox-Passwort, LXC-IPs, Docker-Setup). Die aktuelle Referenz liegt im **proxmox-Skill** unter `references/goetschi-infrastruktur.md`. Vor Ort prüfen via SSH, Proxmox API oder `skill_view(name='proxmox', file_path='references/goetschi-infrastruktur.md')`.

## Goetschi Labs – Notion Datenbanken

Die folgenden Datenbank-IDs sind für Goetschi Labs konfiguriert (Notion API Key: aus Credentials / Qdrant):

| Datenbank | ID |
|-----------|----|
| Knowledge Base | `36581c83-f6d9-814e-a7c6-c557ac79ff0b` |
| Cron Jobs | `36581c83-f6d9-81ff-a34c-f31b77794956` |
| Kontakte | `36c81c83-f6d9-8025-b94f-ca6b3734f8b6` |
| Aufgaben/Tickets | `36581c83-f6d9-8178-9215-e0e1e6a27672` |
| Skills | `36581c83-f6d9-81a6-a694-c02a3e1541f4` |

**Credential-Hierarchie (wichtigste Regel):**
1. Qdrant (type:credential AND service:<name>)
2. Notion (Knowledge Base / Kontaktdatenbank)
3. Confluence (Skill-Seiten YAML-Frontmatter)
4. Obsidian (letzte Quelle)

**Notion = Source of Truth für Kalender** (Google Kalender ist obsolet).

## Goetschi Labs – Agent Setup & TTS

Für **Michel / Goetschi Labs** sind diese Agent-Config-Einstellungen spezifisch:

```bash
# TTS Stimme (Michel will Florian, männlich, deutsch)
hermes config set tts.edge.voice "de-DE-FlorianMultilingualNeural"

# Credentials per Qdrant (type:credential) abfragen, nicht aus Config
# Qdrant: 10.0.60.179:6333, Key aus Credentials
```

⚠️ **Wichtig wenn Michel die Stimme korrigiert:** Die Standard-Config (`tts.edge.voice`) überschreibt alles. `text_to_speech()` hat **keinen voice Parameter** – es liest immer aus `config.yaml`. Fix: `hermes config set tts.edge.voice "de-DE-FlorianMultilingualNeural"`. Vollständige Troubleshooting-Anleitung in `references/tts-voice-troubleshooting.md`.

**Kommunikationsstil mit Michel:**
- Hochdeutsch (nie Schweizerdeutsch)
- GroupChat: kurz & knapp (✅❌ + Link, kein Status)
- Audio bevorzugt
- Bei ausführlichen Themen: direkt privat schreiben

## Common Pitfalls

1. **Timeouts bei Confluence**: Erster Request nach Pause kann 10-30s dauern (Atlassian Cloud). Immer `timeout=30` setzen.
2. **API Token ≠ Passwort**: Das Token aus der Credentials-Seite ist ein Atlassian API Token und wird direkt als `password` verwendet.
3. **API Token läuft ab**: `X-Seraph-Loginreason: AUTHENTICATED_FAILED` bei Status 200 bedeutet **Token ungültig/abgelaufen**. User muss neuen Token unter https://id.atlassian.com/manage-profile/security/api-tokens generieren.
4. **Jira Library funktioniert nicht mehr**: `atlassian-python-api` nutzt `/rest/api/2/`. Atlassian hat v2 eingestellt. Immer REST v3 (`/rest/api/3/search/jql`) via `requests` nutzen. Confluence v2 funktioniert noch via Library.
5. **Einzelne Requests**: Confluence multiple Requests nacheinander können timeouten – lieber einzeln in separaten terminal()-Calls.
4. **Confluence ist veraltet**: Die Confluence-Dokumentation läuft der echten Infrastruktur hinterher. Immer kritisch hinterfragen und ggf. via SSH / Proxmox API verifizieren.
5. **Proxmox API hat zwei Nodes**: pve01 (10.0.60.10, läuft) und pve02 (nicht erreichbar von diesem Netz). Gestoppte Container auf pve02 blocken trotzdem VMIDs – auch die Liste von pve02 abfragen!
6. **Proxmox exec API für LXCs gibt 501** — `POST /api2/json/nodes/{node}/lxc/{vmid}/exec` ist nicht implementiert. Stattdessen `pct mount` + Host-Filesystem oder SSH auf pve01 + `pct exec` im Container.
7. **Proxmox Password**: Immer aus Qdrant abfragen (`type:credential AND service:proxmox*`). Ist `Riotstar_PROXMOX_13`. pve01 und pve02 haben **das gleiche** Passwort (nicht Louis_one_13).
8. **pct mount blockt bei zweitem Aufruf**: Immer vorher `pct unmount <VMID>` ausführen, sonst hängt es.
11. **protocolVersion `"2024-11-05"` — nicht `"1.0.0"`!** — MCPHub v1.29.0 (und neuer) erwartet das offizielle Datumsformat des MCP Spec. `"1.0.0"` führt zu "Server's protocol version is not supported". Dieses Problem hat 9 von 11 MCPs blockiert und wurde erst durch Trial-and-Error gefunden. Siehe `references/mcp-servers.md` für Details.
12. **Google OAuth-Flow auf privaten IPs blockiert:** Google erlaubt `redirect_uri=http://localhost` aber nicht `http://10.x.x.x:PORT`. Siehe `references/google-mcp-oauth.md` für den kompletten Deployment-Guide inkl. Gmail MCP auf MCPHub.
13. **`pip install google-api-python-client` im MCPHub Container:** Der Gmail MCP braucht 24 Google-Pakete. Ohne sie startet der Server mit `ModuleNotFoundError: No module named 'google'`. Installieren mit: `docker exec mcphub pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`
11. **`!` im Confluence Token bricht Shell heredoc** — Wenn der API-Token ein `!` enthält, wird es in `"""..."""` Strings oder `<<'EOF'` heredocs vom Parser/Shell verschluckt (`SyntaxError: invalid syntax`). Workaround: Token als `sys.argv[1]` via Kommandozeile übergeben, oder aus einer Datei lesen, niemals im Source-Code interpolieren.
12. **protocolVersion `"2024-11-05"` — nicht `"1.0.0"`!** — MCPHub v1.29.0 (und neuer) erwartet das offizielle Datumsformat des MCP Spec. `"1.0.0"` führt zu "Server's protocol version is not supported". Dieses Problem hat 9 von 11 MCPs blockiert und wurde erst durch Trial-and-Error gefunden. Siehe `references/mcp-servers.md` für Details.
13. **Google OAuth-Flow auf privaten IPs blockiert:** Google erlaubt `redirect_uri=http://localhost` aber nicht `http://10.x.x.x:PORT`. Siehe `references/google-mcp-oauth.md` für den kompletten Deployment-Guide inkl. Gmail MCP auf MCPHub.
14. **`pip install google-api-python-client` im MCPHub Container:** Der Gmail MCP braucht 24 Google-Pakete. Ohne sie startet der Server mit `ModuleNotFoundError: No module named 'google'`. Installieren mit: `docker exec mcphub pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`

## Proxmox API — LXC Operationen (Goetschi Labs)

Bei Goetschi Labs laufen alle LXCs auf pve01 (10.0.60.10). Die Proxmox API ist über HTTPS Port 8006 erreichbar.

### Authentifizierung
```python
import requests
session = requests.Session()
session.verify = False
r = session.post("https://10.0.60.10:8006/api2/json/access/ticket",
                 data={"username": "root@pam", "password": "<PASS>"}, timeout=15)
data = r.json().get('data', {})
session.headers.update({"CSRFPreventionToken": data.get('CSRFPreventionToken', '')})
session.cookies.set("PVEAuthCookie", data.get('ticket', ''))
```
Passwort aus Qdrant: `type:credential AND service:proxmox*`

### SSH in Container (wenn LXC SSH blockt)
PVE exec API funktioniert **nicht** für LXCs (gibt 501). Workaround:
```bash
# 1. SSH auf pve01 (sshpass)
sshpass -p "Riotstar_PROXMOX_13" ssh -o StrictHostKeyChecking=no root@10.0.60.10
# 2. Auf pve01: SSH im LXC konfigurieren
pct exec 118 -- bash -c '
  echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
  echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
  systemctl restart sshd'
# 3. Von NOVA aus per sshpass in den Container
sshpass -p "Louis_one_13" ssh root@10.0.60.139 "hostname"
```

### Neuen LXC erstellen (Proxmox API + SSH-Workflow)

```python
# Nächste freie VMID ermitteln
r = session.get("https://10.0.60.10:8006/api2/json/access/ticket",
                data={"username": "root@pam", "password": "<PASS>"}, timeout=15)
# Check pve01 UND pve02! Auch gestoppte Container auf pve02 blocken IDs.
r = session.get("https://10.0.60.10:8006/api2/json/nodes/pve01/lxc", timeout=15)
lxcs = r.json().get('data', [])
all_vmids = sorted([l.get('vmid') for l in lxcs])
# ID 101..118, lücken suchen

# LXC erstellen (mit pw + autostart + nesting)
create_data = {
    "vmid": free_vmid,
    "hostname": "<name>",
    "ostemplate": "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst",
    "storage": "local-lvm",
    "rootfs": 32,
    "memory": 2048,
    "swap": 512,
    "cores": 2,
    "net0": "name=eth0,bridge=vmbr0,ip=dhcp",
    "password": "Louis_one_13",
    "unprivileged": 1,
    "features": "nesting=1",
    "start": 1,
    "onboot": 1
}
r2 = session.post("https://10.0.60.10:8006/api2/json/nodes/pve01/lxc",
                  data=create_data, timeout=120)

# Task-ID aus UPID extrahieren und warten
task_upid = r2.json().get('data', '')
for i in range(30):
    time.sleep(3)
    r = session.get(f"https://10.0.60.10:8006/api2/json/nodes/pve01/tasks/{task_upid}/status", timeout=15)
    data = r.json().get('data', {})
    if data.get('status') == 'stopped':
        break
```

### SSH in frischen LXC aktivieren (Ubuntu default: kein Root-PW-Login)

```bash
# 1. SSH auf pve01 (das Passwort kommt aus Qdrant: type:credential AND service:proxmox*)
sshpass -p "Riotstar_PROXMOX_13" ssh -o StrictHostKeyChecking=no root@10.0.60.10

# 2. SSH im neuen LXC konfigurieren
pct exec <VMID> -- bash -c '
  echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
  echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
  systemctl restart sshd
  echo "SSH fertig"

# 3. Von NOVA aus in den Container
sshpass -p "Louis_one_13" ssh -o StrictHostKeyChecking=no root@<LXC_IP> "hostname"
```

Die IP des neuen LXCs findet man im UniFi (aktive Clients), nicht in der Proxmox API (keq Guest Agent, 501).

### LXC löschen
```python
# Stop + Delete
session.delete(f"https://10.0.60.10:8006/api2/json/nodes/pve01/lxc/<VMID>", timeout=30)
```

### pct mount — Host-Filesystem auf LXC rootfs zugreifen

⚠️ **Wichtigste Regel: pct mount blockt bei zweitem Aufruf!**

Immer `pct unmount <VMID>` vor erneutem `pct mount` ausführen. Der mount bleibt auch nach `pct stop` aktiv.

Die Proxmox exec API (POST /nodes/{node}/lxc/{vmid}/exec) gibt 501 für LXCs — funktioniert nicht. Stattdessen:  

```bash
# Auf pve01: LXC rootfs mounten  
pct mount <VMID>   # Mountet nach /var/lib/lxc/<VMID>/rootfs

# Dateien direkt auf dem Host manipulieren
ls /var/lib/lxc/110/rootfs/opt/
cp /var/lib/lxc/110/rootfs/root/package.json /var/lib/lxc/118/rootfs/root/

# Fertig? unmounten
pct unmount <VMID>
```

**Achtung:** Docker auf dem LXC muss nicht laufen für den Zugriff auf Docker-Stacks unter `/opt/` oder Docker-Volumes unter `/var/lib/docker/volumes/`. Bei unprivilegierten LXCs haben Dateien mapped UIDs (100000+) — das stört `cp` nicht, aber Inhalte bleiben korrekt.

**Hängende LVM-Disk nach Löschung:**
```bash
pct destroy 110 --purge
# Fehler: "lvremove: Logical volume contains a filesystem in use"
# Der LXC ist WEG (Config gelöscht), nur der LVM-Layer hängt.
rm -f /etc/pve/lxc/<VMID>.conf
# Disk kann nicht gelöscht werden bis pve01 Reboot. Workaround:
umount -l /var/lib/lxc/<VMID>/rootfs 2>/dev/null
dmsetup remove Disk-vm--<VMID>--disk--0 2>/dev/null
lvremove -f Disk/vm-<VMID>-disk-0 2>/dev/null  # Meist blockt es trotzdem
```
Wenn `dmsetup info zeigt "Open count: 1"` und alles andere fehlschlägt: Die Disk wird erst beim nächsten pve01 Neustart freigegeben. Der LXC ist trotzdem gelöscht.

### Coolify Installation & Docker-Compose Deployment

```bash
# Auf frischem Ubuntu LXC (24.04):
curl -fsSL https://cdn.coollabs.io/coolify/install.sh -o /tmp/install.sh
bash /tmp/install.sh
# Fertig in ~2 Minuten

# Docker Compose im LXC deployen (nicht via Coolify API, direkt via SSH)
sshpass -p "Louis_one_13" ssh root@10.0.60.139 "
  cd /opt/<stack> && docker compose pull && docker compose up -d
"
```

### Task-Status verfolgen (Proxmox API)
Wenn ein neuer LXC via API erstellt wird, erhält man eine UPID. Der Status kann so abgefragt werden:
```python
import time
task_upid = r2.json().get('data', '')
for i in range(30):
    time.sleep(3)
    r = session.get(f"https://10.0.60.10:8006/api2/json/nodes/pve01/tasks/{task_upid}/status", timeout=15)
    data = r.json().get('data', {})
    if data.get('status') == 'stopped':
        break
```

### UniFi VLAN-Fehldiagnose — Geräte sehen sich nicht

**Häufigste Ursache: Geräte in UNTERSCHIEDLICHEN VLANs, aber der User denkt sie sind gleich.**

⚠️ **Trap:** Der User sagt "beide sind im IoT-Netz" aber der Philips TV (10.0.10.x) hängt im Client VLAN während die Hue Bridge (10.0.20.x) im IoT VLAN ist — die 10.x Prefixe verraten sofort das VLAN.

**Vorgehen:**
1. Alle aktiven Clients scannen: `GET /proxy/network/api/s/default/stat/sta`
2. **Nicht nur** nach Client Isolation oder Firewall-Regeln suchen — die VLAN-Zugehörigkeit checken!
3. VLAN steht im UniFi als `vlan` Feld (Integer)
4. Philips Geräte MAC Prefix: `00:17:88` (Hue Bridge), `40:aa:56` (Philips TV)

**Network Override (Client in anderes VLAN verschieben):**
```python
# 1. Alle Netzwerke auflisten, IoT-Netz-ID finden
r = session.get("https://10.0.10.1/proxy/network/api/s/default/rest/networkconf", timeout=15)
networks = {n.get('name',''): n.get('_id','') for n in r.json().get('data', [])}
iot_net_id = networks.get('VLAN20_IOT', '')

# 2. Client in UniFi finden (auch wenn offline, in /rest/user)
r = session.get("https://10.0.10.1/proxy/network/api/s/default/rest/user", timeout=15)
devices = r.json().get('data', [])
tv = [d for d in devices if 'philips' in d.get('name','').lower() or '40:aa:56' in d.get('mac','')]

# 3. Network Override setzen
session.put(f"https://10.0.10.1/proxy/network/api/s/default/rest/user/{tv[0]['_id']}",
            json={"network_id": iot_net_id, "name": "philips tv"}, timeout=15)
```

**Zwei UniFi-Passwörter (Wichtig):**
- `Riotstar_UNIFI_13` — älteres Passwort, Account kann locked sein
- `Riotstar_MICHEL_13` — aktuell funktionierendes Passwort

Bei 403 "locked": einfach das andere Passwort probieren. Account entsperrt sich nach ~5-10 Min von selbst.

**UniFi API Auth:**
```python
session = requests.Session()
session.verify = False
r = session.post("https://10.0.10.1/api/auth/login",
                 json={"username": "hassio", "password": "Riotstar_MICHEL_13"}, timeout=15)
# CSRF aus JWT extrahieren
import base64, json
cookie = session.cookies.get("TOKEN", "")
parts = cookie.split(".")
payload = json.loads(base64.b64decode(parts[1] + "=="))
session.headers.update({"X-CSRF-Token": payload.get("csrfToken", "")})
```

## MCPHub — Status (Update 07.06.2026)

MCPHub (10.0.60.170:3000) auf CT107 wurde am 07.06.2026 **komplett neu deployt** (Container-Neustart, Config reset). Aktuell:

| Aspekt | Status |
|--------|--------|
| **Server läuft** | ✅ `samanhappy/mcphub:latest` — healthy |
| **Notion MCP** | ✅ 22 Tools, connected |
| **Eigene stdio MCPs** | ✅ 10 Python-Server deployed (siehe `references/mcp-servers.md`) |
| **Connected (07.06)** | ✅ 4 Server, 41 Tools (Qdrant, PostgreSQL, MinIO, Notion) |
| **Auth (API-Key)** | ❌ Bearer/Login broken — 401 / Internal Server Error |

### Stdio-Strategie statt npm/OpenAPI/SSE

Alle öffentlichen MCP-Pakete (npm) existieren **nicht**:
- `@kovi/mcp-confluence`, `@kovi/mcp-jira`, `qdrant-mcp`, `atlassian-mcp` → alle 404
- OpenAPI-MCPs scheitern an `$ref`-Auflösung (Qdrant, Home Assistant, Asterisk)
- `samanhappy/mcphub` hat Python 3.13 im Container

**Lösung:** 10 hand-crafted Python stdio-MCP-Server (reines stdlib). Siehe `references/mcp-servers.md` für:
- Protokoll-Format (Content-Length Header + JSON-RPC 2.0)
- Initialize Response MUSS `protocolVersion: "1.0.0"` sein (nicht 0.1.0!)
- Credential-Map für alle 10 Server
- Deployment via `cat | docker exec -i mcphub bash -c "cat > /path"`

**Workaround für Agenten (wenn MCPHub nicht auth-fixbar):**
- **Notion:** via MCPHub — aber Auth broken, nur lokaler Zugriff auf CT107
- **Jira/Confluence:** Direkt via atlassian-python-api (siehe Setup oben)
- **Alle anderen:** Direkt via curl/Python auf die REST-APIs

## LXC File Transfer (ohne SSH in den LXC)

Wenn SSH in einen frischen LXC blockt (Ubuntu default: `PermitRootLogin prohibit-password`):

### Methode 1: pct mount + Host-Filesystem
```bash
# Auf pve01 (oder Host):
pct mount <VMID>  # mountet rootfs nach /var/lib/lxc/<VMID>/rootfs
# Dann direkt darauf zugreifen:
ls /var/lib/lxc/110/rootfs/opt/
cp -r /var/lib/lxc/110/rootfs/opt/* /var/lib/lxc/118/rootfs/opt/
pct unmount <VMID>
```

**Achtung:** Bei unprivilegierten LXCs haben die Dateien mapped UIDs (100000+). `cp` funktioniert aber trotzdem sauber auf dem Host.

### Methode 2: SSH über pve01 aktivieren
```bash
# Auf pve01:
sshpass -p "<PVE_ROOT_PW>" ssh root@10.0.60.10
# Dann im frischen LXC SSH konfigurieren:
pct exec <VMID> -- bash -c '
  echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
  echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
  systemctl restart sshd'
```

Danach kann von NOVA aus per `sshpass -p "<LXC_PW>" ssh root@<LXC_IP>` zugegriffen werden.

### Methode 3: Bind-Mount (pct set -mp0)

Wenn ein LXC keine NFS/CIFS mounten kann (Permission denied wegen fehlender CAP_SYS_ADMIN), ist ein Host-Bind-Mount die Lösung:

```bash
pct set <VMID> -mp0 /pfad/auf/host,mp=/pfad/im/container

# Beispiel: Paperless consume
pct set 103 -mp0 /var/tmp/paperless-consume,mp=/opt/paperless/consume
```

**Wichtig:** Der Bind-Mount überschreibt das Zielverzeichnis komplett. Vor Backup:
```bash
rsync -a /opt/paperless/consume/ /tmp/backup/
```

**Permissions:** chown funktioniert nicht auf Bind-Mount (Operation not permitted). Provider nobody:nogroup + 777 auf Host setzen.

### Methode 4: Samba + rsync via pve01 (für Qemu VMs)

Wenn ein Dienst auf einer Qemu VM läuft (z.B. CT201 CasaOS) und ein LXC darauf zugreifen soll, aber Firewall/VLAN blockt:

**Workflow:** Qemu VM (Samba) -> pve01 (rsync Cron) -> LXC (Bind Mount)

```bash
# 1. SSH-Key auf pve01 zur VM deployen
cat ~/.ssh/id_ed25519.pub | sshpass -p "VM_PW" ssh user@vm-ip \
  "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# 2. rsync Cron (alle 2 Min)
rsync -avz --rsh="ssh -o StrictHostKeyChecking=no" \
  user@vm-ip:/share/path/ /var/tmp/consume/

# 3. Bind-Mount in LXC
pct set <VMID> -mp0 /var/tmp/consume,mp=/opt/paperless/consume
```

## Verification Checklist
- [ ] `pip3 install atlassian-python-api requests` installiert
- [ ] Confluence-Verbindung: `confluence.get_all_spaces()` gibt Spaces zurück
- [ ] Jira-Verbindung: `POST /rest/api/3/search/jql` gibt Tickets zurück (NICHT `jira.jql` — v2 ist deprecated!)
## Referenced Files

| File | Content |
|------|---------|
| `references/goetschi-infrastruktur.md` | Vollständige LXC/VM-Tabelle + Monitoring + Credentials |
| `references/grafana-recovery.md` | Grafana Password Recovery + Service Account + Datasource Provisioning |
| `references/tts-voice-troubleshooting.md` | TTS-Voice-Config für Michel |
| `references/mcp-servers.md` | MCPHub stdio-Protokoll + Credential-Map |
| `references/coolify-deployment.md` | Coolify-Installation + Docker-Compose-Deployment |
| `references/mcphub-setup-and-debugging.md` | MCPHub Initial-Setup + Fehlerdiagnose |
| `references/mcphub-agent-access.md` | MCPHub Agenten-Zugriff (Bearer-Auth, Credentials) |
| `references/mcphub-unifi-debugging.md` | UniFi VLAN-Fehldiagnose |
| `references/google-mcp-oauth.md` | Google OAuth-Flow für MCPHub |
| `references/agent-onboarding.md` | Agent-Onboarding Confluence-Seite |

- [ ] Credentials korrekt aus Memory abgerufen

---
name: browserless-chromium
description: Browserless (headless Chromium) Docker-Container auf dem Dokploy-Host — Port 3005, Token, API-Endpoints, Nutzung im Hermes-Container.
triggers:
  - "browser_navigate"  # Jedes Mal wenn ich Browser brauche, MUSS dieser Skill geladen sein
  - "browser_click"
  - "browser_type"
  - "browser_snapshot"
  - "browser_vision"
  - "browser_console"
  - "browser_back"
  - "browser_scroll"
  - "browser_get_images"
  - "browserless"
  - "chromium"
  - "headless browser"
  - "web scraping"
  - "page laden"
  - "website aufrufen"
mandatory: true  # Immer laden wenn ein Browser-Tool oder verwandter Task
related_skills:
  - dokploy-port-management  # Falls Port-Änderung nötig
---

# Browserless / Chromium

Browserless ist ein headless Chromium-Container, der via REST API ferngesteuert werden kann. Läuft auf dem **Dokploy-Host** (`10.0.60.121`) und wird von Hermes für Web-Aufgaben genutzt.

## 🚨 BEI JEDER VERWENDUNG: Quick-Check (30 Sekunden)

Bevor ich ein Browser-Tool nutze, **MUSS** ich kurz prüfen ob Browserless läuft:

```bash
curl -s -o /dev/null -w "%{http_code}" http://10.0.60.121:3005/ 2>&1
```

- **301** oder **404** → OK, Browserless läuft ✅
- **000** oder Connection Refused → **Container ist down** → Troubleshooting-Sektion unten!
- **keine Ausgabe nach 3s** → Timeout → Troubleshooting!

> ⚠️ **MERKE:** Port ist **3005** (NICHT 3000)! 3000 ist nur intern via Traefik.
> ⚠️ **Token:** `rqwhefqph8fms7vv` muss immer als Header mitgesendet werden.

---

## Infrastruktur

| Metadaten | Wert |
|-----------|------|
| **Host** | `10.0.60.121` |
| **Port** | `3005` (direkt via Host, NICHT 3000 mehr) |
| **Token** | `rqwhefqph8fms7vv` |
| **Container-Name** | `goetschi-labs-browserless-lelgmv-browserless-1` |
| **Image** | `ghcr.io/browserless/chromium:latest` |
| **Dokploy-Projekt** | `goetschi-labs-browserless-lelgmv` |
| **Compose-Pfad** | `/etc/dokploy/compose/goetschi-labs-browserless-lelgmv/code/docker-compose.yml` |
| **Traefik-Domain** | `goetschi-labs-browserless-9f6f5b-10-0-60-121.traefik.me` |

## Zugriff

### Direkt (empfohlen für Hermes)
```
http://10.0.60.121:3005
Token: rqwhefqph8fms7vv
```

### Über Traefik (via Domain, falls konfiguriert)
```
http://goetschi-labs-browserless-9f6f5b-10-0-60-121.traefik.me
```

## API-Endpoints

Browserless stellt eine REST API + WebSocket-Endpoints bereit:

| Endpoint | Beschreibung |
|----------|-------------|
| `/` | Root (404 — kein Inhalt) |
| `/docs` | Swagger-Dokumentation (301 Redirect) |
| `/function` | Serverless Functions (301) |
| `/json` | JSON API |
| `/version` | Versionsinfo |
| `/healthz` | Healthcheck (antworted 200 bei Gesundheit) |
| `/content` | Webscraping (statisches HTML) — ⚠️ **Limitiert:** `/content` mit Token-Header funktioniert in manchen Versionen nicht. In dem Fall: **curl + python3** direkt nutzen (siehe Fallback-Abschnitt) |

Alle Requests benötigen den Header: `Token: rqwhefqph8fms7vv`

## 🔧 KRITISCH: Hermes Browser-Tools mit Browserless verbinden

Die Hermes `browser_*`-Tools (`browser_navigate`, `browser_snapshot`, etc.) nutzen Browserless **NICHT automatisch**. Sie brauchen entweder:
- **Lokales Chrome/Chromium** (installiert via `agent-browser install`), ODER
- **CDP URL** in der Hermes Config (`/opt/data/config.yaml`), die auf Browserless zeigt

### CDP URL konfigurieren (empfohlen!)

Damit `browser_*`-Tools den Browserless-Container nutzen:

```yaml
# In /opt/data/config.yaml unter `browser:`
browser:
  cdp_url: "ws://10.0.60.121:3005?token=rqwhefqph8fms7vv"
  engine: cdp
```

Nach Änderung: Hermes neustarten (oder Gateway-Config reload).

### Fallback A: Playwright auf Hermes-Host (bei totem Browserless)

Wenn Browserless-Container down isch und nöd schnell wieder hochchunt (Image-Pull 1.2GB timet oft us), **Playwright direkt uf Hermes** installiere:

```bash
# 1. Playwright installiere (113MB, viel chlinner als Browserless 1.2GB)
pip3 install playwright --break-system-packages

# 2. Chromium Headless Shell installiere
playwright install chromium

# 3. Falls libnspr4 fehlt:
apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2

# 4. Nutze (Python):
# from playwright.sync_api import sync_playwright
# with sync_playwright() as p:
#     browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
#     page = browser.new_page()
#     page.goto(url, wait_until='networkidle', timeout=30000)
#     # ... page.inner_text(), page.screenshot(), etc.
#     browser.close()
```

✅ Vorteil: Läuft lokal, kein externer Container nötig, kleine Download-Grösse.
❌ **Einschränkung (23.05.2026):** Headless-Chromium (headless_shell) wird vo JavaScript-Schwergewichts-SPAs (Atlassian id.atlassian.com, React-Portale, CAPTCHA-geschützte Sites) oft **nöd korrekt z'reddere** — interaktivi Elemente sind leer, Body bleibt null. Für einfachi Webseite (Doku, statischi HTML) funktioniert's perfekt.

### Fallback B: Web-Recherche ohne Browser-Tools

Wenn Browser-Tools (Browserless + Playwright beide nöd verfüegbar) fehlschlagen, kann Web-Recherche **direkt via curl + python3** erfolgen:

```python
import urllib.request, re, html

url = 'https://example.com'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')

# HTML säubern
text = re.sub(r'<script[^>]*>.*?</script>', '', data, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', text)
text = html.unescape(text)
lines = [l.strip() for l in text.split('\n') if l.strip()]
```

✅ Vorteil: Kein Browserless nötig, kein Token, kein Container-Check.
❌ Kein JavaScript (statisches HTML reicht für 90% der Fälle: Doku, Preise, API-Referenzen).

## Browserless REST API (Direktzugriff)

Browserless stellt eine REST API + WebSocket-Endpoints bereit. **Wichtig:** Nicht alle Browserless-Versionen haben alle Endpoints aktiviert!

## Wartung

### Container neustarten
```python
import paramiko
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', '<PASSWORT>', timeout=10)
s.exec_command('docker restart goetschi-labs-browserless-lelgmv-browserless-1')
s.close()
```

### Port ändern
Siehe Skill `dokploy-port-management`.

### Logs ansehen
```bash
# Auf dem Host via SSH
docker logs goetschi-labs-browserless-lelgmv-browserless-1 -n 50
```

## Troubleshooting — KOMPLETT (keine Knowledge-Lücke)

### Flow: Browserless antwortet nicht

```
1. curl http://10.0.60.121:3005/  → 000? → Weiter zu 2
                                     301/404? → Weiter zu 3

2. SSH zum Host via paramiko:
   s.exec_command("docker ps --filter 'name=browserless'")

   2a. Container NICHT in Liste → Neustarten:
       s.exec_command("cd /etc/dokploy/compose/goetschi-labs-browserless-lelgmv/code && docker compose up -d --remove-orphans")
   
   2b. Container IST in Liste, aber Status "restarting" oder "unhealthy":
       s.exec_command("docker logs goetschi-labs-browserless-lelgmv-browserless-1 -n 50")
       → Logs lesen, Fehler googlen/skill aktualisieren

   2c. Container läuft (Up XX minutes, healthy):
       s.exec_command("ss -tlnp | grep 3005")
       → Port nicht da? Docker-Compose-Check (siehe unten)

3. curl antwortet mit 301/404 → Port OK, aber Browser-Tool hängt:
   s.exec_command("docker restart goetschi-labs-browserless-lelgmv-browserless-1")
   sleep 10
   curl nochmal prüfen
```

### Docker-Compose prüfen (bei Port-Problemen)

```python
import paramiko
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', '<PASSWORT>', timeout=10)

# Compose-Datei prüfen
i,o,_ = s.exec_command("cat /etc/dokploy/compose/goetschi-labs-browserless-lelgmv/code/docker-compose.yml")
print(o.read().decode())

# Container-Ports prüfen
i,o,_ = s.exec_command("docker ps --filter 'name=browserless' --format '{{.Names}} | {{.Status}} | {{.Ports}}'")
print(o.read().decode())
s.close()
```

### Kompletter Reset (wenn alles andere fehlschlägt)

```python
import paramiko, time
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', '<PASSWORT>', timeout=10)

# 1. Stack komplett entfernen
s.exec_command("docker stack rm goetschi-labs-browserless-lelgmv")
time.sleep(5)

# 2. Stack neu deployen
i,o,_ = s.exec_command("cd /etc/dokploy/compose/goetschi-labs-browserless-lelgmv/code && docker compose up -d --remove-orphans", timeout=60)
print(o.read().decode())

# 3. Warten + prüfen
time.sleep(10)
i,o,_ = s.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/")
print("Status:", o.read().decode())

s.close()
```

### SSH-Zugang schlägt fehl

| Symptom | Lösung |
|---------|--------|
| `Permission denied (publickey,password)` | Passwort falsch → in Memory nachschlagen (`Louis_one_13`) |
| `Connection refused` | SSH-Daemon auf Host tot → via Proxmox WebUI neustarten |
| Timeout | Host nicht erreichbar → Netzwerk prüfen (Homelab-intern)

| Problem | Lösung |
|---------|--------|
| **Container antwortet nicht** | `docker restart <container>` — meist reicht das |
| **Port nicht erreichbar** | Prüfen mit `ss -tlnp | grep 3005` auf dem Host |
| **Healthcheck schlägt fehl** | Container braucht ~5-10s nach Start für Health |
| **"Token invalid"** | Header `Token: rqwhefqph8fms7vv` setzen |
| **Browser-Tool hängt** | Browserless-WebSocket disconnected — Container neustarten |

## Änderungshistorie

- **14.05.2026:** Port von 3000 (nur intern) auf 3005 (Host-Port) geändert. Docker-Compose editiert und Stack neu deployed.
- **14.05.2026:** Skill erstellt mit vollständiger Troubleshooting-Dokumentation, Quick-Check und Diagnose-Flow.

## Cronjob-Vorschlag: Browserless-Watchdog

Damit Browserless nie unbemerkt ausfällt, kann man folgenden Cronjob einrichten:

**Prompt:** "Prüfe ob Browserless auf 10.0.60.121:3005 antwortet. Wenn nicht (000 oder Connection Refused), starte den Container via SSH neu und melde mir das Ergebnis. Wenn alles OK ist, melde nichts (nur bei Problemen)."

**Skills:** `browserless-chromium`, `dokploy-port-management`
**Intervall:** `every 30m`
**Delivery:** zurück zu Michel

---
name: guten-morgen-call
description: Hermes' Guten-Morgen-Weckruf — sammelt Daten aus Kalender, Mail, Trading, Wetter und System, generiert ein Nerd-Briefing als TTS und ruft Michel per Asterisk an.
category: telephony
version: 1.3.0
triggers:
  - guten morgen
  - weckruf
  - morning call
  - briefings
  - nerd-briefing
  - guten-morgen-call
  - wake up call
related_skills:
  - apollo-call
  - google-workspace
  - mt5-trading-bot
  - unifi-network
---

# Guten Morgen Call — Nerd-Briefing Weckruf ☀️🤓

## Übersicht

Hermes weckt Michel (+41796459743) mit einem dynamischen Audio-Briefing.
Sammelt Daten aus 5+ Quellen parallel und generiert einen persönlichen,
nerdigen Morgen-Report — als TTS per edge-tts (Hermes: de-DE-KillianNeural, Hochdeutsch).

## Voice Convention

❗ **KRITISCH: Immer HOCHDEUTSCH (Schriftdeutsch) für Calls/TTS, NIE Schweizerdeutsch!**
Schweizerdeutsch klingt bei TTS unnatürlich und wird vom STT-Modell nicht gut erkannt.

| Agent | Voice | Sprache |
|-------|-------|---------|
| **Apollo** | `de-DE-FlorianMultilingualNeural` | Hochdeutsch |
| **Hermes** | `de-DE-KillianNeural` | Hochdeutsch |
| **Nova** | `de-DE-SeraphinaMultilingualNeural` | Hochdeutsch |

**Regel:** Jeder Agent eigene Stimme. Niemals doppelt vergeben.

## Voraussetzungen

Auf dem Hermes-Container **muss installiert sein**:

```bash
pip install paramiko       # SSH/SFTP zu Asterisk (statt sshpass)
```

`paramiko` ist üblicherweise schon über das Hermes-venv vorhanden.

Prüfen:

```bash
python3 -c "import paramiko; print(paramiko.__version__)"
which ffmpeg
edge-tts --list-voices 2>/dev/null | grep -iE "killian|florian"
```

Das Script nutzt Pythons `requests`-Modul (kein `curl` per subprocess), weil
`&` im POST-Data in subprocess(shell=True) unzuverlässig escaped wird.

## Workflow

```
┌─────────────────┐
│ Daten sammeln    │ ← Kalender, Gmail, MT5, Wetter, System (sequentiell)
├─────────────────┤
│ Briefing text    │ ← Generiert personalisierten Nerd-Text
├─────────────────┤
│ TTS (edge-tts)   │ ← KillianNeural, Hochdeutsch
├─────────────────┤
│ Audio konvert.  │ ← 2s Pause, 8kHz alaw/ulaw/wav
├─────────────────┤
│ Upload ↙ Asterisk│ ← SFTP (paramiko) nach beiden Sounds-Verzeichnissen
├─────────────────┤
│ Anruf via SSH   │ ← paramiko exec_command: asterisk -rx originate
├─────────────────┤
│ Telegram Report  │ ← Summary an Goetschi Labs Gruppe senden
└─────────────────┘
```

### Telegram-Benachrichtigung nach dem Call

Nach erfolgreichem Call eine kurze Zusammenfassung an die Goetschi Labs Telegram-Gruppe senden.

**Ansatz A — Telethon (Michels User-Account, empfohlen, funktioniert zuverlässig)**

```python
import json, asyncio
from pathlib import Path
from telethon import TelegramClient

CONFIG = json.loads(Path("/opt/data/home/.hermes/telegram_config.json").read_text())
SESSION = "/opt/data/home/.hermes/michel_telethon.session"

async def main():
    client = TelegramClient(SESSION, int(CONFIG["api_id"]), CONFIG["api_hash"])
    await client.start()
    channel_id = -1002300386092  # Goetschi Labs Group
    msg = "HERMES: \\u2600\\ufe0f Weckruf abgeschlossen\\n\\n..."
    await client.send_message(channel_id, msg)
    await client.disconnect()

asyncio.run(main())
```

Vorteil: Kein Bot-Token nötig, funktioniert immer wenn Telethon-Session valide ist.

**Ansatz B — Bot Token (falls TELEGRAM_BOT_TOKEN in `.env` gesetzt):**

```python
import requests, os
token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = "-1002300386092"
msg = "HERMES: \\u2600\\ufe0f Weckruf abgeschlossen\\n\\n..."
requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": msg}, timeout=10)
```

**Konvention:** Prefix mit `"HERMES: \\u2600\\ufe0f Weckruf abgeschlossen"`, dann Bullet-Liste
der wichtigsten Fakten.

### TTS-Längen-Management

Der Weckruf soll **30-45 Sekunden** dauern (~80-110 Wörter). Längere TTS
(60s+) wirkt zu ausführlich für einen Weckruf.

**Faustregel:** Maximal 3-4 Bullet-Points im Briefing. Bei vielen Datenquellen
die unwichtigsten weglassen (Energie, Test-Bots wenn offline, etc.)

**Erfahrungswert (21.05.2026):** Eine TTS mit ~180 Wörtern dauerte 1:02 Minuten —
das ist die OBERGRENZE. Für 30-45s Ziel auf 80-110 Wörter kürzen. Keine
Einleitungssätze, kein "ich habe auch noch...", nur die Fakten.

| Datenpunkt | Priorität | Immer? |
|------------|-----------|--------|
| Wetter | 🔴 Hoch | Ja |
| MT5 LIVE | 🔴 Hoch | Ja |
| System/Uptime | 🟡 Mittel | Ja, ein Satz |
| Kalender-Heute | 🟢 Niedrig | Nur wenn echte Termine (keine Cron-Events) |
| Mails | 🟢 Niedrig | Nur wenn wichtig (UniFi-Alarme = ja) |
| Energie/Tibber | ⚪ Optional | Nur wenn konfiguriert |
| MT5 Test-Bots | ⚪ Optional | Nur wenn erreichbar; sonst überspringen |

### 6. Energiedaten (optional)
- Tibber-API nur abrufen wenn konfiguriert (`~/.hermes/.env` → `TIBBER_TOKEN`)
- **Kein Tibber-Token:** Datenpunkt kommentarlos überspringen, nicht im Briefing erwähnen
- Prüfung: `grep TIBBER ~/.hermes/.env 2>/dev/null` oder `cat ~/.hermes/config.yaml | grep -i tibber`

### 7. MT5 Test-Bots (optional)
- Bot01 (10.0.60.101) und Bot02 (10.0.60.102) sind **seit 27.04.2026 persistent offline**
- Wenn sie nicht erreichbar sind: überspringen, nicht im Briefing erwähnen
- Nur erwähnen wenn sie plötzlich wieder ONLINE sind

### Script-Interna (paramiko statt sshpass)

Weil der Hermes-Container **kein root** hat (`sshpass` nicht installierbar), nutzt das Script
**paramiko** (Python SSH-Bibliothek) für:

- **SFTP-Upload** der Sound-Dateien zu Asterisk (`/var/lib/asterisk/sounds/` + `/usr/share/asterisk/sounds/`)
- **SSH exec_command** für `chown asterisk:asterisk` und `asterisk -rx originate ...`

Bei einem Deployment auf einem Container mit `sshpass` könnte man zurückwechseln,
aber paramiko ist zuverlässiger (kein Shell-Escape, keine externen Abhängigkeiten).

## Script

Das Hauptscript liegt unter:

```
scripts/guten-morgen-call.py
```

> ⚠️ **Bekannte Bug-Historie (19.05.2026):** Siehe `references/bugfix-2026-05-19.md` — Drei kritische Bugs (Voice, Phone-Format, Extension) wurden behoben. Vor Änderungen am Script zwingend lesen, um Regressionen zu vermeiden.

### Aufruf

```bash
# Dry-Run (nur Daten sammeln + Briefing ausgeben, kein Call)
python3 /opt/data/skills/telephony/guten-morgen-call/scripts/guten-morgen-call.py --dry-run

# Vollständiger Durchlauf (sammelt, generiert TTS, ruft an)
python3 /opt/data/skills/telephony/guten-morgen-call/scripts/guten-morgen-call.py
```

### One-Shot Schedule (via Webhook/kein Cron)

Für den Weckruf um 08:30 wird das Script als One-Shot um 08:25 gestartet:

```bash
python3 /opt/data/skills/telephony/guten-morgen-call/scripts/guten-morgen-call.py
```

Das Script selbst braucht ca. 30-45s von Start bis Anruf.

## Datenquellen im Detail

### 1. Google Calendar
- **Empfohlen: Direkt via Python googleapiclient** (funktioniert auch ohne `gws` CLI)
  ```python
  from google.auth.transport.requests import Request
  from google.oauth2.credentials import Credentials
  from googleapiclient.discovery import build

  creds = Credentials.from_authorized_user_file("/root/.hermes/google_token.json")
  if not creds.valid and creds.expired:
      creds.refresh(Request())
  service = build("calendar", "v3", credentials=creds)
  events = service.events().list(calendarId="primary",
      timeMin=today_start, timeMax=today_end,
      singleEvents=True, orderBy="startTime").execute()
  ```
- ⚠️ **Ganztägige Events:** Das `start`-Feld ist **direkt ein String** (`"2026-05-15"`),
  nicht `{dateTime: ...}` wie Google oft dokumentiert. Beide Fälle parsen.
- Alternative: `google-workspace/scripts/google_api.py`
### 2. Gmail / E-Mails

**Empfohlen: Google API via Python googleapiclient**

⚠️ **Himalaya CLI funktioniert NICHT mit Gmail OAuth2** auf diesem System. Der prebuilt Himalaya v1.2.0 Binary wurde ohne das `oauth2` Cargo-Feature kompiliert, daher scheitert die Gmail-Verbindung. Stattdessen direkt die Google Gmail API nutzen:

```python
gmail = build("gmail", "v1", credentials=creds)
results = gmail.users().messages().list(userId="me",
    q="is:unread in:inbox", maxResults=10).execute()
```

- `is:unread` Search, max 5-10
- Filtert auf "wichtige" Mails per Keyword-Liste (Rechnung, Bank, Password, etc.)
- System-Mails (UniFi, Google Calendar Benachrichtigungen) rausfiltern — nur echte

### 3. MT5 Trading (LIVE)
- Host: `10.0.60.104:8080`
- API-Token via **michel / Louis_one_13** (⚠️ Dashboard-Guest-Credentials funktionieren NICHT für API!)
- Status + Summary-Endpunkte
- Python `requests.Session()` statt curl subprocess (vermeidet Shell-Escape-Probleme)

### 4. MT5 Trading (Test)
- Host: `10.0.60.101:8080`
- Credentials: `guest / guest123` (funktioniert auf Test-Bot)

### 5. Wetter
- **Empfohlen: Python `requests` (vermeidet Security-Scanner-Blockaden bei curl mit schemeless URLs)**
  ```python
  import requests
  r = requests.get("https://wttr.in/Zurich?format=%C+%t+feels+like+%f,+wind+%w,+humidity+%h&lang=de", timeout=10)
  # → "Wolkenlos +13°C feels like +13°C, wind ↖8km/h, humidity 22%"
  ```
- `curl wttr.in/Zürich` wird oft vom Security-Scanner geblockt (schemeless URL).
  Python `requests` mit explizitem `https://`-Schema umgeht das.
- Liefert: Condition, Temperatur, Wind, Luftfeuchtigkeit

### 6. System
- `uptime -p`
- `df -h /` (Festplatte)
- `free -h` (RAM)

## Sicherheit / Credentials

Credentials sind **im Script hartcodiert** (Michels explizite Anweisung für
diesen Skill). Bei Fork/Weitergabe `.env` oder Skill-Referenz nutzen.

| Quelle | Wo Credentials | Typ |
|--------|---------------|-----|
| Asterisk SSH | `root` / Script | LXC-Passwort |
| Google | `~/.hermes/google_token.json` | OAuth (Auto-Refresh) |
| MT5 LIVE | michel/Louis_one_13 | API Token |
| MT5 Test | guest/guest123 | API Token |

## Troubleshooting

| Problem | Ursache | Fix |
|---------|---------|-----|
| ❌ `ModuleNotFoundError: No module named 'paramiko'` | fehlt im Hermes-venv | `pip install paramiko` |
| ❌ `Authentication failed` bei SSH | Falsches Asterisk-Passwort | Credentials prüfen (aktuell: `Louis_one_13`) |
| ❌ TTS/edge-tts timed out | Netzwerk oder Voice-Download | Mit kurzem Text testen: `edge-tts --voice de-DE-KillianNeural --text "Test" --write-media /tmp/t.mp3` |
| ❌ MT5 Auth failed | Falsche Credentials | Dashboard-Creds ≠ API-Creds! Immer `michel/Louis_one_13` für API |
| ❌ MT5 Balance $0 | MT5 Terminal getrennt | Normal Nachts — Bot hat MT5 nicht laufen |
| ❌ Anruf kommt nicht an / Call zeigt NO ANSWER | Erster originate-Versuch failt oft — Salt-Trunk braucht Retry | 3x `channel originate` in schneller Folge starten (siehe apollo-call v5.0 Retry-Pattern). Wichtig: PHONE_NUM = `0796459743` (Swiss-Format, NICHT +41 — der apollo-out Dialplan converted sälber) |
| ❌ Konnte keinen Asterisk erreichen | SSH zu 10.0.60.167 | Container läuft? `ping 10.0.60.167` |
| ❌ Calendar keine Events | Ganztägige Events: `start` ist String, nicht Dict | Script parst beides |
| ❌ Call klingelt nicht / demo-congrats abgespielt | Extension `s@default` verwendet statt `s@apollo-external` | `s@default` spielt demo-congrats. Immer `channel originate Local/0796459743@apollo-out extension s@apollo-external` |
| ❌ Call nicht durchgekommen trotz originate | Rufnummer mit +41 Prefix | Swiss-Format OHNE +41: `0796459743`. Der Dialplan macht +41 draus. |
| ❌ Falsche TTS-Stimme gehört | VOICE-Variable im Script falsch | Hermes: `de-DE-KillianNeural`. Apollo: `de-DE-FlorianMultilingualNeural`. NIE Schweizerdeutsch. |
| ⚠️ DeprecationWarning für utcnow() | Python 3.13+ | Harmlos, kann ignoriert werden |
| ❌ wttr.in curl geblockt (security scanner) | Schemeless URL `wttr.in/...` ohne `https://` | Python `requests.get("https://wttr.in/...")` verwenden |
| ❌ Kein Tibber/Strompreis | Fehlender Tibber-API-Key | Datenpunkt kommentarlos überspringen |
| ❌ MT5 Test-Bots offline | Persistent seit 27.04.2026 | Überspringen, nur erwähnen wenn online |
| ⏱️ TTS zu lang (>60s) | Zu viele Datenpunkte im Briefing | Auf 3-4 Kernpunkte beschränken, max ~110 Wörter (gemessen 21.05.: 180 Wörter = 62s) |
| ❌ Himalaya kann Gmail nicht lesen | Prebuilt binary ohne OAuth2-Feature | Google API direkt via googleapiclient nutzen |
| ❌ Telegram sendMessage failed | Bot-Token nicht in `.env` | `TELEGRAM_BOT_TOKEN` in `~/.hermes/.env` setzen, oder Telethon-Ansatz nutzen |

## ⚠️ Wichtiger Hinweis: Zwei verschiedene Morgen-Calls

Michel hat am 19.05.2026 klargestellt: Der **Weckruf** (dieses Script, 07:00) ist NICHT der **Morgen-Briefing/Standup Call**.

| Call | Zeit | Inhalt | Status |
|------|------|--------|--------|
| ☀️ **Weckruf** (dieses Script) | 07:00 | Kurz: Wetter, Termine, Strom, System | ✅ Funktioniert |
| 🎯 **Morgen Briefing** | 07:05 | Ausführlich: Was gelernt, was geplant | ❌ Noch nöt implementiert |

NICHT verwechseln! Der Weckruf ist ein kurzer Fakten-Überblick, kein detaillierter Standup-Bericht.

---
name: telefonie-referenz
category: telephony
description: Vollständige Telefonie-Referenz — Asterisk, Dograh, TTS, Call-Workflows auf CT117 (10.0.60.60)
---

# Telefonie-Referenz (CT117)

## Architektur

| Komponente | IP | Status |
|---|---|---|
| **Asterisk** 20.x (pjsip) | 10.0.60.60 | ✅ CT117 |
| **Dograh** Voice Gateway | 10.0.60.60:3004 | ✅ CT117 |
| **NOVA-Call-API** (REST, alt) | 10.0.60.167:5001 | ⛔ CT112 — läuft noch, schlägt fehl (Asterisk auf CT117) |
| **NOVA-Call-API** (REST, neu) | 10.0.60.60:5050 | ✅ CT117 — Systemd, FastAPI, self-contained |
| **Scripts** (nova-*.py) | /opt/hermes167/data/scripts/ | ✅ CT112 |
| **MCPHub** | 10.0.60.170:3000 | ✅ 11 MCPs |

⭐ **Wichtig:** Asterisk + Dograh laufen **nicht mehr** auf CT112/NOVA (10.0.60.167). Beide am 07.06.2026 auf CT117 konsolidiert. **Scripts (nova-notify.py, nova-call-api.py) sind noch auf CT112** — sie referenzieren lokale Asterisk-Kommandos und schlagen mit "Asterisk nöd gfunde" fehl.

## Asterisk (CT117)

### Basis
- Version: **20.19.0** (nicht 18.x — aktualisiert)
- Pfad: `/etc/asterisk/`
- Sound-Verzeichnis: `/usr/share/asterisk/sounds/` (astdatadir — **NICHT** /var/lib/asterisk/sounds/)
- User: `asterisk` (UID 110)
- Zugriff via SSH auf Proxmox Host: `pct exec 117 -- timeout 10 asterisk -rx '...'`

### SIP Trunk — Salt (Swisscom/Quickline)
- Trunk: `salt-trunk` (pjsip)
- Check: `asterisk -rx 'pjsip show registrations'`
- Dialstring: `PJSIP/${EXTEN}@salt-trunk`
- Format: Direkte 079... (kein +41/41-Präfix)

### Verfügbare Dialplan-Kontexte auf CT117

| Context | Zweck | Extension | Sound | Erstellt am |
|---|---|---|---|---|
| `[apollo-out]` | Ausgehende Calls via Salt-Trunk — wählt Nummer | 079..., +41... oder \\_. | Kein Playback | vor 07.06.2026 |
| `[nova-local]` | **Lokale Calls mit Ansage** — spielt Sound ab | `s` | `apollo_notify` (.alaw/.ulaw/.wav) | vor 07.06.2026 |
| `[nova-local-vm]` | Lokale Calls mit Voicemail | `s` | `apollo_notify` | vor 07.06.2026 |
| `[nova-call-vm]` | Call-With-Recording | `s` | via MixMonitor | vor 07.06.2026 |
| **`[nova-api]`** | **Calls via NOVA-Call-API (Port 5050)** | `s` | **`nova_dynamic`** (TTS-generiert) | **07.06.2026** |
| `[stasis-callbot]` | Dograh-betriebene Calls | dynamisch | — | vor 07.06.2026 |

⚠️ **Wichtig:** `nova-local-out` existiert **nicht** auf CT117 — das war der Context auf NOVA (CT112). Für einen einfachen Anruf mit Ansage nutze **`nova-local`** (Context) mit **`s`** (Extension) — der spielt `apollo_notify` ab. Für einen reinen Wahl-Anruf (ohne Ansage) nutze `apollo-out` mit der Telefonnummer als Extension.

### Call-Files (empfohlen)
```bash
# Einfacher Anruf mit Ansage (Context: nova-local, spielt apollo_notify)
cat > /var/spool/asterisk/outgoing/nova_call.call << 'CALLC'
Channel: PJSIP/0796459743@salt-trunk
Context: nova-local
Extension: s
Priority: 1
CallerID: "NOVA"
MaxRetries: 2
RetryTime: 60
WaitTime: 120
CALLC
chown asterisk:asterisk /var/spool/asterisk/outgoing/nova_call.call

# Reiner Anruf ohne Ansage (Context: apollo-out, wählt direkt)
cat > /var/spool/asterisk/outgoing/nova_test.call << 'CALLC'
Channel: PJSIP/0796459743@salt-trunk
Context: apollo-out
Extension: 0796459743
Priority: 1
CallerID: "NOVA Test"
MaxRetries: 2
RetryTime: 60
WaitTime: 60
CALLC
chown asterisk:asterisk /var/spool/asterisk/outgoing/nova_test.call
```

### Workflow: TTS-Audio bereitstellen

CT117 hat **kein edge-tts** und **kein python3-venv**. Audio muss extern generiert werden:

1. **Audio auf CT112 generieren** (dort ist edge-tts 7.2.8 installiert):
   ```python
   import subprocess, sys
   # via Python-Modul (nicht CLI — CLI ist nicht im PATH)
   subprocess.run([sys.executable, "-m", "edge_tts",
       "--voice", "de-DE-SeraphinaMultilingualNeural",
       "--rate", "+30%",
       "--text", "Hallo Michel, hier ist NOVA.",
       "--write-media", "/tmp/audio.mp3"
   ], check=True, capture_output=True)
   # Konvertieren
   subprocess.run(["ffmpeg", "-y", "-i", "/tmp/audio.mp3", "-ar", "8000",
       "-ac", "1", "-sample_fmt", "s16", "/tmp/audio.wav"], check=True)
   subprocess.run(["ffmpeg", "-y", "-i", "/tmp/audio.wav", "-f", "alaw", "/tmp/audio.alaw"], check=True)
   subprocess.run(["ffmpeg", "-y", "-i", "/tmp/audio.wav", "-f", "mulaw", "/tmp/audio.ulaw"], check=True)
   ```

2. **Via Proxmox-Host (10.0.60.10) zu CT117 kopieren**:
   ```bash
   pct pull 112 /tmp/audio.alaw /tmp/audio.alaw
   pct pull 112 /tmp/audio.ulaw /tmp/audio.ulaw
   pct push 117 /tmp/audio.alaw /tmp/audio.alaw
   pct push 117 /tmp/audio.ulaw /tmp/audio.ulaw
   ```

3. **Auf CT117 als apollo_notify bereitstellen** (Context nova-local spielt `apollo_notify`):
   ```bash
   cp /tmp/audio.alaw /usr/share/asterisk/sounds/apollo_notify.alaw
   cp /tmp/audio.ulaw /usr/share/asterisk/sounds/apollo_notify.ulaw
   chown asterisk:asterisk /usr/share/asterisk/sounds/apollo_notify.*
   chmod 644 /usr/share/asterisk/sounds/apollo_notify.*
   ```

### Bekannte Pitfalls (aus der Praxis)
- **`defaultlanguage=de` → Sound muss in `de/` Unterverzeichnis! (KRITISCH — 07.06.2026)**
  - Asterisk auf CT117 hat `defaultlanguage = de` in `asterisk.conf`
  - Playback sucht daher in `/usr/share/asterisk/sounds/de/apollo_notify.*`
  - **NICHT** direkt in `/usr/share/asterisk/sounds/apollo_notify.*`
  - Nach jedem Sound-Deploy MÜSSEN die Dateien auch ins `de/` Verzeichnis:
    ```bash
    mkdir -p /usr/share/asterisk/sounds/de
    cp /usr/share/asterisk/sounds/apollo_notify.* /usr/share/asterisk/sounds/de/
    chown -R asterisk:asterisk /usr/share/asterisk/sounds/de/
    ```
  - **Symptom ohne `de/`:** Call wird ANSWERED, aber sofort `Hangup()` — kein Playback. CDR zeigt nur `Hangup` als Application, kein `Playback(apollo_notify)`. Call endet nach ~5 Sekunden.
  
- **Alte Sound-Dateien überschatten neue** — Alte .wav/.alaw/.ulaw in `/var/lib/asterisk/sounds/` werden vor neuen in `/usr/share/asterisk/sounds/` gefunden, wenn sie grösser sind! **Immer `find / -name "apollo_notify.*" -delete` vor jedem Deploy.**
- **Ansagen müssen NEUTRAL sein** — Kein Agentenname hardcoden! Siehe Wichtige Regeln.
- **Sound-Name ist `apollo_notify`, nicht `nova_*`** — der Context `nova-local` spielt `apollo_notify` ab. Wenn du den Sound anders nennst, wird er nicht gefunden → stummer Call.
- **`nova-local-out` existiert nicht auf CT117** — nutze stattdessen `nova-local` (mit Ansage) oder `apollo-out` (ohne Ansage).
- **Sound-Ownership:** Immer `chown asterisk:asterisk + chmod 644` — sonst Permission denied bei ~1.12s → Call bricht ab.
- **Sound-Pfad:** Primär `/usr/share/asterisk/sounds/` (astdatadir). `/var/lib/asterisk/sounds/` wird NICHT durchsucht, kann aber alte Dateien enthalten die via Sound-Discovery gefunden werden.
- **Alte Formate:** Alte .wav/.gsm überschatten neue .alaw — vor deploy löschen.
- **Edge-TTS:** 
  - `--write-media` mit .wav-Endung produziert AAC/MPEG-ADTS, kein echtes WAV. Immer via ffmpeg konvertieren.
  - Nutze **Python-Modul**, nicht CLI: `python3 -m edge_tts --text "..." --voice de-DE-SeraphinaMultilingualNeural --rate +30% --write-media /tmp/audio.mp3`
  - `echo "..." | edge-tts` funktioniert NICHT (CLI fehlt im PATH)
- **Number-Format:** `PJSIP/079...@salt-trunk` — OHNE +41.
- **REST API auf CT112:** `nova-call-api.py` läuft noch auf CT112 (Port 5001) — schlägt mit "Asterisk nöd gfunde" fehl, da Asterisk auf CT117 ist. Noch nicht migriert.
- **Alte Call-Files ignorieren** — wenn ein Call-File fehlerhaft ist (falscher Context), löschen und neu erstellen. Asterisk löscht Call-Files nach Verarbeitung.
- **CDR-Diagnose f. stumme Calls (Korrektur 07.06.2026):** Nach Sound-Deploy war Call stumm. CDR zeigte nur `Hangup()` in Application, kein `Playback(apollo_notify)`. Ursache: `defaultlanguage=de` → Sound fehlte im `de/` Unterverzeichnis. Lösung: Sound in `/usr/share/asterisk/sounds/de/` deployen + `dialplan reload`.
- **pct push erfordert SEPARATE SSH-Calls:** Chained pct push/pull in einem SSH-Befehl schlägt feil. Immer getrennt ausführen: `pct pull 112 ...` → `pct push 117 ...` → `pct exec 117 ...`
- **Audio-Format-Prüfung:** `file /usr/share/asterisk/sounds/apollo_notify.alaw` sollte "CCITT G.711" zeigen. WAV sollte "RIFF ... Microsoft PCM, 16 bit, mono 8000 Hz" sein. Nur "data" = Problem.

### Nützliche Kommandos
```bash
asterisk -rx 'pjsip show registrations'           # Trunk-Status
asterisk -rx 'dialplan show nova-local'            # Dialplan prüfen
asterisk -rx 'core show channels'                  # Aktive Calls
asterisk -rx 'core show channels verbose'          # Detailliert
tail -50 /var/log/asterisk/full                    # Live-Log
tail -1 /var/log/asterisk/cdr-csv/Master.csv       # Letzter CDR
ls -la /usr/share/asterisk/sounds/apollo_notify.*  # Sound-Dateien
ls -la /var/spool/asterisk/outgoing/               # Call-Files
```

## Dograh — AI Voice Gateway
- URL: `http://10.0.60.60:3004`
- Credentials: `henryari` / `Henry_ari_2026_Mike!` (NUR Asterisk ARI/AMI)
- Skill: `dograh-voice-gateway`

## Credentials
- **Asterisk AMI:** henryami / Henry_ari_2026_Mike!
- **Asterisk ARI:** henryari / Henry_ari_2026_Mike!
- ⚠️ **NUR für Asterisk!** NICHT für Atlassian/Jira/Confluence verwenden!

## TTS-Standards
- **Stimme:** de-DE-SeraphinaMultilingualNeural (edge-tts)
- **Rate:** +30%
- **Sprache:** HOCHDEUTSCH/SCHRIFTDEUTSCH — NIEMALS Schweizerdeutsch!
- **Format:** .alaw + .ulaw (für Asterisk)
- **Sanitizer:** Emojis, Symbole, URLs, ASCII-Art, Englisch entfernen
- **Konvertierung:** `ffmpeg -i input -ar 8000 -ac 1 -sample_fmt s16 output`

## Anruf-Typen

### 1. Einfacher Benachrichtigungsanruf (nova-local-call)
TTS auf CT112 generieren → Sound als `apollo_notify` auf CT117 deployen → Call-File mit Context `nova-local` → Asterisk spielt Ansage ab → Auflegen

### 2. Call-With-Recording (nova-call-vm)
TTS → Sound → Call-File → Asterisk → Ansage → MixMonitor → BEEP → Sprechen → WaitForSilence → Goodbye → STT+LLM+Action

**Whitelist:**
- **BOSS** (Michel): voller STT+LLM+Action
- **AGENT** (Team): STT+Kurz-Check+Notify
- **EXTERN** (Default): Roh-Audio zu Michel

### 3. NOVA-Call-API (REST, NEU — 07.06.2026)
Self-contained FastAPI auf CT117 (10.0.60.60:5050). Spricht Asterisk lokal an — kein SSH nötig.

**Infrastruktur:**
- **Host:** CT117 (10.0.60.60), Port 5050
- **Service:** Systemd `nova-call-api.service` (Autostart + Restart)
- **Pfad:** `/opt/nova-call-api/nova-call-api.py`
- **Venv:** `/opt/nova-call-api/venv/` (edge-tts + fastapi + uvicorn)
- **Endpunkt:** `http://10.0.60.60:5050/`
- **Auth:** Kein API-Key — nur Netzwerkzugriff auf CT117 nötig

**Endpoints:**
```
GET  /health          → Systemstatus (Asterisk-Version, Trunk-Status)
POST /call            → Anruf auslösen (JSON Body)
GET  /docs            → Swagger UI
```

**POST /call — Payload:**
```json
{
  "number": "0796459743",
  "message": "Hallo. Das ist ein neutraler Testanruf.",
  "playback_file": "nova_welcome",
  "caller_id": "NOVA System"
}
```

**Parameter:**
| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `number` | string | ✅ | Zielrufnummer (ohne +41) |
| `message` | string | ✅ | TTS-Text für die dynamische Ansage |
| `playback_file` | string | ❌ | Soundfile-Name (ohne Extension), wird vor TTS-Ansage abgespielt |
| `caller_id` | string | ❌ | Anrufer-ID (Default: "NOVA System") |

**Soundfiles (werden beim API-Start pre-deployed):**
| Name | Text |
|------|------|
| `nova_welcome` | "Hallo. Hier ist ein automatischer Anruf vom System." |
| `apollo_goodbye` | "Auf Wiederhören." |
| `apollo_vm_prompt` | "Bitte hinterlassen Sie eine Nachricht nach dem Signalton." |
| `hermes_response` | "Vielen Dank für Ihren Anruf." |

**Wichtig:** Alle Soundfiles sind **NEUTRAL** — kein Agentenname hardcoded!

**Beispiel (Curl):**
```bash
curl -X POST http://10.0.60.60:5050/call \
  -H "Content-Type: application/json" \
  -d '{
    "number": "0796459743",
    "message": "Hallo. Testanruf von der neuen API.",
    "playback_file": "apollo_goodbye"
  }'
```

**Workflow (intern):**
1. TTS via edge-tts generieren (venv Python auf CT117)
2. In WAV → alaw → ulaw konvertieren (ffmpeg)
3. Sound nach `/usr/share/asterisk/sounds/` + `de/` deployen
4. Asterisk-Call-File mit Context `nova-api` (spielt `nova_dynamic` ab)
5. Call-File in `/var/spool/asterisk/outgoing/`

**Bekannte Probleme & Fixes:**
- ⚠️ Sound-Index: Nach Sound-Deploy muss `core reload` (nicht nur `dialplan reload`) ausgeführt werden, sonst findet Asterisk die neuen Sound-Dateien nicht. `core show sound nova_dynamic` gibt dann "not found in index" selbst wenn die Datei physikalisch existiert.
- Der API-Code ruft aktuell **kein** `core reload` auf — das ist ein TODO.

**Python-Beispiel (für Agenten):**
```python
import urllib.request, json

payload = {
    "number": "0796459743",
    "message": "Hallo. Das ist ein Testanruf.",
    "playback_file": "nova_welcome"
}
req = urllib.request.Request(
    "http://10.0.60.60:5050/call",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode())
    print(f"✅ Call initiated: {result}")
except Exception as e:
    print(f"❌ Call failed: {e}")
```

### 4. Status Call (morning-status-call)
17+ Datenquellen → LLM(DeepSeek V4 Flash via LiteLLM) → TTS → Anruf an Michel

REST API auf Port 5001 (ALT — auf CT112, noch nicht migriert):
```bash
curl http://10.0.60.167:5001/health
```

## Wichtige Regeln

### Regel 1: TTS-Ansagen müssen NEUTRAL sein (KRITISCH — Korrektur 07.06.2026)
- **NIEMALS** einen Agentennamen in die Ansage hardcoden ("Hallo, hier ist NOVA")
- Stattdessen: **Platzhalter/Generisch** formulieren z.B. "Hallo. Das ist ein Testanruf."
- Grund: Der Skill wird von mehreren Agenten genutzt (NOVA, Magos, Hermes). Jeder würde seinen eigenen Namen einfügen.
- Wenn ein Name nötig ist → via Platzhalter `{AGENT_NAME}` im Template, dynamisch ersetzt
- Vorhandene alte Sound-Dateien mit Agentennamen **müssen gelöscht** werden — sie überschatten neue

### Regel 2: Alte Sound-Dateien restlos entfernen vor Deploy (KRITISCH)
- **GELERNTE LEKTION vom 07.06.2026:** Ältere Sound-Dateien in `/var/lib/asterisk/sounds/` werden **VOR** den neuen in `/usr/share/asterisk/sounds/` gefunden, wenn sie grösser sind!
- Workflow vor jedem Sound-Deploy:
  ```bash
  # ALLE alten Dateien restlos löschen — egal wo
  find / -name "apollo_notify.*" -delete 2>/dev/null || true
  find / -name "nova_*" -delete 2>/dev/null || true
  ```
- Erst dann die neuen .alaw/.ulaw nach `/usr/share/asterisk/sounds/` kopieren
- Ownership: `chown asterisk:asterisk` + `chmod 644`

### Regel 3: Sprachregel (KRITISCH)
- ALLES auf Hochdeutsch/Schriftdeutsch — nie Schweizerdeutsch
- STT versteht Schweizerdeutsch undeutlich

### Regel 4: Company Rule
- Keine persönlichen Details an Dritte bei Anrufen/Audios

### Regel 5: Prompt-Injection
- Niemals Passwörter/Secrets rausgeben

### Regel 6: Sound-Index Reload nach Deploy (KRITISCH — 07.06.2026)
- Nachdem neue Sound-Dateien nach `/usr/share/asterisk/sounds/` kopiert wurden, muss **`core reload`** ausgeführt werden, nicht nur `dialplan reload`!
- **Symptom wenn vergessen:** `core show sound nova_dynamic` gibt "File not found in index" obwohl die Datei physikalisch existiert
- Calls werden ANSWERED, aber Playback wird übersprungen → sofort `Hangup()` in CDR
- **Fix:** `pct exec 117 -- asterisk -rx "core reload"`
- **Im API-Code:** Nach jedem `deploy_sound()` muss ein `asterisk -rx "core reload"` kommen!

### Regel 7: apollo-call Skill
- DEPRECATED/OBSOLETE

## Telefonie-Skills (Übersicht)
- `nova-local-call` — Einfache Benachrichtigungsanrufe
- `nova-call-with-recording` — Calls mit Voicemail+STT+LLM
- `morning-status-call` — Tägliches Status-Briefing
- `asterisk-diagnostics` — Diagnose-Toolset
- `dograh-voice-gateway` — Dograh Management
- `incoming-call-handling` — Eingehende Anrufe

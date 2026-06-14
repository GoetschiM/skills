# ARI Testing Session — 19.05.2026

## Session 1 — Proof of Concept ARI Integration (Morning)

## Ziel
Test ob Hermes via ARI an Asterisk-Konferenz (ConfBridge) teilnehmen kann: joinen, zuhören, antworten.

## Was funktioniert ✅

### 1. ARI grundlegend ✅
- ARI WebSocket verbindet erfolgreich: `ws://henryari:HermesVB2026@10.0.60.167:8088/ari/events?app=callbot&api_key=henryari:HermesVB2026`
- StasisStart-Event wird bei Anruf auf Extension mit `Stasis(appname)` ausgelöst
- Channel answer, Playback, Recording via ARI REST API funktionieren
- Test-Call via `channel originate` → ARI antwortet, spielt sounds, recorded

### 2. Sound Playback ✅
- Verfügbare Asterisk-Sounds: `hello-world`, `goodbye`, `beep`, `nova_welcome`, `apollo_goodbye`
- ARI Playback: `POST /channels/{id}/play {"media": "sound:hello-world"}`

### 3. Recording ✅
- `POST /channels/{id}/record {"name":"test","format":"wav","maxDurationSeconds":10,"maxSilenceSeconds":1.5}`
- RecordingFinished-Event kommt über WebSocket
- Achtung: HTTP 409 beim zweiten Record auf gleichem Channel

### 4. Conference Setup ✅
- `[from-internal]` context für SIP-Endpoints (100=Apollo, 101=Michel)
- Extension 8000 → `ConfBridge(8000)` für Konferenz
- Extension 8001 → `MixMonitor(${RECFILE})` + `ConfBridge(8000)` für Hermes mit Recording
  ```ini
  [hermes-conference]
  exten => 8001,1,NoOp(Hermes joins conf with recording)
   same => n,Set(RECFILE=/var/spool/asterisk/monitor/hermes_${STRFTIME(${EPOCH},,%Y%m%d_%H%M%S)}.wav)
   same => n,MixMonitor(${RECFILE})
   same => n,ConfBridge(8000)
   same => n,Hangup()
  ```

### 5. Channel in Conference joinen ✅
- CLI: `asterisk -rx "channel originate Local/8001@hermes-conference extension 8001@hermes-conference"`
- ARI: `POST /ari/channels {"endpoint":"Local/8001@hermes-conference","app":"callbot","callerId":"Hermes"}`
- ConfBridge zeigt Users: `confbridge list` → 8000: 2 Users

## Probleme & Learnings ⚠️

### Local Channel hält nicht dauerhaft
- `channel originate` erstellt Local-Channel-Paar → geht in ConfBridge
- Channel fällt nach ~10-30s wieder weg (originate completed)
- **Lösungsansätze:**
  - ARI-App die den Channel aktiv managed und bei ChannelDestroyed reconnectet
  - SIP-Registrierung für Hermes (Extension 104) als richtiger Endpoint
  - ConfBridge `wait_marked=yes` + marked user → hält Conference offen

### ARI Config Änderungen
- `module reload ari` geht nicht → "No such module 'ari'"
- Stattdessen: `module reload res_ari.so`
- Oder: `core restart now` (unterbricht aktive calls!)

### ConfBridge MixMonitor Recording
- MixMonitor startet nur auf meinem Channel, nicht auf der ganzen Conference
- Für Conference-Recording: `record_conference=yes` im bridge profile
- Oder: MixMonitor auf jedem Teilnehmer-Channel einzeln

### Von-internal Context Fehlt
- PJSIP-Endpoints (100=apollo, 101=Michel) referenzieren `context=from-internal`
- Context war nicht definiert → interne Anrufe konnten nicht geroutet werden
- Lösung: `[from-internal]` in extensions.conf definieren

## Session 2 — Outgoing Call + TTS Integration (Evening)

### Outgoing Call via Salt-Trunk ✅
- ARI POST /channels mit `"endpoint": "PJSIP/+41796459743@salt-trunk"` + `"callerId": "+413****7977"`
- Channel wird erstellt mit state=Down (ringing)
- Wenn Angerufener abhebt → StasisStart-Event auf der callbot-app
- **Wichtig:** salt-trunk muss `Contact` mit Status `Avail` ha — sonst Failed

### TTS Integration ✅
- edge-tts generiert MP3 (24kHz, mono)
- Umwandlig für Asterisk: `ffmpeg -i input.wav -ar 8000 -ac 1 -sample_fmt s16 output.wav`
- TTS-File ins Asterisk sounds-Verzeichnis: `/var/lib/asterisk/sounds/hermes_welcome.wav`
- ARI Playback: `{"media": "sound:hermes_welcome"}` (ohne .wav-Endung)
- **Bewies:** TTS mit de-DE-ConradNeural funktioniert (7.7s für "Hallo Michel...")
- Zweite TTS-Datei: `/var/lib/asterisk/sounds/hermes_response.wav` (131KB, ConradNeural)

### Callbot v3 — Mit TTS und fixed Sleeps
- `/usr/local/bin/ari_callbot_v3.py` — Erste Version mit:
  - Outgoing/Incoming unified handler
  - TTS-Welcome statt Asterisk-Standard-Sounds
  - Recording mit `maxSilenceSeconds: 2.0` für natürliches Turn-Taking
  - **Problem:** `await asyncio.sleep(3)` nach Play statt auf PlaybackFinished zu warten
  - **Problem:** `await asyncio.sleep(8)` nach Record statt auf RecordingFinished zu warten
  - Diese festen Sleeps brechen bei längerer/kürzerer TTS-Dauer oder unerwarteten Verzögerungen

### ARI WebSocket mit Python (Websockets 15.x)
```python
async with websockets.connect(WS_URL, max_size=2**20, ping_interval=20) as ws:
    # ping_interval statt timeout (wird in 15.x nöd unterstützt)
```

### 🔴 CRITICAL: TTS Voice/Language Rule (User-Korrektur)
- **TTS/Audio = NUR Hochdeutsch, NIE Schwiizerdütsch.** User hat sich lautstark beschwert.
- **Stimme = de-DE-ConradNeural (männlich).** NIE de-CH-LeniNeural (Frau, Schweiz).
- **Memory updated + Skill embedded.** Dä Regel gildet für ALLI Agenten (Schwarmwissen).

## Session 3 — Event-Driven Callbot v4 + Outgoing Call Test (Late Evening)

### Problem: fixed Sleeps in v3 brechen den Flow
Der erste Outgoing-Call-Test mit v3 zeigte:
- Welcome-Sound wurde nicht abgespielt (Race: Play gestartet aber sleep(3) zu kurz/falsch getimed)
- Recording lief 35s statt bei Stille zu stoppen
- Keine Garantie dass der Anrufer das Willkommen gehört hat bevor aufgenommen wird

### Lösung: Event-Driven Architektur (v4)
**Kernprinzip:** Statt `asyncio.sleep(X)` → auf ARI-Events warten (PlaybackFinished, RecordingFinished).

```python
class CallSession:
    def __init__(self, channel_id, caller, events):
        self.playback_done = asyncio.Event()
        self.recording_done = asyncio.Event()

    async def on_playback_finished(self, ev):
        self.playback_done.set()  # ← Weiter geht's!

    async def on_recording_finished(self, ev):
        rec = ev.get("recording", {})
        self.recording_path = rec["name"] + "." + rec["format"]
        self.recording_done.set()

    async def play(self, sound, wait=True):
        self.playback_done.clear()
        await ari("POST", f"/channels/{cid}/play", {"media": f"sound:{sound}"})
        if wait:
            await asyncio.wait_for(self.playback_done.wait(), timeout=30)

    async def record(self, max_duration=30, max_silence=2.0):
        self.recording_done.clear()
        await ari("POST", f"/channels/{cid}/record", {
            "name": f"rec_{ts}", "format": "wav",
            "maxDurationSeconds": max_duration,
            "maxSilenceSeconds": max_silence,
        })
        await asyncio.wait_for(self.recording_done.wait(), timeout=max_duration + 10)
```

**Event-Driven Flow:**
1. Answer → Play(hermes_welcome) → **wartet auf PlaybackFinished** (echte Ende-Erkennung)
2. Record(maxSilenceSeconds=2.0) → **wartet auf RecordingFinished** (Silence oder Timeout)
3. Download WAV → STT → LLM → TTS → Play(hermes_response) → **wartet auf PlaybackFinished**
4. Play(apollo_goodbye) → Hangup

**Timeout-Schutz:** Falls der Event nie kommt (Channel stirbt, Caller hängt auf), bricht ein `asyncio.wait_for(..., timeout=30)` die Wartezeit ab.

### Outgoing Call Test mit v4
- HTTP 200: Channel erstellt `PJSIP/salt-trunk-00000068`, state=Down (klingelt)
- Callbot v4 läuft auf Nova (PID war aktiv) und wartet auf StasisStart
- **Ergebnis noch offen** — der Test wurde in dieser Session gestartet aber nicht abgeschlossen

### Deployment des Skripts auf Nova
```bash
# Datei übertragen (Base64-Pipe, da SSH-Heredocs oft Exit 255)
base64 /usr/local/bin/ari_callbot_v4.py | sshpass -p "$PASS" ssh root@10.0.60.167 "base64 -d > /usr/local/bin/ari_callbot_v4.py && chmod +x /usr/local/bin/ari_callbot_v4.py"

# Starten
sshpass -p "$PASS" ssh root@10.0.60.167 'setsid python3 -u /usr/local/bin/ari_callbot_v4.py > /tmp/ari_callbot_v4.log 2>&1 &'

# Status prüfen
sshpass -p "$PASS" ssh root@10.0.60.167 'ps aux | grep ari_callbot'
```

**Wichtig:** Alte v3-Prozesse müssen vor dem Start von v4 beendet werden (sonst konkurrieren zwei Apps um dieselbe Extension).

### TTS-Dateien neu deployen (nach Format-Korrektur)
edge-tts → 24kHz MP3 → ffmpeg → 8kHz PCM WAV für Asterisk:
```bash
edge-tts --voice de-DE-ConradNeural --text "Hallo Michel, hier ist Hermes..." /tmp/welcome.mp3
ffmpeg -y -i /tmp/welcome.mp3 -ar 8000 -ac 1 -sample_fmt s16 /tmp/hermes_welcome.wav
base64 /tmp/hermes_welcome.wav | sshpass -p "$PASS" ssh root@10.0.60.167 "base64 -d > /var/lib/asterisk/sounds/hermes_welcome.wav && chown asterisk:asterisk /var/lib/asterisk/sounds/hermes_welcome.wav"
```

### Key Learning: Event-Driven vs. Fixed Sleeps
| Aspekt | v3 (fixed sleep) | v4 (event-driven) |
|--------|-------------------|-------------------|
| Timing | Schätzung, bricht bei Latenz | Exakt, wartet auf echtes Ende |
| Race Conditions | Häufig (Sound noch nicht fertig) | Keine (Event garantiert Fertig) |
| Code-Komplexität | Einfach (lineare sleeps) | Mittel (Events + callbacks) |
| Zuverlässigkeit | Niedrig | Hoch |
| Timeout-Schutz | Keiner | asyncio.wait_for(timeout=30) |
| Silence Detection | Nicht getestet | RecordingFinished mit maxSilence=2.0 |

## Nächste Schritte (nach Session 3)

1. **Outgoing Call testen** — Michel anrufen, v4 sollte Welcome korrekt abspielen, dann auf Silence warten
2. **STT integrieren** — Recording-Download nach RecordingFinished, dann faster-whisper (tiny/base)
3. **LLM integrieren** — Transkript an lokales LLM (Ollama) senden, Antwort generieren
4. **TTS-Pipeline schliessen** — Antwort per edge-tts konvertieren, nach Nova deployen, abspielen
5. **Loop** — Nach Response wieder Record starten (Mehrfach-Dialog)
6. **Persistente Conference-Teilnahme** — Hermes als permanenten ConfBridge-Teilnehmer
7. **Barge-In (Phase 2)** — Silero VAD auf eingehendem Audio-Stream

## Konferenz-Room Status (Ende Session 3)
- Extension 8000 → ConfBridge(8000) ✅
- Extension 7001 im [from-internal] Context → Stasis(callbot) ✅
- ARI-Callbot v4 auf Nova deployed und läuft ✅
- TTS-Dateien deployed: hermes_welcome.wav (123KB), hermes_response.wav (131KB) ✅
- Outgoing Call via ARI → Salt-Trunk → klingelt bei Michel ✅
- STT/LLM/TTS-Loop: noch offen (nächster Schritt)

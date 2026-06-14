# ARI Pipeline v2 — Echtzeit-Dialog-Architektur 🎤

**Stand:** 19.05.2026 20:00
**Ort:** Nova (10.0.60.167), Asterisk ARI
**Prozess PID:** 136195 (läuft via `setsid` im Hintergrund)
**Script:** `/usr/local/bin/hermes_pipeline_ari.py`

## Architektur-Überblick

```
Asterisk Call → Stasis(hermes-pipeline) → WebSocket Event
    → answer channel → Play(welcome) → PlaybackFinished event
    → STT Loop (max 3 Turns):
        → MixMonitor start (record channel audio)
        → Process: wait for file → faster-whisper transcribe
        → LLM generate response (Ollama/API)
        → edge-tts generate speech → convert to 8kHz WAV
        → POST /channels/{id}/play (response)
        → wait PlaybackFinished → next turn
    → Play(goodbye) → hangup
```

## Script-Struktur (`hermes_pipeline_ari.py`)

```python
class HermesAsteriskPipeline:
    """
    ARI-Stasis-App für Echtzeit-Dialog.
    - WebSocket-Listener für Events
    - ARI-REST-Client für Channel-Management
    - MixMonitor für Audio-Erfassung
    - Context-Steuerung für Dialog-Phasen
    """
```

### Haupt-Komponenten

1. **WebSocket-Client** (`websockets` library)
   - Verbindet zu `ws://henryari:HermesVB2026@10.0.60.167:8088/ari/events?app=hermes-pipeline&api_key=...`
   - `ping_interval=20` (wichtig: `timeout`-Parameter wird in WS 15.x nöd supportet)
   - Empfängt Events wie: `StasisStart`, `PlaybackFinished`, `ChannelHangupRequest`, `ChannelDestroyed`

2. **ARI-REST-Client** (`aiohttp` + BasicAuth)
   - `POST /channels/{id}/answer` — Call annehmen
   - `POST /channels/{id}/play` — Media abspiele (sound: oder file:)
   - `DELETE /channels/{id}/play/{playbackId}` — Playback abbreche (barge-in)
   - `POST /channels/{id}/record` — Recording starte (⚠️ ARI-Recording spiechert nöd uf Platte, MixMonitor isch besser)
   - `DELETE /channels/{id}` — Channel hangup

3. **MixMonitor-Integration**
   - `POST /channels/{id}/variable?variable=MIXMONITOR_FILENAME&value=/tmp/input.wav`
   - Oder via `channel originate` mit MixMonitor im Dialplan
   - **Wichtig:** MixMonitor schribt WAV-File asynchron. S'File isch erst komplett wenn Channel destroyed wird odr via `StopMixMonitor()`

4. **Dialog-Phase-Management**
   - `_state = "WELCOME" | "LISTEN" | "PROCESS" | "SPEAK" | "GOODBYE"`
   - Jede Phase handled spezifischi Events
   - Timeout: falls in LISTEN z'lang kei Audio → Wiederholig

### Dialog-Loop (Pseudo-Code)

```python
async def on_stasis_start(self, channel_id):
    await self.answer(channel_id)
    await self.play_welcome(channel_id)
    self.turn_count = 0

async def on_playback_finished(self, event):
    if self.state == "WELCOME":
        self.state = "LISTEN"
        self.start_mixmonitor(channel_id)
    elif self.state == "SPEAK":
        self.turn_count += 1
        if self.turn_count < 3:
            self.state = "LISTEN"
            self.start_mixmonitor(channel_id)
        else:
            self.state = "GOODBYE"

async def listen_timeout(self, channel_id):
    self.state = "PROCESS"
    self.stop_mixmonitor(channel_id)
    # wait for file to flush
    text = await faster_whisper.transcribe(f"/tmp/hermes_input_{cid}.wav")
    response = await llm.generate(text)
    await self.tts_and_play(channel_id, response)
    self.state = "SPEAK"
```

## Betrib uf Nova

### Startere/Pipeline neustarte

```bash
# Aktuelle Pipeline killen
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 "pkill -f hermes_pipeline_ari"

# Pipeline starte (detached via setsid)
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 \
  'setsid python3 -u /usr/local/bin/hermes_pipeline_ari.py > /tmp/hermes_pipeline_ari.out 2>&1 &'

# Log prüfe
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 "cat /tmp/hermes_pipeline_ari.out"
```

### App-Status prüfe

```bash
# WebSocket verbunde? App registriert?
curl -u "henryari:HermesVB2026" http://10.0.60.167:8088/ari/applications
# → ["name":"hermes-pipeline","channel_ids":[]]
```

### Pipeline updaten

Script deploye:
```bash
base64 /usr/local/bin/hermes_pipeline_ari.py | \
  sshpass -p 'Louis_one_13' ssh root@10.0.60.167 \
  "base64 -d > /usr/local/bin/hermes_pipeline_ari.py && chmod +x /usr/local/bin/hermes_pipeline_ari.py && pkill -f hermes_pipeline_ari && setsid python3 -u /usr/local/bin/hermes_pipeline_ari.py > /tmp/hermes_pipeline_ari.out 2>&1 &"
```

## Bekannti Limitatione (Stand 19.05.)

1. **Sequentielli ARI Playbacks verlüüred RTP uf PJSIP** — Ersti Playback funktioniert, zweiti + folgendi nüm (RTP-Stream verlore). Ursache: ARI Playback öffnet temporäre RTP-Stream wo nach Playback zuemacht. PJSIP chan nöd neu verhandle für zweiti Playback. **Workaround:** E Plan B bruucht.

2. **MixMonitor vs Named Pipe** — Aktuell MixMonitor (File-basiert). Für echte Echtzit müsst Named Pipe oder ExternalMedia her. MixMonitor schribt erst nach Channel destroy/Stop inegschribe — verzögeret de Dialog.

3. **STT-Latenz** — faster-whisper tiny brucht ~1.5s uf CPU (Nova i5-6500T). Das isch merklich im Dialog.

4. **No barge-in** — Aktuelle Loop isch half-duplex: Hermes redet → Michel redet → Hermes redet. Sobald Hermes afoot z'rede, cha Michel nöd unterbreche. Barge-in brucht Silero VAD + ExternalMedia.

5. **Turn-Zähler** — Uf max 3 Turns begrenzt zum Teste. Muss für Produktion erhöht oder unbegrenzt werde.

## Nächste Schritt

1. ✅ Grundgerüst läuft (WebSocket + ARI REST)
2. ⬜ MixMonitor durch Named Pipe ersetze (nöd blockierend)
3. ⬜ Silero VAD integriere für e biz weniger Output-Latenz + Barge-in
4. ⬜ ExternalMedia RTP Streaming (voll sync, lowest Latenz)
5. ⬜ Multi-Agent-Konferenz (GL-46)

## Verwandti Referenze

- `ari-pjsip-evening-debug-20260519.md` — RTP-Verlust-Debug Session
- `gosub-u-parameter-verified-20260519.md` — Dialplan-Alternative (verifiziert)
- `hermes-autoplay-dialplan-20260519.md` — Dialplan-basierti AutoPlay-Kontext
- `voice_pipeline_research.md` — Full research document

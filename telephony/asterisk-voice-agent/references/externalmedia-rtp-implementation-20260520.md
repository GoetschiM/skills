# ExternalMedia RTP Implementation & ARI Call Routing Fix — 20.05.2026

## Session Overview
Built and deployed the ExternalMedia RTP pipeline (`hermes_pipeline_extmedia.py`) to solve the ARI Sequential RTP Loss bug. Also discovered that CLI `channel originate ... application Stasis` doesn't work for PJSIP/Salt trunks.

## Key Discoveries

### 1. 🚨 CLI `application Stasis` is BROKEN for PJSIP/Salt trunks
```bash
# ❌ DOES NOT WORK — goes through dialplan 'from-salt-inbound' instead of Stasis
asterisk -rx 'channel originate PJSIP/41796459743@salt-trunk application Stasis hermes-pipeline'

# ✅ WORKS — POST /ari/channels with app parameter
curl -X POST -u henryari:HermesVB2026 \
  http://127.0.0.1:8088/ari/channels \
  -d '{"endpoint":"PJSIP/+41796459743@salt-trunk","app":"hermes-pipeline","callerId":"+413****7977","timeout":60}'
```

**Result when using CLI:** Channel shows `PJSIP/salt-trunk-000000a8!from-salt-inbound!s!1!Down!AppDial2!` — it's in the `from-salt-inbound` dialplan context, not Stasis. When the callee answers, the dialplan runs its default voicemail flow.

**Result when using ARI API:** Channel is created directly in Stasis from the moment of creation. StasisStart fires at creation time (not answer time). Pipeline can interact immediately.

### 2. ExternalMedia RTP works
```bash
POST /ari/channels/externalMedia
{"app":"hermes-pipeline", "external_host":"127.0.0.1:9001", "format":"ulaw"}
```
Response includes:
- Channel ID: `1779296319.761`
- `channelvars.UNICASTRTP_LOCAL_PORT`: `15880` (dynamic, from RTP port range 10000-20000)
- `channelvars.UNICASTRTP_LOCAL_ADDRESS`: `127.0.0.1`

This creates a UnicastRTP channel. After bridging it with the call channel:
- **Receive:** RTP (μ-law) arrives at our UDP socket on :9001
- **Send:** RTP (μ-law) goes to Asterisk's UNICASTRTP_LOCAL_PORT

### 3. Pipeline deployed and running
- Script: `/usr/local/bin/hermes_pipeline_extmedia.py`
- Process: `python3 -u /usr/local/bin/hermes_pipeline_extmedia.py`
- Started via: `setsid python3 -u /usr/local/bin/hermes_pipeline_extmedia.py > /tmp/hermes_extmedia.out 2>&1 &`
- ARI App registered: `hermes-pipeline` (0 channels when idle)
- WebSocket: ESTABLISHED to 127.0.0.1:8088 ✅

### 4. Test Call Results
- **Call 1** (CLI `channel originate PJSIP/... application Stasis`): Michel said "als ich abnahm beendete der Call" — call entered `from-salt-inbound` dialplan, played voicemail welcome, then ended.
- **Call 2** (ARI API `POST /ari/channels`): Channel created (ID: 1779296545.767, State: Down). Michel may not have answered this one (already told me first call ended).

### 5. TTS Tool Fallback Pattern
The `text_to_speech` tool returned "No TTS provider available" despite edge-tts being installed (7.2.8) and configured as the TTS provider. Workaround:
```bash
edge-tts --voice de-DE-ConradNeural --text "..." --write-media /tmp/hermes_tts.mp3
```
Then include `MEDIA:/tmp/hermes_tts.mp3` in the response to deliver via Telegram as voice bubble.

## Architecture Components

### Python Modules Used
- `websockets` — ARI WebSocket (v15.x, no `timeout` param, use `ping_interval=20`)
- `aiohttp` — ARI REST API calls (BasicAuth)
- `audioop` — μ-law ↔ PCM conversion (`ulaw2lin`, `lin2ulaw`, `rms`)
- `struct` — RTP header packing/unpacking
- `faster_whisper` — Speech-to-text (tiny model, CPU int8)
- `edge_tts` — Text-to-speech (de-DE-ConradNeural)
- `ffmpeg` — Audio format conversion (24kHz MP3 → 8kHz PCM)

### RTP Packet Format
- Header: 12 bytes (`!BBHII` struct)
- Payload: μ-law encoding (8-bit @ 8000Hz)
- Payload Type: 101 (μ-law/PCMU)
- SSRC: 0xDEADBEEF (arbitrary)
- Pacing: 20ms between 160-byte chunks

### VAD (Phase 1)
Simple RMS-based threshold VAD (not Silero yet):
- `audioop.rms(pcm_frame, 2) / 32768.0` — normalized RMS
- Threshold: 0.02
- Silence detection: 15 consecutive frames (~480ms)
- Frames: 5 per receive batch (~160ms window)

## Files
- `/usr/local/bin/hermes_pipeline_extmedia.py` — Deployed pipeline on Nova
- `skill: asterisk-voice-agent -> scripts/hermes_pipeline_extmedia.py` — Skill copy
- `/tmp/hermes_extmedia.log` — Runtime log on Nova
- `/tmp/hermes_pipeline_ari.py` — Old v2 pipeline (still exists, not running)

## Open Issues
1. Silero VAD still needed (currently RMS-based, less accurate)
2. LLM integration: currently echoes user's text back in canned response
3. No barge-in yet (VAD runs during listen-only phase)
4. First test call with ExternalMedia still pending
5. Call routing via CLI `application Stasis` is broken — always use ARI REST API

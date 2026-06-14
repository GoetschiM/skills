---
name: asterisk-voice-agent
description: "Real-time bidirectional voice conversation pipeline for Asterisk PBX — STT (faster-whisper) → LLM → TTS with ExternalMedia RTP livestream, VAD turn-taking, and barge-in. Build agents that can hear, understand, and speak in phone calls."
tags: [asterisk, voice, stt, tts, vad, ari, realtime, externalmedia, livestream]
category: telephony
---

# Asterisk Voice Agent — Live Dialog Pipeline 🎙️

## 🔴 CRITICAL — TTS Voice & Language Rules

1. **Language:** TTS/Audio/Calls = **NUR Hochdeutsch.** KEIN Schweizerdeutsch.
2. **Voice:** `de-DE-ConradNeural` (männlich). NIE `de-CH-LeniNeural` oder `de-CH-JanNeural`.
3. **Fallback:** Tool first. If `text_to_speech` fails → CLI: `edge-tts --voice de-DE-ConradNeural ...`
4. **Audio-Summaries:** User mag sie, aber NUR Hochdeutsch + ConradStimme.
5. **TTS Server-down:** Use **gTTS proxy** (see below) — don't wait for edge-tts to recover.

## Trigger

- User wants **live bidirectional voice dialog** with an AI agent over phone
- User asks about **voice pipelines, STT→LLM→TTS integration with Asterisk**
- User mentions **conference calls, barge-in, turn-taking**
- User says **"Livestream, nicht Voicemail"**

## CURRENT CANONICAL APPROACH ✅ — ExternalMedia RTP Input + Bridge Playback Output

### Architecture (verified live 20.05.2026)

```
                            ┌──────────────────┐
Michel's Phone ←→ Asterisk  │  PJSIP Channel    │
   (salt trunk)            └────────┬─────────┘
                                     │
                             ┌───────┴────────┐
                             │  Mixing Bridge  │  ← POST /ari/bridges
                             └───────┬────────┘
                                     │
                      ┌──────────────┼──────────────┐
                      │                              │
             ┌────────┴────────┐           ┌─────────┴────────┐
             │ ExternalMedia   │           │ Bridge Playback  │
             │ (RTP → Python)  │           │ (TTS → Michel)   │
             └────────┬────────┘           └─────────┬────────┘
                      │                              │
              ┌───────┴───────┐              ┌───────┴───────┐
              │   Python      │              │   Python      │
              │ VAD → STT →   │              │ LLM → TTS →   │
              │ LLM → [TTS]   │              │ POST /bridges │
              └───────────────┘              └───────────────┘
```

**Flow:**
1. `POST /ari/channels` with `endpoint: PJSIP/+41...@salt-trunk, app: hermes-pipeline`
2. On StasisStart → create mixing bridge → add Michel's channel
3. Create ExternalMedia channel → add to bridge (receives Michel's audio as μ-law RTP)
4. Python listens on UDP port 9001 for μ-law RTP packets
5. VAD (RMS-based) detects speech → accumulates into speech buffer
6. On 1.5s silence → process speech buffer: WAV → faster-whisper STT → [LLM]
7. TTS via gTTS proxy on Hermes → save as Asterisk sound
8. `POST /bridges/{id}/play` with TTS sound → Michel hears response
9. GOTO 5 (loop, up to 10 turns, or until hangup)

### Key Technical Details

**Call Establishment:**
```python
r = requests.post(f"{AST_URL}/channels",
    params={"endpoint": f"PJSIP/+41796459743@salt-trunk",  # {num}@{trunk} format!
            "app": "hermes-pipeline",
            "callerId": "+4131779777",
            "timeout": 60},
    auth=("henryari", "HermesVB2026"))
# Accept HTTP 200 or 201! Both indicate success.
```

**ExternalMedia Channel (receives Michel's live RTP):**
```python
r = requests.post(f"{AST_URL}/channels/externalMedia",
    params={"app": "hermes-pipeline",
            "external_host": "127.0.0.1:9001",  # Python listens here
            "format": "ulaw"},
    auth=auth)
# → HTTP 200/201, channel created. Add to bridge immediately.
# Don't wait for StasisStart on ExternalMedia channels — they don't trigger it.
```

**Bridge Playback (sends TTS to Michel):**
```python
# Copy TTS WAV to Asterisk sounds dir
shutil.copy2(tts_file, f"{SOUNDS_DIR}/{sound_name}.wav")
os.chmod(dest, 0o644)

# Play via bridge — unlimited sequential playbacks work!
r = requests.post(f"{AST_URL}/bridges/{brid}/play",
    params={"media": f"sound:{sound_name}"}, auth=auth)
```

### VAD Tuning

```
SimpleVAD(threshold=500, min_speech_ms=500, min_silence_ms=1500)
```
- **Verified threshold:** 500 (tested live 20.05.2026) — threshold 300 caused false triggers on bridge noise → empty STT
- **Critical bug:** VAD triggers on bridge background noise too. Fix: check `currently_playing` flag before processing VAD events.
- **Speech accumulation pattern:** On `speech_start`, drain rtp_buffer into speech_buffer. On `in_speech`, continue accumulating. On `speech_end`, process speech_buffer (NOT rtp_buffer).
- **Min audio guard:** ignore speech segments < 800 bytes (<100ms).

### TTS Fallback: gTTS API Proxy

When edge-tts fails (Microsoft server outage or Nova network issue):
```
Hermes (10.0.60.156)                     Nova (10.0.60.167)
┌────────────────────┐                   ┌──────────────────┐
│ TTS API Server     │ ← HTTP POST :8765 │ Pipeline         │
│ :8765             │  text="..."        │ calls API instead │
│ gTTS → ffmpeg →  │ ──────────────────→ │ of edge_tts      │
│ WAV 8kHz         │   WAV response      │ locally           │
└────────────────────┘                   └──────────────────┘
```

Start on Hermes: `python3 /tmp/tts_api_server.py` (listens on port 8765)
Pipeline calls: `POST http://10.0.60.156:8765` with `{"text": "..."}` → returns WAV

### State Machine Pattern

Use mutable class singleton to avoid Python scoping issues with cross-thread flags:
```python
class State: pass  # single file
S = State()
S.mic_speaking = False   # VAD detected speech
S.currently_playing = False  # Bridge playback active → ignore VAD
S.processing = False     # STT/LLM/TTS in progress
S.interrupt = False      # Barge-in requested
S.running = True         # Dialog loop active
```

### Pipeline Script

Deployed on Nova at `/usr/local/bin/hermes_live_pipeline.py`:
```bash
# Start (background)
nohup python3 /usr/local/bin/hermes_live_pipeline.py > /var/log/hermes_live.log 2>&1 &

# Stop
pkill -f hermes_live_pipeline

# Cleanup (remove stale bridges)
bash /tmp/cleanup_pipeline.sh

# Check log
cat /var/log/hermes_live.log
```

## ARI Configuration (Nova: 10.0.60.167)

**`/etc/asterisk/ari.conf`:**
```ini
[general]
enabled = yes
[henryari]
type = user
read_only = no
password = HermesVB2026
```

**Dialplan** (extensions.conf):
```ini
[hermes-ari]
exten => s,1,Stasis(hermes-pipeline)
 same => n,Hangup()
exten => _X.,1,NoOp(Hermes ARI Pipeline)
 same => n,Answer()
 same => n,Stasis(hermes-pipeline)
 same => n,Hangup()
```

## Verified Commands

```bash
# Check ARI connectivity
curl -u "henryari:HermesVB2026" http://10.0.60.167:8088/ari/endpoints

# Check channels in app
curl -s -u henryari:HermesVB2026 http://127.0.0.1:8088/ari/applications \
  | python3 -c "import sys,json; [print(f'App {a[\"name\"]}: {len(a.get(\"channel_ids\",[]))}ch') for a in json.load(sys.stdin)]"

# Kill active channels
asterisk -rx "core show channels concise" | cut -d"!" -f1 | while read ch; do asterisk -rx "hangup request $ch"; done
```

## Related Skills

### dograh-voice-platform — Higher-Level Voice Platform

For a **higher-level voice platform** (Dograh) that can use this Asterisk pipeline as its ARI provider, see the `dograh-voice-platform` skill (`telephony/dograh-voice-platform`). It provides:

- Visual workflow builder (drag & drop, no code)
- Browser WebRTC calls (no phone needed)
- Knowledge Base / RAG for documents
- Campaigns (automated outbound calls)
- Custom Tools (HTTP/MCP tools for API integration)
- 120+ API endpoints

**Relationship:** `asterisk-voice-agent` = the low-level real-time dialog pipeline (VAD → STT → LLM → TTS via ExternalMedia RTP). Dograh = the full platform orchestrating multiple such pipelines with UI, campaigns, and integrations.

## References

- `references/voice-live-pipeline-session-20260520.md` — Full session log from ExternalMedia breakthrough (RTP reception, VAD, STT, gTTS fix)
- `references/bridge-playback-breakthrough-20260520.md` — Bridge playback verification (sequential audio works)
- `references/externalmedia-rtp-implementation-20260520.md` — Original ExternalMedia RTP implementation details
- `references/hermes-pipeline-ari-dev-20260519.md` — ARI pipeline dev history
- `scripts/hermes_live_pipeline.py` — Current live dialog pipeline (ExternalMedia + Bridge Playback)
- `scripts/hermes_voice_pipeline.py` — Archived: Bridge+Record pipeline (deprecated)
- `references/backup/asterisk-backup.md` — Asterisk config/sounds/CDR backup to MinIO procedure
- `references/backup/cronjob-jira-logging.md` — Cron-job Jira logging convention (SUP-28)
- `references/backup/session-2026-05-17.md` — Original backup implementation session log

## 🔐 Asterisk Backup & Restore

**Rule:** Backup MUST run before every configuration change (dialplan, PJSIP, ARI). No change without backup.

See `references/backup/asterisk-backup.md` for the full procedure including:
- **What is backed up:** `/etc/asterisk/` (all configs), custom sounds (`apollo_*`, `hermes_*`), CDR logs (`Master.csv`)
- **Target:** MinIO `/data/asterisk-backups/` via SCP/Paramiko (NOT `mc` — times out from this container)
- **Frequency:** Daily 04:00 UTC (06:00 CEST summer — staggered from Hermes backup at 03:00)
- **Restore:** only on explicit command — `python3 /root/.hermes/scripts/asterisk-restore.py [date|latest]`
- **MinIO connectivity:** Use Paramiko SSH to 10.0.60.121, not `mc` CLI. Credentials: username `root`, password from `.env`.
- **Jira logging:** After each run, script logs to SUP-28: `[TS] Asterisk Backup | Status: OK/Dauer/Size/CDR count`

**Dependencies:** `pip install --break-system-packages paramiko`

**Cron job:** Created daily at 04:00 UTC. Verify with `cronjob action=list`.

## 📞 Critical Call Safety (Sekundentakt-Verbot!)

**🔴 ABSOLUTE RULE: NEVER call Michel more than once per test iteration.**

- One pipeline run = one call. If the call ends, the pipeline stops. NO restart loops.
- Auto-restart causes "Sekundentakt-Anrufe" (a call every second) — Michel's worst experience. He will STOP you immediately.
- Before making a test call: CHECK that no previous pipeline process is still running. `pkill -f pipeline_name` first.
- Before making a test call: CHECK that no stale call files exist in `/var/spool/asterisk/outgoing/`.
- If a test call fails (wrong audio, wrong TTS, no response), KILL the pipeline process, FIX the code, restart — don't just "try again" with the same binary.

**🔴 3-Strike Escalation Rule:** If the same error occurs 3 times in a row (e.g., user hangs up, audio not heard, VAD not triggering), STOP all testing immediately. Log the full failure state to a Jira ticket (GL-49), update the ticket description + comment with exact error, and let Michel decide the next approach. Do NOT keep trying the same fix. Do NOT iterate blindly. Michel says: "Es ist immer das Gleiche" — break the pattern.

## Testing Strategy

**🔴 NEVER test a voice pipeline by calling the user repeatedly.** Each failed call erodes trust.

Preferred testing flow:
1. **Silent testing (no call):** Test STT offline with pre-recorded WAV files. Test TTS audio files by playing them locally with ffplay. Test LLM response generation without the call loop.
2. **Bridge-only playback test:** Test that TTS audio plays correctly via `POST /ari/bridges/{id}/play` with Michel answering ONCE. This confirms audio path works.
3. **Record-only test:** Test that ExternalMedia receives RTP audio by logging packet count. Verify Michel's voice arrives before adding TTS playback.
4. **Full pipeline test — ONE call max.** Get in, verify, get out. Document results immediately.
5. **After test:** Kill all pipeline processes. Verify `ls /var/spool/asterisk/outgoing/` is empty.

## Current Pitfalls

- **🔴 API accepts HTTP 200 AND 201** for `POST /channels` and `POST /channels/externalMedia`. Don't check for exactly 201 — both are success.
- **🔴 ExternalMedia channels don't StasisStart** — they're created directly in the app. No waiting needed.
- **🔴 "Cannot record channel while in bridge"** — ARI Record is useless for dialog. Use ExternalMedia RTP for input.
- **🔴 Endpoint format:** `PJSIP/+41...@salt-trunk` (NUMBER@TRUNK), NOT `PJSIP/salt-trunk` with separate extension.
- **🔴 CLI `channel originate ... application Stasis` enters dialplan, not Stasis** — always use ARI REST API `POST /ari/channels`.
- **🔴 VAD triggers on bridge mix** — ExternalMedia in bridge receives ALL bridge audio (both Michel AND our TTS). Use `currently_playing` flag to ignore VAD during playback.
- **🔴 Bridge echo after playback** — After bridge playback finishes, audio continues echoing in the bridge for 1-2s. MUST flush RTP buffer AND wait 1-2 seconds before starting VAD, otherwise VAD detects own playback as "Michel speaking".
- **🔴 Empty STT after false VAD** — noise/silence accumulates in speech_buffer → empty transcription. Guard with minimum audio bytes (>800B = 100ms) and higher VAD threshold (500). Check RMS of converted PCM before processing.
- **🔴 edge-tts Microsoft outage** — Microsoft TTS servers (edge.microsoft.com) are unreliable. PRIMARY use gTTS proxy. edge-tts is fallback ONLY.
- **🔴 gTTS proxy** — TTS API server runs on Hermes (10.0.60.156:8765). Pipeline on Nova calls POST http://10.0.60.156:8765 with {text: "..."} → returns WAV. Start: `python3 /tmp/tts_api_server.py`.
- **🔴 Welcome text — ABSOLUTELY CRITICAL.** Michel HATES pre-recorded samples ("Hello World", "goodbye"). Welcome MUST be LIVE TTS every call: "Hallo Michel, hier ist Hermes. Ich höre dich, los gehts!" Generate fresh via gTTS proxy each time — never use a static sound file for welcome or goodbye.
- **🔴 SSHs heredocs with complex quoting often fail (exit 255)** — break into one-liners, write Python fix scripts locally and SCP, or use base64 pipe.
- **🔴 No-silence-test limitation** — every outbound call requires Michel to answer. Prefer component-level tests (STT with files, TTS with ffplay) before calling.
- **🔴 Call-file safety** — check `/var/spool/asterisk/outgoing/` for stale files before calling. Set `MaxRetries: 0`.
- **🔴 gTTS generates MP3 not WAV** — The TTS API server handles conversion to 8kHz 16-bit mono WAV for Asterisk. If calling gTTS directly, always convert.
- **🔴 Open-mic state machine** — Use mutable `State` class singleton (not globals) to avoid Python scoping issues when cross-thread flags are modified inside `run()`.
- **🔴 Nova deployment host is low-resource** — see `references/nova-hardware-profile.md` for CPU, RAM, and model size constraints on 10.0.60.167.

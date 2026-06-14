# Voice Pipeline v3.0 — Stabilized Learnings (20.05.2026)

## What Works (Verified Live) ✅

1. ExternalMedia RTP receives Michel's voice through bridge
2. VAD (threshold=500, min_speech=500ms, min_silence=1500ms) detects speech
3. Speech accumulation into buffer (μ-law → WAV)
4. STT via faster-whisper tiny (German)
5. TTS via gTTS API proxy on Hermes
6. Bridge playback delivers TTS back to Michel
7. Dialog loop: multiple turns within one call
8. Clean hangup + bridge teardown

## Key Bugfix History

| Bug | Symptom | Fix |
|-----|---------|-----|
| "Cannot record channel while in bridge" | ARI Record fails | Use ExternalMedia instead (no recording) |
| VAD detects own playback | Empty STT (echo in bridge) | Flush rtp_buffer + 1.5s wait after playback |
| edge-tts returns "No audio" | TTS fails always | gTTS proxy on Hermes (10.0.60.156:8765) |
| Empty STT despite speech_buf>0 | Noise triggers VAD | Minimum 800B guard + RMS check < 500 skip |
| wait_ev_cond positional arg error | Welcome TTS falls back | Use `lambda e: True` as 2nd arg, or use `play_sound()` |
| Auto-restart loop | Endless calls | Remove while True; one call per run |
| Welcome always hello-world | User hates it | Live TTS "Hallo Michel, hier ist Hermes" |
| Variable scoping in python | UnboundLocalError crashes | State class singleton instead of globals |

## TTS Proxy Architecture

```
Hermes (10.0.60.156): python3 /tmp/tts_api_server.py (port 8765)
  - Accepts POST with {"text": "..."}
  - Tries edge-tts first (ConradNeural, de-DE)
  - Falls back to gTTS if edge-tts unavailable
  - Returns 8kHz 16-bit mono WAV
  
Pipeline calls:
  POST http://10.0.60.156:8765 with json={"text": "..."}
  → response.content written to /tmp/hermes_tts_turn{N}.wav
  → copied to /var/lib/asterisk/sounds/
  → played via POST /bridges/{id}/play
```

## Pipeline File

Deployed at `/usr/local/bin/hermes_live_pipeline.py` on Nova.

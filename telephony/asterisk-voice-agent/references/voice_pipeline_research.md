# Asterisk Voice Pipeline — Full Research Document

> **Date:** 2026-05-19
> **Context:** Local open-source pipeline: Asterisk PBX + faster-whisper + edge-tts + LLM + Silero VAD
> **Servers:** Nova (Asterisk @ 10.0.60.167), Hermes (Python agent @ 10.0.60.156)

---

## 1. Key Reference Implementations

### A. Harvix-AI-Calling (⭐ Best Overall Match)
**Repo:** https://github.com/shyam302/Harvix-AI-Calling

This is the most relevant single reference. Architecture:
- **Asterisk ARI Stasis** — Python connects via ARI WebSocket, listens for events
- **Half-duplex turn-taking** — Record user audio via ARI → download WAV → faster-whisper → LLM (vLLM) → Supertonic TTS (local neural) → play audio on channel
- **No ExternalMedia** — Uses ARI's built-in recording API (simple, reliable)
- **VAD is ASTERISK-SIDE** — Asterisk's `Record()` maxSilenceSeconds handles VAD; no Silero VAD in pipeline
- **Thread pool** — `inference_pool.py` with semaphore-guarded concurrent whisper/TTS slots
- **Pipeline latency tracked** per-turn with breakdown

**Key Files:**
| File | Purpose |
|------|---------|
| `ari_app/ari_loop.py` | ARI WebSocket loop, dispatches StasisStart/RecordingFinished/PlaybackFinished |
| `ari_app/call_session.py` | Per-call orchestrator: listen → STT → LLM → TTS → play (main loop) |
| `ari_app/stt.py` | faster-whisper integration, ffmpeg to 16kHz, CUDA/CPU fallback |
| `ari_app/tts.py` | Supertonic TTS to 8kHz WAV for Asterisk |
| `ari_app/llm.py` | OpenAI-compatible vLLM client with streaming |
| `ari_app/inference_pool.py` | Thread pool with semaphore concurrency control |
| `ari_app/conversation.py` | Text trimming, filler removal, Hindi grammar fixes |
| `asterisk_snippets/` | Sample configs for ARI, PJSIP, extensions |

**Latency Profile (from their logs):**
- Silence detection: ~0.85-1.4s (Asterisk-side)
- STT: ~200-800ms (varies by model size)
- LLM: ~300-1000ms (depends on model)
- TTS synthesis: ~200-800ms
- TTS playback: proportional to audio length
- **End-to-end: 1.5-3s typical** (half-duplex)
- Bottleneck is typically TTS playback length or LLM latency

### B. Ai-chatbot / Barbie Builders (⭐ Barge-In Reference)
**Repo:** https://github.com/devansharora710/Ai-chatbot

This project uses **ExternalMedia RTP streaming** for true full-duplex + barge-in:
- **Asterisk ExternalMedia** — Creates a bidirectional RTP stream between Asterisk and Python
- **Silero VAD in Python** — Runs per-frame (32ms chunks) on the incoming RTP stream
- **Barge-in** — During TTS playback, VAD still runs on incoming audio. If >=3 consecutive speech frames (~100ms), triggers barge_in event → cancels current TTS → starts LISTEN mode.
- **Separate processes** — Whisper as subprocess, Piper TTS as subprocess, ARI controller as main process
- **Piper TTS via RTP** — Piper outputs raw PCM to stdout → worker sends RTP packets directly back

### C. NPCL-Asterisk-ARI-Assistant (Enterprise Reference)
**Repo:** https://github.com/letsdeepchat/AsteriskARI-Bot

Most polished but uses **OpenAI Realtime API** (cloud, $0.06/min):
- OpenAI WebRTC Realtime API for voice-to-voice
- ARI ExternalMedia streaming for bi-directional audio
- Structured as FastAPI app with 10+ specialized modules
- Not suitable for local-only requirement but great reference for production structuring

---

## 2. Architecture Comparison

| Aspect | ARI Recording (Harvix) | ExternalMedia RTP (Ai-chatbot) |
|--------|----------------------|-------------------------------|
| **Complexity** | Simple, proven | More complex |
| **Latency** | Higher (record→download→transcribe) | Lower (real-time streaming) |
| **Barge-in** | Can't interrupt during playback | Native support via VAD on stream |
| **VAD** | Asterisk-side (maxSilenceSeconds) | Python-side (Silero VAD, per-frame) |
| **Audio format** | WAV file on disk | Raw RTP stream (μ-law/PCMU) |
| **Concurrent calls** | Easy (each call independent) | More state management |
| **Reliability** | Very reliable (proven) | Can be fragile (RTP timing) |
| **Network** | Works across servers (HTTP) | Needs low-latency between servers |

---

## 3. Component Deep-Dives

### 3.1 Asterisk Integration

**ARI Recording approach** (half-duplex):
```python
# Start recording (Asterisk handles silence detection internally)
POST /channels/{id}/record
{
  "name": "rec-xxx",
  "format": "wav",
  "maxDurationSeconds": 20,
  "maxSilenceSeconds": 1.4,
  "terminateOn": "none"
}
# Wait for RecordingFinished event via WebSocket
# Download WAV
GET /recordings/stored/{name}/file
# Transcribe -> LLM -> TTS -> Play
POST /channels/{id}/play {"media": "sound:custom/tts-xxx"}
```

**ExternalMedia approach** (full-duplex with barge-in):
```
POST /bridges
POST /channels/externalMedia
{ "channelId": "stt-xxx", "format": "ulaw", "external_host": "10.0.60.156:9999" }
POST /bridges/{id}/addChannel { "channel": ["stt-xxx", "orig-channel"] }
```

### 3.2 Voice Activity Detection (VAD)

**Silero VAD** (best option):
- Load model: `silero_vad.load_silero_vad()` — 1.8MB ONNX model
- Process 32ms frames at 8kHz (256 samples per frame)
- Returns speech probability (0.0-1.0)
- Threshold: 0.95 (phone-call tuned)
- Silence to end: 13 frames (~414ms) of non-speech
- Barge-in trigger: 3 consecutive speech frames (~100ms)

**Alternative — WebRTC VAD** (no dependencies):
- Python `webrtcvad` package
- Less accurate than Silero but much lighter

### 3.3 Speech-to-Text (STT)

**faster-whisper** (already installed 1.2.1):
- Uses CTranslate2 under the hood (faster than original Whisper)
- Model sizes: tiny (39M), base (74M), small (244M), medium (769M), large-v3 (1550M)
- Phone-tuned parameters (see SKILL.md)
- Supports both CPU (int8) and GPU (float16) compute

**Performance (CPU int8, 3s audio):**
- `tiny.en` on CPU: ~1.5s
- `base.en` on CPU: ~2.9s

### 3.4 Text-to-Speech (TTS)

**edge-tts** (already installed 7.2.8):
- Uses Microsoft Edge's online TTS service (free, no API key needed)
- Voice selection: `de-CH-LeniNeural` (Swiss German), `de-DE-KatjaNeural` (German)
- First audio in ~300-600ms, streaming thereafter
- **Limitation:** Cloud-dependent (no local fallback without internet)

**Local alternatives:**
| TTS | Quality | Latency | Local |
|-----|---------|---------|-------|
| Piper TTS | Good (neural) | ~200ms first audio | ✅ |
| Supertonic | Excellent | ~300-800ms | ✅ (needs GPU) |
| Coqui TTS | Very good | ~500ms | ✅ |
| edge-tts | Excellent | ~300-600ms | ❌ (cloud) |

### 3.5 LLM Integration

Any OpenAI-compatible API works:
- **Ollama** (local) — easiest setup
- **vLLM** (local, GPU) — fastest local option
- **llama.cpp** (local, CPU) — works without GPU

Key optimization: keep responses short (1-2 sentences, <260 chars) for natural phone conversation speed.

---

## 4. Cloud API Alternatives (if local too slow)

| Service | Cost/min | Built-in PSTN | Notes |
|---------|----------|---------------|-------|
| VAPI.ai | $0.05-0.10 | ✅ Direct SIP | Most mature |
| ElevenLabs | $0.05-0.10 | ✅ Direct SIP | Best voice quality |
| OpenAI Realtime | $0.30/min | ❌ WebRTC only | Best understanding |
| Gemini Live | ~$0.02-0.05 | ❌ WebSocket | Very cost-effective |

---

## 5. Open Questions

1. **edge-tts cloud dependency** — Works only with internet. For truly local fallback, need Piper TTS.
2. **Cross-server RTP timing** — ExternalMedia RTP between Nova and Hermes. Same LAN, should be fine.
3. **Multiple concurrent calls** — Harvix handles well with semaphore pools.
4. **LLM provider** — If no local GPU for vLLM, use Ollama as fallback.
5. **Asterisk sound file permissions** — Need to verify where Asterisk can read TTS WAV files.

# Asterisk Voice Pipeline — Research Summary

> Date: 2026-05-19
> Context: Local open-source pipeline: Asterisk PBX + faster-whisper + edge-tts + LLM + Silero VAD
> Servers: Nova (Asterisk @ 10.0.60.167), Hermes (Python agent @ 10.0.60.156)

## 1. Key Reference Implementations

### A. Harvix-AI-Calling (Best Overall Match)
**Repo:** https://github.com/shyam302/Harvix-AI-Calling

Most relevant single reference:
- **Asterisk ARI Stasis** — Python connects via ARI WebSocket
- **Half-duplex turn-taking** — Record → download WAV → faster-whisper → LLM → TTS → play
- **VAD is Asterisk-side** — maxSilenceSeconds in Record() API
- **Thread pool** — semaphore-guarded concurrent whisper/TTS slots
- **Latency tracked** per-turn with breakdown

Key files: `ari_app/ari_loop.py`, `ari_app/call_session.py`, `ari_app/stt.py`, `ari_app/tts.py`, `ari_app/llm.py`, `ari_app/inference_pool.py`, `ari_app/conversation.py`

Latency profile (from logs):
- Silence detection: ~0.85-1.4s (Asterisk-side)
- STT: ~200-800ms (varies by model)
- LLM: ~300-1000ms
- TTS: ~200-800ms
- **End-to-end: 1.5-3s typical**

### B. Ai-chatbot / Barbie Builders (Barge-In Reference)
**Repo:** https://github.com/devansharora710/Ai-chatbot

Uses **ExternalMedia RTP streaming** for true full-duplex + barge-in:
- **Asterisk ExternalMedia** — Bidirectional RTP stream (μ-law/PCMU)
- **Silero VAD** — per-frame (32ms) on incoming RTP stream
- **Barge-in** — During TTS playback, if ≥3 consecutive speech frames (~100ms) → cancel TTS → LISTEN mode
- **Separate processes** — Whisper subprocess, Piper TTS subprocess, ARI controller

### C. NPCL-Asterisk-ARI-Assistant (Enterprise Reference)
**Repo:** https://github.com/letsdeepchat/AsteriskARI-Bot

Most polished but uses **OpenAI Realtime API** ($0.06/min):
- OpenAI WebRTC Realtime API for voice-to-voice
- ARI ExternalMedia streaming
- FastAPI app with 10+ specialized modules
- 200+ test cases, Docker/Kubernetes ready

## 2. Architecture Comparison

| Aspect | ARI Recording (Harvix) | ExternalMedia RTP (Ai-chatbot) |
|--------|----------------------|-------------------------------|
| Complexity | Simple, proven | More complex |
| Latency | Higher (record→download→transcribe) | Lower (real-time streaming) |
| Barge-in | Can't interrupt during playback | Native support via VAD on stream |
| VAD | Asterisk-side (maxSilenceSeconds) | Python-side (Silero VAD, per-frame) |
| Audio format | WAV file on disk | Raw RTP stream (μ-law/PCMU) |
| Concurrent calls | Easy (each call independent) | More state management |
| Reliability | Very reliable (proven) | Can be fragile (RTP timing) |
| Network | Works across servers (HTTP) | Needs low-latency between servers |

## 3. Component Details

### Whisper Optimisation (faster-whisper params from Harvix)
```python
{
    "beam_size": 1, "best_of": 1, "temperature": 0.0,
    "condition_on_previous_text": False, "without_timestamps": True,
    "vad_filter": True, "no_speech_threshold": 0.55,
    "compression_ratio_threshold": 2.4, "log_prob_threshold": -1.0,
    "vad_parameters": {"min_silence_duration_ms": 400, "speech_pad_ms": 80}
}
```
Performance (CPU int8): tiny.en ~100-300ms, base.en ~200-500ms, small ~400-1000ms.

### TTS Options
| TTS | Quality | Latency | Local | Notes |
|-----|---------|---------|-------|-------|
| edge-tts | Excellent | ~300-600ms | ❌ (cloud) | Free via Microsoft Edge |
| Piper TTS | Good (neural) | ~200ms | ✅ | 1-2GB models, fast on CPU |
| Supertonic | Excellent | ~300-800ms | ✅ | ONNX-based, needs GPU |
| Coqui TTS | Very good | ~500ms | ✅ | Discontinued but works |

### VAD (Silero VAD)
- ONNX model, 1.8MB
- Process 32ms frames at 8kHz (256 samples)
- Speech threshold: 0.95 (phone-call tuned)
- Silence to end: 13 frames (~414ms)
- Barge-in trigger: 3 frames (~100ms)

### LLM Integration
Any OpenAI-compatible API: vLLM (local GPU), Ollama (local, easy), llama.cpp (local CPU), OpenAI/Gemini API (cloud).

Key: keep responses short (1-2 sentences, <260 chars).

## 4. Turn-Taking Logic

**Half-duplex (Harvix):**
1. Answer call → play greeting
2. LOOP: prepare_to_listen() → start_recording(maxSilence=1.5) → wait_for(RecordingFinished) → download WAV → transcribe → filter silence hallucinations → LLM → TTS → play
3. Until caller hangs up

**Barge-in (Ai-chatbot):**
```
Modes: LISTEN | SPEAK | IDLE
VAD on ALL incoming audio regardless of mode

SPEAK mode: if 3+ consecutive speech frames → barge_in → cancel TTS → buffer speech → LISTEN
LISTEN mode: accumulate speech → sustained silence (414ms) → process with Whisper → LLM → SPEAK
```

## 5. Latency Budget

Target: <1.5s end-to-end

| Stage | Target (ms) |
|-------|-------------|
| VAD/silence detection | 300-500 |
| STT (Whisper base) | 200-400 |
| LLM (small model) | 200-600 |
| TTS first chunk | 200-400 |
| TTS playback | 0-300 |
| **Total** | **~900-2200** |

Optimisation strategies:
1. Use tiny or base Whisper models
2. Pipeline TTS synthesis and playback
3. LLM streaming → send sentences to TTS as they arrive
4. Short reply limit (1-2 sentences, <260 chars)
5. Pre-load all models at startup
6. Thread pool for concurrent inference

## 6. Implementation Roadmap

**Phase 1 — Basic Half-Duplex (1-2 days)**
1. Set up ARI connection with Asterisk
2. Implement StasisStart → answer → recording loop
3. Integrate faster-whisper STT
4. Integrate LLM (start with simple text response)
5. Integrate edge-tts for TTS playback
6. End-to-end: call → speak → AI responds

**Phase 2 — Production Hardening**
7. Async concurrency with inference pool
8. Graceful hangup handling
9. Logging and latency tracking
10. Multi-call support
11. Config from environment variables

**Phase 3 — Full-Duplex + Barge-In**
12. Implement ExternalMedia RTP streaming
13. Add Silero VAD for real-time speech detection
14. Implement barge-in: interrupt TTS when caller speaks
15. Buffering and pre-roll for seamless turn transitions

## 7. Dependencies

```bash
# Phase 1
pip install httpx websockets openai

# Phase 2
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install silero-vad
```

Already installed: faster-whisper 1.2.1, edge-tts 7.2.8, numpy, onnxruntime, ffmpeg, websockets.

## 8. Asterisk Configuration Needed

```conf
# /etc/asterisk/http.conf
[general]
enabled=yes
bindaddr=127.0.0.1
bindport=8088

# /etc/asterisk/ari.conf
[general]
enabled=yes
[callbot]
type=user
read_only=no
password_format=plain
password=<your_password>

# /etc/asterisk/extensions.conf — route extension to Stasis app
[from-internal]
exten => 7001,1,Stasis(callbot)
```

## 9. Open Questions

1. edge-tts cloud dependency — needs internet. Local fallback: Piper TTS (~200ms first audio)
2. Cross-server RTP timing between 10.0.60.167 and 10.0.60.156 — sub-5ms expected (same LAN)
3. Multiple concurrent calls — Harvix handles with semaphore pools
4. LLM provider — if no local GPU → Ollama or API fallback
5. Asterisk sounds directory permissions

## 10. Summary

| Question | Answer |
|----------|--------|
| Best Asterisk integration | ARI (Stasis app + WebSocket events) |
| Best VAD | Silero VAD (Python, ONNX, per-frame) |
| Best local STT | faster-whisper (base/small model) |
| Best local TTS | Piper TTS (local) or edge-tts (cloud, free) |
| Sub-1s latency achievable? | Yes with optimisations |
| Best reference | Harvix-AI-Calling (architecture); Ai-chatbot (barge-in) |
| Cost | $0 if local (Ollama + edge-tts/Piper) |

---
name: asterisk-voice-pipeline
description: "⚠️ SUPERSEDED by `asterisk-voice-agent` — this skill is kept for reference only. See asterisk-voice-agent for the current, comprehensive guide."
tags: [asterisk, voice, stt, tts, vad, ari, realtime, dialog, telephony, superseded]
---

# Asterisk Voice Pipeline — Bidirektionaler Dialog am Telefon

## Trigger-Bedingungen

- User fragt: "Wie bringe ich einen Agenten dazu, dass er am Telefon zuhören und antworten kann?"
- User spricht über: Voice AI, Echtzeit-Dialog, Telefon-Assistent, STT/TTS-Pipeline
- User erwähnt: barge-in, turn-taking, voice activity detection, whisper pipeline
- User sagt "wir brauchen einen Prototyp für bidirektionalen Call"
- Task involviert: ARI, ExternalMedia, ConfBridge in Kombination mit Whisper + TTS

## Übersicht

**Ziel:** Ein AI-Agent (Hermes, Apollo oder Nova) kann einen eingehenden Asterisk-Anruf entgegennehmen, dem Anrufer **zuhören (STT)**, die Aussage **verarbeiten (LLM)** und **antworten (TTS)** — in Echtzeit, mit natürlichem Turn-Taking und optionaler Unterbrechungsmöglichkeit (barge-in).

**Zwei Architektur-Phasen:**

| Phase | Ansatz | Latenz | Barge-In | Komplexität |
|-------|--------|--------|----------|-------------|
| 1 — Half-Duplex | ARI Recording → WAV → Whisper → LLM → TTS → Playback | ~1.5-3s | ❌ | Einfach, bewährt |
| 2 — Full-Duplex | ARI + ExternalMedia RTP → Silero VAD → Whisper → LLM → TTS | ~0.8-1.5s | ✅ | Mittelschwer |

## Was wir bereits haben (19.05.2026)

| Komponente | Tool | Status |
|------------|------|--------|
| STT | **faster-whisper 1.2.1** | ✅ Installiert (CPU int8) |
| TTS | **edge-tts 7.2.8** | ✅ Installiert (cloud, gratis) |
| TTS (local) | Piper TTS (1-2GB Modelle) | ❌ Müsste installiert werden |
| Audio | numpy, ffmpeg, onnxruntime | ✅ Installiert |
| Telefonie | ARI, AMI, AGI | ✅ Verfügbar auf Asterisk |
| Netzwerk | LAN (10.0.60.x), sub-1ms Latenz | ✅ |
| VAD | Silero VAD (ONNX) | ❌ pip install silero-vad |

## Phase 1 — Half-Duplex (ARI Recording)

**Referenz-Repo:** [Harvix-AI-Calling](https://github.com/shyam302/Harvix-AI-Calling)

### Architektur

```
Anrufer → Asterisk (Stasis-App) → ARI WebSocket → Python Controller
                                                   ↓
                                           maxSilenceSeconds=1.5
                                                   ↓
                                      RecordingFinished Event
                                                   ↓
                                      Download WAV (HTTP GET)
                                                   ↓
                                     faster-whisper (base Model)
                                                   ↓
                                            LLM (Ollama/vLLM)
                                                   ↓
                                          edge-tts Synthese
                                                   ↓
                                     ARI Playback → Asterisk → Anrufer hört
                                                   ↓
                                          ← LOOP (nächster Turn) →
```

### Implementierung

**Asterisk-Konfiguration (auf Nova 10.0.60.167):**

```conf
; /etc/asterisk/http.conf
[general]
enabled=yes
bindaddr=127.0.0.1
bindport=8088

; /etc/asterisk/ari.conf
[general]
enabled=yes
[callbot]
type=user
read_only=no
password_format=plain
password=<sicheres_passwort>

; /etc/asterisk/extensions.conf
[from-internal]
exten => 7001,1,Stasis(callbot)
```

**Python-Core-Loop (pseudocode):**

```python
class CallSession:
    async def run(self, channel_id):
        await self.answer(channel_id)
        await self.play_sound(channel_id, "welcome")
        while not self.hangup_detected:
            # 1. LISCHTE
            recording = await self.start_recording(channel_id, max_silence=1.5)
            recording_event = await self.wait_for("RecordingFinished")
            wav_bytes = await self.download_recording(recording.name)

            # 2. TRANSCRIBIERE
            segments = self.whisper_model.transcribe(wav_bytes, beam_size=1, temperature=0)
            text = " ".join(s.text for s in segments)

            # 3. DENKE
            reply = self.llm.generate(text)

            # 4. SPRECH
            audio = await self.edge_tts.speak(reply)
            await self.play_audio(channel_id, audio)
```

### Whisper-Optimierung (aus Harvix übernommen)

```python
whisper_params = {
    "beam_size": 1,           # Maximale Geschwindigkeit
    "best_of": 1,             # Kein Beam-Search-Overhead
    "temperature": 0.0,       # Deterministisch
    "condition_on_previous_text": False,
    "without_timestamps": True,
    "vad_filter": True,       # Vorverarbeitung durch Whisper-VAD
    "no_speech_threshold": 0.55,
    "compression_ratio_threshold": 2.4,
    "log_prob_threshold": -1.0,
    "vad_parameters": {
        "min_silence_duration_ms": 400,
        "speech_pad_ms": 80
    }
}
```

**Modell-Empfehlung:** `base` oder `small` für Telefonate (1-3s Sprachausschnitte, begrenztes Vokabular). CPU int8: ~200-500ms.

### Turn-Taking Logik (Phase 1)

```
1. Answer call
2. Play opening greeting
3. LOOP:
   a. prepare_to_listen() — warte bis Playback fertig, leere Buffer
   b. start_recording() — ARI Record mit maxSilenceSeconds=1.5
   c. wait_recording() — blockiere bis RecordingFinished-Event
   d. download WAV + Whisper transkribieren
   e. Silence-Halluzinationen wegfiltern ("bye", "uh", "hmm", leere Transkripte)
   f. An LLM senden, Antwort erhalten
   g. TTS synthetisieren + auf Kanal abspielen
4. Until caller hangs up or session limit reached
```

## Phase 2 — Full-Duplex mit Barge-In

**Referenz-Repo:** [Ai-chatbot / Barbie Builders](https://github.com/devansharora710/Ai-chatbot)

### Architektur

```
Asterisk ──ExternalMedia RTP (μ-law)──→ Python (Port 9999)
                                              ↓
                                    Silero VAD per Frame (32ms)
                                              ↓
                                ┌──────────────────────────────┐
                                │                              │
                     VAD=Speech (LISTEN)            VAD=Speech (SPEAK)
                                │                              │
                    Sammle Buffer                    → Cancel TTS
                                │                              │
                    Silence > 400ms                   Buffer Speech
                                │                              │
                    Whisper STT                       → Switch to LISTEN
                                │
                    LLM → TTS → Playback via RTP
```

### VAD-Integration (Silero VAD)

```python
import silero_vad

vad = silero_vad.load_silero_vad()  # 1.8MB ONNX-Modell

# Pro 32ms-Frame (256 Samples bei 8kHz)
SPEECH_THRESHOLD = 0.95
SILENCE_FRAMES_TO_END = 13     # ~414ms non-speech → utterance END
BARGE_IN_TRIGGER = 3           # ~100ms speech während TTS → BARGE-IN

mode = "LISTEN"
silence_counter = 0
speech_buffer = []

for frame in rtp_stream(samples=256):
    prob = vad(frame, 8000)
    
    if mode == "SPEAK":
        if prob > SPEECH_THRESHOLD:
            speech_counter += 1
            if speech_counter >= BARGE_IN_TRIGGER:
                cancel_tts_playback()
                mode = "LISTEN"
                speech_counter = 0
        else:
            speech_counter = max(0, speech_counter - 1)
    
    elif mode == "LISTEN":
        if prob > SPEECH_THRESHOLD:
            speech_buffer.append(frame)
            silence_counter = 0
        else:
            silence_counter += 1
            if silence_counter >= SILENCE_FRAMES_TO_END and len(speech_buffer) > 0:
                # End-of-Utterance → transcribe
                audio = encode_speech(speech_buffer)
                text = whisper.transcribe(audio)
                reply = llm.generate(text)
                tts_stream = edge_tts.stream(reply)
                mode = "SPEAK"
                speech_buffer = []
                silence_counter = 0
```

### Wichtige VAD-Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| Schwellwert Speech | 0.95 | Telefon-getuned (höher als Standard) |
| Silence-to-End | 13 Frames | ~414ms ohne Sprache → Utterance-Ende |
| Barge-In | 3 Frames | ~100ms Sprache während TTS → Unterbrechung |
| Frame-Grösse | 32ms (256s @ 8kHz) | Silero VAD Standard |
| Audio-Format | μ-law (PCMU) | Asterisk RTP Standard |

## Latenz-Budget

Ziel: **<1.5s End-to-End** für ein natürliches Gespräch.

| Stufe | Ziel (ms) | Optimierung |
|-------|-----------|-------------|
| VAD/Silence | 300-500 | Silero VAD; maxSilenceSeconds=1.5 (einfach) |
| STT (Whisper base) | 200-400 | CPU int8, beam_size=1, kurze Äusserungen |
| LLM | 200-600 | Streaming, kleine Modelle (1-2 Sätze Antwort) |
| TTS first chunk | 200-400 | edge-tts streaming, Piper für local |
| TTS Playback | 0-300 | Überlappend mit nächstem Turn |
| **Total** | **~900-2200** | Akzeptabel für Telefonat |

## Kosten

| Setup | Kosten | Bemerkung |
|-------|--------|-----------|
| Lokal (Ollama + edge-tts) | 0 CHF | edge-tts gratis via Microsoft Edge |
| Lokal (Ollama + Piper TTS) | 0 CHF | Komplett offline, 1-2GB Modelle |
| Cloud-LLM (OpenAI/Gemini) | ~0.01-0.10 CHF/Min | Für geringste Latenz |
| Fertig-API (OpenAI Realtime) | ~0.06 CHF/Min | Alles aus einer Hand |

## Dependencies

```bash
# Phase 1 (ARI + Recording)
pip install httpx websockets openai

# Phase 2 (ExternalMedia + Barge-In)
pip install torch --index-url https://download.pytorch.org/whl/cpu  # oder CUDA
pip install silero-vad

# Optionale TTS-Fallbacks
pip install piper-tts  # lokales TTS
```

## Best Practices & Hinweise

- **Pre-load alle Modelle** beim Start (nicht pro Call)
- **Thread-Pool** für konkurrierende Inference (Semaphore-gesteuert)
- **Kurze Antworten** (1-2 Sätze, <260 chars) für natürliche Gesprächsgeschwindigkeit
- **Silence-Halluzinationen filtern** — Whisper transkribiert oft "Bye", "Uh", "Hmm" oder leere Strings bei Stille
- **LLM-Streaming nutzen** — Antwort satzweise an TTS-Pipeline übergeben
- **Hangup sauber behandeln** — StasisEnd-Event fängt auflegen ab
- **Latency tracken** — pro Turn die Phasen-Latenzen loggen

## Abgrenzung zu anderen Skills

| Skill | Fokus |
|-------|-------|
| **apollo-call** | Einweg-TTS-Ansage (kein Dialog) |
| **guten-morgen-call** | Morgendlicher Weckruf (kein Dialog) |
| **asterisk-voice-pipeline** (dieser) | Bidirektionaler Voice-Dialog mit STT→LLM→TTS |
| **asterisk-backup** | Config-Sicherung (nicht verwandt) |

## Referenzen

- `references/voice-pipeline-research.md` — 16KB Research-Doku mit Quellcode-Auszügen aus 3 Open-Source-Referenzprojekten
- GL-46: Multi-Agent-Konferenz (Dach-Ticket, blockiert durch diese Pipeline)
- GL-47: Real-Time Voice Pipeline (dieses Thema als Jira-Ticket)
- Harvix-AI-Calling: https://github.com/shyam302/Harvix-AI-Calling
- Ai-chatbot/Barbie: https://github.com/devansharora710/Ai-chatbot
- NPCL-Asterisk-ARI: https://github.com/letsdeepchat/AsteriskARI-Bot

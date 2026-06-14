# ExternalMedia RTP — Implementation Reference

## Why ExternalMedia RTP?

**Problem:** ARI Sequential RTP Loss — after the FIRST `POST /channels/{id}/play` on a PJSIP channel, all subsequent playbacks produce NO audio. Bridge and Redirect workarounds both fail (verified 20.05.2026).

**Solution:** ARI ExternalMedia application — creates a dedicated RTP stream between Asterisk and an external application (Python). The application:
- Receives raw audio frames from the call (μ-law, A-law, or linear PCM)
- Sends raw audio frames to the call (TTS output)
- Has FULL control over RTP — no sequential playback bug

This is THE approach for true full-duplex live dialog.

## Architecture

```
Caller's Phone → Salt Trunk → Asterisk PJSIP Channel
                                        │
                              ARI ExternalMedia App
                              (Python, raw RTP socket)
                                        │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                    Silero VAD    faster-whisper   edge-tts
                    (32ms frames)  (STT)          (TTS output)
                          │             │             │
                          └─────────────┼─────────────┘
                                        ▼
                                     LLM
                                  (Antwort)
```

## Asterisk Configuration

### `http.conf` — Verify enabled
```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
```

### `ari.conf` — Verify ARI user
```ini
[general]
enabled = yes

[callbot]
type = user
read_only = no
password = HermesVB2026
```

### `extensions.conf` — ExternalMedia Stasis entry
```ini
; Hermes Voice Pipeline — ExternalMedia RTP
[hermes-external-media]
exten => s,1,NoOp(Hermes ExternalMedia Pipeline)
 same => n,Stasis(hermes-pipeline)
 same => n,Hangup()
```

### `res_rtp_asterisk.conf` — ExternalMedia RTP ports (optional, default range)
```ini
[general]
; ExternalMedia uses the standard RTP port range
; Default: 10000-20000
; For high concurrency, widen:
; rtpstart=10000
; rtpend=30000
```

## ExternalMedia API Reference

### Creating an ExternalMedia channel (ARI REST API)

```http
POST /ari/channels/externalMedia
Content-Type: application/json

{
  "app": "hermes-pipeline",
  "external_host": "10.0.60.156:10000",
  "format": "ulaw",
  "data": {
    "channelId": "existing-channel-id",
    "variables": {
      "HERMES_CALLER": "Michel"
    }
  }
}
```

**Python (aiohttp):**
```python
async def create_external_media(session, external_host="10.0.60.156:10000"):
    url = f"{BASE}/ari/channels/externalMedia"
    payload = {
        "app": "hermes-pipeline",
        "external_host": external_host,
        "format": "ulaw"
    }
    async with session.post(url, json=payload) as r:
        if r.status in (200, 201):
            result = await r.json()
            return result  # Contains channel id, RTP info
```

**Response:**
```json
{
  "id": "external-media-12345",
  "state": "Up",
  "name": "ExternalMedia/10.0.60.156:10000-12345",
  "creationtime": "2026-05-20T20:00:00.000+0000",
  ...
}
```

### Key Parameters

| Parameter | Description | Value |
|-----------|-------------|-------|
| `app` | Stasis app name | `hermes-pipeline` |
| `external_host` | IP:port where Python listens | `10.0.60.156:10000` (Hermes) |
| `format` | Audio codec | `ulaw` (μ-law, 8kHz) — best for telephony |
| `data.channelId` | Optional: bridge to existing channel | Omit for pure ExternalMedia |

### Audio Format Details

- **μ-law (ulaw):** 8kHz, 8-bit, 64kbps — standard for PSTN/PJSIP
- **A-law (alaw):** 8kHz, 8-bit, 64kbps — European standard
- **SLIN (slin16):** 16kHz, 16-bit linear PCM — better for STT
- **SLIN48 (slin48):** 48kHz — high quality, larger bandwidth

**Recommendation:** Use `ulaw` for telephony (matching Salt trunk), convert to 16kHz PCM for STT.

## Python RTP Server Implementation

### Dependencies
```bash
pip install av  # PyAV for audio codec handling
pip install numpy  # Audio processing
```

### Minimal RTP Receiver (UDP socket)
```python
import socket
import av
import numpy as np

def start_rtp_listener(host="0.0.0.0", port=10000):
    """Listen for RTP μ-law frames from Asterisk ExternalMedia."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    sock.settimeout(30)  # Timeout if no audio

    # RTP buffer
    rtp_buffer = bytearray()
    
    while True:
        data, addr = sock.recvfrom(2048)  # Max RTP packet size
        
        # Parse RTP header (12 bytes minimum)
        if len(data) < 12:
            continue
            
        version = (data[0] >> 6) & 0x03
        payload_type = data[1] & 0x7F
        
        # Extract payload (skip 12-byte header + optional CSRC/extension)
        header_len = 12
        payload = data[header_len:]
        
        # μ-law frames are 8-bit samples, 160 bytes = 20ms audio
        rtp_buffer.extend(payload)
        
        # Process when we have enough audio (e.g., 400ms = 3200 bytes ulaw)
        if len(rtp_buffer) >= 3200:
            process_audio_chunk(bytes(rtp_buffer))
            rtp_buffer.clear()
```

### More robust: use PyAV for RTP
```python
import av

# PyAV handles RTP parsing, depacketization, and codec conversion
input_container = av.open("rtp://0.0.0.0:10000", format="rtp", 
                          options={"protocol_whitelist": "rtp,udp"})
```

### Sending RTP Audio back to Asterisk
```python
import socket
import struct
import time

def send_rtp_audio(sock, dest_addr, pcm_data, seq=0, ts=0, ssrc=12345):
    """Send PCM audio as μ-law RTP packets."""
    # Convert PCM16 to μ-law (if needed)
    # Asterisk expects raw μ-law frames
    
    # RTP header (12 bytes)
    version = 2
    padding = 0
    extension = 0
    csrc_count = 0
    marker = 0
    payload_type = 0  # μ-law
    
    first_byte = (version << 6) | (padding << 5) | (extension << 4) | csrc_count
    second_byte = (marker << 7) | payload_type
    
    header = struct.pack('!BBHII', first_byte, second_byte, seq, ts, ssrc)
    
    # 20ms chunks (160 bytes μ-law at 8kHz)
    chunk_size = 160
    for i in range(0, len(pcm_data), chunk_size):
        chunk = pcm_data[i:i+chunk_size]
        packet = header + chunk
        sock.sendto(packet, dest_addr)
        
        # Wait exactly 20ms (real-time pacing)
        time.sleep(0.020)
```

## Full Pipeline Integration (Event-driven)

### State Machine
```
States: IDLE | LISTENING | PROCESSING | SPEAKING

IDLE → CALL_START → LISTENING
LISTENING → (silence detected) → PROCESSING
PROCESSING → (TTS ready) → SPEAKING
SPEAKING → (speech detected / barge-in) → LISTENING
SPEAKING → (TTS done) → LISTENING (next turn)
```

### Dialog Loop
```python
async def dialog_loop(pipeline, channel_id, rtp_sock, caller_addr):
    """Full STT → LLM → TTS → playback loop."""
    
    await pipeline.play_welcome(channel_id)  # ARI Play (first = works)
    
    for turn in range(5):  # Max 5 turns
        # 1. LISTEN — collect audio via RTP
        audio_chunks = []
        silence_frames = 0
        speaking = False
        
        while True:
            frame = await recv_rtp_frame(rtp_sock, timeout=0.1)
            if frame is None:
                silence_frames += 1
                if speaking and silence_frames > 13:  # ~400ms silence
                    break  # End of speech
                continue
            
            vad_prob = silero_vad(frame)
            if vad_prob > 0.95:
                speaking = True
                silence_frames = 0
                audio_chunks.append(frame)
        
        if not audio_chunks:
            continue  # No speech detected
        
        # 2. STT
        audio_bytes = b''.join(audio_chunks)
        text = await faster_whisper.transcribe(audio_bytes)
        
        # 3. LLM
        response = await llm.generate(text)
        
        # 4. TTS → RTP
        tts_audio = await edge_tts.synthesize(response)
        
        # 5. SPEAK — send via RTP (NOT ARI Playback!)
        await send_rtp_audio(rtp_sock, caller_addr, tts_audio)
        
        # 6. Barge-in check during speaking
        # (Needs async monitor of incoming RTP for speech frames)
    
    await pipeline.play_goodbye(channel_id)
```

## VAD Integration (Silero)

```python
import torch
from silero_vad import load_silero_vad

model, utils = load_silero_vad()
(get_speech_timestamps, _, _, _, _) = utils

def vad_on_frame(raw_pcm_frame):
    """Process single 32ms frame (512 samples @ 16kHz)."""
    tensor = torch.from_numpy(np.frombuffer(raw_pcm_frame, dtype=np.int16))
    tensor = tensor.float() / 32768.0  # Normalize to [-1, 1]
    prob = model(tensor, 16000).item()
    return prob

# Thresholds (phone-call tuned):
SILENCE_THRESHOLD = 0.3
SPEECH_THRESHOLD = 0.95
BARGE_IN_FRAMES = 3       # ~100ms speech = barge-in
END_OF_SPEECH_FRAMES = 13  # ~400ms silence = end of turn
```

## Codec Conversion Roadmap

| Input | Convert to | For |
|-------|-----------|-----|
| μ-law (8kHz, 8-bit) | PCM S16LE (16kHz, 16-bit) | STT (faster-whisper) |
| PCM S16LE (24kHz) | μ-law (8kHz, 8-bit) | RTP back to call |
| edge-tts MP3 output | PCM S16LE (16kHz) | Mix with VAD processing |

**Conversion with PyAV:**
```python
import av

def ulaw_to_s16le(ulaw_data):
    """Convert μ-law 8kHz to PCM16 16kHz."""
    codec = av.CodecContext.create("pcm_mulaw", "r")
    codec.sample_rate = 8000
    codec.channels = 1
    
    packet = av.Packet(ulaw_data)
    frames = codec.decode(packet)
    
    if frames:
        # Resample to 16kHz
        frame = frames[0]
        resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000
        )
        resampled = resampler.resample(frame)
        return resampled.planes[0].to_bytes()
```

## Testing Strategy (without calling Michel)

### Internal Test via Local Channel
```bash
# Create a Local channel that enters Stasis
asterisk -rx "channel originate Local/s@hermes-external-media application Stasis hermes-pipeline"
```

This creates a channel pair:
- One side enters Stasis (ExternalMedia receives audio)
- Other side is available for ConfBridge/Playback testing

### Loopback Test
1. Start ExternalMedia app on Hermes (10.0.60.156:10000)
2. Create ExternalMedia channel via ARI
3. Play a test audio file into the RTP stream
4. Verify the app receives and processes it

### Full Integration Test (requires Michel on call)
1. `channel originate PJSIP/41796459743@salt-trunk application Stasis hermes-pipeline`
2. StasisStart fires when Michel answers
3. ExternalMedia channel is created (RTP to Hermes)
4. Welcome plays via ARI (first Playback = works)
5. Dialog loop via RTP starts (subsequent audio via RTP, not ARI)

## Known Limitations

- **ExternalMedia only supports UDP**, not TCP. Ensure firewall allows UDP on chosen port.
- **One RTP stream per ExternalMedia channel.** For multiple streams (e.g., conference), create multiple ExternalMedia channels.
- **Latency:** RTP over LAN is sub-1ms. The bottleneck is STT (~1.5s) and TTS (~0.5s), not network.
- **No built-in barge-in in ExternalMedia** — must be implemented in the Python app via VAD on incoming RTP frames.
- **ExternalMedia channel does NOT support ARI Playback** — use direct RTP send for audio out.
- **Format mismatch:** If Salt trunk uses μ-law but ExternalMedia is configured for SLIN, the audio will be garbled. Always match the codec.

## References

- [Asterisk ExternalMedia Documentation](https://wiki.asterisk.org/wiki/display/AST/Asterisk+18+ExternalMedia)
- [Ai-chatbot/Barbie — RTP implementation reference](https://github.com/devansharora710/Ai-chatbot)
- [Asterisk RTP Port Configuration](https://wiki.asterisk.org/wiki/display/AST/Asterisk+RTP+Configuration)
- [Harvix-AI-Calling — ARI stasis loop with RTP](https://github.com/harvix-ai/Harvix-AI-Calling)

# Live Voice Pipeline Session — 20.05.2026 (Evening)

## Breakthrough: ExternalMedia RTP Input WORKS!

**Milestone:** First successful live capture of Michel's voice via Asterisk ExternalMedia RTP.
Pipeline ran continuously for 800+ VAD loops, Michel spoke, STT transcribed "Hallo Hallo..." and "Hast du mich gehört jetzt? Ich denke nicht."

## Architecture Evolution

### v1: Bridge+Record Pipeline (FAILED)
- Used `POST /channels/{id}/record` for input
- ❌ "Cannot record channel while in bridge" — ARI doesn't allow recording bridged channels
- Workaround: Remove channel from bridge → record → add back → play
- Clunky, breaks natural dialog flow

### v2: ExternalMedia RTP Input + Bridge Playback Output (CURRENT ✅)
- **Input:** `POST /channels/externalMedia` → μ-law RTP stream → Python UDP socket on port 9001
- **Output:** Bridge playback `POST /bridges/{id}/play` (verified working for sequential audio)
- **VAD:** Simple RMS-based threshold on incoming PCM chunks
- **STT:** faster-whisper tiny on the accumulated speech buffer
- **TTS:** gTTS proxy on Hermes (10.0.60.156:8765) when edge-tts is down

## Session Log

### Component Verification

| Component | Status | Evidence |
|-----------|--------|----------|
| ARI POST /channels | ✅ HTTP 200/201 | Channel created, StasisStart fires on answer |
| ExternalMedia creation | ✅ HTTP 200/201 | Channel created, added to bridge |
| RTP reception | ✅ 1500+ packets | Michel's audio received as μ-law via UDP :9001 |
| Bridge Playback | ✅ Welcome+Beep played | Michel confirmed hearing hello-world |
| VAD speech detection | ✅ Loops 93-785 | Detected speech_start, accumulated 519 chunks |
| VAD speech accumulation | ✅ 96800B (12s) | speech_buffer captured actual audio |
| STT | ✅ 1st run | Transcribed "Hallo, Hallo, Hallo, Hallo und Ciao, Ruhe." |
| STT | ⚠️ 2nd run empty | False VAD on noise → 96800B noise → empty transcription |
| TTS (edge-tts) | ❌ Microsoft outage | "No audio was received" — global server issue |
| TTS (gTTS proxy) | ✅ 53838B WAV | Google TTS via Hermes API, ffmpeg to 8kHz WAV |
| Dialog Loop | ✅ Continuous | Runs up to 10 turns, re-listens after each turn |

### Bug Fixes Applied

1. **Endpoint format:** `PJSIP/+41...@salt-trunk` (not `PJSIP/salt-trunk` + extension)
2. **Number format:** `+41` (not `++41`) for Swiss E.164
3. **HTTP status:** Accept 200 AND 201 for POST /channels
4. **ExternalMedia StasisStart:** Don't wait for it — channels enter app immediately
5. **State scoping:** `class State` mutable singleton to avoid Python UnboundLocalError on cross-function assignments
6. **VAD during playback:** `currently_playing` flag prevents VAD from detecting our own TTS as "speech"
7. **Speech accumulation:** Separate `speech_buffer` from `rtp_buffer` — don't drain RTP buffer during every VAD loop iteration

### Remaining Issues

1. **VAD threshold too sensitive** — triggered on bridge noise/silence during 2nd call
2. **gTTS quality** — slower than edge-tts, different voice
3. **No LLM response** — currently echoes user text back, no real conversation
4. **Barge-in** — VAD checks for energy during playback but `POST /playbacks/{id}` delete for interrupt not fully tested
5. **Cleanup** — pipeline doesn't always clean up bridges/hangup on error

### Key Commands Used

```bash
# Deploy pipeline to Nova
sshpass -p 'Louis_one_13' scp /tmp/hermes_live_pipeline.py root@10.0.60.167:/usr/local/bin/

# Start
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 "nohup python3 /usr/local/bin/hermes_live_pipeline.py > /var/log/hermes_live.log 2>&1 & echo PID=\$!"

# Check log (wait 15s for call setup + speech)
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 "cat /var/log/hermes_live.log"

# Kill
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 "pkill -f hermes_live_pipeline"

# Clean bridges
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 "bash /tmp/cleanup_pipeline.sh"

# TTS API server (on Hermes)
python3 /tmp/tts_api_server.py
```

### ExternalMedia RTP Details

**Creation:**
```python
r = requests.post("http://127.0.0.1:8088/ari/channels/externalMedia",
    params={"app": "hermes-pipeline",
            "external_host": "127.0.0.1:9001",
            "format": "ulaw"},
    auth=("henryari", "HermesVB2026"))
```

**RTP Listener (Python raw UDP):**
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
sock.bind(("0.0.0.0", 9001))
sock.settimeout(0.5)

# Each packet: 12B RTP header + 160B μ-law payload (20ms @ 8kHz)
while running:
    try:
        data, addr = sock.recvfrom(2048)
        if len(data) > 12:
            ulaw_frame = data[12:]  # strip RTP header
            with rtp_lock:
                rtp_buffer.append(ulaw_frame)
    except socket.timeout:
        pass
```

**VAD Processing (loop):**
```python
# Take 1 chunk (160B = 20ms) per loop iteration
chunk = rtp_buffer.pop(0)
pcm = audioop.ulaw2lin(chunk, 2)  # 160B → 320B PCM

result = vad.detect(pcm)

if result == 'speech_start':
    # Start accumulating into speech_buffer
    speech_buffer.clear()
    speech_buffer.extend(rtp_buffer); rtp_buffer.clear()
    speech_buffer.append(chunk)
    
elif result == 'in_speech':
    speech_buffer.append(chunk)
    
elif result == 'speech_end':
    speech_ulaw = b"".join(speech_buffer)
    # Process with STT...
```

### gTTS API Server (Hermes-side)

```python
# On Hermes (10.0.60.156), port 8765
class TTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = json.loads(self.rfile.read())
        text = data["text"]
        
        # gTTS → MP3 → ffmpeg → 8kHz WAV
        tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3")
        tts = gTTS(text, lang="de", slow=False)
        tts.save(tmp_mp3.name)
        
        tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav")
        subprocess.run(["ffmpeg", "-y", "-i", tmp_mp3.name,
                       "-ar", "8000", "-ac", "1", "-sample_fmt", "s16",
                       tmp_wav.name], capture_output=True)
        
        # Return WAV binary
        with open(tmp_wav.name, "rb") as f:
            self.wfile.write(f.read())
```

## User Communication

- Michel was excited: "OMG du hast mich wirklich gehört!" but noted "Begrüßung und Antwort geht noch nicht"
- He explicitly rejected "Voicemail-style" recording: "Livestream, nicht eine Voice-Mail Recording"
- Confirmed hearing hello-world + beep in bridge playback test
- Was frustrated by false VAD -> silence -> wait -> hangup

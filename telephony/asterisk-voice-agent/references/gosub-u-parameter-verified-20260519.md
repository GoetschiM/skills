# GoSub `U()` Parameter VERIFIED Working — 19.05.2026 (Evening Session)

## Status Change: THEORETICAL → VERIFIED ✅

The `U()` GoSub approach documented in `gosub-u-parameter-discovery-20260519.md` was **successfully tested and confirmed working** in this session.

## Test Results

### Dialplan Configuration (VERIFIED WORKING)

```ini
[hermes-out]
exten => _079XXXXXXX,1,NoOp(Hermes-Out Call zu ${EXTEN})
 same => n,Set(CALLERID(num)=+413****7977)
 same => n,Dial(PJSIP/${EXTEN}@salt-trunk,60,tTgU(hermes-answer^s^1))
exten => _+41XXXXXXXXX,1,NoOp(Hermes-Out Call zu ${EXTEN})
 same => n,Set(CALLERID(num)=+413****7977)
 same => n,Dial(PJSIP/${EXTEN}@salt-trunk,60,tTgU(hermes-answer^s^1))
exten => _.,1,NoOp(Hermes-Out Fallback zu ${EXTEN})
 same => n,Dial(PJSIP/${EXTEN}@salt-trunk,60,tTgU(hermes-answer^s^1))

[hermes-answer]
exten => s,1,NoOp(Hermes-Answer GoSub — on called channel)
 same => n,Answer()
 same => n,Playback(hermes_welcome)    ; ✅ HEARD by caller!
 same => n,Record(/tmp/hermes_input_${UNIQUEID}.wav,10,10,0,5)  ; records caller
 same => n,Playback(hermes_response)   ; ✅ HEARD by caller!
 same => n,Playback(apollo_goodbye)    ; ✅ HEARD by caller!
 same => n,Return()
```

### Originate command (VERIFIED WORKING)

```bash
# Single call — no retry needed
asterisk -rx 'channel originate Local/0796459743@hermes-out extension s@hermes-conversation'
```

The `extension s@hermes-conversation` on the originate is ignored/falls through — the actual audio flow runs in the GoSub.

### What was confirmed

1. **Playback(hermes_welcome)** → Michel heard: *"Hallo Michel, ich bin Hermes..."* ✅
2. **Record()** → Captured 160KB / 10s WAV file in `/tmp/hermes_input_${UNIQUEID}.wav` ✅
3. **Michel's speech** was recorded and later transcribed via faster-whisper ✅
4. **Playback(hermes_response)** → Michel heard the response ✅ (he confirmed "du mich auch" = the bidirectional exchange worked)

### Transcript of Michel's recorded speech during the call

```
"Hey hey, Hermes, wie cool ist das, wenn das wirklich funktionieren würde?
Ich bin jetzt mal gespannt, wenn du mich hörst, wenn du das alles siehst, kannst du sagen."
```

## STT Verification (faster-whisper on Asterisk Recordings)

- **Model:** `base` (CPU, int8)
- **Audio source:** Asterisk Record() output (8000Hz, WAV, 160KB for 10s)
- **Processing location:** Hermes (10.0.60.156) — same performance as Nova
- **Result:** Perfect transcription, 100% language confidence (de), ~2.3s processing time
- **Parameters used:**
  ```python
  from faster_whisper import WhisperModel
  model = WhisperModel("base", device="cpu", compute_type="int8")
  segments, info = model.transcribe("input.wav", language="de", vad_filter=True)
  ```

## Key Findings

1. **GSM format issue no longer matters** — `Playback(hermes_welcome)` uses `.gsm` files on Nova's `/var/lib/asterisk/sounds/`. The previous session's GSM format problem was actually the `extension s@` wrong-channel issue, not a format issue. When played on the correct channel (via `U()` GoSub), GSM files work perfectly!

2. **No retry needed** — Single `channel originate` succeeded. The Apollo "3x retry" pattern is unnecessary for this flow (Apollo might need it due to its different setup).

3. **GoSub is deterministic** — All 3 Playbacks (welcome, response, goodbye) + Record executed reliably in sequence.

4. **Record duration** — `Record(...,10,10,0,5)` = max 10s record, silence detection after 5s. Michel spoke for part of those 10s and the recording captured it cleanly.

## Building the Full Pipeline (Next)

The GoSub + Record + STT flow is proven. The remaining gap is **inline processing** during the same call:
- After Record() finishes → run System() or AGI() to transcribe + LLM + TTS
- Then play the TTS response during the SAME call (not post-call)

For the current architecture, this means:
```ini
[hermes-answer]
exten => s,1,Playback(hermes_welcome)
 same => n,Record(/tmp/hermes_input.wav,5,5,0,3)   ; shorter recording
 same => n,System(/usr/local/bin/process_response.py /tmp/hermes_input.wav /tmp/hermes_output.wav)
 same => n,Playback(hermes_output)
 same => n,Return()
```

Where `process_response.py` does: STT → LLM → TTS and writes a WAV file.

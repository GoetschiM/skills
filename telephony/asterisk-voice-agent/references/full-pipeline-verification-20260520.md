# ExternalMedia + Bridge Playback Full Pipeline Verification

**Date:** 2026-05-20
**Test:** First complete live dialog: Welcome → Listen → STT → LLM → TTS → Bridge Playback
**Result:** ✅ SUCCESS — Michel heard and responded

## Verified Flow

```
1. POST /ari/channels → StasisStart ✅
2. POST /ari/bridges → bridge created ✅
3. POST /ari/bridges/{id}/addChannel (Michel's channel) → 204 ✅
4. POST /ari/channels/externalMedia (port 9001, ulaw) → HTTP 200 ✅
5. POST /ari/bridges/{id}/addChannel (ExternalMedia) → 204 ✅
6. UDP listener on 9001 receives μ-law RTP → 1500+ packets ✅
7. POST /ari/bridges/{id}/play (hello-world) → Michel heard welcome ✅
8. 1s RTP buffer flush (after welcome, drop bridge echo) ✅
9. VAD detects Michel speaking → speech buffer (16320B / ~2s) ✅
10. SPTS: "Ich freue, da kommt mir immer das Hello World, du hörst nicht."
11. LLM generates response (hardcoded placeholder) ✅
12. POST http://10.0.60.156:8765 (gTTS proxy) → 154KB WAV ✅
13. Copy WAV to Asterisk sounds/ dir ✅
14. POST /ari/bridges/{id}/play (TTS sound) → Michel heard response ✅
15. Call ended by user after successful turn ✅
```

## Issues Encountered & Resolved

### Issue 1: ARI Record "Cannot record channel while in bridge"
- `POST /channels/{id}/record` fails with this error when channel is in a bridge
- **Fix:** Use ExternalMedia RTP for input capture instead

### Issue 2: VAD triggers on bridge echo
- After welcome playback, bridge still carries residual audio
- ExternalMedia in bridge receives everything — including our own playback
- **Fix:** 1-second RTP buffer flush after welcome + `currently_playing` flag to skip VAD during playback

### Issue 3: edge-tts Microsoft server outage 2026-05-20
- Microsoft returned "Our services aren't available right now"
- **Fix:** gTTS proxy on Hermes (port 8765) as fallback

### Issue 4: VAD threshold tuning
- threshold=300: triggered on background noise → empty STT
- threshold=500: worked correctly for Michel's voice level
- min_speech_ms=500: avoid false positives from short noise bursts
- min_silence_ms=1500: enough gap between turns but not too long

### Issue 5: Endpoint format for ARI call
- `PJSIP/+41796459743@salt-trunk` (NUMBER@TRUNK) ✅
- `PJSIP/salt-trunk` with separate `extension=` ❌ (no StasisStart)

## Test Transcript

- **Michel:** "Hallo, Hallo, Hallo, Hallo, Hallo, Hallo und Ciao, Ruhe."
- **Michel:** "Hast du mich gehört jetzt? Ich denke nicht."
- **Michel:** "Ich freue, da kommt mir immer das Hello World, du hörst nicht."
- **Hermes:** (gTTS) "Du hesch gseit: « Ich freue, da kommt mir immer das Hello World, du hörst nicht.» Das isch mega spannend! Verzell mir meh."
- **Michel:** [hung up after hearing response]

## State Machine Pattern

```python
class State:
    pass

S = State()
S.mic_speaking = False
S.currently_playing = False
S.processing = False
S.interrupt = False
S.running = True
```

Used instead of global variables to avoid Python scoping issues in cross-thread code.

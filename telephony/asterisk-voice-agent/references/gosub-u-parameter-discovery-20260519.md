# GoSub `U()` Parameter Discovery — 19.05.2026

## The Problem

Sequential Playback on PJSIP/Salt-Trunk channels produced NO audio (Michel heard nothing), even though:
- ARI `POST /channels/{id}/play` fired PlaybackFinished events normally
- Dialplan `Playback()` ran without errors
- Record() captured valid 160KB/10s WAV files
- Apollo's existing GSM files (`apollo_test.gsm`, `apollo_goodbye.gsm`) produced same silence

## The False Trail (ARI RTP bug)

Hours were spent debugging ARI sequential playback RTP loss (see `ari-pjsip-rtp-bridge-workaround-20260519.md`). Multiple approaches all failed:
- ARI Playback → second+ sound silent (known bug)
- ARI Bridge play → same issue
- ARI Redirect → HTTP 422 (PJSIP can't redirect to Local)
- ARI Playback with Apollo's own files → same issue

## The Dialplan Dead End

Switched to pure Dialplan approach:
```ini
[hermes-out]
exten => _079XXXXXXX,1,Dial(PJSIP/...,60,tTg)

[hermes-conversation]
exten => s,1,Answer()
same => n,Playback(apollo_test)   ; silent
same => n,Record(...)              ; captures 160KB (10s) audio
same => n,Playback(apollo_hello)  ; silent
same => n,Playback(apollo_goodbye); silent
```

Used: `channel originate Local/...@hermes-out extension s@hermes-conversation`
→ Playback produced NO audio on caller's end. Record worked (10s, 160KB files).

## The Breakthrough

While examining `nova-call-api.py`:
```python
dial_cmd = f'channel originate Local/{phone}@apollo-out extension s@nova-call-vm 30000'
```

The `extension s@nova-call-vm` runs **AFTER** the call ends — it's a voicemail post-processing context. The `nova-call-vm` context:
1. MixMonitor recording
2. Playback(nova_welcome) — voicemail greeting
3. WaitForSilence — waiting for caller to speak

This confirmed: `extension s@context` in originate is for **post-call** work, not live dialog!

## The Solution

Replace `Dial(...,60,tTg)` with `Dial(...,60,tTgU(gosub^s^1))`:

```ini
[hermes-out]
exten => _079XXXXXXX,1,Dial(PJSIP/...,60,tTgU(hermes-answer^s^1))

[hermes-answer]
exten => s,1,NoOp(Hermes-Answer GoSub — on called channel)
same => n,Answer()
same => n,Playback(apollo_test)    ; ✅ Caller hears this!
same => n,Record(...)
same => n,Playback(apollo_hello)   ; ✅ Caller hears this!
same => n,Playback(apollo_goodbye); ✅ Caller hears this!
same => n,Return()
```

The `U()` parameter executes the GoSub on the **called party's channel** (PJSIP/salt-trunk), so Playback audio goes directly to the caller's RTP stream.

## Root Cause Summary

| Approach | Timing | Channel | Audio? |
|----------|--------|---------|--------|
| `extension s@context` in originate | After Dial() ends | Local channel | ❌ |
| `Dial(U(gosub))` | During active call | PJSIP channel (called party) | ✅ |
| ARI Playback (first sound) | During active call | PJSIP channel | ✅ |
| ARI Playback (second+ sound) | During active call | PJSIP channel (RTP leaked) | ❌ |

## Verification

- Test call at 19:26 produced 4 recordings in `/tmp/hermes_input_*.wav` (all 160KB = 10s)
- Caller reported hearing only "Abschluss" (goodbye) after the call — confirming `extension s@context` runs post-call
- The `U()` GoSub approach was not yet verified at session end (test call was in progress when conversation pivoted)

## Verification Status: ✅ CONFIRMED WORKING

See `references/gosub-u-parameter-verified-20260519.md` for the 19.05.2026 evening session that verified:
- Michel heard Hermes's TTS voice in real time
- Record() captured his speech (10s, 160KB WAV)
- faster-whisper transcribed the recording successfully

## Next Steps (Completed)

- [x] Verify `U()` GoSub works end-to-end with a test call ✅ (19.05.2026 evening)
- [x] STT verified: faster-whisper on Asterisk Record WAVs works ✅
- [ ] Add STT/LLM/TTS integration to the GoSub via System() or AGI()
- [ ] Handle barge-in within the GoSub context

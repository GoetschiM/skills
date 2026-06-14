# ARI/PJSIP RTP Sequential Playback Bug — Session 2026-05-19

## Summary
Discovered that ARI `POST /channels/{id}/play` on PJSIP/Salt trunk channels
loses RTP after the FIRST sound. All subsequent playbacks produce zero audio
(no RTP frames reach the far end) even though Asterisk reports PlaybackStarted
and PlaybackFinished events normally.

## Verification
Test callbot v5 played 4 sounds sequentially:
1. `sound:tt-weasels` (standard GSM) → **Caller heard it** ✅
2. `sound:hermes_welcome` (custom GSM/alaw/ulaw/WAV) → **Silent** ❌
3. `sound:apollo_goodbye` (known working GSM) → **Silent** ❌
4. `sound:apollo_test` (GSM, attempted 4th) → **HTTP 404** (channel dead)

Only sound #1 produced audible audio to the caller. Sounds #2-3 fired
PlaybackFinished events but no RTP audio. By sound #4, the PJSIP channel
was already destroyed by Salt (30s RTP timeout).

## Root Cause
When ARI plays media on a PJSIP channel in Stasis, Asterisk opens a
temporary RTP media stream specifically for the playback. After the
playback completes, the stream is closed. When a second playback request
is made, Asterisk fails to re-establish the RTP stream — the Playback is
"successful" from Asterisk's perspective (file read, frame decode, internal
processing) but no RTP frames are sent to the PJSIP endpoint.

This is a known limitation of ARI + PJSIP Stasis channel media handling.
The channel owner (Stasis app) is expected to manage its own RTP, but the
ARI Playback API acts as a one-shot injector that doesn't leave the RTP
pipeline open for reuse.

## Attempted Workaround 1 — Bridge-Based Playback ❌ (FAILS for Salt PJSIP)
Instead of playing on the channel directly, add the channel to a mixing
bridge and play sounds via the bridge:

```python
bridge = await ari("POST", "/bridges", {"type": "mixing", "name": "hold-bridge"})
await ari("POST", f"/bridges/{bridge['id']}/addChannel", {"channel": cid})
await ari("POST", f"/bridges/{bridge['id']}/play", {"media": "sound:first"})  # ✅ works
await ari("POST", f"/bridges/{bridge['id']}/play", {"media": "sound:second"}) # ❌ SILENT
```

**Status: FAILS the same way as direct channel.** First sound plays, second+
sounds produce no audio. RTP still drops after the first bridge playback.
Tested with `ari_bridge_test.py` — caller heard only apollo_goodbye, not
the second hermes_welcome. Log showed both PlaybackFinished events.

## Attempted Workaround 2 — Dialplan Redirect 🏗️ (CURRENTLY BEING TESTED)
Instead of ARI Playback, redirect the channel to a Dialplan context that
plays the sound via regular Asterisk Playback(), then returns to Stasis:

### Dialplan (`extensions.conf`)
```ini
; === Dialplan Playback (RTP-safe via redirect) ===
[hermes-autoplay]
; STATE = 1 (welcome), 2 (response), 3 (goodbye)
exten => _X!,1,Verbose(2,Hermes autoplay stage ${STATE})
same => n,GotoIf($["${STATE}" = "1"]?welcome)
same => n,GotoIf($["${STATE}" = "2"]?response)
same => n,Goto(goodbye)
same => n(welcome),Set(SOUND_FILE=hermes_welcome)
same => n,GoTo(play)
same => n(response),Set(SOUND_FILE=hermes_response)
same => n,GoTo(play)
same => n(goodbye),Set(SOUND_FILE=apollo_goodbye)
same => n(play),NoOp(Playing ${SOUND_FILE})
same => n,Playback(${SOUND_FILE})
same => n,Stasis(callbot)
```

### ARI Python (redirects instead of play)
```python
# Set channel variable STATE to control which sound plays
await ari("POST", f"/channels/{cid}/variable",
          {"variable": "STATE", "value": "1"})

# Redirect to dialplan — the channel leaves Stasis, plays, returns
result = await ari("POST", f"/channels/{cid}/redirect",
                   {"endpoint": "Local/playback@hermes-autoplay"})

# Wait for Stasis re-entry (StasisStart event fires)
await stasis_reentry.wait(timeout=30)
```

### Why it might work
Dialplan Playback() is the standard Asterisk media operation — it opens and
reuses the RTP stream through Asterisk's established bridge/channel path,
not through ARI's temporary injector. Redirect creates a Local channel pair
that bridges the PJSIP channel to the dialplan, keeping RTP alive.

**⚠️ Not yet verified** — being tested in `ari_callbot_v6.py`.

## Known Limitation
As of this writing (2026-05-19), **NO workaround has been found** that
reliably produces audibile audio for sequential playbacks on PJSIP/Salt
trunk via ARI. The root cause is deeper in Asterisk's PJSIP media handling
— the temporary RTP stream opened by the first Playback closes after the
playback and cannot be reopened for subsequent Playbacks, whether via
direct channel, bridge, or any other ARI media operation.

## Scripts (chronological evolution v1→v6)
- `/usr/local/bin/ari_callbot_v2.py` — Basic proof-of-concept (sleep-based)
- `/usr/local/bin/ari_callbot_v3.py` — TTS + recording via fixed sleep()
- `/usr/local/bin/ari_callbot_v4.py` — **Event-driven** (async PlaybackFinished/RecordingFinished)
- `/usr/local/bin/ari_callbot_v5.py` — Debug variant (standard sound first to isolate PJSIP audio)
- `/usr/local/bin/ari_test_simple.py` — 4-sound sequential playback test (no recording)
- `/usr/local/bin/ari_bridge_test.py` — Bridge-based playback test (FAILED on Salt)
- `/usr/local/bin/ari_callbot_v6.py` — **Dialplan redirect approach** (under test)

# Hermes-Autoplay Dialplan Context — 2026-05-19

## Purpose
RTP-safe playback on PJSIP/Salt trunk channels. Instead of ARI
`POST /channels/{id}/play` (which loses RTP after the first sound),
redirect the channel to this dialplan context which uses Asterisk's
native `Playback()` — then returns to `Stasis(callbot)`.

## Required Extension in `/etc/asterisk/extensions.conf`

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

## Usage from ARI Python

```python
# 1. Set STATE variable to control which sound plays
await ari("POST", f"/channels/{cid}/variable",
          {"variable": "STATE", "value": "1"})

# 2. Redirect channel to dialplan
# Channel leaves Stasis, enters dialplan, plays sound, returns via Stasis()
await ari("POST", f"/channels/{cid}/redirect",
          {"endpoint": "Local/playback@hermes-autoplay"})

# 3. Wait for channel to re-enter Stasis
# StasisStart event fires with the same channel ID
await stasis_start_event.wait(timeout=30)
```

## State Machine

| STATE | Sound | Action |
|-------|-------|--------|
| 1 | hermes_welcome | Greeting |
| 2 | hermes_response | Response after recording |
| 3 | apollo_goodbye | Farewell |

## Status
- **2026-05-19:** First version deployed to Nova. Under test.
- The redirect creates a Local channel pair bridging the PJSIP channel
  to the dialplan, then returns via `Stasis(callbot)`. This is the
  standard Asterisk media path (not ARI's temporary injector), which
  should keep RTP alive across sequential playbacks.

# Hermes Outbound Dialplan Calls — Working Pattern ✅

**Date:** 2026-05-19  
**Purpose:** Verified pattern for dialplan-based outbound calls to Michel via Salt trunk

## Core Finding

ARI `POST /channels/{id}/play` has a fatal bug on PJSIP channels: **only the first playback produces audio**. All subsequent playbacks fire events but send no RTP audio. No ARI workaround exists (bridge play, redirect all fail).

**Solution:** Use pure Dialplan-based outbound calls via `channel originate`.

## Dialplan Contexts Created

### `[hermes-out]` — Outbound Dial
```ini
[hermes-out]
exten => _079XXXXXXX,1,NoOp(Hermes-Out Call zu ${EXTEN})
same => n,Set(CALLERID(num)=+413****7977)
same => n,Dial(PJSIP/${EXTEN}@salt-trunk,60,tTg)
exten => _+41XXXXXXXXX,1,NoOp(Hermes-Out Call zu ${EXTEN})
same => n,Set(CALLERID(num)=+413****7977)
same => n,Dial(PJSIP/${EXTEN}@salt-trunk,60,tTg)
exten => _.,1,NoOp(Hermes-Out Fallback zu ${EXTEN})
same => n,Dial(PJSIP/${EXTEN}@salt-trunk,60,tTg)
```

### `[hermes-conversation]` — Post-Answer Flow
```ini
[hermes-conversation]
exten => s,1,NoOp(Hermes Conversation Start)
same => n,Answer()
same => n,Playback(hermes_welcome)
same => n,Record(/tmp/hermes_input_${UNIQUEID}.wav,10,10,0,5)
same => n,Playback(hermes_response)
same => n,Playback(apollo_goodbye)
same => n,Wait(1)
same => n,Hangup()
```

## Verified Behaviour

1. **Call connects** ✅ — via `channel originate Local/079...@hermes-out extension s@hermes-conversation`
2. **Welcome plays via Playback() in dialplan** ✅ — dialplan Playback correctly maintains RTP (unlike ARI Playback)
3. **Recording via Record() starts** ✅ — confirmed by `core show channels` showing Record application
4. **Recording files are saved** ✅ — `/tmp/hermes_input_{UNIQUEID}.wav` created with correct duration
5. **3x retry pattern** ✅ — first originate often fails (NO ANSWER), concurrent 2nd/3rd succeed

## Next Steps

To add STT/LLM/TTS between Record and Playback(response):
- Option A: `System()` app → runs script that processes recording, generates TTS, copies sound file
- Option B: `AGI()` → connects to external Python FastAGI server for stateful conversation
- Option C: `WaitExten()` → pauses dialplan, external process handles logic, then `Goto()` continues

## Dead Ends

| Approach | Result |
|----------|--------|
| ARI POST /channels/{id}/play | ❌ First play OK, second+ silent |
| ARI POST /bridges/{bridgeId}/play | ❌ Same as above |
| ARI POST /channels/{id}/redirect (to Local) | ❌ HTTP 422: "Endpoint technology 'Local' does not match channel technology 'PJSIP'" |
| Dialplan redirect (v6) | ❌ Redirect fails on PJSIP channels |
| ARI test_simple (sequential play) | ❌ Channel gets 404 after 3 plays |

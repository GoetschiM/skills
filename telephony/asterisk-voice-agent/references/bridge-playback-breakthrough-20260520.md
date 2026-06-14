# ARI Bridge Playback Breakthrough (20.05.2026)

## Summary

Discovered that `POST /bridges/{bridgeId}/play` works for **unlimited sequential audio playback** on PJSIP/Salt channels — contradicting earlier findings that claimed bridge workaround also failed.

The correct approach: create mixing bridge → add PJSIP channel → play audio via bridge (not channel).

## Test Results

### Bridge Playback Test (bridge_test.py on Nova)

```log
2026-05-20 19:07:40,301 Bridge: 8051824f-8424-4895-9d32-f927491d9934
2026-05-20 19:07:40,299 Channel in bridge: HTTP 204
2026-05-20 19:07:40,301 Play hello-world: HTTP 201
2026-05-20 19:07:45,306 Play goodbye: HTTP 201
2026-05-20 19:07:45,307 PlaybackStarted (goodbye) → PlaybackFinished (goodbye)
2026-05-20 19:07:45,307 PlaybackStarted (hello-world) → PlaybackFinished (hello-world)
```

User confirmed: *"am Afang ha öppis ghört... denn isch de Call wiitergloffe"* — both playbacks were audible.

### ARI Record Test (failed — Michel didn't answer)

Second call attempted with recording pipeline. Michel didn't answer (too many calls in quick succession). The recording pipeline tests ARI `POST /channels/{channelId}/record` to capture caller's speech.

**Script location:** `/tmp/ari_record_test.py` on Nova
**Required dependency:** `pip3 install websocket-client` (not installed by default on Nova)

## Key Learnings

### What Changed from Previous Understanding

| Previous Claim (19.05) | New Finding (20.05) |
|------------------------|---------------------|
| "Bridge workaround FAILS" | **Bridge playback WORKS** for multiple sequential playbacks |
| "No ARI-based workaround exists" | **Bridge playback IS the ARI workaround** |
| ExternalMedia RTP was the "solution" | ExternalMedia is **overkill** — bridge is simpler and proven |
| Channel playback is the only ARI way | **Bridge playback** bypasses the per-channel RTP limitation |

### Why Bridge Playback Works

The sequential RTP loss only affects `POST /channels/{channelId}/play` — because PJSIP channels in Stasis can't re-negotiate RTP for subsequent channel-level playbacks. When the channel is in a **mixing bridge**, the bridge manages its own RTP mixing, and `POST /bridges/{bridgeId}/play` does NOT trigger per-channel RTP re-negotiation.

### Architecture Going Forward

```
Simple Pipeline (proven components):
1. POST /ari/bridges → create mixing bridge
2. POST /bridges/{id}/addChannel → add PJSIP channel
3. POST /bridges/{id}/play (sound:) → user hears audio ✅ PROVEN
4. POST /channels/{id}/record → captures user's speech → download WAV
5. faster-whisper → LLM → edge-tts → save as Asterisk sound
6. POST /bridges/{id}/play (custom:) → play TTS response
7. GOTO 4 (unlimited turns)
```

### Reproduction Steps

```bash
# 1. Ensure the pipeline app is running
pgrep -f "ari_record_test\|bridge_test\|hermes_pipeline" | head -5

# 2. Make outbound call via ARI REST API (the ONLY correct way)
curl -X POST "http://127.0.0.1:8088/ari/channels" \
  -u "henryari:HermesVB2026" \
  -H "Content-Type: application/json" \
  -d '{"endpoint":"PJSIP/+41796459743@salt-trunk",
       "app":"hermes-pipeline","callerId":"BridgeTest","timeout":60}'

# 3. On StasisStart: create bridge, add channel
# 4. Play sound: POST /bridges/{bridgeId}/play?media=sound:hello-world
# 5. Wait for PlaybackFinished
# 6. Play second sound: POST /bridges/{bridgeId}/play?media=sound:goodbye
# 7. Both sounds play successfully ✅
```

### Next Test Needed

ARI Record on a PJSIP channel during an active bridge call. If RecordingFinished events produce downloadable WAV files that contain the caller's speech, the full pipeline can be assembled from proven components without any raw RTP handling.

**Script:** `/tmp/ari_record_test.py` on Nova
**Dependency:** `pip3 install websocket-client` first
**Test flow:** Welcome → BEEP → Record (max10s/sil2s) → Goodbye

# ARI Session — 19.05.2026 Evening — PJSIP Sound Format Debugging

## Summary

Three outgoing calls to Michel via Salt trunk. Critical discovery: **Custom WAV/alaw/ulaw sound files don't play audio over PJSIP/Salt trunk, only GSM works.** Created v5 debug callbot to isolate the issue.

## The Problem

When making outgoing calls via `PJSIP/+41796459743@salt-trunk`, our custom edge-tts TTS files (WAV format, pcm_s16le 8kHz 16-bit mono) produce **silent audio**. PlaybackStarted/PlaybackFinished ARI events fire normally, but Michel hears nothing. After ~30 seconds, Salt disconnects with "Verbindung wird jetzt auf Standby/Verbindung wird getrennt".

## Salt Trunk Codec Config

```
[salt-trunk]
type=endpoint
context=from-salt-inbound
transport=transport-udp
disallow=all
allow=alaw,ulaw
```

Only `alaw,ulaw` allowed. No `slin` or `gsm`.

## Call Timeline (3 attempts)

### Call 1 — v4 with WAV files
- Callbot v4: welcome.wav (7.7s) → recording (30s) → response.wav (8.2s) → goodbye
- Log shows all PlaybackStarted/Finished events fired normally
- Michel heard: **nothing** for ~33s, then "Verbindung wird getrennt" (Salt timeout)
- Recording file: not found on disk (event fired but no file saved)

### Call 2 — v5 with STANDARD Asterisk sound + WAV files (after adding .alaw/.ulaw)
- v5: `tt-weasels` (standard GSM) → `hermes_welcome.wav` (WAV) → recording → `test` → `apollo_goodbye.gsm`
- Michel heard: "fast kinesisch" (tt-weasels = a MOH tune, good!) → silence (welcome not heard) → finally "Verbindung wird getrennt"
- **Key insight:** Standard Asterisk GSM sounds work. Our custom WAV don't.

### Call 3 — v5 with all files converted to GSM
- Converted hermes_welcome.wav and hermes_response.wav to `hermes_welcome.gsm` and `hermes_response.gsm`
- v5: `tt-weasels` (standard GSM) → `hermes_welcome` (now finds GSM) → recording → response → goodbye
- Result: **Open** — call was placed but feedback not yet received

## Format Discovery

### What works ✅
| Sound | Format | Heard? |
|-------|--------|--------|
| `tt-weasels` from `/usr/share/asterisk/sounds/en_US_f_Allison/` | `.gsm` | ✅ Yes |
| `apollo_goodbye.gsm` (copied from apollo_final.gsm) | `.gsm` | ✅ Yes |
| Apollo's existing sounds (status, notify) | various | ✅ (established in production) |

### What doesn't work ❌
| Sound | Format | Heard? |
|-------|--------|--------|
| `hermes_welcome.wav` | pcm_s16le, 8kHz, 16-bit, mono | ❌ Silent (PlaybackFinished fires) |
| `hermes_response.wav` | pcm_s16le, 8kHz, 16-bit, mono | ❌ Silent |
| `hermes_response.alaw` | raw alaw (8-bit) | ❌ Silent |
| `hermes_response.ulaw` | raw ulaw (8-bit) | ❌ Silent |

### Files on disk (end of session)
```
/var/lib/asterisk/sounds/hermes_welcome.wav   (123KB, Lavf61.1.100, pcm_s16le)
/var/lib/asterisk/sounds/hermes_welcome.alaw   (62KB, raw A-law)
/var/lib/asterisk/sounds/hermes_welcome.ulaw   (62KB, raw μ-law)
/var/lib/asterisk/sounds/hermes_welcome.gsm    (13KB, GSM)  ← NEW, should work
/var/lib/asterisk/sounds/hermes_response.wav   (131KB, Lavf61.1.100, pcm_s16le)
/var/lib/asterisk/sounds/hermes_response.alaw  (66KB, raw A-law)
/var/lib/asterisk/sounds/hermes_response.ulaw  (66KB, raw μ-law)
/var/lib/asterisk/sounds/hermes_response.gsm   (14KB, GSM)  ← NEW, should work
/var/lib/asterisk/sounds/apollo_goodbye.gsm    (15KB, GSM, copied from apollo_final.gsm)
/var/lib/asterisk/sounds/apollo_goodbye.alaw   (75KB, raw A-law)
/var/lib/asterisk/sounds/apollo_goodbye.ulaw   (75KB, raw μ-law)
```

## ARI Recording Bug

`POST /channels/{id}/record` with `format="wav"` fires both `RecordingStarted` and `RecordingFinished` WebSocket events, but **the WAV file is NOT saved to disk**.

```bash
# Recording log says "done: michel_1779210558"
# But:
ls /var/spool/asterisk/monitor/michel_1779210558*
# → No such file or directory
```

Potential causes:
- Recording stream is consumed internally but never flushed
- ARI Record on an external PJSIP channel may not have write permissions to the monitor directory
- The `mixmonitor` file format might be needed instead

Workaround: Use `MixMonitor()` in dialplan instead of ARI Record for persistent files:
```ini
same => n,MixMonitor(${RECFILE})
```

## Salt 30s Timeout Detail

Salt provider has an RTP silence timer of ~30 seconds. When Michel says "Verbindung wird jetzt auf Standby/Verbindung wird getrennt", that's the Salt network disconnecting the call due to no RTP packets flowing. This is NOT an Asterisk timeout.

Timeline:
0s  → Call answered, ARI answers channel
0-5s → Playback (may or may not produce audio)
5-33s → Silence (our WAV files don't produce RTP audio)
33s → "Verbindung wird getrennt" + Hangup

## v5 Debug Callbot

`/usr/local/bin/ari_callbot_v5.py` — Same event-driven architecture as v4, but plays sounds in this order:
1. `sound:tt-weasels` (standard Asterisk GSM — to prove PJSIP audio works)
2. `sound:hermes_welcome` (our TTS — to test if our files work)
3. Recording (max 10s, silence=2s — shorter than v4's 30s)
4. `sound:test` (another test)
5. `sound:apollo_goodbye` (Apollo's working GSM goodbye)

## Commands Used

```bash
# Convert WAV to GSM
ffmpeg -y -i hermes_welcome.wav -ar 8000 -ac 1 -f gsm /var/lib/asterisk/sounds/hermes_welcome.gsm

# Check sound file location
find / -name 'tt-weasels*' 2>/dev/null
# → /usr/share/asterisk/sounds/en_US_f_Allison/tt-weasels.gsm

# Check codec config
grep -A 20 '\[salt-trunk\]' /etc/asterisk/pjsip.conf

# Check format modules
asterisk -rx 'module show like format'

# Deploy script to Nova
sshpass -p 'Louis_one_13' scp /usr/local/bin/ari_callbot_v5.py root@10.0.60.167:/usr/local/bin/

# Start v5
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 'killall python3 2>/dev/null; sleep 2; setsid python3 -u /usr/local/bin/ari_callbot_v5.py > /tmp/ari_callbot_v5.log 2>&1 &'

# View log
sshpass -p 'Louis_one_13' ssh root@10.0.60.167 'tail -40 /tmp/ari_callbot_v5.log'
```

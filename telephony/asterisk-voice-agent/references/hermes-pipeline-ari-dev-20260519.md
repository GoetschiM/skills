# ARI Pipeline Development — 19.05.2026 Evening Session

## Key Outcomes

### 1. ✅ ARI Stasis-App WebSocket proven working
- `ws://127.0.0.1:8088/ari/events?api_key=henryari:HermesVB2026&app=hermes-pipeline`
- App "hermes-pipeline" registers automatically when WebSocket connects
- **StasisStart event received** when a channel enters Stasis(hermes-pipeline)
- Verified: WebSocket → App registration → Events → Works end-to-end

### 2. 🆕 Dialplan context `[hermes-ari]`
```ini
[hermes-ari]
exten => s,1,Stasis(hermes-pipeline)
 same => n,Hangup()
exten => _X.,1,NoOp(Hermes ARI Pipeline — Stasis)
 same => n,Answer()
 same => n,Stasis(hermes-pipeline)
 same => n,Hangup()
```
- `s` extension: for `channel originate ... extension s@hermes-ari` (clean)
- `_X.` extension: for direct calls to any extension number
- Both go to Stasis(hermes-pipeline) which is handled by the ARI app

### 3. 🆕 ARI Pipeline Script: `/usr/local/bin/hermes_pipeline_ari.py`
- Clean, event-driven architecture (no more v2-v6 callbots)
- Server mode: just wait for Stasis calls
- Call mode: `python3 hermes_pipeline_ari.py call 0796459743`
- Play welcome via `POST /ari/channels/{id}/play`
- (TODO) Audio streaming via ExternalMedia or MixMonitor

## Call-File Safety Incident

**What happened:**
NOVA's call-file `/var/spool/asterisk/outgoing/nova_call_1779213393.call` had:
```
MaxRetries: 1
RetryTime: 30
```
This caused Asterisk to automatically retry the call every ~30-60 seconds, resulting in 6+ unwanted calls to Michel in rapid succession.

**Detection procedure:**
```bash
# 1. Check for call-files
ls -la /var/spool/asterisk/outgoing/

# 2. Kill active channels (use concise for full names!)
asterisk -rx "core show channels concise" | cut -d"!" -f1 | while read ch; do
  asterisk -rx "hangup request $ch"
done

# 3. Delete call-files
rm -f /var/spool/asterisk/outgoing/nova_*.call

# 4. Verify no more active channels
asterisk -rx "core show channels"
```

**Lesson learned:**
- NEVER set `MaxRetries: > 0` in test call-files
- NEVER trigger outbound calls without user permission
- Check `/var/spool/asterisk/outgoing/` for stale files before making any call

## Dialplan-Edit Pitfall

When using `echo "exten => ..." >> /etc/asterisk/extensions.conf` the extension lands OUTSIDE any context (orphan). Always use:
```bash
# Safe: insert after [context-name] header line
sed -i '/^\[hermes-ari\]/a\
exten => s,1,Stasis(hermes-pipeline)\
 same => n,Hangup()' /etc/asterisk/extensions.conf

# Or: Python regex replacement for whole context blocks (preferred)
python3 -c "
import re
with open('/etc/asterisk/extensions.conf') as f:
    content = f.read()
content = re.sub(
    r'\[hermes-ari\].*?(?=\n\[|\Z)',
    '[hermes-ari]\nexten => s,1,Stasis(hermes-pipeline)\n same => n,Hangup()',
    content, flags=re.DOTALL
)
with open('/etc/asterisk/extensions.conf', 'w') as f:
    f.write(content)
"
```

## Utter No-Call Rule

The user EXPLICITLY said "Du rufst mich viel zu viel an" and "Hermes, beende das. Du rufst 100 mal an." Test calls cause SEVERE frustration.

**Hard rules:**
1. NEVER make a test call to the user's real phone number
2. Before any call: check for active channels + stale call-files first
3. Internal testing only (conference 8000, Local channels in Stasis)
4. After any call test: immediately kill all channels and clean up call-files
5. If you find calls from another agent (NOVA): stop them and notify user

## SSH Connection Hangs

Long `sshpass` heredocs with `nohup` inside can hang. Use this pattern:
```bash
# First: kill any stale processes
sshpass ... "pkill -f my_script"

# Second: start fresh
sshpass ... "nohup python3 /path/script.py > /tmp/out.log 2>&1 &"
# Then separately verify with:
sshpass ... "cat /tmp/out.log"
```

# Call-File Safety & Cleanup (19.05.2026)

## The Incident

NOVA placed a call-file at `/var/spool/asterisk/outgoing/nova_call_1779213393.call`:

```
Channel: Local/0796459743@apollo-out
Context: nova-local
Extension: s
Set: AUDIO_WAIT=5
CallerID: NOVA <0796459743>
MaxRetries: 1
RetryTime: 30
WaitTime: 120
```

With `MaxRetries: 1` and `RetryTime: 30`, Asterisk re-dialed Michel every ~30-60 seconds.
Result: 6+ unwanted calls, user extremely frustrated ("ich trei durch").

## The Fix

```bash
# 1. Kill all active channels
asterisk -rx "core show channels concise" | cut -d"!" -f1 | while read ch; do
  asterisk -rx "hangup request $ch"
done

# 2. Delete all call-files
rm -f /var/spool/asterisk/outgoing/nova_call_*.call
```

## Root Cause

NOVA creates call-files for voicemail/notification calls. The `MaxRetries: 1` parameter makes Asterisk retry if the first attempt fails or is missed. Combined with `RetryTime: 30`, this causes repeated calls.

## Prevention

- ALWAYS check `/var/spool/asterisk/outgoing/` before ANY outbound call activity
- Set `MaxRetries: 0` in test call-files
- For production call-files: `MaxRetries: 1` with user's explicit consent
- After tests: delete call-files immediately
- When finding stale call-files from another agent: inform user before acting

## Monitoring

To detect active call-files:
```bash
ls -la /var/spool/asterisk/outgoing/
```

To detect active calls to a specific number:
```bash
asterisk -rx "core show channels" | grep "0796459743"
```

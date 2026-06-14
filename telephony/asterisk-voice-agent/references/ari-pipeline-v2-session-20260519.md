# ARI Pipeline v2 Session — 19.05.2026 (outbound + Nova interference + WS credential discovery)

## Session Overview

User confirmed readiness for 2nd test call (voice: "I've been ready"). Fixed critical bug in `hermes_pipeline_ari.py`, deployed, tested ARI outbound via `application Stasis`.

## Learnings

### 1. `channel originate PJSIP/... application Stasis <app>` — State Machine

```bash
asterisk -rx 'channel originate PJSIP/41796459743@salt-trunk application Stasis hermes-pipeline'
```

- The channel is created in state **"Down"** (ringing).
- The `application Stasis` parameter means the channel will enter Stasis **AFTER the call is answered**.
- If the callee does NOT answer, the channel is destroyed and **no StasisStart event is ever fired**.
- This is DIFFERENT from `channel originate` with a Local channel + dialplan, where the Local channel enters Stasis immediately (even before the Dial completes).

**Use case:** For answered outbound calls where you want the full pipeline to start when the called party picks up.

**Limitation:** You cannot tell *why* the call didn't go through — no-ring, rejected, busy, or timeout all look the same (channel never enters Stasis).

### 2. The `api_key=***` Bug (WebSocket)

In `hermes_pipeline_ari.py` the WebSocket URL was:

```python
self.ws_url = f"ws://{ARI_HOST}:{ARI_PORT}/ari/events?api_key=***&app={ARI_APP}"
```

**The `***` is a literal string!** The WebSocket tried to authenticate with `api_key=***` (the three asterisks as literal password), which silently fails. ARI returns no error — it just never registers the app.

**Fix:**
```python
self.ws_url = f"ws://{ARI_HOST}:{ARI_PORT}/ari/events?api_key={ARI_USER}:{ARI_PASS}&app={ARI_APP}"
```

**Verification test** (proved WebSocket + credentials work):
```python
import asyncio, websockets

url = "ws://127.0.0.1:8088/ari/events?api_key=henryari:HermesVB2026&app=hermes-pipeline"
async with websockets.connect(url, ping_interval=30) as ws:
    print("Verbunden!")  # ✅
    msg = await asyncio.wait_for(ws.recv(), timeout=5)
    # → TimeoutError (expected — no channels in Stasis yet)
```

**Key insight:** The app appears registered in `GET /ari/applications` when the WebSocket is connected. If the app is NOT listed, the WebSocket isn't authenticated.

### 3. Nova Active Call Interference

While testing Hermes outbound calls, NOVA was simultaneously calling Michel via Apollo-Out:

```
Channel: Local/0796459743@apollo-out-00000099;2  (state=Up)
Channel: PJSIP/salt-trunk-0000008d                (state=Up)
```

This overlaps with Hermes test calls — Michel may receive competitor calls mid-test.

**Pre-test safety check (before ANY outbound call):**
```bash
# List ALL active channels
asterisk -rx "core show channels"

# Check for NOVA call-files in outgoing spool
ls -la /var/spool/asterisk/outgoing/

# Check who is registered on Salt trunk
curl -s -u "henryari:HermesVB2026" http://127.0.0.1:8088/ari/channels | python3 -c "
import sys,json
for c in json.load(sys.stdin):
    print(f'{c[\"name\"]}: {c[\"state\"]} caller={c[\"caller\"][\"name\"]})'
"
```

If other agents have active calls, coordinate or wait.

### 4. `sshpass` Quoting Strategy for Multi-Line Python

Running Python one-liners with nested quotes over `sshpass ssh` is fragile. The only reliable patterns:

**Pattern 1 — Write file, scp, run (RECOMMENDED):**
```bash
write_file /tmp/test.py "...python code..."  # on Hermes
scp /tmp/test.py root@10.0.60.167:/tmp/
sshpass -p '...' ssh root@10.0.60.167 "python3 /tmp/test.py"
```

**Pattern 2 — Single-quote outer, no f-strings inside (works for simple cases):**
```bash
sshpass -p '...' ssh root@10.0.60.167 'python3 -c "print(1+1)"'
```

**Pattern 3 — Avoid nested f-string brackets (breaks over SSH):**
```python
# ❌ This fails — f-string [{d["key"]}] causes SyntaxError
python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"key\"]}')"

# ✅ Use separate variables instead
python3 -c "import sys,json; d=json.load(sys.stdin); key=d.get('key','?'); print(key)"
```

## Pipeline Check Status (EOD 19.05.2026)

- ✅ WebSocket connects and authenticates (test confirmed "Verbunden!")
- ✅ App registered in ARI (`GET /ari/applications` → `hermes-pipeline: 0 channels`)
- ⬜ No StasisStart event received — because Michel must answer the call for the PJSIP channel to enter Stasis
- ⬜ Pipeline v2 code (Playback → MixMonitor → STT → TTS → Playback loop) **not yet exercised** because no channel entered Stasis

## Commands Used

```bash
# Create outbound PJSIP channel → Stasis (only enters Stasis AFTER answer)
asterisk -rx 'channel originate PJSIP/41796459743@salt-trunk application Stasis hermes-pipeline'

# Check ARI app registered
curl -s -u "henryari:HermesVB2026" 'http://127.0.0.1:8088/ari/applications'

# Kill and restart pipeline (3-step pattern to avoid SSH hang)
# Step 1: kill old process
ssh root@10.0.60.167 "pkill -f hermes_pipeline_ari"
# Step 2: ensure dead
ssh root@10.0.60.167 "pgrep -f hermes_pipeline_ari"  # → empty = good
# Step 3: start clean
ssh root@10.0.60.167 "nohup python3 /usr/local/bin/hermes_pipeline_ari.py > /tmp/hermes_pipeline_ari.out 2>&1 &"
# Step 4: verify
sleep 5
ssh root@10.0.60.167 "curl -s -u ... 'http://127.0.0.1:8088/ari/applications'"
```

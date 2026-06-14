---
name: system-monitoring
description: "Periodic system health checks via no_agent cronjobs — check TCP, HTTP, DNS services; alert-on-failure via Telegram; auto-log to Qdrant."
tags: [monitoring, health-check, cron, no-agent, alerting, infrastructure]
category: devops
---

# System Health-Check Monitoring

Pattern for running periodic health checks on Goetschi Labs infrastructure. Uses `no_agent=True` cronjobs with a Python script.

## Architecture

```
Cron (every 4h)
  └── no_agent script (health-check.py)
        ├── TCP port check (MinIO, Qdrant, Nextcloud, etc.)
        ├── HTTP/S check (Actual Budget, Paperless, Dokploy)
        ├── DNS resolution check (radislione.net, grow-pro.ch)
        └── Results → Qdrant (for history)
              │
              ├── All OK → silent (no output, nothing sent)
              └── Failures → Telegram message to this chat
```

## Key Pattern

```python
# Silent-on-success pattern:
if fail_count > 0:
    print(output)  # Sent to Telegram by cron
    sys.exit(0)    # Exit 0 even on failures (cron delivers output)
else:
    # Print nothing — cron sees empty output, sends nothing
    sys.exit(0)
```

## Creating a Health-Check Script

### 1. Script Location

Place in `~/.hermes/scripts/` — cron paths are relative to this directory.

### 2. Check Types

| Type | Tool | Use Case |
|------|------|----------|
| TCP | Python socket | Services without HTTP (MinIO, Qdrant, SSH) |
| HTTP HEAD | curl -s -o /dev/null -w "%{http_code}" | Web services |
| HTTPS (insecure) | curl -sk | Self-signed/internal HTTPS |
| DNS | socket.getaddrinfo() | Domain resolution |

### 3. curl vs urllib

Prefer `curl` over Python `urllib` for HTTP checks — better timeout handling, follow-redirect, SSL cert control:

```python
r = subprocess.run(
    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
     "--connect-timeout", "8", "--max-time", "12",
     url],
    capture_output=True, text=True, timeout=20
)
```

### 4. HTTPS with Self-Signed / mkcert Certs

Services behind mkcert need `-k` (insecure) flag for curl since the root CA isn't installed outside the hosting machine:

```python
cmd = ["curl", "-sk", ...]  # -k to skip cert validation
```

### 5. Qdrant Integration

Save every run to Qdrant for audit trail:

```python
subprocess.run([
    "python3", qdrant_script, "store",
    f"Health-Check {timestamp}: {results}",
    "--type", "note", "--source", "system"
], env={"QDRANT_HOST": "10.0.60.179", "QDRANT_PORT": "6333", "QDRANT_API_KEY": ""})
```

### 6. Services to Include

Include the full infrastructure — future agents can add to the list:

- Core storage: MinIO (tcp:9000), Qdrant (tcp:6333)
- Web apps: Paperless, Actual Budget (HTTP+HTTPS), Nextcloud, n8n, Home Assistant
- Infrastructure: Dokploy, Asterisk, Apollo Kali, Hermes Call API
- External: DNS checks for all company domains

### 7. Cron Setup

```bash
cronjob action=create \
  name="Health-Check (description)" \
  schedule="every 4h" \
  no_agent=true \
  script=health-check.py \
  deliver="telegram:Goetschi Lab's (group)"
```

The script resolves relative to `~/.hermes/scripts/`. Copy the skill's `scripts/health-check.py` there if running from the skill dir.

**no_agent=true** means:
- The script's stdout IS the message content (delivered to origin chat)
- Empty stdout = no notification (silent-on-success)
- No LLM tokens consumed
- Script output sent verbatim

## Trigger

- User asks for monitoring/health-check of infrastructure
- User asks "is everything OK?" or "was there a failure?"
- User asks about periodic system checks
- New service added to infrastructure → add to health-check script

## Pitfalls

### Timeout Handling
Set generous timeouts for each check (5-10s). One slow service shouldn't delay the whole run.

### curl Exit Codes
`curl` exits 0 even on HTTP 404/500 — use `-w "%{http_code}"` and check the response code, not the exit code.

### DNS on Hermes Container
Hermes container DNS resolves private domains but may not resolve expired/removed domains. Check with `socket.getaddrinfo()` or `nslookup` rather than assuming resolution.

### No SSL Cert Validation
When checking HTTPS endpoints with self-signed/mkcert certs from the Hermes container, always use `-k` (insecure) — the root CA is installed on the service host, not in the Hermes container.

### Exit Code Convention
Use `sys.exit(0)` even when failures are printed — cron interprets non-zero exit as "script failed" and may not deliver output cleanly. Let the output content (empty vs. failure details) drive the notification.

### No Secrets in Script
- Qdrant logging for every run (healthy or not)
**Cleanup:** Find the parent process (PPID) of the zombies, then kill it. Zombies are reaped when their parent dies:
```bash
# Find parent of zombies
ps -eo pid,ppid,stat,comm | awk '$3=="Z" {print $2}' | sort | uniq -c | sort -rn | head -3
# Kill the parent to reap all zombies — this works even if zombies are stopped (T state)
kill -KILL <PARENT_PID>   # Use -KILL (not -TERM) for stopped processes
# Verify cleanup
ps aux | grep -w Z | wc -l
```

**Detection — include in every health-check script:**
```python
# Count zombies
zombie_count = 0
for entry in os.listdir('/proc'):
    if entry.isdigit():
        try:
            with open(f'/proc/{entry}/status') as f:
                if 'Z (zombie)' in f.read():
                    zombie_count += 1
        except: pass
if zombie_count > 10:
    print(f"⚠️ {zombie_count} zombie processes detected!")
```

**Cleanup:** Find the parent process (PPID) of the zombies, then kill it. Zombies are reaped when their parent dies:
```bash
# Find parent of zombies
ps -eo pid,ppid,stat,comm | awk '$3=="Z" {print $2}' | sort | uniq -c | sort -rn | head -3
# Kill the parent to reap all zombies
kill -TERM <PARENT_PID>
# If SIGTERM doesn't work (process in 'T' stopped state), use SIGKILL
kill -KILL <PARENT_PID>
```

**Prevention in no_agent scripts:**
- Always use `subprocess.run()` with explicit `timeout=` — never `subprocess.Popen()` without `wait()`
- Set script-internal timeouts shorter than the cron's 120s timeout (e.g., 15s per curl call, 60s total)
- If a check consistently times out, exclude it rather than letting it accumulate zombies

## Delivery Targets

Health-check alerts can be sent to any connected chat. See `references/delivery-targets.md` for finding targets.

**Current production config:** alerts go to **Goetschi Lab's (group)** Telegram chat (set via cronjob `deliver` parameter — target format: `telegram:Goetschi Lab's (group)`).

⚠️ **2026-06-03: Cron job removed.** The `984819eda982` health-check cron (created from `system-monitoring`) was deleted because its underlying `health-check.py` script spawned 58 zombie `curl`/`grep` processes (PPID was syncthing via containerd-shim) over multiple runs. The zombies caused load average >20 and I/O wait >15%. Lesson: no_agent health-check scripts must properly reap child processes (`subprocess.run()` with `timeout=`, never bare `Popen` without `wait()`). If recreating, rewrite the script with strict process lifecycle management.

**Creating a new health-check cron:**
```bash
cronjob action=create \
  name="Health-Check (description)" \
  schedule="every 4h" \
  no_agent=true \
  script=health-check.py \
  deliver="telegram:Goetschi Lab's (group)"
```

## Reference Script

See `scripts/health-check.py` — the Goetschi Labs production health check, checks 15+ services every 4 hours. Uses curl for HTTP, socket for TCP, and DNS resolution. Silent-on-success with automatic Qdrant logging.

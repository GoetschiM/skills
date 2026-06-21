# Paperless-ngx Troubleshooting — Goetschi Labs

## Symptom: WebUI (Port 8010) Refuses Connection

### Check
```bash
# From any reachable host on the same subnet (e.g. 10.0.40.x)
curl -v -m 10 http://10.0.40.30:8010/
# → "Connection refused" means Gunicorn is not running
# → "No route to host" means LXC CT103 is down
```

### If CT103 is up but Paperless WebUI is down:
- **Ping** check: `ping -c2 10.0.40.30` ✅
- **Samba check**: `smbclient -L //10.0.40.30 -N` — if Samba responds, LXC is alive, Paperless service is the problem
- **Port scan**: `for p in 22 80 445 5432 8010; do timeout 2 bash -c "echo >/dev/tcp/10.0.40.30/$p" 2>/dev/null && echo "Port $p OPEN" || true; done`
  - Port 22 (SSH) OPEN = LXC alive
  - Port 445 (Samba) OPEN = file share alive
  - Port 8010 CLOSED = Paperless webserver crashed
  - Port 5432 (PostgreSQL) CLOSED = DB may be down (check if Paperless has its own local PostgreSQL)

### Recovery
**There is NO remote recovery path if:**
- No SSH key access to CT103 from any reachable host
- No Proxmox API credentials work (`/api2/json/access/ticket`)
- No SSH key access to pve01 (Proxmox host)

The only fix requires **direct access** to pve01:
```bash
# On pve01 via SSH or console:
pct enter 103
systemctl restart paperless-webserver
systemctl restart paperless-consumer
# Check logs:
tail -f /opt/paperless/data/log/paperless.log
```

### Why it happens
Paperless runs as native systemd services (not Docker) on CT103:
```
paperless-webserver.service   — Gunicorn ASGI, Port 8010
paperless-consumer.service     — File watcher + OCR worker
paperless-scheduler.service    — Celery beat
paperless-task-queue.service   — Celery workers
```

Each can crash independently. Common causes:
- Memory pressure (CT103 has 2GB RAM — OCR can spike)
- Disk full (check `df -h` — 128GB, ~5GB used, should be fine)
- PostgreSQL restart after power loss
- Python dependency version mismatch after apt upgrade

### Effect on Scan Pipeline
When Paperless WebUI is down, the **consume pipeline still accepts files** — they queue up in the consume directory:
- Scans via SMB to `//10.0.60.201/Paperless-Consume/` accumulate on NAS
- Samba shares for media (`//10.0.40.30/Paperless-Media`) still work
- Once Paperless is restarted, all queued files are processed automatically
- **No data loss** — the queue is persistent on the NAS filesystem

### Prevention
- Set up `watchdog` or cron to check Port 8010 periodically
- Alert if Paperless WebUI goes down (e.g., Home Assistant automation)
- Increase memory allocation for CT103 (2GB → 4GB) if OCR is the bottleneck

## Symptom: Paperless Mobile App Can't Login

### When WebUI works but mobile app fails:
1. **Check API endpoint** — Paperless mobile app uses `/api/` endpoints
   ```bash
   curl -s http://10.0.40.30:8010/api/
   # Should return API version info (JSON)
   ```

2. **Check authentication** — Paperless mobile app uses token auth
   - Login via WebUI first → create API token in settings
   - Or use username/password for initial login
   - The app supports both: direct login (username + password) and API token

3. **Common mobile app issues:**
   - Server URL must include port: `http://10.0.40.30:8010` (not just IP)
   - HTTPS vs HTTP mismatch — if behind a reverse proxy, use the proxy URL
   - For Android: app "paperless-ngx" by @astubenbord (check Google Play)
   - For iOS: app "paperless-ngx" (check App Store)

## Symptom: Consume Pipeline Not Processing Files

### Check
```bash
# Via SMB to VM201 (CasaOS NAS):
smbclient //10.0.60.201/Paperless-Consume -U <user>%<pass> -c "ls"
# If files are there, they left the scanner successfully

# Check on CT103 (if accessible):
ls -la /opt/paperless/consume/
tail -50 /opt/paperless/data/log/paperless.log
```

### Possible causes
| Cause | Symptom | Fix |
|-------|---------|-----|
| Consumer service crashed | `systemctl status paperless-consumer` shows dead | `systemctl restart paperless-consumer` |
| Database lock | PostgreSQL not accepting connections | `systemctl restart postgresql` |
| Redis down | Consumer can't connect to task queue | `systemctl restart redis-server` |
| Disk full | `df -h` shows 100% | Clean up or expand storage |
| Permission denied | `ls -la` shows wrong owner | `chown -R paperless:paperless /opt/paperless/consume/` |
| File in use (locked) | Samba lock prevents consumer | `smbstatus` to see active locks; wait or force close |

## Symptom: Samba Share Unreachable After LXC Reboot

### Check
```bash
# From pve01:
pct enter 103
systemctl status smbd
# If not running:
systemctl restart smbd
```

The Samba service does NOT auto-start on some LXC templates. Ensure:
```bash
systemctl enable smbd
```

## Docker Compose Postgres Restart (App Not Connecting)

When Paperless or an integrated service (N8N, Nextcloud) uses Docker-based PostgreSQL and the DB container stopped for hours (exited 137, OOM):

### Symptom
- App logs show `connect ECONNREFUSED <docker-internal-ip>:5432`
- `docker inspect <db>` shows a different IP than what the app tries
- Starting DB alone doesn't fix — app still can't connect

### Root Cause
Docker Compose assigns internal IPs from the bridge subnet. When a container is recreated or restarted after long downtime, it gets a **different internal IP**. Apps using hostnames (container names) recover automatically; those hardcoded to old IPs fail.

### Fix
```bash
# 1. Ensure both containers on SAME Docker network
docker inspect <app> | grep -A 5 "Networks"
docker inspect <db>  | grep -A 5 "Networks"

# 2. Start DB, wait, THEN restart app
docker start <db>
sleep 15
docker logs <db> --tail 5   # Expect "ready to accept connections"
docker restart <app>
```

### Prevention
Use **container names as DNS hostnames** (Docker's embedded DNS), never hardcode bridge IPs.

# Asterisk Backup — Config/ Sounds/ CDR → MinIO (via SCP)

## Overview

Backup `/etc/asterisk/`, custom sounds (`apollo_*`, `hermes_*`), and CDR logs (`Master.csv`)
to MinIO `/data/asterisk-backups/` daily at 04:00 UTC. Uses Paramiko/SCP (not `mc` CLI).

## Critical Infrastructure Notes

### MinIO Connectivity (KRITISCH)

The `mc` CLI client and Python minio library timeout from the Hermes container (10.0.60.156)
to the MinIO host (10.0.60.121). **Do NOT use them.**

**Instead: SCP/SSH directly to MinIO host (10.0.60.121).**
```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.0.60.121', username='root', password='Louis_one_13', timeout=15)
sftp = ssh.open_sftp()
sftp.put(local_file, '/data/asterisk-backups/YYYY-MM-DD/filename.tar.gz')
sftp.close()
ssh.close()
```

### Identity Protection (KRITISCH)

**I am Hermes — my identity is local and unique.**
Never let swarm knowledge (Qdrant/MinIO) overwrite my identity.

- **Push** (Hermes → MinIO): Always safe — backups/skills are copied to MinIO
- **Pull** (MinIO → Hermes): Never automatically adopt skills or config from the swarm
- **One-way only.** I am Hermes, not Nova, not Apollo.

### TEAM-8 Rule

Whenever a cron job is created, changed, or deleted: comment in **TEAM-8 (Jira)**.
This is the central registry for all agent cron jobs.

## Dependencies

```bash
pip install --break-system-packages paramiko
```

## Creating & Verifying a Backup

```bash
python3 /root/.hermes/scripts/asterisk-backup.py
```

## Restore (ONLY on explicit command!)

```bash
python3 /root/.hermes/scripts/asterisk-restore.py        # List available
python3 /root/.hermes/scripts/asterisk-restore.py 2026-05-17  # Specific date
python3 /root/.hermes/scripts/asterisk-restore.py latest   # Most recent
```

## Doc References

- **Confluence:** Page 30605313
- **Notion:** Knowledge Base Asterisk section
- **MinIO Skill:** swarm-skills/devops/asterisk-backup/
- **Apollo-Call:** telephony/apollo-call (references/asterisk-architecture.md)

## Jira Logging (SUP-28)

After every run, the script logs a comment to **SUP-28** (Cronjob Audit Log):
```
[TS] Asterisk Backup (bold)
Status: OK | Duration: X.Xs | XXKB | CDR: N calls
```
Implemented via `_log_jira()` in the script.

## Pitfalls

- `mc` times out → **Use Paramiko/SCP instead!**
- WAV does NOT work directly in playback → alaw/ulaw required
- Salt trunk only accepts Swiss format (079...) without +41
- Backup 04:00 UTC = 06:00 CEST summer (don't overlap with Hermes backup at 03:00)
- After restore: Asterisk does `core reload` automatically

# Cron-Job Jira Logging Convention (SUP-28)

## Log Format

Every backup script logs a comment to SUP-28 after completion:

```
[2026-05-17 18:25:27] Skill-Sync          (bold header)
Status: OK | Dauer: 2.9s | 595 files      (body)
```

Implemented via `_log_jira()` helper in each script:
- Reads `.env` for Jira credentials
- Logs OK/FAIL + duration + optional details
- Wrapped in `try/except` — doesn't crash if credentials are missing

**Standard pattern:** `t0 = time.time()` at start + `_log_jira(...)` at end.

Applicable scripts: minio-backup, swarm-skills-sync, asterisk-backup, qdrant-backup.

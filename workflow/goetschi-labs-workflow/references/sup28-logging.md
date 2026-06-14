# SUP-28: Cronjob-Logging-Konvention

## Übersicht

Alli Cronjobs auf Hermes logge nach jedem Durchlauf en Kommentar i SUP-28.
Das erlaubt Monitoring ohni aktiv Ha nudefahre.

## Aktivi Cronjobs (Stand 17.05.2026)

| Job | Zeitplan | Script | Logger |
|-----|----------|--------|--------|
| MinIO Backup | 0 3 * * * | minio-backup.py | ✅ `_log_jira()` |
| Schwarm Skill-Sync | 0 2 * * * | swarm-skills-sync.py | ✅ `_log_jira()` |
| Qdrant Snapshot | 0 3 * * 0 | qdrant-backup.py | ✅ `_log_jira()` |
| Asterisk Backup | 0 4 * * * | asterisk-backup.py | ✅ `_log_jira()` |
| GitHub Skill-Sync | 0 * * * * | skill-sync.sh | ❌ **noch kei Logging** — no_agent, shell-script |

## Log-Format

```
[YYYY-MM-DD HH:MM:SS] Job-Name           (bold header)
Status: OK | Dauer: X.Xs | Detail         (body)
```

## Integration in jedes Script

```python
import os, json, urllib.request, base64, time

def _log_jira(status, duration, details=""):
    try:
        env = {k: v for k, v in (line.split('=', 1) for line in open('/opt/data/home/.hermes/.env') if '=' in line)}
        auth = base64.b64encode(f"{env['ATLASSIAN_EMAIL']}:{env['ATLASSIAN_TOKEN']}".encode()).decode()
        body = json.dumps({
            "body": {
                "type": "doc", "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Status: {status} | Dauer: {duration}s | {details}"}]
                }]
            }
        }).encode()
        req = urllib.request.Request(
            "https://goetschi.atlassian.net/rest/api/3/issue/SUP-28/comment",
            data=body, method="POST",
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass  # Logging darf nie de Hauptprozess stoppe

# Usage at start:
t0 = time.time()
# ... main logic ...
_log_jira("OK", round(time.time() - t0, 1), "optional details")
```

## Besonderheite

- **no_agent Jobs (true):** Logge über `_log_jira()` im Script selber
- **no_agent Jobs (shell):** GitHub Skill-Sync isch e bash-script, loggt aktuell no nöd. Könnt per `curl` vum Script us ergänzt werde.
- **Fehlerfall:** `_log_jira("FAIL", ...)` mit Fehlermeldig
- **SUP-28** isch debünd — alli Jobs schribed i de gliich Ticket
- **try/except-gschützt:** Wenn Jira nöd erreichbar isch, schlaft de Job nöd

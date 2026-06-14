# MinIO Setup & Maintenance

## Host
- LXC 505 (10.0.60.106) — standalone LXC, not Docker on Dokploy
- Migrated from Dokploy on 23.05.2026
- Docker Compose: `/etc/dokploy/compose/homelab-minio-0sa7uj/code/docker-compose.yml`
- .env: `/etc/dokploy/compose/homelab-minio-0sa7uj/code/.env`

## Service Backup Script

`scripts/backup-service.sh` is a generic script for backing up arbitrary service configs (LiteLLM, n8n, Jira, etc.):

```bash
# Simple: provide config directories
SERVICE_ENV_PREFIX=LITELLM bash scripts/backup-service.sh litellm /etc/litellm /opt/litellm

# With GitHub Upload
GITHUB_TOKEN='***' GITHUB_REPO='...' \
  SERVICE_ENV_PREFIX=LITELLM bash scripts/backup-service.sh litellm /etc/litellm /opt/litellm
```

Pitfall: MinIO is not reachable from Nova (156) — different subnet/firewall.

## Legacy (SCP/Paramiko)

The legacy scripts `scripts/minio-backup.py` and `scripts/qdrant-backup.py` use SCP and haven't been migrated to the LXC. Current approach uses `mc cp` directly.

## Cronjobs (current)

| Cronjob | Script | Schedule | ID | Status |
|---------|--------|----------|----|--------|
| Self-Backup zu GitHub / Minio | LLM-prompt + Skills | So 02:00 | ab2cf65e3682 | Likely replaced by dual_backup.sh |
| Health-Check | health-check.py | alle 4h | 984819eda982 | ✅ no_agent |

---
name: hermes-backup
description: "Backup Hermes configuration to MinIO S3 + GitHub Releases. Covers scheduling, verification, selective restore, dual-backup scripts, and identity-safe operations."
version: 1.0.0
author: Hermes Agent
category: devops
tags: [backup, minio, github, restore, hermes, mc]
---

# Hermes Backup — MinIO & GitHub

> **Umbrella skill.** Formerly split across `devops/minio-backup` and `devops/github-backup`. Both targets use the same source data (`config.yaml memories/ skills/ home/.hermes/`) and the same packing strategy (tar.gz). The `dual_backup.sh` script hits both in one shot.

## Quick Start

```bash
# Single shot — backup to one target
cd /opt/data && tar czf /tmp/hermes-backup.tar.gz config.yaml memories/ skills/ home/.hermes/

# To MinIO:
mc cp /tmp/hermes-backup.tar.gz homelab/hermes-backups/$(date +%Y-%m-%d_%H%M)_hermes-full-backup.tar.gz

# To GitHub Releases:
# (see section below for full workflow)
```

## Trigger

- User says "Backup machen", "Config sichern", "zu Minio hochladen", "GitHub Release"
- Cronjob for regular backups
- Before/after large config changes, before migration

## MinIO Target

| Parameter | Value |
|-----------|-------|
| **Endpoint** | `http://10.0.60.106:9000` |
| **S3 API Port** | `9000` |
| **Access Key** | `admin` |
| **Secret Key** | `Louis_one_13` |
| **Bucket** | `hermes-backups` |
| **API Signature** | `S3v4` |

### mc CLI Setup

```bash
# Install (if not present)
curl -sL https://dl.min.io/client/mc/release/linux-amd64/mc -o /tmp/mc
chmod +x /tmp/mc && cp /tmp/mc ~/.local/bin/mc

# Alias setzen (einmalig)
mc alias set homelab http://10.0.60.106:9000 admin Louis_one_13 --api S3v4
```

### MinIO Backup Variants

**A — With temp file (simpler):**
```bash
cd /opt/data && tar czf /tmp/hermes-backup.tar.gz config.yaml memories/ skills/ home/.hermes/
mc cp /tmp/hermes-backup.tar.gz homelab/hermes-backups/$(date +%Y-%m-%d_%H%M)_hermes-full-backup.tar.gz
rm /tmp/hermes-backup.tar.gz
```

**B — Pipe (no temp file):**
```bash
cd /opt/data && tar czf - config.yaml memories/ skills/ home/.hermes/ | mc pipe homelab/hermes-backups/$(date +%Y-%m-%d_%H%M)_hermes-full-backup.tar.gz
```

### Cleanup old backups (keep last 7)
```bash
mc ls homelab/hermes-backups/ | sort | head -n -7 | awk '{print $NF}' | while read f; do mc rm "homelab/hermes-backups/$f"; done
```

## GitHub Releases Target

| Parameter | Value |
|-----------|-------|
| **Repo** | `GoetschiM/hermes-private-backups` (private) |
| **Token** | Fine-Grained PAT (Contents: Write) — see references/credentials |
| **⚠️ Known stale since 07.06.2026** — token may need rotation |

### GitHub Backup Workflow

```bash
TOKEN='...'
OWNER='GoetschiM'
REPO='hermes-private-backups'
DATE_TAG="backup-$(date +%Y-%m-%d-%H%M%S)"

cd /opt/data && tar czf /tmp/hermes-backup.tar.gz config.yaml memories/ skills/ home/.hermes/

# Create release
RELEASE_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/releases" \
  -d "{\"tag_name\":\"$DATE_TAG\",\"name\":\"Config Backup $DATE_TAG\",\"body\":\"Automatic Hermes Backup\"}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('id'))")

# Upload asset
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/gzip" \
  --data-binary @/tmp/hermes-backup.tar.gz \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=hermes-config-${DATE_TAG}.tar.gz"

rm /tmp/hermes-backup.tar.gz
```

### Cleanup old releases (keep last 10)
```bash
# See references/github-release-cleanup.md
```

## Dual Backup Script (Recommended — no_agent cron)

The `dual_backup.sh` script (at `/root/.hermes/scripts/dual_backup.sh`) backs up to BOTH targets in one shot, with auto-repair for MC alias drift and auto-cleanup for old releases.

```bash
# Test
/root/.hermes/scripts/dual_backup.sh

# Cron (recommended)
cronjob action=create \
  name="Dual Backup (MinIO + GitHub)" \
  schedule="0 2 * * 0" \
  no_agent=true \
  script=dual_backup.sh \
  deliver="local"
```

## Verification

```bash
# 1. File count
tar tzf /tmp/hermes-backup.tar.gz | wc -l  # ~866 files

# 2. Structure check
tar tzf /tmp/hermes-backup.tar.gz | grep -E '(config\.yaml|MEMORY\.md|USER\.md|skills/.+/SKILL\.md|home/\.hermes/\.env)' | head -5

# 3. MinIO verification
mc stat "homelab/hermes-backups/$(date +%Y-%m-%d)_*-backup.tar.gz" 2>&1 | grep -E 'Name|Size'
```

## Restore (⚠️ Only on explicit user command — never automatic!)

```bash
# 1. Find latest backup from MinIO
mc ls homelab/hermes-backups/ | sort | tail -1

# 2. Download
mc cp "homelab/hermes-backups/$BACKUP" /tmp/restore.tar.gz

# 3. Inspect before extracting
tar tzf /tmp/restore.tar.gz | head -20

# 4. Extract
cd /opt/data && tar xzf /tmp/restore.tar.gz
```

### Selective Restore (for secondary instances)

Exclude `config.yaml`, `home/.hermes/.env`, and `home/.hermes/config.yaml` to avoid overwriting the target instance identity:

```bash
cd /opt/data && tar xzf /tmp/restore.tar.gz \
  skills/ memories/ \
  --exclude=config.yaml \
  --exclude=home/.hermes/.env \
  --exclude=home/.hermes/config.yaml
```

### After Selective Restore: fix ownership + merge missing skills
```bash
chown -R root:root /opt/data/memories/ /opt/data/skills/ /opt/data/home/.hermes/
cd /opt/data/skills
for cat in */; do for skilldir in "$cat"*/; do
  skillname=$(basename "$skilldir")
  target="/root/.hermes/skills/$cat/$skillname"
  if [ -d "$skilldir" ] && [ ! -d "$target" ]; then
    mkdir -p "/root/.hermes/skills/$cat"
    cp -r "$skilldir" "$target"
  fi
done; done
```

## Identity Protection Rules

- ✅ **Push** (local → MinIO/GitHub): Always safe
- ❌ **Pull** (MinIO/GitHub → local): Never auto-restore on running instances
- ✅ **Selective restore** only on fresh/empty secondary instances
- ❌ Swarm knowledge (Qdrant/MinIO) must never overwrite local identity

## ⚠️ Known Issues

- **MC Alias Drift (28.05.2026):** MinIO moved from Dokploy (10.0.60.121) to standalone LXC (10.0.60.106). Alias wasn't updated — the `dual_backup.sh` has auto-repair.
- **GitHub Token 401:** Current PAT may have expired. Fix: generate new token with `contents: write` scope, update in references/credentials.md.
- **Network topology:** MinIO (10.0.60.106) not reachable from Nova (156) — different VLAN/subnet.
- **`.atlassian.env` not in backup** — lies outside backup paths. Manual restore needed.

## References

- `references/minio-setup.md` — Full MinIO deployment details, mc alias, bucket setup
- `references/github-release-setup.md` — Repo setup, token scope requirements, release lifecycle
- `references/dual-backup-script.md` — dual_backup.sh specifics, auto-repair, cleanup
- `references/service-backup-script.md` — Generic `backup-service.sh` for backing up third-party service configs (LiteLLM, n8n, Jira, etc.)
- `references/publish-to-swarm-skills.md` — Skill distribution to the `swarm-skills/` bucket
- `references/second-device-setup.md` — Second-instance credential reference

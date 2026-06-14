# GitHub Release Setup

## Repo
- `GoetschiM/hermes-private-backups` (private)
- Fine-Grained PAT with `contents: write` scope
- Token known stale since ~07.06.2026 — may need rotation

## Security Rules
1. **Never** commit credentials into git history
2. **Only** release assets (tarballs) contain sensitive data
3. At accidental commit: rotate token immediately (git history can't be safely scrubbed)

## Known Problems
- ❌ Release on **empty repo** not possible — need initial commit (README.md) first
- ✅ Token must be Fine-Grained PAT with access to the target repo
- ⚠️ New private repos are invisible to existing tokens — must be granted in token settings
- ⚠️ Release tags persist as orphaned refs after release deletion — must delete separately
- ⚠️ Token 401 "Bad credentials": expired or repo access revoked. Generate new one.

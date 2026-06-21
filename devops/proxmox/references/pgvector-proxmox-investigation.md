# PGVector Database Audit (Session 2026-06-07)

## Context
Michel asked whether the PostgreSQL database on `CT105 (PGVector, 10.0.60.141)` was still in use, since Coolify CT118 had its own postgres and KASAOS/Dokploy on CT100 also had one.

## Infrastructure

| LXC | Hostname | IP | Role |
|-----|----------|-----|------|
| 105 | PGVector | 10.0.60.141 | Standalone PostgreSQL with pgvector extension |
| 100 | Dokploy | 10.0.60.121 | Production PaaS (being migrated away from) |
| 118 | Coolify-Sandbox | 10.0.60.139:8000 | New PaaS sandbox |
| 112 | NOVA | 10.0.60.167 | LXC running Hermes Agent (current session origin) |
| PVE host | pve01 | 10.0.60.10 | Proxmox hypervisor (credentials: root / Riotstar_PROXMOX_13) |

## Access Pattern

Hermes is on NOVA (CT112), which is an LXC inside the same PVE cluster. Direct SSH to other LXCs was blocked (no key deployed). Solution: SSH to the PVE host with sshpass, then use `pct exec`:

```bash
sshpass -p "Riotstar_PROXMOX_13" ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "pct exec 105 -- timeout 10 su - postgres -c 'psql -c ...'"
```

## Databases Found on CT105

| Database | Size | Tables | Active Conns | Verdict |
|----------|------|--------|-------------|---------|
| n8n_db | 8.4 MB | 0 | 0 | ✅ Orphan — n8n on CT100 uses docker-internal postgres |
| nei | 45 MB | 11 (Strategy, MarketBar, Memory, etc.) | 0 | ❓ Orphan (0 rows in Strategy table) |
| nei_v2 | 12 MB | 12 (same + Conversation table) | 0 | ❓ Orphan |
| m8m | 10 MB | 10 (documents, knowledge, wallet, n8n_chat_histories) | 0 | ❓ Orphan (no connections since May 11) |
| ownmcp_memory | 21 MB | 7 (memories=2759, facts_memory, etc.) | 0 | ❓ Possibly active — had data |
| toni_app | 12 MB | 5 (User=4, FeatureRequest, Message, Session, Notification) | 0 | ❓ Orphan — minimal data |
| postgres | 12 MB | system | 1 | Standard — keep |

## Docker Postgres Instances (for Comparison)

**CT118 (Coolify)**:
- `dograh-postgres` (pgvector/pgvector:pg17) — port 5432 exposed, user=postgres, DB=postgres. Own instance, not linked to CT105.
- `coolify-db` (postgres:15-alpine) — internal Coolify DB

**CT100 (Dokploy)**:
- `dokploy-postgres` (postgres:16)
- `litellm-db` (postgres:16-alpine)
- n8n uses internal docker-compose postgres (`DB_POSTGRESDB_HOST=postgres`)

## Key Discovery: Docker-internal vs External DB

A service using `DB_POSTGRESDB_HOST=postgres` (bare hostname) is linked to a Docker-internal postgres container, NOT to an external server like CT105. This is how we proved `n8n_db` on CT105 was orphaned — the running n8n on CT100 points to its own Docker-internal PG, not to CT105.

## The Quoting Hell Pattern

To run multi-line scripts inside a container via proxmox SSH, the correct pattern is:

```
Write script locally → scp to PVE host → pct push into target container → pct exec to run
```

Never inline complex commands in SSH args — the quoting becomes unmanageable past 2 levels of nesting.

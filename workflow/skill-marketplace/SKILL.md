---
name: skill-marketplace
version: 1.0.0
category: workflow
description: Konzept und Architektur für en konsistente Skill-Marketplace — Source of Truth für alli Hermes-Skills (GitHub + MinIO + MCPHub).
tags:
  - marketplace
  - skills
  - catalog
  - repository
  - mcp
  - minio
  - github
triggers:
  - skill marketplace
  - skill registry
  - skill catalog
  - skills verwalte
  - skill sync
  - goetschi skills
  - source of truth skills
---

# Skill Marketplace — Konzept

## Problem

D'Skills ligged aktuell **uf 3+ Ort** — aber niemmerme konsistent:

| Ort | Inhalt | Problem |
|-----|--------|---------|
| `~/.hermes/skills/` | ~30 Skills | **Source of Truth?** Aber nume lokal |
| **MinIO** (10.0.60.106:9000) | Backup/Files | **Nöd aktuell**, nöd organisiert |
| **Notion/Confluence** | Doku | **Hand-pflegt**, lauft usenand |
| **GitHub** | `goetschi-org/hermes-agent-skills` | **Veraltet** — Stand April 2026 |

**Ziel:** Ein einzige, konsistente Source of Truth für alli Skills.

## Was es scho git (Fertiglösige)

Uf GitHub gits scho ähnlichi Projekt:

| Projekt | Stars | Beschrieb |
|---------|-------|-----------|
| **Leon-Drq/openagentskill** ⭐174 | Next.js-WebApp — Browse/Search/Upload/Recommend vo Skills + MCP-Integration. **Bruucht Vercel/Supabase** |
| **frank-luongt/faos-skills-marketplace** ⭐22 | **930+ Skills** als Markdown + Claude-Plugins. **Statisch**: nume GitHub, kei Suchi/API |
| **UseAI-pro/openclaw-skills-security** ⭐63 | Kuratierti, security-first Skills (Markdown). Arbeitet mit Codex CLI, Claude Code |
| **brooks-builds/skill-registry** | Einfache Skill-Registry für AI-Agents |
| **GitHub MCP Registry** (built-in) | In GitHub "Ecosystem" — neue MCP Registry direkt uf GitHub |

## Empfohleni Architektur: Goetschi Skills Hub

Mir händ **alli Komponente** scho — müend nume verchnüpft werde:

```
┌──────────────────────────────────────────────────┐
│              Source of Truth                      │
│        GitHub: goetschi-labs/skills               │
│  (Markdown-Skills + Catalog + Actions)            │
└──────────┬───────────────────────────────┬───────┘
           │ git push/pull                  │ sync
           ▼                                ▼
┌──────────────────┐           ┌──────────────────────┐
│    MinIO S3       │           │  MCPHub Skill Server  │
│  (Backup/Cache)   │           │  (Search/Install/API) │
│  10.0.60.106:9000 │           │  10.0.60.170:3000     │
└──────────────────┘           └──────────────────────┘
```

### Struktur uf GitHub

```
goetschi-labs/skills/
├── CATALOG.md              # Vollständigi Liste aller Skills
├── devops/
│   ├── dokploy/
│   │   └── SKILL.md
│   └── proxmox/
│       └── SKILL.md
├── ai/
│   ├── liteLLM/
│   │   └── SKILL.md
│   └── huggingface/
│       └── SKILL.md
├── security/
│   └── kali-container/
│       └── SKILL.md
└── .github/workflows/
    └── sync-skills.yml     # GitHub Action: Push → MinIO + MCPHub
```

### GitHub Action (Idee)

```yaml
name: Sync Skills
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sync to MinIO
        run: mc cp --recursive skills/ minio/skills/
      - name: Notify MCPHub
        run: curl -X POST https://10.0.60.170:3000/api/skills/reload
```

## Nächsti Schritt

1. **GitHub Repo alege:** `goetschi-labs/skills` (öffentlich oder privat)
2. **Alli bestehende Skills importiere** vo `~/.hermes/skills/` ins Repo
3. **CATALOG.md generiere** us den Frontmatter-YAMLs
4. **GitHub Action** für MinIO-Sync (braucht MinIO Zugriff)
5. **MCPHub Skill-Server** — en MCP wo `skill_search()`, `skill_install()`, `skill_publish()` chan
6. **Contributing Guide** — wie mer en neui Skill iireicht (SKILL.md + Frontmatter + references/)

## Alternative: GitHub MCP Registry

GitHub het sither 2026 e **built-in MCP Registry** — under "Ecosystem → MCP Registry". Wär evtl. eifacher für discoverable MCP-Skills, aber weniger kontrolliert als eigeni Lösung.

## Referenz

- GitHub Suche: `[skill-marketplace](https://github.com/topics/skill-marketplace)` — 40+ Repos
- `openagentskill` — Next.js, fullstack, Vercel/Supabase
- `faos-skills-marketplace` — 930 statischi Skills, nume GitHub

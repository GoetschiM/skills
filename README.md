# 🧠 Goetschi Labs Skills

Zentrale Source of Truth für alli Hermes-Agent Skills.

## Struktur
```
skills/
├── CATALOG.md           # Vollständigi Skill-Liste
├── <category>/
│   └── <skill-name>/
│       ├── SKILL.md     # Skill-Definition
│       └── references/  # Referenz-Dateie
└── server/              # MCP-Skill-Server
```

## Nutzig
- **Via MCPHub:** `http://skills.goetschi-labs.ch/mcp`
- **Via GitHub:** `git clone https://github.com/GoetschiM/skills.git`
- **Via MinIO:** `mc cp minio/skills/...`

## Entwicklung
1. Skill im richtige Category-Ordner erstelle
2. `SKILL.md` nach Vorlag
3. PR uf main → GitHub Action validiert + syncs MinIO + MCPHub

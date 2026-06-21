---
name: knowledge-base
description: "Build, maintain, and query persistent knowledge bases. Covers Karpathy-style LLM Wiki (interlinked markdown files) and Obsidian vault operations (read, search, create, edit notes)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [knowledge-base, wiki, obsidian, notes, markdown, research, vault]
    related_skills: [arxiv, ocr-and-documents]
---

# Knowledge Base

Persistent knowledge management using two complementary approaches: the Karpathy LLM Wiki pattern (self-contained markdown wiki with cross-references) and Obsidian vault operations (read, search, create, edit notes in an Obsidian vault).

## Approach 1: LLM Wiki (Karpathy Pattern)

Build and maintain a persistent, compounding knowledge base as interlinked markdown files. Based on Andrej Karpathy's LLM Wiki pattern — unlike RAG, the wiki compiles knowledge once and keeps it current.

### Architecture

```
wiki/
├── SCHEMA.md           # Conventions, structure rules, domain config
├── index.md            # Sectioned content catalog with one-line summaries
├── log.md              # Chronological action log (append-only, rotated yearly)
├── raw/                # Layer 1: Immutable source material
│   ├── articles/       # Web articles, clippings
│   ├── papers/         # PDFs, arxiv papers
│   └── transcripts/    # Meeting notes, interviews
├── entities/           # Layer 2: Entity pages (people, orgs, products)
├── concepts/           # Layer 2: Concept/topic pages
├── comparisons/        # Layer 2: Side-by-side analyses
└── queries/            # Layer 2: Filed query results
```

### Core Operations

**Ingest** a source: capture raw material → cross-reference existing pages → create/update wiki pages → update index + log

**Query** the wiki: read index → search for relevant pages → synthesize answer

**Lint** the wiki: orphan pages, broken wikilinks, stale content, contradictions

Full guide: see `/skills/research/llm-wiki/SKILL.md`.

## Approach 2: Obsidian Vault

Read, search, create, and edit notes in an Obsidian vault via filesystem tools.

### Quick reference

| Operation | Command |
|-----------|---------|
| Read a note | `read_file "$VAULT/My Note.md"` |
| List notes | `search_files "*.md" target="files" path="$VAULT"` |
| Create a note | `write_file "$VAULT/New Note.md" "...markdown..."` |
| Append to a note | `patch` or `write_file` with full rewrite |
| Search content | `search_files "query" path="$VAULT" file_glob="*.md"` |

Vault path: `$OBSIDIAN_VAULT_PATH` env var, otherwise `~/Documents/Obsidian Vault`.

Use `[[wikilinks]]` to link notes. Obsidian works as a viewer for the LLM Wiki — the wiki directory is an Obsidian vault out of the box.

Full guide: see `/skills/note-taking/obsidian/SKILL.md`.

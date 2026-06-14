# Goetschi Labs — Source of Truth Architecture (v1.0, 24.05.2026)

## Überblick

Goetschi Labs betreibt e **6-Layer-Architektur** — jede Layer het sin exklusive Zweck
und isch Source of Truth für bestimmti Datekategorie. Kei Layer macht was en andere
macht. Das verhindert Redundanz, Chaos und veralteti Informatione.

---

## Layer 1: 🧠 Obsidian → Cognitive Knowledge Layer

**Server:** CouchDB 10.0.60.121:5984 (Dokploy)
**Credentials:** user=obsidian_sync / pw=ObsidianSync_p6W7aB2yT9
**Plugin:** Self-hosted LiveSync
**Verifiziert:** 24.05.2026 ✅

### Zweck
Technischi Architektur, Wissensnetz, Agentewüsse, SOP Drafts, Brainstorming,
Systemzämmehäng, Langzeit-Knowledge, Research.

### Erlaubt
✅ Markdown, Wikilinks, technischi Dokumentation, semantischi Beziehige

### Nöd erlaubt
❌ Ticketing, Projektmanagement, finali Unternehmensrichtlinie

### Source of Truth für
- Technischi Zämmehäng
- AI-Kontext
- Architekturwüsse
- Agent-Wissensnetz (Wikilinks)

### Zugriff (für anderi Agenten)
```
http://10.0.60.121:5984
user: obsidian_sync
pass: ObsidianSync_p6W7aB2yT9
Plugin: Self-hosted LiveSync (Obsidian Community Plugin)
```

---

## Layer 2: 🧬 Qdrant → Semantic Memory Layer

**Server:** 10.0.60.179:6333
**Collections:** goetschi_labs_contacts (218+), goetschi_labs_memory (386+)

### Zweck
Embeddings, semantischi Suechi, AI Retrieval, Langzeit-Memory.

### Erlaubt
✅ Embeddings, semantic recall, context retrieval

### Nöd erlaubt
❌ Originaldate verwalte, manuelli Bearbeitig

### Source of Truth für
**KEINE Primärdate.** Qdrant isch nume en **Index** — nöd d'Woorheit sälber.

### Wichtig
Qdrant spiegelt wider was i andere Layer (Obsidian, Jira, Confluence) gschribe wird.
Wenn d'Primärdate glöscht wird, isch de Qdrant-Eintrag nüm gültig.

---

## Layer 3: 📦 MinIO → Object Storage Layer

**Server:** 10.0.60.106:9000
**Credentials:** admin / Louis_one_13
**Buckets:** documents/, swarm-skills/

### Zweck
Dateie, Audio, Screenshots, PDFs, Modelle, Exporte.

### Source of Truth für
- Binärdate
- Medie (Bilder, Audio, Video)
- Grossi Assets (Modelle, Exports, Backups)

---

## Layer 4: 🐙 GitHub → Code Authority Layer

**Repo:** hermes-agent-skills (privat) → goetschi-labs/

### Zweck
Source Code, CI/CD, Versionierig, technischi Releases.

### Source of Truth für
- Produktionscode
- Infrastrukturcode
- Configs
- Skill-Verzeichnis (goetschi-labs/*)

---

## Layer 5: 🎫 Jira → Operational Task Layer

**URL:** goetschi.atlassian.net
**User:** michelgoetschi@gmail.com

### Zweck
Tickets, Bugs, Sprints, operativi Arbeit.

### Source of Truth für
- Task Status
- Priorisierig
- Delivery
- Aktuelli Arbeite

---

## Layer 6: 📚 Confluence → Official Company Knowledge

**URL:** goetschi.atlassian.net/wiki

### Zweck
Finali Policies, offizielli Dokumentation, Team-Guidelines,
Mitarbeiterwüsse.

### Source of Truth für
- Offizielli Prozäss
- Firmerichtlinie
- Finalisierti Doku

---

## Knowledge Lifecycle

Jedes Wüsse im System durchlauft 4 Phasä:

```
DRAFT ──→ REVIEWED ──→ VERIFIED ──→ ARCHIVED
  ↑           ↑              ↑              ↑
 AI        Mensch        Fachtrack       System
(Agent)   (Michel)      (Prod-Check)    (Cleanup)
```

### Wer darf was?

| Phase | Berechtigti | Nöd berechtigti |
|-------|------------|----------------|
| **DRAFT** erstelle | Hermes, Nova, Apollo (alli Agenten) | — |
| **DRAFT → REVIEWED** | Michel (oder Beauftragte) | Agenten |
| **REVIEWED → VERIFIED** | Nur Michel persönlich | Agenten, AI, Automatisme |
| **VERIFIED → ARCHIVED** | Admin / System-Setup | Automatischi Löschige |

### Regel
**AI-Agenten dürfen NUR DRAFT erstelle — nie öppis uf VERIFIED setze.**
Das verhindert Halluzinations-Chaos: Kei Agent chan us Versehe falschi
Informatione als "verified" markiere.

---

## Agent-Rollen-Matrix

| Agent | Primäre Layer | Fokus | Prinzip |
|-------|--------------|-------|---------|
| **Apollo** | Layer 4 (GitHub) + Layer 1 (Obsidian) | System Hacker, Deep Debugging, OSINT, Data Analysis, Root Cause Finding | GitHub first. Obsidian für Architekturwüsse. |
| **Hermes** | Layer 2 (Qdrant) + Layer 6 (Confluence) | Executor, Integrator, Automation, Cron Jobs, Pipelines, Workflow-Orch. | Qdrant Retrieval first. Confluence für Policies. |
| **Nova** | Layer 1 (Obsidian) + Layer 6 (Confluence) | Telephony, Voice, SOP Retrieval, User Interaction, Audio | Obsidian für SOPs. Confluence für Guidelines. |

### Zusammespiel
- **Apollo** baut / hackt → schribt Architekturwüsse i **Obsidian** (Layer 1)
- **Hermes** orchestriert / stabilisiert → nutzt **Qdrant** (Layer 2) für Retrieval, **Jira** (Layer 5) für Tasks
- **Nova** kommuniziert / interagiert → nutzt **Obsidian** (Layer 1) für SOPs, **Confluence** (Layer 6) für Guidelines
- **Gmeinsam:** Alli nutzed **GitHub** (Layer 4) für Code, **MinIO** (Layer 3) für Files

---

## Diagramm

```
┌─────────────────────────────────────────────────────────┐
│                    GOETSCHI LABS                         │
├───────────┬───────────┬───────────┬───────────┬─────────┤
│  APOLLO   │  HERMES   │   NOVA    │           │         │
│ Code+Infra│Orchestrier│ Comms/SOP │           │         │
├───────────┴───────────┴───────────┤           │         │
│                                    │           │         │
│  ┌─────┐ ┌──────┐ ┌─────┐ ┌────┐  │ ┌──────┐  │ ┌────┐  │
│  │ 🧠  │ │ 🧬  │ │ 📦  │ │ 🐙  │  │ │ 🎫  │  │ │ 📚  │  │
│  │Obsid│ │Qdrant│ │MinIO│ │GitHub│  │ │Jira │  │ │Confl│  │
│  │     │ │      │ │     │ │     │  │ │     │  │ │     │  │
│  │10.60│ │10.60 │ │10.60│ │goets│  │ │goets│  │ │goets│  │
│  │.121 │ │.179  │ │.106 │ │chi- │  │ │chi  │  │ │chi  │  │
│  │:5984│ │:6333 │ │:9000│ │labs │  │ │     │  │ │     │  │
│  └─────┘ └──────┘ └─────┘ └────┘  │ └──────┘  │ └────┘  │
│                                    │           │         │
│ Cognitive  Semantic   Object   Code │  Tasks    │  Docs    │
│ Knowledge  Memory    Storage  Auth  │           │          │
└─────────────────────────────────────────────────────────┘
```

# Schwarmwissen-Architektur — Goetschi Labs

Stand: 17.05.2026 | Ticket: GL-36 (Erledigt)

## Übersicht

Alle Agenten (Apollo/Hermes 156, Nova, zukünftige) teilen eine gemeinsame Wissensbasis
über zwei zentrale Systeme: **Qdrant** (Vektorsuche) und **Minio** (Datei-Backup/Skill-Storage).

```
                    AGENTEN
  Hermes (Apollo)    Nova (.121)    Zukünftige Agenten
         \               |               /
          \              |              /
           \             |             /
            ┌────────────┴────────────┐
            │        QDRANT           │
            │   10.0.60.121:6333      │
            │                         │
            │ goetschi_labs_contacts  │
            │ goetschi_labs_memory    │
            │ Test-RAG                │
            └──────────┬──────────────┘
                       │
            ┌──────────┴──────────────┐
            │        MINIO            │
            │   10.0.60.121:9000      │
            │                         │
            │ swarm-skills/           │
            │   └── qdrant-snapshots/ │
            │ hermes-backups/         │
            │ nova-backups/           │
            └─────────────────────────┘
```

## Datenfluss

### Wissen speichern (Agent → Qdrant)
1. Agent hat neue Erkenntnis (Infrastruktur, Credential, Workaround)
2. Embedding via fastembed (384d, multilingual-MiniLM-L12-v2)
3. Upsert in `goetschi_labs_memory` mit type/source/payload
4. Optional: gleichzeitiger Eintrag in Notion Knowlage DB

### Wissen abrufen (Agent liest Qdrant)
1. Agent hat Frage / braucht Kontext
2. Embedding der Frage via fastembed
3. Semantic Search auf `goetschi_labs_memory` (oder contacts)
4. Top-N Resultate mit Payload (Text, Source, Type)

## Collection-Schemas

### goetschi_labs_memory
```
{
  "text": "Der vollständige Wissenstext",
  "type": "infrastructure",   // infrastructure, skills, known-issue, architecture_decision, identity, notion, atlassian, docker, smarthome, archived
  "source": "apollo-conversation",  // system, sysadmin, user, apollo-conversation
  "created_at": "2026-05-17T12:00:00"
}
```

### goetschi_labs_contacts
```
{
  "display_name": "Hans Muster",
  "first_name": "Hans", "last_name": "Muster",
  "phones": [{"label": "Mobile", "value": "0791234567"}],
  "city": "Solothurn",
  "relationship": "friend",   // family, friend, business, emergency, unknown
  "embedding_text": "Hans Muster. Beziehung: Freund"
}
```

## Offene Punkte (laut GL-39)
- Telegram /kontakt Command für semantische Kontaktsuche auf Qdrant
- Notion-Sync: Kontakt-DB ↔ Qdrant (3-fach Backup)
- Updates bei CSV-Reimport

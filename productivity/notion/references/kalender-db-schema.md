# Kalender-DB — Master Calendar

**DS:** `28c81c83-f6d9-80a9-b82c-000b8dbe62a2`
**Typ:** Data Source (Notion Calendar Database)
**Beschreibung:** Plane und verwalte deine Kalender
**Teamspace:** Goetschi Labs

## Aktuelles Schema (Stand 22.05.2026)

| Property | Typ | Beschreibung |
|----------|-----|-------------|
| Inhaltsname | title | Event-Titel (z.B. "Tonio Entwicklung", "Fahrstunde", "Sing racing endlich anrufen") |
| Datum | date | Startzeit / Endzeit (ISO-8601 mit Timezone) |
| Notizen | relation | Relation zu Notizen-DB (DS: `28c81c83-f6d9-8074-a792-000b3dcbb19e`) |
| Kontakte | relation | Relation zu Kontakte-DB (DS: `28c81c83-f6d9-807f-bb4c-000b47295cea`) |
| Aufgaben | relation | Relation zu Aufgaben-DB (DS: `28c81c83-f6d9-80bb-909f-000b169fef92`) |
| Projekte | relation | Relation zu Projekte-DB (DS: `28c81c83-f6d9-80b1-9f36-000b9be4f083`) |
| Mehrfachauswahl | multi_select | Tags / Kategorien |

## Geplante Schema-Erweiterung (GL-65, 22.05.2026)

Zusätzlich zu bestehenden Properties:

| Property | Typ | Optionen | Zweck |
|----------|-----|----------|-------|
| **Quelle** | select | Hermes, Apollo, NOVA | Welcher Agent hat Event erstellt |
| **Beschreibung** | rich_text | — | Details, Links, Zusammenfassung |
| **Status** | status | Geplant, Aktiv, Abgeschlossen | Lebenszyklus des Events |
| **Google-ID** | rich_text | — | Google Calendar Event-ID für Upsert |

## Notion-as-Master-Calendar Pattern (Architektur)

### Problem
Alle drei Agenten (Hermes, Apollo, NOVA) teilen denselben Google OAuth-Token. Dieser läuft regelmässig ab (invalid_grant) und blockiert dann alle Calendar-Operationen.

### Lösung (Michel, 22.05.2026)
Notion Kalender-DB als **Single-Source-of-Truth** für alle Termine. Ein Hermes-Cron-Job synct periodisch die Notion-Kalenderdaten in den Google Calendar.

**Vorteile:**
- Notion-Auth (API-Key) läuft nicht ab — stabiler als OAuth
- Daten bleiben erhalten, auch wenn Google-Token stirbt
- Ein zentraler Sync-Cron statt 3 unabhängigen Calendar-Integrationen
- OAuth-Fehler nur beim Sync-Cron sichtbar — einfacheres Alerting

### Sync-Cron Architektur (Hermes, alle 3h, no_agent)

```
1. Query Notion Kalender-DB nach Events (letzte 48h + nächste 7 Tage)
2. Filter: wo Status != Abgeschlossen
3. Für jedes Event:
   a. Wenn Google-ID vorhanden: Google Calendar API Event updaten
   b. Wenn keine Google-ID: Neues Event erstellen, Google-ID in Notion speichern
4. Bei OAuth-Fehler:
   a. DM-Alert an Michel
   b. Cron pausieren bis Token erneuert (via setup.py --auth-url)
5. Log: Anzahl erstellte/geupdatete Events
```

### Agenten-Integration
- **Hermes:** Schreibt Cron-Job-Events in Kalender-DB, betreibt Sync-Cron
- **Apollo:** Liest/schreibt persönliche Termine in Kalender-DB
- **NOVA:** Liest/schreibt Kalender-Events (Journal-Termine, Briefings)

### Nächste Implementierungsschritte (aus GL-65)
1. Google OAuth-Token erneuern (Browser-Redirect via setup.py --auth-url)
2. Kalender-DB Schema erweitern (Quelle, Beschreibung, Status, Google-ID)
3. Sync-Script schreiben (Python, no_agent Cron)
4. Cron-Job anlegen (alle 3h, deliver origin falls Fehler)
5. Agenten umstellen: Crons schreiben in Notion, Sync-Cron übernimmt Google Calendar

## API-Zugriff

```bash
source /opt/data/home/.hermes/.env
DS_KALENDER="28c81c83-f6d9-80a9-b82c-000b8dbe62a2"
DB_KALENDER="28c81c83f6d980a9b82c000b8dbe62a2"

# Alle Events abfragen (nächste 7 Tage)
START=$(date -u -d "+0 days" +%Y-%m-%d)
END=$(date -u -d "+7 days" +%Y-%m-%d)
curl -s -X POST "https://api.notion.com/v1/data_sources/$DS_KALENDER/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "and": [
        {"property": "Datum", "date": {"on_or_after": "'"$START"'"}},
        {"property": "Datum", "date": {"on_or_before": "'"$END"'"}}
      ]
    },
    "sorts": [{"property": "Datum", "direction": "ascending"}]
  }'

# Neues Event erstellen
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "'"$DB_KALENDER"'"},
    "properties": {
      "Inhaltsname": {"title": [{"text": {"content": "Event-Titel"}}]},
      "Datum": {"date": {"start": "2026-05-22T14:00:00+02:00", "end": "2026-05-22T15:00:00+02:00"}}
    }
  }'
```

## Verknüpfungen
- **GL-65:** Notion-as-Master-Calender ticket
- **Cron Jobs DB:** Events in Kalender-DB referenzieren Cron-Einträge via relations

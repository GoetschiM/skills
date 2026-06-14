# Agent Sync Kalender — Notion DB Schema

Source of Truth for all agent cron events (Hermes, Apollo, NOVA). Wird alle 3h mit Google Calendar synchronisiert.

## DB IDs

| Parameter | Wert |
|-----------|------|
| **DB ID** | `36881c83f6d981378029fe74b56aaffa` |
| **DS ID** | `36881c83f6d812eafbc000bd2b39db3` |
| **Schema** | Siehe Notion-Skill: `productivity/notion` |

## Properties

| Property | Typ | Beschreibung |
|----------|-----|-------------|
| **Inhaltsname** | title | Name des Events, Prefix z.B. `🔁`, `📞`, `📊`, `📧` |
| **Datum** | date | Start-Zeitpunkt des Events (ISO 8601) |
| **Quelle** | select | Hermes / Apollo / NOVA — welcher Agent |
| **Beschreibung** | rich_text | Schedule-Info, Skills, Details |
| **Status** | select | Geplant / Aktiv / Abgeschlossen — für Cron-Events immer `Aktiv` |
| **Verknüpfung** | rich_text | Cron-Job-ID zum Cross-Reference (`Cron: ab2cf65e3682`) |

## Beispiel-Eintrag (curl)

```bash
CAL_DB_ID="36881c83f6d981378029fe74b56aaffa"
source /opt/data/home/.hermes/.env

curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "'"$CAL_DB_ID"'"},
    "properties": {
      "Inhaltsname": {"title": [{"type": "text", "text": {"content": "🔁 Self-Backup zu GitHub / Minio"}}]},
      "Datum": {"date": {"start": "2026-05-24T04:00:00+02:00"}},
      "Quelle": {"select": {"name": "Hermes"}},
      "Beschreibung": {"rich_text": [{"type": "text", "text": {"content": "Wöchentlich So 04:00 CH — Backup GitHub + MinIO"}}]},
      "Status": {"select": {"name": "Aktiv"}},
      "Verknüpfung": {"rich_text": [{"type": "text", "text": {"content": "Cron: ab2cf65e3682"}}]}
    }
  }'
```

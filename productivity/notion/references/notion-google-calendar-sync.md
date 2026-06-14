# Notion → Google Calendar Sync Architecture

Proposed architecture for decoupling agent calendar writes from Google Calendar OAuth.

## Problem

All three agents (Hermes, Apollo, NOVA) share one Google OAuth token stored at `~/.hermes/google_token.json`. This token expires periodically and the refresh fails with `invalid_grant`. When it breaks, no agent can create/update calendar events. Data in Notion stays safe, but the Google Calendar copy goes stale.

## Solution (Michel, 22.05.2026)

**Notion as Master Calendar** — agents write events to a dedicated Notion database. A single Hermes cron job syncs Notion → Google Calendar every 3-4 hours.

### Advantages

- Notion API key (static, no expiry) is the source of auth — never breaks
- Data survives Google OAuth failures
- One sync cron replaces three independent Calendar integrations
- OAuth errors only affect the sync cron, not agents — easier alerting

## Architecture

```
Agent (Hermes/Apollo/NOVA)
    │ POST /v1/pages (Notion Kalender DB)
    ▼
┌─────────────────────────────┐
│  📅 Kalender (Agent Sync)   │  ← Master Calendar in Notion
│  DB: 36881c83...            │
│  DS: 36881c83...            │
├─────────────────────────────┤
│  Properties:                │
│  · Inhaltsname (title)      │
│  · Datum (date)             │
│  · Quelle (select)          │
│  · Beschreibung (rich_text) │
│  · Status (select)          │
│  · Verknuepfung (rich_text) │
└──────────┬──────────────────┘
           │ Sync-Cron (alle 3h, no_agent)
           ▼
┌─────────────────────────────┐
│  Google Calendar            │  ← Mirror — read-only for agents
│  Calendar ID:               │
│  5f1b8749aab8428...@group.  │
└─────────────────────────────┘
```

## Sync Cron Workflow

1. Query Notion Kalender DB: events from last 48h + next 7 days
2. For each Notion event:
   - If no Google Calendar event ID stored → create new event
   - If existing ID found → update event (summary, date, description)
   - If Notion event deleted/archived → delete from Google Calendar
3. On OAuth failure (`invalid_grant`, `401`):
   - Log error, do NOT crash
   - Send DM to Michel with refresh instructions
   - Cron self-pauses until token renewed
4. Output: list of created/updated/deleted events per run

## Notion Kalender DB Schema (Agent Sync)

Data source: `36881c83-f6d9-812e-afbc-000bd2b39db3`
Database: `36881c83f6d981378029fe74b56aaffa`

| Property | Type | Options |
|----------|------|---------|
| Inhaltsname | title | Event name |
| Datum | date | Start + End (ISO 8601) |
| Quelle | select | Hermes, Apollo, NOVA |
| Beschreibung | rich_text | Event details |
| Status | select | Geplant, Aktiv, Abgeschlossen |
| Verknuepfung | rich_text | External IDs, links |

## Cron Setup

```bash
# Step 1: Ensure OAuth token works
python $HOME/.hermes/skills/productivity/google-workspace/scripts/setup.py --check

# Step 2: Write sync script
# → /root/.hermes/scripts/notion-to-google-calendar.py

# Step 3: Create cron (example — adjust schedule and OAuth check)
cronjob action=create \
  name="Notion Calendar Sync" \
  schedule="0 */3 * * *" \
  script="/root/.hermes/scripts/notion-to-google-calendar.py" \
  no_agent=true
```

## Next Steps (from GL-65)

1. Google OAuth token refresh (Michel runs `setup.py --auth-url`)
2. Write and deploy sync script
3. Create cron job (every 3h)
4. Update all agents: write calendar events to Notion instead of Google Calendar directly
5. Remove direct Google Calendar writes from agent skills

## Related Tickets

- **GL-65**: Google Calendar OAuth: Notion als Master-Kalender + Sync-Cron
- **GL-46**: Dach-Ticket Voice-Pipeline (referenced for multi-agent coordination)

---
name: notion
description: "Notion API + ntn CLI: pages, databases, markdown, Workers."
version: 2.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [NOTION_API_KEY]
metadata:
  hermes:
    tags: [Notion, Productivity, Notes, Database, API, CLI, Workers]
    homepage: https://developers.notion.com
---

# Notion

Talk to Notion two ways. Same integration token works for both — pick by what's available.

◆ **`ntn` CLI** — Notion's official CLI. Shorter syntax, one-line file uploads, required for Workers. macOS + Linux only as of May 2026 (Windows support "coming soon"). **Default when installed.**
◆ **HTTP + curl** — works everywhere including Windows. **Default fallback** when `ntn` isn't installed.

## Setup

### 1. Get an integration token (required for both paths)

1. Create an integration at https://notion.so/my-integrations
2. Copy the API key (starts with `ntn_` or `secret_`)
3. Store in `~/.hermes/.env`:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. **Share target pages/databases with the integration** in Notion: page menu `...` → `Connect to` → your integration name. Without this, the API returns 404 for that page even though it exists.

### 2. Install `ntn` (preferred path on macOS / Linux)

```bash
# Recommended
curl -fsSL https://ntn.dev | bash

# Or via npm (needs Node 22+, npm 10+)
npm install --global ntn

ntn --version    # verify
```

**Skip `ntn login` — use the integration token instead.** This works headlessly, no browser needed:
```bash
export NOTION_API_TOKEN=$NOTION_API_KEY      # ntn reads NOTION_API_TOKEN
export NOTION_KEYRING=0                       # don't try to use the OS keychain
```

Add those exports to your shell profile (or to `~/.hermes/.env`) so every session inherits them.

### 3. Choose path at runtime

```bash
if command -v ntn >/dev/null 2>&1; then
  # use ntn
else
  # fall back to curl
fi
```

Windows users: skip step 2 entirely until native `ntn` ships — Path B works fine. If you want CLI ergonomics now, install `ntn` inside WSL2.

## API Basics

`Notion-Version: 2025-09-03` is required on all HTTP requests. `ntn` handles this for you. In this version, what users call "databases" are called **data sources** in the API.

## Path A — `ntn` CLI (preferred, macOS / Linux)

### Raw API calls (shorthand for curl)
```bash
ntn api v1/users                                  # GET
ntn api v1/pages parent[page_id]=abc123 \         # POST with inline body
  properties[title][0][text][content]="Notes"
ntn api v1/pages/abc123 -X PATCH archived:=true   # PATCH; := is non-string (bool/num/null)
```

Syntax notes:
- `key=value` — string fields
- `key[nested]=value` — nested object fields
- `key:=value` — typed assignment (booleans, numbers, null, arrays)

### Search
```bash
ntn api v1/search query="page title"
```

### Read page metadata
```bash
ntn api v1/pages/{page_id}
```

### Read page as Markdown (agent-friendly)
```bash
ntn api v1/pages/{page_id}/markdown
```

### Read page content as blocks
```bash
ntn api v1/blocks/{page_id}/children
```

### Create page from Markdown
```bash
ntn api v1/pages \
  parent[page_id]=xxx \
  properties[title][0][text][content]="Notes from meeting" \
  markdown="# Agenda

- Q3 roadmap
- Hiring"
```

### Patch a page with Markdown
```bash
ntn api v1/pages/{page_id}/markdown -X PATCH \
  markdown="## Update

Shipped the prototype."
```

### Query a database (data source)
```bash
ntn api v1/data_sources/{data_source_id}/query -X POST \
  filter[property]=Status filter[select][equals]=Active
```

For complex queries with `sorts`, multiple filter clauses, or compound logic, pipe JSON in:
```bash
echo '{"filter": {"property": "Status", "select": {"equals": "Active"}}, "sorts": [{"property": "Date", "direction": "descending"}]}' | \
  ntn api v1/data_sources/{data_source_id}/query -X POST --json -
```

### File uploads (one-liner — biggest CLI win)
```bash
ntn files create < photo.png
ntn files create --external-url https://example.com/photo.png
ntn files list
```

Compare to the 3-step HTTP flow (create upload → PUT bytes → reference).

### Useful env vars
| Var | Effect |
|---|---|
| `NOTION_API_TOKEN` | Auth token (overrides keychain) — set this to your integration token |
| `NOTION_KEYRING=0` | File-based creds at `~/.config/notion/auth.json` instead of OS keychain |
| `NOTION_WORKSPACE_ID` | Skip the workspace picker prompt |

## Path B — HTTP + curl (cross-platform, default on Windows)

All requests share this pattern:

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

On Windows the `curl` shipped with Windows 10+ works as-is. PowerShell users can also use `Invoke-RestMethod`.

### Search
```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

### Read page metadata
```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Read page as Markdown (agent-friendly)

Easier to feed to a model than block JSON.

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Read page content as blocks (when you need structure)
```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Create page from Markdown

`POST /v1/pages` accepts a `markdown` body param.

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "properties": {"title": [{"text": {"content": "Notes from meeting"}}]},
    "markdown": "# Agenda\n\n- Q3 roadmap\n- Hiring\n\n## Decisions\n- Ship MVP Friday"
  }'
```

### Patch a page with Markdown

⚠️ **API Version 2025-09-03 format:** The markdown PATCH endpoint requires a `type` field. Simple `{"markdown":"..."}` does NOT work.

```bash
# Insert content (appends to page bottom)
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"type":"insert_content","insert_content":{"content":"## Update\n\nShipped the prototype."}}'

# Replace entire page content
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"type":"update_content","update_content":{"content":"## Full replacement\n\nNew content here."}}'

# Replace a range (start_line + end_line)
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"type":"replace_content_range","replace_content_range":{"start_line":3,"end_line":5,"content":"## New heading\n\nReplacement text"}}'
```

### Create page in a database (typed properties)
```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "xxx"},
    "properties": {
      "Name": {"title": [{"text": {"content": "New Item"}}]},
      "Status": {"select": {"name": "Todo"}}
    }
  }'
```

### Query a database (data source)
```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Active"}},
    "sorts": [{"property": "Date", "direction": "descending"}]
  }'
```
## Create a database

⚠️ **API Version trap:** `POST /v1/data_sources` with `Notion-Version: 2025-09-03` returns 400: "Creating new databases with data sources is not supported in this endpoint for API version 2025-09-03 and later."

**Use `POST /v1/databases` with the legacy API version instead:**

```bash
curl -s -X POST "https://api.notion.com/v1/databases" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "Done"}]}},
      "Date": {"date": {}}
    }
  }'
```

After creation, query the new database using the data_sources endpoint with `2025-09-03`:

```bash
DS_ID=$(curl -s "https://api.notion.com/v1/databases/$DB_ID" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | python3 -c "import sys,json; d=json.load(sys.stdin); ds=d.get('data_sources',[]); print(ds[0]['id'] if ds else '')")
curl -s -X POST "https://api.notion.com/v1/data_sources/$DS_ID/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"page_size": 50}'
```

### Update page properties
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

### Append blocks to a page
```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello from Hermes!"}}]}}
    ]
  }'
```

### File uploads (3-step flow)
```bash
# 1. Create upload
curl -s -X POST "https://api.notion.com/v1/file_uploads" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"filename": "photo.png", "content_type": "image/png"}'

# 2. PUT bytes to the upload_url returned above
curl -s -X PUT "{upload_url}" --data-binary @photo.png

# 3. Reference {file_upload_id} in a page/block payload
```

## Property Types

Common property formats for database items:

- **Title:** `{"title": [{"text": {"content": "..."}}]}`
- **Rich text:** `{"rich_text": [{"text": {"content": "..."}}]}`
- **Select:** `{"select": {"name": "Option"}}`
- **Multi-select:** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **Date:** `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- **Checkbox:** `{"checkbox": true}`
- **Number:** `{"number": 42}`
- **URL:** `{"url": "https://..."}`
- **Email:** `{"email": "user@example.com"}`
- **Relation:** `{"relation": [{"id": "page_id"}]}`

## API Version 2025-09-03 — Databases vs Data Sources

- **Databases became data sources.** Use `/data_sources/` endpoints for queries and retrieval.
- **Two-level ID access:**
  - `database_id` — used when creating pages: `parent: {"database_id": "..."}`
  - `data_sources[0].id` — the actual DS ID, nested under the `data_sources` array in the GET /v1/databases/{id} response. Extract with `ds[0]['id']`.
- Search returns databases as `"object": "data_source"` with the DS ID in the `id` field.

## Notion Workers (advanced, requires `ntn`)

Workers are TypeScript programs Notion hosts for you. One worker can expose any combination of:
- **Syncs** — pull data from external APIs into a Notion database on a schedule (default 30 min).
- **Tools** — appear as callable tools inside Notion's Custom Agents.
- **Webhooks** — receive HTTP events from external services (GitHub, Stripe, etc.) and act in Notion.

**Plan / platform gating:**
- CLI works on all plans. **Deploying Workers requires Business or Enterprise.**
- `ntn` is macOS/Linux only as of May 2026. Windows users need WSL2 or to wait for native support.
- Free through August 11, 2026; metered on Notion credits after.

### Minimal Worker

```bash
ntn workers new my-worker      # scaffold
cd my-worker
# Edit src/index.ts
ntn workers deploy --name my-worker
```

`src/index.ts`:
```typescript
import { Worker } from "@notionhq/workers";

const worker = new Worker();
export default worker;

worker.tool("greet", {
  title: "Greet a User",
  description: "Returns a friendly greeting",
  inputSchema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
  execute: async ({ name }) => `Hello, ${name}!`,
});
```

### Webhook capability

```typescript
worker.webhook("onGithubPush", {
  title: "GitHub Push Handler",
  execute: async (events, { notion }) => {
    for (const event of events) {
      // event.body, event.rawBody (for signature verification), event.headers
      console.log("got delivery", event.deliveryId);
    }
  },
});
```

After deploy: `ntn workers webhooks list` shows the URL Notion generates. Treat that URL as a secret — anyone with it can POST events unless you add signature verification.

### Worker lifecycle commands

```bash
ntn workers deploy
ntn workers list
ntn workers exec <capability-key> -d '{"name": "world"}'
ntn workers sync trigger <key>            # run a sync now
ntn workers sync pause <key>
ntn workers env set GITHUB_WEBHOOK_SECRET=...
ntn workers runs list                     # recent invocations
ntn workers runs logs <run-id>
ntn workers webhooks list
```

When asked to build a Worker, scaffold with `ntn workers new`, write the code in `src/index.ts`, set any secrets with `ntn workers env set`, and deploy. Notion's docs at https://developers.notion.com/workers cover the full API surface.

## Notion-Flavored Markdown (used by `/markdown` endpoints)

Standard CommonMark plus XML-like tags for Notion-specific blocks. Use **tabs** for indentation.

**Blocks beyond CommonMark:**
```
<callout icon="🎯" color="blue_bg">
	Ship the MVP by **Friday**.
</callout>

<details color="gray">
<summary>Toggle title</summary>
	Children indented one tab
</details>

<columns>
	<column>Left side</column>
	<column>Right side</column>
</columns>

<table_of_contents color="gray"/>
```

**Inline:**
- Mentions: `<mention-user url="..."/>`, `<mention-page url="...">Title</mention-page>`, `<mention-date start="2026-05-15"/>`
- Underline: `<span underline="true">text</span>`
- Color: `<span color="blue">text</span>` or block-level `{color="blue"}` on the first line
- Math: inline `$x^2$`, block `$$ ... $$`
- Citations: `[^https://example.com]`

**Colors:** `gray brown orange yellow green blue purple pink red`, plus `*_bg` variants for backgrounds.

Headings 5/6 collapse to H4. Multiple `>` lines render as separate quote blocks — use `<br>` inside a single `>` for multi-line quotes.

## Choosing the Right Path

| Task | mac / Linux | Windows |
|---|---|---|
| Read/write pages, search, query databases | `ntn api ...` | curl |
| Read a page for an agent to summarize | `ntn api v1/pages/{id}/markdown` | curl `/markdown` endpoint |
| Upload a file | `ntn files create < file` | 3-step HTTP flow |
| One-off API exploration | `ntn api ...` | curl |
| Build a sync / webhook / agent tool hosted by Notion | `ntn workers ...` | WSL2 + `ntn workers ...` |

## Notes

- Page/database IDs are UUIDs (with or without dashes — both accepted).
- Rate limit: ~3 requests/second average. The CLI doesn't bypass this.
- The API cannot set database **view** filters — that's UI-only.
- Use `"is_inline": true` when creating data sources to embed them in a page.
- Always pass `-s` to curl to suppress progress bars (cleaner agent output).
- Inline Teamspace databases: `/v1/databases/` may return 0 properties — use `/v1/data_sources/` instead. See `references/teamspace-inline-databases.md`.
- Pipe JSON through `jq` when reading: `... | jq '.results[0].properties'`.
- Notion also ships an MCP server now (`Notion MCP`, ~91% more token-efficient on DB ops than the previous version) — wire it via Hermes' MCP support if you want streaming Notion access from inside a session, but the paths above are enough for most one-shot tasks.
- ⚠️ **API-Version prüfen:** Wenn `/markdown` oder `append_blocks` en "error" git, kontrollier de **`Notion-Version` Header**. `2022-06-28` wird vom `/markdown`-Endpoint NICHT unterstützt (HTTP 400, zeigt nur "error"). Fix: `curl -H "Notion-Version: 2025-09-03"`.

## 🏢 Goetschi Labs — Company Workspace

**Teamspace Startseite:** https://www.notion.so/Teamspace-Startseite-4b881c83f6d9822a917481c8862f1d46
**Notion Integration:** "Michels new workspace" (Bot-ID: f43e644e-ec3f-4708-8746-0fed55d99ca7)
**Valid API Token:** `ntn_NOTION_TOKEN_1` (this token WORKS — the old one `ntn_NOTION_TOKEN_2` from config.yaml is STALE and returns "API token is invalid")

### Pages / Dokumente

| Name | ID / URL |
|------|----------|
| **Kontakte / Adressbuch** | https://www.notion.so/Kontakte-Adressbuch-36a81c83f6d981ff8347f6e61a0c742c |

### Verfuegbare Datenbanken

| Name | Beschreibung | ID |
|------|-------------|-----|
| **Trading Journal** | Page: 4 DBs (Accounts, Trades, Journals, Transactions) fuer MT5-Bot-Tracking. Clean-Slate-Start Mai 2026. Siehe `references/trading-journal-schema.md` fuers volle Schema | Page: `36781c83f6d9819ebd2cfeebee1152fa` |
| Cron Jobs | Autoritative Cron-Liste fuer alle Agenten | `36581c83f6d981ffa34cf31b77794956` |
| **Kalender** | Master-Kalender-DB fuer Termine aller Agenten (Hermes, Apollo, NOVA). Schema: Inhaltsname (title), Datum (date), Notizen/Kontakte/Aufgaben/Projekte (relations), Mehrfachauswahl. Siehe `references/kalender-db-schema.md`. | DS: `28c81c83-f6d9-80a9-b82c-000b8dbe62a2` |
| **Kalender (Agent Sync)** | Calendar fuer Hermes/Apollo/NOVA-Events. Schema: Inhaltsname (title), Datum (date), Quelle (select: Hermes/Apollo/NOVA), Beschreibung (rich_text), Status (select: Geplant/Aktiv/Abgeschlossen), Verknuepfung (rich_text). Sync alle 3h → Google Calendar. Siehe `references/notion-google-calendar-sync.md`. | DB: `36881c83f6d981378029fe74b56aaffa`, DS: `36881c83f6d812eafbc000bd2b39db3` |

**Cron Jobs DB Properties:**
- **Jobname** (title) -- Name des Cronjobs
- **Beschreibung** (rich_text) -- Beschreibung
- **Schedule** (rich_text) -- Zeitplan
- **Host** (select) -- NOVA LXC, Dokploy, Extern, **Hermes**, **Apollo**, **Nova**
- **Status** (select) -- Aktiv, Pausiert, Beendet
- **Typ** (select) -- Agent-Run, no_agent, Backup
- **Letzter Lauf** (date) -- Letzte Ausfuehrung

### API-Zugriff auf Cron Jobs DB

```bash
source /opt/data/home/.hermes/.env
DS_ID="36581c83-f6d9-8188-9f74-000b80fc93a6"
DB_ID="36581c83f6d981ffa34cf31b77794956"

# Alle Eintraege abfragen
curl -s "https://api.notion.com/v1/data_sources/$DS_ID/query" -X POST \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"page_size": 50}'

# Neuen Eintrag erstellen
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "parent": {"database_id": "'"$DB_ID"'"},
    "properties": {
      "Jobname": {"title": [{"type": "text", "text": {"content": "Jobname"}}]},
      "Beschreibung": {"rich_text": [{"type": "text", "text": {"content": "Beschreibung"}}]},
      "Schedule": {"rich_text": [{"type": "text", "text": {"content": "taeglich 03:00 UTC"}}]},
      "Host": {"select": {"name": "Hermes"}},
      "Status": {"select": {"name": "Aktiv"}},
      "Typ": {"select": {"name": "Backup"}}
    }
  }'
```

### Data Source Schema (Select-Optionen aktualisieren)

```bash
source /opt/data/home/.hermes/.env
DS_ID="36581c83-f6d9-8188-9f74-000b80fc93a6"

# Aktuelle Optionen lesen
curl -s "https://api.notion.com/v1/data_sources/$DS_ID" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"

# Host-Optionen mit Patch setzen
curl -s -X PATCH "https://api.notion.com/v1/data_sources/$DS_ID" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "properties": {
      "Host": {
        "select": {
          "options": [
            {"name": "NOVA LXC", "color": "blue"},
            {"name": "Dokploy", "color": "orange"},
            {"name": "Extern", "color": "purple"},
            {"name": "Hermes", "color": "green"},
            {"name": "Apollo", "color": "pink"},
            {"name": "Nova", "color": "yellow"}
          ]
        }
      }
    }
  }'
```

### Teamspace Startseite updaten

```bash
# Lesen
curl -s "https://api.notion.com/v1/pages/4b881c83f6d9822a917481c8862f1d46/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"

# Content anhaengen (insert)
curl -s -X PATCH "https://api.notion.com/v1/pages/4b881c83f6d9822a917481c8862f1d46/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"type":"insert_content","insert_content":{"content":"## Neue Section\n\nContent here..."}}'
```

### ⚠️ API Version Pitfalls (Zusammenfassung)

| Problem | Symptom | Fix |
|---------|---------|-----|
| **DB erstellen** | `POST /v1/data_sources` → 400 | `POST /v1/databases` mit `Notion-Version: 2022-06-28` |
| **Markdown update** | `update_content` → 400 | `update_content` schlägt fehl wenn d'API e neuere Format `content_updates`-Array erwartet. Workaround: `insert_content` (appends) statt `update_content`. Oder per `ntn` CLI patches mache. |
| **Pages with inline-DB markdown** | `GET /pages/{id}/markdown` gibt unvollständige Ausgabe | Inline-DBs (`is_inline: true`) werden nicht als child databases in der API abgebildet; erscheinen im markdown als `<database .../>` Tags, Inhalt bleibt separat erfassbar |
| **Markdown lesen** | `GET /pages/{id}/markdown` → 400 | `Notion-Version: 2025-09-03` verwenden (nicht 2022-06-28) |
| **Query data source** | `GET /v1/databases/{id}/query` → 0 results | `POST /v1/data_sources/{id}/query` mit `Notion-Version: 2025-09-03` (siehe Teamspace-inline-DBs) |

### Hinweis: TEAM-8 ist deprecated
Seit 19.05.2026 wird TEAM-8 (Jira) nicht mehr fuer Cron-Listen verwendet. Alle Crons gehoeren in die Notion Cron Jobs DB.

# Notion Teamspace Inline Databases

## The Problem

When Nova creates a database inline inside a Teamspace page (via Notion's new "Teamspace" feature), the database uses the new "data source" format. This causes two API quirks:

1. **`/v1/databases/{database_id}` returns 0 properties** — you can create pages in it, but the schema (select options, property types) is invisible.
2. **`/v1/data_sources/{data_source_id}`** works for reading schema and updating select options, but may return 404 if the integration wasn't explicitly shared with the individual database (not just the parent page).

## Two IDs: database_id vs data_source_id

Every inline Teamspace database has TWO IDs:

- **database_id** — used when creating pages via `parent: {"database_id": "..."}`
- **data_source_id** — used when querying entries and reading/updating schema

Both IDs can be extracted from the Teamspace page's markdown output:

```xml
<database url="https://www.notion.so/{slug}{database_id}" 
          inline="false" 
          data-source-url="collection://{data_source_id}">Name</database>
```

Extract them:
- **database_id**: last 32 characters of the `url` parameter (before any query string)
- **data_source_id**: the UUID after `collection://` in `data-source-url`

## Step-by-step workflow

### 1. Check the database schema

DO NOT use `/v1/databases/{id}` — it returns 0 properties:

```bash
# BAD: returns 0 properties for inline databases
curl -s "https://api.notion.com/v1/databases/{database_id}" -H "..."
```

USE `/v1/data_sources/{id}` instead:

```bash
# GOOD: returns full schema with select options
curl -s "https://api.notion.com/v1/data_sources/{data_source_id}" -H "..."
```

### 2. Update select options

To add a new Host option (e.g., "Hermes", "Apollo"):

```bash
source /opt/data/home/.hermes/.env

# First, get current options
curl -s "https://api.notion.com/v1/data_sources/{data_source_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" | python3 -c "import json,sys; d=json.load(sys.stdin); opts = d['properties']['Host']['select']['options']; print(json.dumps({'properties': {'Host': {'select': {'options': opts}}}}))" > /tmp/current_opts.json

# Edit /tmp/current_opts.json to add new options, then PATCH
curl -s -X PATCH "https://api.notion.com/v1/data_sources/{data_source_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2025-09-03" \
  -d @/tmp/current_opts.json
```

### 3. Create a page entry

USES `database_id` (NOT data_source_id):

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "parent": {"database_id": "{database_id}"},
    "properties": {
      "Jobname": {"title": [{"type": "text", "text": {"content": "Job Name"}}]},
      "Beschreibung": {"rich_text": [{"type": "text", "text": {"content": "Description"}}]},
      "Schedule": {"rich_text": [{"type": "text", "text": {"content": "taeglich 03:00 UTC"}}]},
      "Host": {"select": {"name": "Hermes"}},
      "Status": {"select": {"name": "Aktiv"}},
      "Typ": {"select": {"name": "Backup"}}
    }
  }'
```

The response parent will show `"type": "data_source_id"` — this is normal.

### 4. Query entries

USES `data_source_id`:

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"page_size": 50}'
```

## Gotchas

- **Rate limit**: ~3 req/s. Add `sleep 0.5` between batch operations.
- **execute_code sandbox**: sourcing `/opt/data/home/.hermes/.env` inside subprocess may not work due to missing `shell=True`. Use terminal() directly for multi-step workflows.
- **Page creation succeeds but subsequent read returns 404**: the integration was likely disconnected mid-session. Re-share the database in Notion UI.
- **New select options are auto-created** when you use a name that doesn't exist yet? NO — Notion returns validation error. You must PATCH the data_source first to add the option, then create the page.
- **Markdown PATCH** endpoint requires a `type` field: `{"type":"insert_content","insert_content":{"content":"..."}}`.

## Goetschi Labs workspace data (19.05.2026)

- Teamspace Startseite: `4b881c83-f6d9-822a-9174-81c8862f1d46`
- Cron Jobs DB: database_id=`36581c83f6d981ffa34cf31b77794956`, data_source_id=`36581c83-f6d9-8188-9f74-000b80fc93a6`
- Host options: NOVA LXC, Dokploy, Extern, Hermes, Apollo, Nova
- Integration: "Michels new workspace" (Bot-ID: f43e644e-ec3f-4708-8746-0fed55d99ca7)

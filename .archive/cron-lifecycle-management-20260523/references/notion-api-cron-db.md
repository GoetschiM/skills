# Notion Cron Jobs DB — API Reference

## IDs (CRITICAL — these are DIFFERENT!)

| Type | ID | Format |
|------|----|--------|
| **Data Source ID** (for queries) | `36581c83-f6d9-8188-9f74-000b80fc93a6` | With dashes |
| **Database ID** (for page creation) | `36581c83f6d981ffa34cf31b77794956` | **Without** dashes! |
| **DB ID for v1/databases** | `36581c83-f6d9-81ff-a34c-f31b77794956` | With dashes (derived from db ID) |

## Query endpoints

| Endpoint | URL | Works for | Notes |
|----------|-----|-----------|-------|
| Data source query | `POST /v1/data_sources/{DS_ID}/query` | ✅ Returns non-archived entries only | `archived: true` filter is **ignored** |
| Database query | `POST /v1/databases/{DB_ID}/query` | ❌ 400 error with wrong ID format | Only works with correct DB ID format |

## Page operations

| Operation | URL | Method | Version Header |
|-----------|-----|--------|----------------|
| Create page | `POST /v1/pages` | POST | `2025-09-03` or `2022-06-28` |
| Archive page | `PATCH /v1/pages/{page_id}` | PATCH | **MUST use `2022-06-28`** |
| Update properties | `PATCH /v1/pages/{page_id}` | PATCH | Either version works |

## Properties (German schema)

```json
{
  "Jobname": {"title": [{"type": "text", "text": {"content": "HERMES: Cron Name"}}]},
  "Beschreibung": {"rich_text": [{"type": "text", "text": {"content": "Description"}}]},
  "Schedule": {"rich_text": [{"type": "text", "text": {"content": "Mo-Fr 08:00 CH"}}]},
  "Host": {"select": {"name": "Hermes"}},
  "Status": {"select": {"name": "Aktiv"}},
  "Typ": {"select": {"name": "Agent-Run"}}
}
```

## Pitfalls discovered

1. **Data source ID ≠ database ID** — They are different UUIDs! The data source ID (`36581c83-f6d9-8188-9f74-000b80fc93a6`) works for `/v1/data_sources/` queries but NOT for `/v1/pages/` creation. For page creation, use the database ID without dashes (`36581c83f6d981ffa34cf31b77794956`) as `parent.database_id`.

2. **No reliable way to query archived entries** — The `POST /v1/data_sources/{DS_ID}/query` endpoint does NOT support filtering by `archived` status. Passing `{"archived": true}` in the body is silently ignored and returns all entries. The `POST /v1/databases/{DB_ID}/query` endpoint with `{"filter": {"archived": {"equals": true}}}` should work but requires the correct database ID format.

3. **Property names are case-sensitive** — `Jobname` not `jobname` or `JobName`. `Beschreibung` not `description`. Always use the exact German property names from the DB schema.

4. **Notion-Version header is CRITICAL** — The `2025-09-03` version returns HTTP 400 errors when PATCHing pages with `archived` field. Always use `2022-06-28` for PATCH operations. The `2025-09-03` version works for `POST /v1/data_sources/{DS_ID}/query`.

5. **After archiving, entries disappear from queries** — You can't verify the archive was successful by querying the DB. The entry simply won't appear in subsequent `data_sources/query` results. Check by trying to PATCH it again (will get 404) or verify the HTTP 200 response from the archive PATCH.

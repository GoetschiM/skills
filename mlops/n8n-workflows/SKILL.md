---
name: n8n-workflows
description: Build, deploy, and manage n8n workflows — including PostgreSQL-direct deployment, REST API operations, credential management, Google OAuth2 setup, LLM integration, and Gmail dispatch patterns. Covers Goetschi Labs n8n instance (CT100:5678) and generic n8n administration.
version: 1.0.0
author: Hermes Agent (Goetschi Labs)
tags: [n8n, workflow-automation, gmail, llm, pgvector, postgresql, goetschi-labs]
---

# n8n Workflows

n8n workflow automation for Goetschi Labs. The n8n instance runs on **CT100 (Dokploy)** at `10.0.60.121:5678` as Docker container `homelab-n8nwithpostgres-pzbt9a-n8n-1`.

## Database

n8n stores everything in a PostgreSQL database (`homelab-n8nwithpostgres-pzbt9a-postgres-1`).

- **DB user:** `michel`
- **DB name:** `n8n`
- **Key tables:**
  - `public.workflow_entity` — workflow definitions (nodes, connections, settings)
  - `public.shared_workflow` — ownership/permissions (links workflow to project)
  - `public.credentials_entity` — stored credentials (encrypted via N8N_ENCRYPTION_KEY)
  - `public.user` — users (email)
  - `public.user_api_keys` — API keys for the public REST API (when enabled)
  - `public.execution_entity` — execution history

### workflow_entity columns

| Column | Type | Notes |
|--------|------|-------|
| `id` | varchar(36) | UUID |
| `name` | varchar(128) | Workflow name |
| `active` | boolean | Is the workflow running? |
| `nodes` | json | Full workflow JSON (all nodes + parameters) |
| `connections` | json | Node connection graph |
| `versionId` | char(36) | UUID, NOT the auto-increment versionCounter |
| `settings` | json | Workflow settings |
| `staticData` | json | Static node data |
| `pinData` | json | Pinned test data |
| `triggerCount` | integer | Number of triggers (default 0) |
| `meta` | json | Optional metadata |
| `isArchived` | boolean | Default false |
| `versionCounter` | integer | Auto-incremented on update (trigger) |
| `createdAt` / `updatedAt` | timestamp(3) with tz | Default CURRENT_TIMESTAMP(3) |

### shared_workflow columns

| Column | Type | Notes |
|--------|------|-------|
| `workflowId` | varchar(36) | FK → workflow_entity |
| `projectId` | varchar(36) | FK → project |
| `role` | text | `'workflow:owner'` (with colon, NOT `'workflowOwner'`! See Pitfall #10) |
| `createdAt` / `updatedAt` | timestamp(3) with tz | |

### Deployment via PostgreSQL (when REST API is unavailable)

Useful when the N8N Public API is disabled (no `N8N_PUBLIC_API_ENABLED=true`), or you want to bypass auth.

**Pitfalls:**
- The `connections` JSON field is a **copy** of the connections from the full workflow JSON in the `nodes` field -- it must match exactly, but it's a **separate extract**. When generating a workflow JSON with a `connections` key, the DB has both: `nodes` (which includes `connections` inside each node) and a separate top-level `connections` column. Extract `connections` from your workflow JSON before inserting.
- `shared_workflow.text` role column (not `roleId` FK) -- plain text `'workflowOwner'`.
- JSON strings with newlines (`\n`) must have single quotes escaped: `'` -> `''`.
- The `versionId` is a UUID, not related to `versionCounter` (which is auto-incrementing).
- The encryption key (`N8N_ENCRYPTION_KEY` env var) encrypts credential data -- you cannot insert or read credentials via SQL.

**INSERT template:**

```sql
INSERT INTO public.workflow_entity (id, name, active, nodes, connections, "versionId", settings, "staticData", "pinData", "triggerCount", meta, "isArchived", "versionCounter")
VALUES (
  '<uuid>',
  'Workflow Name',
  false,
  '<full_workflow_json>'::json,
  '<connections_json>'::json,
  '<version_uuid>',
  '{}'::json,
  NULL,
  '{}'::json,
  0,
  NULL,
  false,
  1
);

INSERT INTO public.shared_workflow ("workflowId", "projectId", role)
VALUES ('<workflow_id>', (SELECT id FROM public.project LIMIT 1), 'workflow:owner');
```

**Python deployment pattern:**

```python
import subprocess, json, uuid

workflow = json.load(open('/tmp/workflow.json'))
connections = workflow['connections']

# Escape single quotes for PostgreSQL
workflow_json = json.dumps(workflow, ensure_ascii=False).replace("'", "''")
connections_json = json.dumps(connections, ensure_ascii=False).replace("'", "''")

ssh_cmd = [
    'sshpass', '-p', 'Riotstar_PROXMOX_13',
    'ssh', '-o', 'StrictHostKeyChecking=no',
    'root@10.0.60.10',
    'pct exec 100 -- bash -c \'docker exec -i homelab-n8nwithpostgres-pzbt9a-postgres-1 psql -U michel -d n8n\''
]

sql = f"""
INSERT INTO public.workflow_entity (id, name, active, nodes, connections, "versionId", ...)
VALUES ('{uuid.uuid4()}', 'My Workflow', false, '{workflow_json}'::json, '{connections_json}'::json, '{uuid.uuid4()}', ...);
INSERT INTO public.shared_workflow (...) VALUES (...);
"""

result = subprocess.run(ssh_cmd, input=sql, capture_output=True, text=True, timeout=30)
```

## N8N REST API

The N8N REST API is at `http://10.0.60.121:5678/rest/` and requires authentication.

### API Keys

When `N8N_PUBLIC_API_ENABLED=true`, API keys are stored in `public.user_api_keys`:

| Column | Description |
|--------|-------------|
| `id` | Key ID |
| `userId` | FK → user |
| `apiKey` | The actual key string |
| `scopes` | JSON array (e.g. `["workflow:read","workflow:write","workflow:execute"]`) |
| `audience` | `'public-api'` |

### Session-based login

```bash
# Login
curl -X POST http://10.0.60.121:5678/rest/login \
  -H 'Content-Type: application/json' \
  -d '{"emailOrLdapLoginId":"email","password":"pass"}'
```

The field is `emailOrLdapLoginId`, not `email` (400 error if wrong).

## Credentials

Credentials are stored encrypted in `public.credentials_entity`. Common types at Goetschi Labs:

| Name | Type | ID |
|------|------|-----|
| Gmail account | gmailOAuth2 | RkoRoxnN2gg5OKF |
| Home Assistant account | homeAssistantApi | ymT63jTOSOEkkPV |
| Notion account | notionApi | pZAEdQ4qnC8X3W1j |
| OpenRouter account | openRouterApi | wSiQRVAsZVIAdoLh |
| Ollama account | ollamaApi | UqyQDPXkE43Ml7rj |
| MinIO (homelab) | s3 | s3-minio-fresh |
| Paperless API | httpHeaderAuth | mXVoKsL6LT0t4bFT |
| NextCloud | httpBasicAuth | Bm7k2nnhQH4KsgAJ |
| Qdrant account | qdrantApi | PMDRed7GZmN2Ag9M |
| SSH Dokploy | sshPassword | wRamobvXtqlA3cI0 |
| Radislione LIVE02 Bot | telegramApi | *(created in N8N UI via BotFather token)* |

**Telegram Bot Credential:** To add a Telegram Bot to N8N:
1. Create a bot via @BotFather on Telegram → get token (`NNNNNNNNNN:AA...`)
2. In N8N UI: **Credentials → Add New → Telegram Bot**
3. Bot Name: `@YourBotName` (from BotFather), Access Token: the token
4. The credential ID is auto-generated by N8N (encrypted) — note it from the URL or use `SELECT id, name FROM credentials_entity WHERE type = 'telegramApi';`

**Important:** Credential data is encrypted with `N8N_ENCRYPTION_KEY`. You cannot **read or create** credential secrets via SQL. However, you **CAN attach existing credentials** to a workflow's nodes via SQL by setting the credential ID reference in the `nodes` JSON:

```sql
-- Set a node's credential reference in the workflow JSON
UPDATE workflow_entity 
SET nodes = jsonb_set(nodes, '{0,credentials}', 
  '{"gmailOAuth2": {"id": "RkoRoxnN2gg5fOKF", "name": "Gmail account"}}'::jsonb)
WHERE id = 'workflow-uuid';
```

The credential `id` (stored in `credentials_entity.id`) and `name` are NOT encrypted — only the `data` column (API keys, tokens, passwords) is encrypted. So you can freely update credential references in workflow node configurations via SQL.

## Gmail Dispatch Workflow Pattern

A proven pattern for intelligent email classification and notification:

1. **Gmail Trigger** (poll every 5 min) — checks for new emails
2. **Parse Email** — Code node: extract subject, from, snippet, messageId
3. **Priority Filter** — Rule-based: important senders → high, newsletter keywords → spam
4. **Spam Filter** — IF node: low-priority emails get silently dropped
5. **LLM Classification** — OpenAI/OpenRouter node: classify into PRIVAT/ARBEIT/RECHNUNG/TRADING/TECHNIK using OpenRouter (Goetschi Labs uses OpenRouter, not direct OpenAI)
6. **Parse Result** — Code node: extract category from LLM response
7. **Notification** — Two options:
   - **Telegram node** (n8n-nodes-base.telegram) — if Telegram Bot credential exists in N8N
   - **Hermes Webhook** (n8n-nodes-base.webhook POST) — when no Telegram credential is available; Hermes receives the POST and forwards to Telegram

**Key design choices:**
- Spam/newsletter emails are filtered BEFORE the LLM call (saves tokens)
- The LLM only sees non-spam emails for classification
- The message includes category tag (PRIVAT/ARBEIT/RECHNUNG/TRADING/TECHNIK), priority, sender, and subject
- No auto-actions (archive/delete) — always notify user first
- Using `openRouter` type instead of `openAi` for the LLM node (OpenRouter API is OpenAI-compatible)

### Hermes Webhook Notification (no Telegram Bot needed)

When N8N has no Telegram Bot credential, configure the final node as a webhook that POSTs to Hermes:

1. In Hermes, create a webhook subscription:
   ```bash
   hermes webhook add gmail-dispatch \
     --description "Gmail Dispatch Workflow Output" \
     --prompt "📬 **{subject}**\nVon: {from}\n📂 {category} | 🔵 {priority}\n📝 {summary}" \
     --deliver "telegram" \
     --deliver-only
   ```
   - `--deliver-only`: Hermes forwards directly to Telegram without LLM processing (zero token cost)
   - The webhook URL: `http://localhost:8644/webhooks/gmail-dispatch`
   - Requires Hermes Gateway running (`hermes gateway start` / `hermes gateway run`)

2. In N8N, replace the Telegram node with a **Webhook** node:
   - Type: `n8n-nodes-base.webhook`
   - Method: POST
   - Path: `/gmail-dispatch` (matches the Hermes webhook route name)
   - Options: Send Body = true
   - Body parameters: map `$json` fields to named parameters

3. **Important**: The N8N server must be able to reach the Hermes Gateway. If they're on the same local network, use the Hermes host's IP (e.g., `http://10.0.60.135:8644/webhooks/gmail-dispatch`) instead of `localhost`.

### Deploying Credential-Updated Workflow

To deploy credential references via SQL (fastest path when N8N API is disabled):

1. Get the credential IDs from `credentials_entity`:
   ```sql
   SELECT id, name, type FROM credentials_entity;
   ```

2. Update the `nodes` JSON in the workflow. The cleanest way is to extract just the nodes array from your workflow, update credential refs in Python, then update the DB:
   ```python
   import json, subprocess
   
   # Read workflow, extract nodes
   wf = json.load(open('workflow.json'))
   nodes = wf['nodes']
   
   # Add credentials to specific nodes
   nodes[0]['credentials'] = {
       "gmailOAuth2": {"id": "RkoRoxnN2gg5fOKF", "name": "Gmail account"}
   }
   
   # Generate SQL — escape single quotes for PostgreSQL
   nodes_json = json.dumps(nodes).replace("'", "''")
   sql = f"UPDATE workflow_entity SET nodes = '{nodes_json}'::jsonb WHERE id = 'workflow-uuid';"
   
   # Execute via psql in Docker
   subprocess.run([
       "sshpass", "-p", "PASS", "ssh", "root@10.0.60.10",
       "pct exec 100 -- docker exec -i homelab-n8nwithpostgres-pzbt9a-postgres-1 psql -U michel -d n8n"
   ], input=sql.encode(), timeout=15)
   ```

3. Activate the workflow:
   ```sql
   UPDATE workflow_entity SET active = true WHERE id = 'workflow-uuid';
   ```

**Critical SQL escaping**: Use `.replace("'", "''")` on the JSON string. Single quotes inside the JSON (e.g., `'` in email subject strings) must be doubled for PostgreSQL string literals. If you see a PostgreSQL error with `COPY` or `syntax error`, it's likely a single-quote escaping issue.

**Multi-layer shell escaping**: When running SQL from a local machine through `sshpass → ssh → bash heredoc → pct exec → docker exec → psql`, each layer strips or mangles quotes. See `references/db-shell-escaping.md` for proven patterns that handle this correctly.

See `templates/gmail-dispatch-workflow.json` for a ready-to-deploy workflow definition (no credentials).
See `templates/gmail-dispatch-workflow-credentials.json` for the complete nodes array with Gmail + OpenRouter credentials and Hermes webhook output.
See `templates/gmail-dispatch-workflow-telegram-credentials.json` for the complete nodes array with Gmail + OpenRouter + Telegram Bot credentials (requires Telegram credential created in N8N UI).

## PGVector Integration

PGVector on CT105 (10.0.60.141:5432) is reachable from CT100 (n8n container). For vector storage of email embeddings, use n8n's PostgreSQL node with pgvector SQL functions:
- Connect to `10.0.60.141:5432`
- Use `pgvector` extension functions: `vector_dims()`, `cosine_distance()`, `l2_distance()`

## Common Pitfalls

1. **N8N Public API disabled by default** — The env var `N8N_PUBLIC_API_ENABLED` is not set on Goetschi Labs n8n. API keys with `audience='public-api'` won't work. Use DB deployment instead.
2. **Single-quote escaping in SQL** — When deploying via DB, the JSON must have `'` → `''` for PostgreSQL string escaping. Use `json.dumps(workflow).replace("'", "''")`. But ALSO beware of shell quoting: if you pipe the SQL through bash (sshpass + ssh + pct exec + docker exec), the shell strips or mangles quotes at every layer. **Safest approach**: Write the SQL to a file, then `cat file | ... psql -f -`. Avoid inline heredocs with complex JSON.
3. **`connections` mirror mismatch** — The `connections` column in `workflow_entity` must exactly match the connections object inside the `nodes` JSON. If they diverge, the workflow will render in N8N but connections won't show.
4. **Credential encryption** — You cannot **read or create** credential secrets via SQL. The `data` column in `credentials_entity` is encrypted with `N8N_ENCRYPTION_KEY`. However you CAN attach existing credentials to workflow nodes via SQL (see Credentials section above).
5. **Only update `nodes`, not the full workflow JSON** — When deploying credential updates to an existing workflow, update ONLY the `nodes` column. Do NOT also update `connections` as a top-level column — the `connections` data inside `nodes` is the source of truth. Updating both can cause mismatches.
6. **Trigger doesn't fire immediately** — Set `active: true` in the DB or activate via UI after deployment. The workflow is deployed as inactive by default.
7. **OpenRouter node type does NOT exist** — There is NO `n8n-nodes-base.openRouter` node type in n8n. Attempting to use it will produce: `Unrecognized node type: n8n-nodes-base.openRouter`. The LLM node MUST use one of:
  - **`n8n-nodes-base.openAi`** (recommended — works with OpenRouter credentials because OpenRouter is OpenAI-compatible)
  - **`n8n-nodes-base.httpRequest`** (⚠️ fallback — hits OpenRouter API directly, BUT very fragile: the nested messages array must be a serialized JSON string, not a JSON object, making expression-based content (`{{$json...}}`) impossible. Prefer the `openAi` type — simpler, supports expressions, works identically with OpenRouter credentials.)

  **Option A: `openAi` type** (simpler):
  ```json
  "type": "n8n-nodes-base.openAi",
  "typeVersion": 2,
  "credentials": {
    "openRouterApi": {
      "id": "wSiQRVAsZVIAdoLh",
      "name": "OpenRouter account"
    }
  },
  "parameters": {
    "model": "openai/gpt-4o-mini",
    "messages": {
      "values": [
        {"role": "system", "content": "Klassifiziere Emails in Kategorien. Antworte NUR mit einem Wort."},
        {"role": "user", "content": "Von: {{ $json.from }}\nBetreff: {{ $json.subject }}"}
      ]
    },
    "options": {"maxTokens": 50, "temperature": 0.1}
  }
  ```
  The credential type (`openRouterApi`) matches the `openRouterApi` credential in the DB even though the node type is `openAi` — this works because OpenRouter extends the OpenAI API.

  **Option B: `httpRequest` type** (when the `openAi` approach somehow fails):
  ```json
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "credentials": {
    "openRouterApi": {
      "id": "wSiQRVAsZVIAdoLh",
      "name": "OpenRouter account"
    }
  },
  "parameters": {
    "method": "POST",
    "url": "https://openrouter.ai/api/v1/chat/completions",
    "authentication": "genericCredentialType",
    "nodeCredentialType": "openRouterApi",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {"name": "model", "value": "openai/gpt-4o-mini"},
        {"name": "messages", "value": "[{\"role\": \"system\", \"content\": \"...\"}, {\"role\": \"user\", \"content\": \"...\"}]"},
        {"name": "max_tokens", "value": 50},
        {"name": "temperature", "value": 0.1}
      ]
    },
    "options": {"timeout": 30000}
  }
  ```
  The downstream parse node then reads the response differently:
  - With `openAi` type: `$json.response` or `$json.choices[0].message.content`
  - With `httpRequest` type: `JSON.parse($json.body).choices[0].message.content`
8. **Updating credentials on an existing workflow via SQL** — When the workflow is already deployed but credentials need updating:
   - Extract ONLY the `nodes` array from your workflow JSON
   - Add credential blocks to the relevant nodes
   - Update via SQL: `UPDATE workflow_entity SET nodes = '<updated_nodes>'::jsonb WHERE id = '<workflow-uuid>';`
   - **Do NOT update `connections` as a separate column** — this must match the connections data inside `nodes`. Only update `nodes`.
   - To activate: `UPDATE workflow_entity SET active = true WHERE id = '<workflow-uuid>';`
9. **Telegram node type for N8N with direct Telegram Bot** — The Telegram notification node uses `n8n-nodes-base.telegram` type. The credential type is `telegramApi`. The credential must be created in the N8N UI (encrypted token) — you cannot create it via SQL. Node parameters support markdown parse mode for rich formatting.
10. **`shared_workflow.role` MUST be `'workflow:owner'` (with colon), NOT `'workflowOwner'`** — This is the most common deployment pitfall. If you insert `shared_workflow` with `role='workflowOwner'`, the workflow will appear in N8N UI but **Autosave will fail** with:
    ```
    Autosave failed: Could not find any entity of type "SharedWorkflow" matching:
    { "where": { "workflowId": "...", "role": "workflow:owner" }, "relations": ["project"] }
    ```
    N8N expects the role to match exactly `'workflow:owner'`. The INSERT template above is correct. If you've already deployed with the wrong role, fix it:
    ```sql
    UPDATE shared_workflow SET role = 'workflow:owner' WHERE "workflowId" = '<workflow-uuid>';
    ```
    No N8N restart needed — the fix takes effect immediately on next save attempt.

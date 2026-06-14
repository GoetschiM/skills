---
name: n8n-api-automation
description: "Programmatically create, activate, and manage n8n workflows and credentials via the REST API. Covers workflow JSON structure, credential types, webhook setup, and the specific quirks discovered on Goetschi Labs' n8n instance (10.0.60.121:5678)."
tags: [n8n, workflow, automation, api, credentials, devops]
category: devops
---

# n8n API Automation

Create and manage n8n workflows programmatically without the UI.

## Endpoints

Base: `http://10.0.60.121:5678/rest/`

| Action | Endpoint | Method |
|--------|----------|--------|
| Login | `/rest/login` | POST |
| List workflows | `/rest/workflows` | GET |
| Get workflow (+nodes) | `/rest/workflows/{id}` | GET |
| Create workflow | `/rest/workflows` | POST |
| Activate | `/rest/workflows/{id}/activate` | POST |
| Deactivate | `/rest/workflows/{id}/deactivate` | POST |
| List credentials | `/rest/credentials` | GET |
| Create credential | `/rest/credentials` | POST |
| List executions | `/rest/executions?workflowId={id}&limit=5` | GET |

## Authentication

**⚠️ CRITICAL: Cookie-based auth is REQUIRED. Bearer Token does NOT work for workflow API calls.**

The `/rest/login` endpoint returns user data (OK) PLUS a session cookie. That cookie is the only way to authenticate subsequent API calls. Using the Bearer token pattern (`Authorization: Bearer <token>`) against `/rest/workflows` returns **401 Unauthorized**.

```bash
# Login + save cookie jar
curl -s -c /tmp/n8n_cookies.txt -X POST "http://10.0.60.121:5678/rest/login" \
  -H "Content-Type: application/json" \
  -d '{"emailOrLdapLoginId":"michelgoetschi@gmail.com","password":"n8n2026!"}'

# All subsequent calls use -b to send the cookie
curl -s -b /tmp/n8n_cookies.txt "http://10.0.60.121:5678/rest/workflows"

# Alternatively, use Python with http.cookiejar.CookieJar:
# (See scripts/ section for a reusable helper)
```

**⚠️ Pitfall 1:** The login field is `emailOrLdapLoginId`, NOT `email`. Using `email` returns `{"code":"invalid_type","expected":"string","received":"undefined"}`.

**⚠️ Pitfall 2:** Cookie expires after some time. Re-login is needed periodically. Always login fresh before batch operations.

**Python auth pattern with CookieJar (reliable):**
```python
import urllib.request, http.cookiejar, json

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
data = json.dumps({"emailOrLdapLoginId":"michelgoetschi@gmail.com","password":"n8n2026!"}).encode()
req = urllib.request.Request("http://10.0.60.121:5678/rest/login", data=data,
                             headers={"Content-Type": "application/json"})
opener.open(req)

# Now opener has cookies, use it for all API calls
req = urllib.request.Request("http://10.0.60.121:5678/rest/workflows")
resp = opener.open(req)
workflows = json.loads(resp.read()).get('data', [])
```

**Reusable helper:** See `scripts/n8n_auth.py` for a complete `n8n_session` class that handles login, cookie management, GET/POST/PATCH, and utility methods like `list_workflows()` and `activate()`.
```

## Workflow JSON Structure

```python
import uuid

wf = {
    "name": "📄 My Workflow Name",
    "description": "What it does",
    "active": False,
    "settings": {"executionOrder": "v1"},
    "tags": ["tag1", "tag2"],
    "nodes": [
        {
            "id": str(uuid.uuid4()),
            "name": "Human-readable Name",
            "type": "n8n-nodes-base.httpRequest",  # node type
            "typeVersion": 4.2,                     # version matters
            "position": [250, 300],                 # [x, y] on canvas
            "parameters": {
                "method": "GET",
                "url": "http://example.com/api",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpBasicAuth",
                # ... more params
            },
            "credentials": {
                "httpBasicAuth": {
                    "id": "credential-id-here",
                    "name": "Credential Name"
                }
            }
        }
    ],
    "connections": {
        "Source Node Name": {
            "main": [[{"node": "Target Node Name", "type": "main", "index": 0}]]
        }
    },
    "homeProject": {"id": "f4PKHJYoUXQAMY4P"}  # Goetschi Labs home project ID
}
```

### Node Types Used

| n8n Type | Display | Notes |
|----------|---------|-------|
| `n8n-nodes-base.scheduleTrigger` | Schedule Trigger | `parameters.rule.interval[0]` = `{"field":"hours","hoursInterval":4}` |
| `n8n-nodes-base.webhook` | Webhook | `parameters.path` = unique path string |
| `n8n-nodes-base.manualTrigger` | Manual Trigger | No params needed |
| `n8n-nodes-base.httpRequest` | HTTP Request | typeVersion 4.2. For custom methods (PROPFIND, MOVE): `method: "CUSTOM"` + `customMethod: "PROPFIND"`. |
| `n8n-nodes-base.code` | Code | `parameters.language` = "python" or "javaScript". For JS, BOTH `code` AND `jsCode` params required. Sandbox blocks `require('http')` and `fetch()` — use HTTP Request nodes for network calls. |
| `n8n-nodes-base.splitInBatches` | Split In Batches | `parameters.batchSize` = 1 |

### Connections

Nodes are wired via the `connections` dict. Each key is the **source node name** (the `name` field in the node), and the value connects to the target:

```python
"connections": {
    "Schedule Trigger Name": {
        "main": [[{"node": "Next Node Name", "type": "main", "index": 0}]]
    },
    "Next Node Name": {
        "main": [[{"node": "Following Node", "type": "main", "index": 0}]]
    }
}
```

Multi-input connections (e.g., Webhook + Schedule → same node):
```python
"connections": {
    "Webhook Node": {
        "main": [[{"node": "Shared Target", "type": "main", "index": 0}]]
    },
    "Schedule Node": {
        "main": [[{"node": "Shared Target", "type": "main", "index": 0}]]
    }
}
```

## Credentials

### Create a credential (PRIOR to creating the workflow)

```python
cred = {
    "name": "NextCloud",
    "type": "httpBasicAuth",        # credential type
    "data": {
        "user": "michel",
        "password": "NextCloud2026!"
    },
    "homeProject": {"id": "f4PKHJYoUXQAMY4P"}
}
# POST /rest/credentials
```

### Available credential types for httpRequest nodes

| credentialType | data fields | Use case |
|---------------|-------------|----------|
| `httpBasicAuth` | `user`, `password` | NextCloud, any Basic Auth |
| `httpHeaderAuth` | `name` (header name), `value` (header value) | Paperless Token auth, API Keys |

### Reference in workflow nodes

```python
"credentials": {
    "httpBasicAuth": {         # must match the genericAuthType
        "id": "the-credential-id",
        "name": "NextCloud"
    }
}
```

HTTP Request node parameters for credential usage:
```python
"parameters": {
    "authentication": "genericCredentialType",
    "genericAuthType": "httpBasicAuth",  # matches the credential type
}
```

## Activating Workflows

There are TWO ways to activate/deactivate workflows. **POST /activate is more reliable** — PATCH active can silently fail (returns 200 without changing the status).

### Method A: POST /activate — PREFERRED (reliable)

```bash
# Activate
curl -s -b /tmp/n8n_cookies.txt -X POST "http://10.0.60.121:5678/rest/workflows/{id}/activate" \
  -H "Content-Type: application/json"

# Deactivate
curl -s -b /tmp/n8n_cookies.txt -X POST "http://10.0.60.121:5678/rest/workflows/{id}/deactivate" \
  -H "Content-Type: application/json"
```

These endpoints do NOT require a `versionId` in the body — n8n resolves it from the workflow's current active version automatically.

### Method B: PATCH (sometimes unreliable)

PATCH the workflow directly with `{"active": true}`. This does NOT require the `versionId`:

```bash
curl -s -b /tmp/n8n_cookies.txt -X PATCH "http://10.0.60.121:5678/rest/workflows/{id}" \
  -H "Content-Type: application/json" \
  -d '{"active":true}'
```

To deactivate:
```bash
curl -s -b /tmp/n8n_cookies.txt -X PATCH "http://10.0.60.121:5678/rest/workflows/{id}" \
  -H "Content-Type: application/json" \
  -d '{"active":false}'
```

### Inline Authentication (No Credential Store)

When credentials aren't saved in n8n (or you want to avoid "Credentials not found"), use `authentication: "none"` and embed credentials in the URL:

```
http://username:password%21@host:port/path
```

Password characters that need URL-encoding: `!` → `%21`, `@` → `%40`, `#` → `%23`, `:` → `%3A`.

**Why:** The HTTP Request node with `authentication: "genericCredentialType"` + `genericAuthType` requires a reference to a pre-saved credential. Without it you get `"Credentials not found"`. Inline auth bypasses this entirely.

### JWT Token Auth Pattern (form-urlencoded body + Bearer forwarding)

Some APIs use a two-step auth: POST form-urlencoded credentials → receive JWT → use JWT as Bearer token on next request. This works natively in n8n HTTP Request nodes:

**Step 1: Get the token**
```python
{
    "method": "POST",
    "url": "http://10.0.60.104:8080/token",
    "authentication": "none",
    "sendBody": True,
    "bodyContentType": "form-urlencoded",
    "contentType": "form-urlencoded",         # ⚠️ REQUIRED — without this n8n defaults to "json"
    "bodyParameters": {"parameters": [
        {"name": "username", "value": "radislione"},
        {"name": "password", "value": "rebelone_21"}
    ]}
}
```

**Step 2: Use the token (expression in header)**
```python
{
    "method": "GET",
    "url": "http://10.0.60.104:8080/api/status",
    "sendHeader": True,
    "headerParameters": {"parameters": [
        {"name": "Authorization", "value": "=Bearer {{ $json[\"access_token\"] }}"}
    ]}
}
```

**Why inline auth works here:** The token endpoint is a simple form-post with HTTP only — no credential store needed. The Bearer token from `$json[\"access_token\"]` is forwarded via expression in the header.

**⚠️ Pitfall:** The `=` prefix on the header value IS required for expression evaluation. Without `=`, the literal string `Bearer {{ $json[\"access_token\"] }}` is sent.

**⚠️ CRITICAL Pitfall:** `bodyContentType: "form-urlencoded"` alone is NOT sufficient. The n8n HTTP Request node (typeVersion 4.2) has a SEPARATE `contentType` parameter that defaults to `"json"`. Without explicitly setting `"contentType": "form-urlencoded"`, n8n sends the body as a JSON object (`{"username":"...","password":"..."}`) even though `bodyContentType` says form-urlencoded. The receiving API returns **HTTP 422** with `"field required"`. Always set BOTH `bodyContentType` AND `contentType` to `"form-urlencoded"` for token endpoints.

### Parallel Output Branches (Fork Execution)

n8n supports multiple output branches from a single node. Each entry in the `main` array represents one output:

```python
"connections": {
    "Source Node": {
        "main": [
            [{"node": "First Target", "type": "main", "index": 0}],    # Output 0
            [{"node": "Second Target", "type": "main", "index": 0}]    # Output 1
        ]
    }
}
```

Both recipients get the **same input data** from the source node — they run in parallel. This is useful for writing to two destinations simultaneously (e.g. Notion + Qdrant):

```python
"connections": {
    "📈 Bot04 Status": {
        "main": [
            [{"node": "📝 Notion Append", "type": "main", "index": 0}],
            [{"node": "🧠 Qdrant", "type": "main", "index": 0}]
        ]
    }
}
```

### Notion API — Append Children Blocks

n8n can write to a Notion page by PATCHing the children endpoint:

```python
{
    "method": "PATCH",
    "url": "https://api.notion.com/v1/blocks/{PAGE_ID}/children",
    "authentication": "none",
    "sendHeader": True,
    "headerParameters": {"parameters": [
        {"name": "Authorization", "value": "Bearer ntn_..."},
        {"name": "Notion-Version", "value": "2025-09-03"}
    ]},
    "sendBody": True,
    "bodyContentType": "json",
    "jsonBody": "={{(()=>{const d=$json[\"metrics\"];return {\"children\":[...]};})()}}"
}
```

**⚠️ Pitfall:** The `jsonBody` expression is a JavaScript IIFE (immediately invoked function expression) wrapped in `={{ }}`. The `(()=>{...})()` pattern is required because n8n evaluates the expression and passes the result as the body — it doesn't execute arbitrary code.

**⚠️ Notion API token expiry:** Notion integration tokens (`ntn_...`) can expire or be revoked. If the Notion node starts returning 401, the token has likely been rotated or expired. The current valid token is in the `productivity/notion` skill. **Always check token freshness against the Notion skill before debugging workflow logic** — a stale token looks like a workflow failure. The Notion page & database IDs are stable; only the token changes.

### Qdrant REST API — Upsert from n8n

n8n can write directly to Qdrant's REST API:

```python
{
    "method": "PUT",
    "url": "http://10.0.60.179:6333/collections/goetschi_labs_memory/points",
    "authentication": "none",
    "sendBody": True,
    "bodyContentType": "json",
    "jsonBody": "={{(()=>{...return {\"points\":[{\"id\":id,\"vector\":" + qdrant_vec + ",\"payload\":{...}}]};})()}}"
}
```

Key points:
- Collection name: `goetschi_labs_memory` (384-dim vectors)
- The vector array for dimension 384 looks like: `[0.001,0.001,...,0.001]`
- In code generation, build this array in Python and embed it into the expression string
- Point ID must be a string (UUID or timestamp-based) — integers are rejected
- Use the `stored_at` timestamp in the payload for time-range queries

### Activation via versionId

PATCH workflow with `{"active": true}` sometimes fails. The reliable approach:

```python
# 1. Get the workflow to extract versionId  
GET /rest/workflows/{id}
# → extract data.versionId

# 2. Activate with versionId
POST /rest/workflows/{id}/activate
{
    "versionId": "extracted-uuid"
}
```

Same pattern for deactivation.

## ⛔ Critical: WebDAV Operations (PROPFIND, MOVE) Need a Proxy

**`method: "CUSTOM"` + `customMethod: "PROPFIND/MOVE"` DOES NOT WORK.**

n8n V4.2 HTTP Request node sends literally "CUSTOM" as the HTTP method string. NextCloud returns:
> There was no plugin in the system that was willing to handle this CUSTOM method.

**Fix:** Run a Node.js proxy INSIDE the n8n container that uses native `http.request` (unrestricted). The workflow calls the proxy via standard GET/POST.

### WebDAV Proxy Pattern

A Node.js server inside the n8n container on an internal port (9876):

**Script location:** `scripts/install_webdav_proxy.sh` (run inside n8n container after Dokploy restart — installs proxy + health guard)
**Reference:** `references/n8n-webdav-proxy-pattern.md`

```
n8n Workflow -> GET/POST -> localhost:9876/list -> native http.request PROPFIND -> NextCloud
n8n Workflow -> GET/POST -> localhost:9876/upload -> download -> Paperless upload -> MOVE to processed/
```

**Proxy endpoints:**
| Endpoint | Method | Params | Returns |
|----------|--------|--------|---------|
| /list | GET | - | {items: [{filename, path, size}]} |
| /upload | GET | path, filename | {success, paperless_status, move_status} |
| /health | GET | - | OK |

**Why the proxy:**
- Native require(http) works (n8n sandbox blocks it)
- PROPFIND/MOVE sent as actual HTTP methods
- Manual multipart building for binary uploads (n8ns built-in multipart sends application/json)
- Can chain operations (download -> upload -> MOVE) in one call

**See:** `references/n8n-webdav-proxy-pattern.md` for complete proxy code and setup.

**Recovery script:** `scripts/install_webdav_proxy.sh` — one-shot install that creates the proxy, starts it, and deploys a guardian loop (30s health-check) that auto-restarts it on crash. Run inside the n8n container via Dokploy web terminal:
```bash
curl -s http://10.0.60.156:9877/install_webdav_proxy.sh | sh
```

### Dynamic Expression Quirks

**`{{ $json.path }}` in the `url` field does NOT evaluate.**

In V4.2 HTTP Request node, expressions in the URL string are sent literally (e.g. the proxy receives `path={{ encodeURIComponent($json.path) }}` as literal text).

**Workaround:** Use `queryParameters` with `sendQuery: true`:

```python
"parameters": {
    "method": "GET",
    "url": "http://127.0.0.1:9876/upload",
    "authentication": "none",
    "sendQuery": True,
    "queryParameters": {"parameters": [
        {"name": "path", "value": "={{ $json.path }}"},
        {"name": "filename", "value": "={{ $json.filename }}"}
    ]},
    "options": {"timeout": 120000, "response": {"responseFormat": "string"}}
}
```

The `={{ }}` syntax in parameter value fields IS evaluated correctly.

### Download binary file (this DOES work)

```python
"parameters": {
    "method": "GET",
    "url": "=http://10.0.60.121:8080/remote.php/dav/files/michel/Watchfolder/{{ $json.path }}",
    "authentication": "none",
    "options": {"timeout": 30000, "response": {"responseFormat": "file"}}
}
```

Note: For the download URL, `=` prefix + `{{ }}` DOES work consistently.

### JavaScript Code node: `{{ }}` in Python f-strings

When generating workflow JSON in Python, `{{` and `}}` in n8n expressions must be escaped in f-strings:
- `{{ $json.path }}` in n8n JSON needs `{{{{ $json.path }}}}` in the Python f-string
- Forgot this? Youll get single braces `{ $json.path }` which n8n treats as literal text

### Python f-string `$json` escaping in shell

When writing Python code that generates n8n JSON containing `$json`, the `$` must not be interpreted by the shell. Use `chr(36)` to build `$json` strings, or write the Python to a file first and execute it separately.

## Code Node (Python) — Parse WebDAV XML

```python
import xml.etree.ElementTree as ET
items = []
data = items[0].get('json', {})
body = data.get('body', '')
try:
    root = ET.fromstring(body)
    ns = {'d': 'DAV:'}
    for resp in root.findall('.//d:response', ns):
        href_el = resp.find('d:href', ns)
        if href_el is None: continue
        href = href_el.text or ''
        fn = href.rstrip('/').split('/')[-1] if href else ''
        if not fn or not fn.lower().endswith('.pdf'): continue
        items.append({'filename': fn, 'size': sz})
except Exception as e:
    return [{'error': str(e)}]
return items
```

## Known Pitfalls

1. **Workflow nodes/connections cannot be updated via PUT/PATCH** — `PUT /rest/workflows/{id}` and `PATCH /rest/workflows/{id}` with full node payloads return 404. Workflow node/connection definitions are immutable after creation. To modify: create a NEW workflow via POST with the updated nodes/connections, then delete the old one (requires archive first).
2. **WebDAV Proxy dies after Dokploy restart (28.05.2026)** — The Node.js proxy (port 9876) inside the n8n container does NOT survive a Dokploy container restart. Symptom: Doc Pipeline workflow → `ECONNREFUSED` on `localhost:9876` at the "List PDFs" node. Workaround (one-shot): `curl -s http://10.0.60.156:9877/install_webdav_proxy.sh | sh` inside the container (Dokploy Web Console or `docker exec`). Permanent fix: deploy the WebDAV proxy as a SEPARATE Docker container managed by Dokploy (see `dokploy` skill → "Container-interni Prozesse" for options).  
   **Exception:** PATCH with `{"active": true|false}` CAN work for activation, but is sometimes unreliable (returns 200 without changing status). **Use POST `/activate` and `/deactivate` instead** for reliable activation/deactivation.
2. **Webhook 404 on activation** — After activating, the webhook URL needs a moment to register. If you immediately call it, you get `404: webhook not registered`. Wait a few seconds or check execution list.
3. **Paperless POST expecting multipart** — The Paperless `/api/documents/post_document/` endpoint expects multipart form data with `title` and `document` (binary) fields. Use `bodyContentType: "multipart-form-data"` with `formBinaryData` field type.
4. **JavaScript Code node requires `jsCode`** — For `language: "javaScript"`, BOTH the `code` AND `jsCode` parameters must be set to the same source string. Without `jsCode`, the node runs empty code → `ERR_ASSERTION` / "Unknown error".
5. **Code node sandbox blocks HTTP** — `require('http')` → `"Module 'http' is disallowed"`, and `fetch()` → `"fetch is not defined"`. Use HTTP Request nodes for all network calls. Code nodes are for data transformation only.
6. **WebDAV (PROPFIND/MOVE) requires a Node.js proxy** — `method: "CUSTOM"` + `customMethod: "PROPFIND"` sends literally "CUSTOM" as the HTTP method. NextCloud rejects it. Run a Node.js proxy inside the container using native `http.request`, call via standard GET/POST.
7. **Schedule trigger format** — The interval format uses nested objects: `parameters.rule.interval[0] = {"field": "hours", "hoursInterval": 4}`.
8. **Inline auth avoids credential store** — `authentication: "none"` with `user:password@host` in URL avoids `"Credentials not found"`. Works for standard GET/POST only.
9. **Execution error inspection** — n8n compresses execution data as a JSON array with string interning. Parse via `json.loads(data['data'])`, then inspect index 5 (error detail), 6 (node → execution mapping), 7 (last executed node name). See `references/execution-error-inspection.md` for the complete parsing guide with dereferencing logic.
10. **HTTP Request `contentType` silently defaults to `"json"`** — Setting `bodyContentType: "form-urlencoded"` on an HTTP Request node is NOT sufficient. The node has a SEPARATE `contentType` parameter that defaults to `"json"` when unset. This causes n8n to send the body as a JSON object instead of form-urlencoded, with NO Content-Type header. APIs expecting form data return **HTTP 422** (`"field required"`). **Fix:** Explicitly set `"contentType": "form-urlencoded"` in the same node's parameters.
11. **`/rest/executions?workflowId={id}` filter is unreliable** — The n8n API may return executions from ALL workflows regardless of the filter parameter. Always verify each execution's `workflowId` field from the individual response. When searching for a specific workflow's executions, scan a wider range (limit=100-200) and filter client-side.
13. **WebDAV Proxy does NOT survive container restarts** — The Node.js proxy (`localhost:9876`) is a background process started manually. Docker/Dokploy container restarts **kill the proxy without restarting it**. The Doc Pipeline workflow then fails with `ECONNREFUSED` on the "List PDFs" node. Diagnosis: `docker exec <container> curl -sf http://127.0.0.1:9876/health` → no response = proxy down. **Fix:** Replace the old 24h-loop startup with a continuous health-check loop (checking every 30s), embed in n8n's entrypoint, or migrate n8n out of Dokploy entirely. See `references/n8n-webdav-proxy-pattern.md` → "Setup & Autostart → Critical: Proxy does NOT survive container restarts".

See `references/n8n-webdav-proxy-pattern.md` for the complete proxy code, setup instructions, and a full working workflow template.

## Security Updates

See `references/security-updates.md` for:
- Version check pattern (SSH → Docker → Node `package.json`)
- Security advisory handling workflow
- Update timeline table
- Upgrade instructions via Dokploy

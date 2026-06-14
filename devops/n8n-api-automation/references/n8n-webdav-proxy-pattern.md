# n8n WebDAV Proxy Pattern

## Problem

n8n's HTTP Request node V4.2 cannot:
1. Send PROPFIND/MOVE methods (sends "CUSTOM" literally)
2. Evaluate `{{ }}` expressions in the URL field
3. Send proper multipart/form-data with binary files

## Solution

Run a Node.js proxy inside the n8n container that uses unrestricted `http.request`.

## Proxy Code (webdav_proxy_v3.js)

```javascript
const http = require('http');
const CREDS = 'Basic ' + Buffer.from('michel:NextCloud2026!').toString('base64');
const NC = 'http://10.0.60.121:8080';
const PP = 'http://10.0.60.121:8015';
const TOKEN = '025610daa28037550aee9b80ee6387819106d792';

function wdav(method, path, opts) {
  return new Promise((ok, nok) => {
    const u = new URL(NC + path);
    const o = {hostname: u.hostname, port: u.port, path: u.pathname + u.search, method,
      headers: {'Authorization': CREDS, ...(opts?.headers||{})}, timeout: 30000};
    if (opts?.body) o.headers['Content-Length'] = Buffer.byteLength(opts.body);
    const r = http.request(o, (res) => {
      let d = ''; res.on('data', c => d += c); res.on('end', () => ok({status: res.statusCode, body: d}));
    });
    r.on('error', nok); r.on('timeout', () => { r.destroy(); nok(new Error('timeout')); });
    if (opts?.body) r.write(opts.body);
    r.end();
  });
}

function download(ncPath) {
  return new Promise((ok, nok) => {
    const u = new URL(NC + ncPath);
    http.get(u, {headers: {'Authorization': CREDS}, timeout: 30000}, (res) => {
      const chunks = []; res.on('data', c => chunks.push(c)); res.on('end', () => ok({status: res.statusCode, data: Buffer.concat(chunks)}));
    }).on('error', nok);
  });
}

function uploadPP(title, pdfBuffer) {
  return new Promise((ok, nok) => {
    const boundary = '----WebDAV' + Math.random().toString(36).substring(2);
    const head = '--' + boundary + '\r\nContent-Disposition: form-data; name="title"\r\n\r\n' + title + '\r\n'
      + '--' + boundary + '\r\nContent-Disposition: form-data; name="document"; filename="' + title + '.pdf"\r\nContent-Type: application/pdf\r\n\r\n';
    const tail = '\r\n--' + boundary + '--\r\n';
    const full = Buffer.concat([Buffer.from(head), pdfBuffer, Buffer.from(tail)]);
    const u = new URL(PP + '/api/documents/post_document/');
    const o = {hostname: u.hostname, port: u.port, path: u.pathname + u.search,
      method: 'POST', headers: {
        'Authorization': 'Token ' + TOKEN, 'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'Content-Length': full.length
      }, timeout: 120000};
    const r = http.request(o, (res) => { let d = ''; res.on('data', c => d += c); res.on('end', () => ok({status: res.statusCode, body: d, headers: res.headers})); });
    r.on('error', nok); r.on('timeout', () => { r.destroy(); nok(new Error('timeout')); });
    r.end(full);
  });
}

http.createServer((req, res) => {
  const u = new URL(req.url, 'http://localhost');
  const cors = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': '*', 'Access-Control-Allow-Headers': '*'};
  if (req.method === 'OPTIONS') { res.writeHead(204, cors); res.end(); return; }
  const jsonOk = (data) => { res.writeHead(200, {...cors, 'Content-Type': 'application/json'}); res.end(JSON.stringify(data)); };
  const jsonErr = (status, msg) => { res.writeHead(status, {...cors, 'Content-Type': 'application/json'}); res.end(JSON.stringify({error: msg})); };

  if (u.pathname === '/list') {
    const body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:displayname/><d:getcontentlength/></d:prop></d:propfind>';
    wdav('PROPFIND', '/remote.php/dav/files/michel/Watchfolder/', {headers: {'Depth': '1', 'Content-Type': 'application/xml'}, body})
      .then(r2 => {
        if (r2.status !== 207) return jsonErr(502, 'PROPFIND failed: '+r2.status);
        const files = [];
        const entries = r2.body.split('<d:response>');
        for (let i = 1; i < entries.length; i++) {
          const e = entries[i];
          const nm = e.match(/<d:displayname>([^<]+)<\/d:displayname>/);
          const hm = e.match(/<d:href>([^<]+)<\/d:href>/);
          if (!nm || !hm) continue;
          const fn = decodeURIComponent(nm[1].trim());
          if (fn === 'Watchfolder' || !fn.toLowerCase().endsWith('.pdf')) continue;
          files.push({filename: fn, path: hm[1], size: 0});
        }
        jsonOk({items: files});
      }).catch(e => jsonErr(500, e.message));

  } else if (u.pathname === '/upload') {
    const ncPath = u.searchParams.get('path');
    const fn = u.searchParams.get('filename');
    if (!ncPath || !fn) return jsonErr(400, 'Missing path/filename');
    const title = fn.replace(/\.pdf$/i, '');
    download(ncPath)
      .then(dl => { if (dl.status !== 200) throw new Error('Download failed: '+dl.status); return uploadPP(title, dl.data); })
      .then(pp => {
        if (pp.status < 200 || pp.status >= 300) throw new Error('Paperless upload failed: '+pp.status);
        const dest = NC + '/remote.php/dav/files/michel/Watchfolder/processed/' + encodeURIComponent(fn);
        return wdav('MOVE', ncPath, {headers: {'Destination': dest}})
          .then(mv => jsonOk({success: true, paperless_status: pp.status, move_status: mv.status, filename: fn, path: ncPath}));
      })
      .catch(e => jsonErr(502, e.message));

  } else if (u.pathname === '/health') {
    res.writeHead(200, {...cors, 'Content-Type': 'text/plain'}); res.end('OK');
  } else {
    res.writeHead(404, cors); res.end('Not found');
  }
}).listen(9876, '0.0.0.0', () => console.log('WebDAV proxy v3 on :9876'));
```

## Setup & Autostart

```bash
# Copy proxy to container
docker cp /tmp/webdav_proxy_v3.js homelab-n8nwithpostgres-pzbt9a-n8n-1:/tmp/

# Initial start
docker exec homelab-n8nwithpostgres-pzbt9a-n8n-1 node /tmp/webdav_proxy_v3.js &
```

### ❗ Critical: Proxy does NOT survive container restarts

When Dokploy crashes/restarts the n8n container, the proxy process is **lost**. There is no init system inside the container to auto-restart it. The n8n workflow "Doc Pipeline - Watchfolder to Paperless" will then fail with:

> **Error:** `ECONNREFUSED` on node **"List PDFs"** (HTTP Request → `http://127.0.0.1:9876/list`)

**Diagnosis:** If the Doc Pipeline workflow shows ECONNREFUSED, the proxy is down. Check with:
```bash
docker exec <n8n-container-name> curl -s http://127.0.0.1:9876/health
# → No response / connection refused = proxy is dead
```

**Fix options (choose one):**

#### Option A: Continuous health-check loop (reliable enough)
```bash
docker exec homelab-n8nwithpostgres-pzbt9a-n8n-1 sh -c "
cat > /tmp/proxy_guard.sh << 'GUARD'
#!/bin/sh
while true; do
  if ! curl -sf http://127.0.0.1:9876/health >/dev/null 2>&1; then
    echo 'Proxy down — restarting'
    node /tmp/webdav_proxy_v3.js &
  fi
  sleep 30
done
GUARD
chmod +x /tmp/proxy_guard.sh
nohup sh /tmp/proxy_guard.sh >/dev/null 2>&1 &
"
```

#### Option B: Embed proxy in n8n entrypoint (permanent fix)
Modify the Docker entrypoint or use a custom CMD that starts both n8n and the proxy. On Dokploy, this means editing the Dockerfile or using a startup command that launches both processes:
```bash
# /tmp/n8n_with_proxy.sh inside container
#!/bin/sh
node /tmp/webdav_proxy_v3.js &
exec n8n start  # or the original CMD
```

#### Option C: LXC migration (complete isolation)
Move n8n to a dedicated LXC container on Proxmox. This eliminates Dokploy-related restarts entirely and allows systemd-managed proxy startup.

## n8n Workflow JSON Structure

```python
wf = {
  "name": "Doc Pipeline - Watchfolder to Paperless",
  "nodes": [
    # Trigger: Webhook + Schedule + Manual -> List PDFs
    {"name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 1,
     "parameters": {"path": "doc-pp", "responseMode": "onReceived", "responseData": "allEntries"}},
    {"name": "Schedule", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.1,
     "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 4}]}}},
    {"name": "Manual", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1},
    # List PDFs: GET proxy /list
    {"name": "List PDFs", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
     "parameters": {"method": "GET", "url": "http://127.0.0.1:9876/list",
      "authentication": "none", "options": {"timeout": 30000, "response": {"responseFormat": "string"}}}},
    # Parse List: Code node - parse JSON string
    {"name": "Parse List", "type": "n8n-nodes-base.code", "typeVersion": 2,
     "parameters": {"code": "", "jsCode": parse_js, "language": "javaScript", "mode": "runOnceForAllItems"}},
    # Loop: SplitInBatches
    {"name": "Loop", "type": "n8n-nodes-base.splitInBatches", "typeVersion": 1,
     "parameters": {"batchSize": 1}},
    # Upload + Move: GET proxy /upload with queryParameters
    {"name": "Upload + Move", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
     "parameters": {"method": "GET", "url": "http://127.0.0.1:9876/upload",
      "authentication": "none", "sendQuery": True,
      "queryParameters": {"parameters": [
        {"name": "path", "value": "={{ $json.path }}"},
        {"name": "filename", "value": "={{ $json.filename }}"}
      ]},
      "options": {"timeout": 120000, "response": {"responseFormat": "string"}}}},
    # Success: Code node
    {"name": "Success", "type": "n8n-nodes-base.code", "typeVersion": 2,
     "parameters": {"code": "", "jsCode": success_js, "language": "javaScript", "mode": "runOnceForAllItems"}}
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "List PDFs", "type": "main", "index": 0}]]},
    "Schedule": {"main": [[{"node": "List PDFs", "type": "main", "index": 0}]]},
    "Manual": {"main": [[{"node": "List PDFs", "type": "main", "index": 0}]]},
    "List PDFs": {"main": [[{"node": "Parse List", "type": "main", "index": 0}]]},
    "Parse List": {"main": [[{"node": "Loop", "type": "main", "index": 0}]]},
    "Loop": {"main": [[{"node": "Upload + Move", "type": "main", "index": 0}]]},
    "Upload + Move": {"main": [[{"node": "Success", "type": "main", "index": 0}]]}
  },
  "settings": {"timezone": "Europe/Zurich", "saveManualExecutions": True},
  "tags": []
}
```

## Python Scripting Pattern

Always script n8n workflow creation in Python to avoid shell quoting issues with `$json`.

```python
D = "$"  # Use variable to avoid shell interpretation of $json

parse_js = f"""const data = typeof $json === 'string' ? JSON.parse($json) : $json;
if (data.items && data.items.length > 0) return data.items;
return [{{json: {{_noFiles: true}}}}];"""

success_js = f"""return [{{json: {{filename: $json.filename, success: $json.success}}}}];"""

wf_json = json.dumps(wf)
```

## Key Lessons

1. **`method: "CUSTOM"` does NOT work** for PROPFIND/MOVE — proxy is required
2. **URL `{{ }}` expressions NOT evaluated** — use `queryParameters` with `sendQuery: true` and `={{ }}` syntax
3. **n8n multipart sends wrong Content-Type** — proxy builds manual multipart buffer
4. **`jsCode` (NOT `code`)** is the correct parameter for JavaScript Code nodes
5. **`{{ }}` in Python f-strings** need `{{{{ }}}}` to produce `{{ }}` in JSON
6. **Archive before delete** — workflow lifecycle: archive -> delete -> create -> activate
7. **Always get a fresh login cookie** before API calls — old cookies expire

## Quick Install (Recovery From Dokploy Crash)

When Dokploy crashes and restarts the n8n container, the proxy is lost. Run this one-liner in the Dokploy web terminal (n8n container console):

```bash
curl -s http://10.0.60.156:9877/install_webdav_proxy.sh | sh
```

This creates the proxy, starts it on `localhost:9876`, and deploys a guardian loop (30s health-check) that auto-restarts the proxy if it dies again. The full script lives at `scripts/install_webdav_proxy.sh` in the n8n-api-automation skill directory.

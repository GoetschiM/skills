# System Discovery & Documentation — Methodology

A systematic approach for discovering an unknown running system (Docker/Dokploy/LXC), understanding its architecture, and documenting it comprehensively in Confluence.

## When to Use

- User says "find this system and document it"
- A new service/container is discovered that isn't documented
- An undocumented system needs analysis (code, DB, API, config)

## Discovery Pipeline (4 Phases)

### Phase 1: Locate the System

**Phase 1A — SSH into the host LXC/VM first:**
```bash
ssh root@<HOST-IP>
# Try known password patterns: Louis_one_*, HermesVB*, Riotstar_*
```

**Phase 1B — Layered inventory scan (always run ALL layers; some hosts lack Docker):**

Layer 1 — Listening ports (finds ALL services, no assumptions):
```bash
ss -tlnp                              # TCP ports + process names
```
Then curl-check every port found: `curl -s --max-time 5 http://<host>:<port>/`

Layer 2 — Running Docker containers (both commands):
```bash
docker ps --format '{{.Names}} {{.Image}} {{.Ports}} {{.Status}}'
docker compose ls                                                    # compose projects
```

Layer 3 — Stopped/inactive Docker containers (reveals paused/failed apps):
```bash
docker ps -a --format '{{.Names}}\t{{.Status}}'
```

Layer 4 — Non-Docker systemd services (for VMs/LXCs running services directly):
```bash
systemctl list-units --type=service --state=running --no-pager
ls /etc/systemd/system/*.service                    # custom services
```

Layer 5 — Project directories (containers, scripts, git repos):
```bash
ls /opt/                                            # standard project dir
ls /opt/docker/                                     # Docker project dirs
ls /root/                                           # root home projects
```

Layer 6 — Dokploy applications (complementary Docker view):
```bash
ls /etc/dokploy/applications/                       # all apps
ls /etc/dokploy/compose/<project>/code/             # compose projects
```

**Git remote (inside code directory):**
```bash
cd <code-dir> && git remote -v && cat .git/config
```

### Phase 2: Read Configuration & Metadata

**Always read (in this order):**
1. `.env` — Environment variables, credentials (REDACTED in docs)
2. `Dockerfile` / `docker-compose.yml` — Build process, ports, dependencies
3. `README.md` — Developer's own documentation
4. `package.json` (Node) / `requirements.txt` (Python) / `Cargo.toml` (Rust) — Dependencies
5. `.git/config` — Git remote URL (source repo)

**Database schema:**
For Prisma: `cat prisma/schema.prisma`
For SQLite: `sqlite3 <db> .tables && sqlite3 <db> .schema <table>`
For raw SQL: migration files in `prisma/migrations/`

### Phase 3: Understand Architecture

**Read key source files:**
- Backend entry point (e.g., `index.js`, `main.py`, `app.py`)
- Extract all API routes: `grep -n '\.get(\|\.post(\|\.put(\|\.delete(' <entry>`
- Read core modules (brain, pipeline, services)
- Frontend route pages: `find src/app -name 'page.js' -o -name 'page.jsx'`

**Identify key components:**
- Auth mechanism (JWT, OAuth, API key, basic auth)
- Database (PostgreSQL, SQLite, MySQL, etc.)
- Message broker (MQTT, Redis Pub/Sub, RabbitMQ)
- External services (Ollama, InfluxDB, Telegram, etc.)
- Cron jobs / scheduled tasks

**Document data flow:**
- How does data enter the system? (MQTT, API, scraping, webhook)
- How is it processed? (pipeline stages, cron cycles)
- Where is it stored? (DB tables, InfluxDB measurements, file system)
- How is it exposed? (API endpoints, Web UI pages, Telegram alerts)

### Phase 4: Document in Confluence

**Page structure (template):**

```html
<h1>System Name — Description</h1>

<h2>Übersicht</h2>
<table>
<tr><td>Status</td><td>🟢 / 🔴</td></tr>
<tr><td>Deployment</td><td>Dokploy (app-name)</td></tr>
<tr><td>Host</td><td>IP:Port</td></tr>
<tr><td>GitHub</td><td>link</td></tr>
<tr><td>Backend</td><td>Language/Framework (Port)</td></tr>
<tr><td>Frontend</td><td>Framework (Port)</td></tr>
<tr><td>Database</td><td>Host:Port / DB name</td></tr>
<tr><td>External Services</td><td>List</td></tr>
</tbody>
</table>

<h2>Architektur</h2>
<ac:structured-macro ac:name="code">
<ac:plain-text-body><![CDATA[
ASCII architecture diagram showing components and data flow
]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Zugangsdaten</h2>
<table>...</table>

<h2>API-Endpunkte</h2>
<h3>Auth</h3>
<ul><li><code>POST /api/auth/login</code> — description</li>...</ul>

<h2>Datenbank-Schema</h2>
<ac:structured-macro ac:name="code">
<ac:plain-text-body><![CDATA[
Tables with descriptions
]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Konfiguration (.env / settings.json)</h2>
<ac:structured-macro ac:name="code">
<ac:plain-text-body><![CDATA[
Key=Value pairs (passwords REDACTED)
]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Verwendung</h2>
<ol><li>Step 1...</li></ol>
```

**Confluence API usage:**
```python
body = json.dumps({
    "type": "page",
    "title": "Page Title",
    "space": {"key": "~5a75b5612d61371e861f4dae"},
    "ancestors": [{"id": "17170454"}],
    "body": {"storage": {"value": html_content, "representation": "storage"}}
})
req = urllib.request.Request(f"{BASE}/rest/api/content", data=body, headers=HEADERS, method="POST")
```

**Common parent page IDs:**
- Infrastruktur (containers, services): **17530881**
- Integrationen (APIs, connectors): **17170454**

## Pitfalls

- **SSH timeouts:** `find`/`grep` on remote hosts can timeout on large filesystems
- **Credentials in docs:** REDACT passwords/IPs in Confluence, keep in skill reference files
- **Docker builds fail:** Network issues pulling images (TLS timeout) — retry
- **No docker-compose.yml:** Dokploy UI-deployed apps only have Dockerfile; create compose for deployment
- **chart-data API param:** name `period` not `range`, returns list not dict
- **Different LXCs same host may have DIFFERENT passwords** — Louis_one_13 works for LXC 100 (Dokploy), but fails for LXC 106 (MinIO) and Proxmox hosts themselves. Try multiple password prefixes (Louis_one_*, HermesVB*, Riotstar_*, Admin_*!) across hosts.
- **Proxmox API auth vs SSH auth differ** — root/Louis_one_13 works for SSH on some LXCs but Proxmox Web-UI API auth returns "authentication failure". The Proxmox API uses PAM or Proxmox VE auth, not the container password.
- **systemd services > Docker ps** — Always run Layer 4 even if Docker is present. NOVA (LXC 167) had 6 systemd services with ZERO Docker containers for its core functionality.

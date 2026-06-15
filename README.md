# 🧠 Skills Hub — Goetschi Labs

Zentrales Skill Marketplace für Hermes Agent.  
Bestehend aus: **MCP-Server** + **Web-Frontend** mit Login, Dashboard, Skills-Explorer und Upload.

---

## 📦 Architektur

```
┌─────────────────────────────────────────────────┐
│  LXC 200 (10.0.60.149)                          │
│  ┌──────────────────────────────────────────┐   │
│  │  skills-hub.service (systemd)            │   │
│  │  python3 server/skills_mcp.py            │   │
│  │                                           │   │
│  │  ┌────────────────────────────────────┐   │   │
│  │  │  Port 8010 (HTTP)                  │   │   │
│  │  │                                     │   │   │
│  │  │  GET  /       → Frontend (index.html) │   │
│  │  │  GET  /style.css → Styles           │   │   │
│  │  │  GET  /app.js   → JavaScript SPA    │   │   │
│  │  │  GET  /api/     → Status (JSON)     │   │   │
│  │  │  POST /        → MCP JSON-RPC       │   │   │
│  │  │  POST /api/upload → Skill Upload    │   │   │
│  │  └────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐    ┌────────────────────┐
│  MCPHub (Gateway)   │◄──►│  GitHub Repo       │
│  10.0.60.170:3000   │    │  GoetschiM/skills   │
└─────────────────────┘    └────────────────────┘
```

---

## 🚀 Setup / Deployment

### 1. LXC 200 erstelle (Proxmox pve01)

```bash
pct create 200 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --storage local-lvm --rootfs 30 \
  --cores 2 --memory 4096 --swap 0 \
  --net0 name=eth0,bridge=vmbr1,ip=10.0.60.149/22,gw=10.0.60.1 \
  --unprivileged 1 --features nesting=1,keyctl=1
pct start 200
```

### 2. Docker installiere (optional, für Builds)

```bash
pct exec 200 -- bash
curl -fsSL https://get.docker.com | sh
```

### 3. Repo klonen

```bash
pct exec 200 -- git clone https://github.com/GoetschiM/skills.git /opt/skills
cd /opt/skills
```

### 4. MCP Server starte

```bash
# Abhängigkeiten
pct exec 200 -- pip install mcp httpx pyyaml python-dotenv

# Manuell starte
pct exec 200 -- python3 /opt/skills/server/skills_mcp.py --port 8010
```

### 5. Systemd Service

File: `/etc/systemd/system/skills-hub.service`

```ini
[Unit]
Description=Skills Hub MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/skills
Environment=SKILLS_REPO_PATH=/opt/skills
ExecStart=/usr/bin/python3 /opt/skills/server/skills_mcp.py --port 8010
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now skills-hub.service
```

### 6. Frontend deploye

D'Frontend-Dateie sind im `/opt/skills/frontend/` Ordner:

| File          | Grösse | Beschreibung                     |
|---------------|--------|----------------------------------|
| `index.html`  | 6.2 KB | SPA-Struktur mit Login + Views   |
| `style.css`   | 12 KB  | Dark Theme (Linear/Vercel Style) |
| `app.js`      | 14 KB  | JavaScript: API, Routing, UI     |

Zum aktualisiere: eifach d'Dateie überschribe und de Server automatisch neu servele (Hot-Reload-fähig).

---

## 🔌 API Reference

### Status (`GET /api/`)

```json
{
  "service": "goetschi-labs/skills-mcp",
  "version": "1.0.0",
  "status": "ok",
  "skills_count": 135
}
```

### MCP Tools (`POST /`)

JSON-RPC 2.0 via HTTP POST auf `/`

#### `list_skills`
```json
{
  "jsonrpc": "2.0", "id": 1,
  "method": "tools/call",
  "params": { "name": "list_skills", "arguments": {} }
}
```
Response: Array von Skill-Objekten `[{name, category, description, version, file}]`

#### `get_categories`
```json
{
  "jsonrpc": "2.0", "id": 2,
  "method": "tools/call",
  "params": { "name": "get_categories", "arguments": {} }
}
```
Response: Array von Category-Objekten `[{category, count, skills: [name, ...]}]`

#### `get_skill`
```json
{
  "jsonrpc": "2.0", "id": 3,
  "method": "tools/call",
  "params": { "name": "get_skill", "arguments": { "name": "skill-name" } }
}
```
Response: Skill-Objekt `{name, category, description, version, content, file}`

#### `pull_from_github`
```json
{
  "jsonrpc": "2.0", "id": 4,
  "method": "tools/call",
  "params": { "name": "pull_from_github", "arguments": {} }
}
```
Git pull vom GitHub Repo (braucht gültige Credentials im Container).

### Skill Upload (`POST /api/upload`)

```json
{
  "name": "my-skill",
  "category": "devops",
  "description": "Tolle Beschreibung",
  "version": "1.0.0",
  "content": "# SKILL.md\n..."
}
```
Legt en neui Datei `/<category>/<name>/SKILL.md` aa.  
Schreibt au `description` und `version` is YAML-Frontmatter.

---

## 🖥️ Frontend

### Login
- **User:** `michel`
- **Pass:** (im JS Hardcoded, siehe `app.js` Zeile 13-14)

### Views
| View        | Route           | Beschreibung                         |
|-------------|-----------------|--------------------------------------|
| Dashboard   | Standard        | Stats, Category-Chips, letzti Skills |
| Skills      | Skills-Explorer | Suchen, Filtere, Karte-Layout        |
| Detail      | Skill-Ansicht   | Markdown-Rendering, Meta-Info        |
| Upload      | Formular        | Neue Skills hochlade                 |

### Features
- ✅ Login mit Session-Storage
- ✅ Dashboard mit Live-Statistiken
- ✅ Skills Explorer mit Such- & Kategorie-Filter
- ✅ Detail-Ansicht mit Markdown-Rendering
- ✅ Upload-Formular (schreibt direkt uf Server)
- ✅ Responsive Design (Desktop + Mobile)
- ✅ Dark Theme (Linear/Vercel Style)

---

## 🔐 Credentials & Zugänge

> ⚠️ **Security Notice:** Die Credentials sind direkt im JavaScript hardcoded  
> (`app.js` Zeile 13-15) und via Browser-Inspect sichtbar.  
> Für Produktion: Backend-Auth oder Reverse-Proxy (Basic Auth) verwende.

| Service         | URL                  | Auth                    |
|-----------------|----------------------|------------------------|
| Skills Hub      | http://10.0.60.149:8010 | michel / Louis_one_13 |
| MCPHub          | http://10.0.60.170:3000 | Hermes / Louis_one_13 |
| GitHub Repo     | https://github.com/GoetschiM/skills | public (read-only) |
| Proxmox pve01   | 10.0.60.10           | root / Riotstar_* |
| LXC 200 (SSH)   | 10.0.60.149          | root / Louis_one_13 |

---

## 🔄 MCPHub Integration

Im MCPHub (10.0.60.170:3000) isch en API-Key `skills-hub` hinterlegt:

```
mcphub_231ecfb5e3837cbe682ae070ccadebc87f6bbb12977b66d451e0e5fd8170a0ac
```

Dä Key wird bim Server-Registriere bruucht:

```bash
curl -X POST http://10.0.60.170:3000/api/servers \
  -H "Authorization: Bearer mcphub_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "skills-hub",
    "type": "sse",
    "url": "http://10.0.60.149:8010"
  }'
```

---

## 🛠️ Entwicklung

### Neie Skill erstelle

```bash
mkdir -p /opt/skills/<category>/<skill-name>
cat > /opt/skills/<category>/<skill-name>/SKILL.md << 'EOF'
---
name: my-skill
category: devops
description: Kurzbeschreibung
version: 1.0.0
---

# My Skill

Skill-Beschreibung und Code...
EOF
```

### Lokal teste

```bash
cd /opt/skills
python3 server/skills_mcp.py --port 8010
curl http://localhost:8010/
curl -X POST http://localhost:8010/ -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_skills","arguments":{}}}'
```

### GitHub Push

```bash
cd /opt/skills
git add .
git commit -m "feat: neie skill XYZ"
git push
```

> **Hinweis:** Für Push wird en gültiger GitHub PAT im `/root/.git-credentials` oder per  
> `git remote set-url origin https://<token>@github.com/GoetschiM/skills.git` bruucht.

---

## 📋 Maintenance

| Was              | Command                                      |
|------------------|----------------------------------------------|
| Service neustarte | `pct exec 200 -- systemctl restart skills-hub` |
| Logs luege       | `pct exec 200 -- journalctl -u skills-hub -f` |
| Port checke       | `pct exec 200 -- ss -tlnp \| grep 8010`       |
| Skill-Count prüefe | `curl http://10.0.60.149:8010/api/`          |
| Backup Skils      | `rsync -av root@10.0.60.149:/opt/skills/ ~/skills-backup/` |

---

## ❗ Bekannti Problem / Limitatione

- **Keine Versionierung** (SemVer) — wird no nöd aktiv verfolgt
- **Keine Revision-Management** — Upload überschribt existierendi Dateie
- **GitHub Token** — Verwende de PAT us Vaultwarden (Eintrag "GitHub Personal Access Token (MCP)")
- **Auth im Frontend** isch hardcoded — nöd für Produktion mit öffentlichem Zugriff
- **MCPHub Registrierig** — Skills Hub isch uf 10.0.60.149:8010, MCPHub muess neu registriert werde

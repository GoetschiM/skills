---
name: goetschi-infra-reference
category: knowledge-management
description: >-
  Zentrales Infrastruktur Reference für Goetschi Labs — Hosts, Services,
  MCP-Server, Vaultwarden, Skills Hub, Credential-Workflow.
  Kann als Vorlage für jedes Homelab verwendet werden.
  Platzhalter (YOUR_*) durch eigene Werte ersetzen.
version: 1.0.0
tags: [infrastructure, reference, vaultwarden, mcphub, skills-hub, template]
---

# 🏗️ Infrastruktur Reference (Template)

Zentrale Dokumentation für alli Infrastruktur-Komponente.
**Source of Truth für Credentials isch Vaultwarden** (nöd Code).

> **Hinweis:** Das isch en Template. Ersetz alli `YOUR_*` Platzhalter mit dine eigene Werte.
> Meine IPs und Credentials sind bewusst rausgfiltred für de öffentlichi Skills Hub.

---

## 🖥 Hosts / Server

| Host          | IP             | SSH User | Zweck                     |
|---------------|----------------|----------|---------------------------|
| **Main**      | YOUR_PROXMOX_IP | root     | Haupt-Proxmox             |
| **App Host**  | YOUR_APP_HOST   | root     | Docker / App-Container    |
| **Gateway**   | YOUR_GATEWAY_IP | root     | Netzwerk-Gateway          |

### Container / VMs

| ID  | Name              | IP             | Zweck                     |
|-----|-------------------|----------------|---------------------------|
| 100 | app-host          | YOUR_APP_IP    | Docker Apps               |
| 107 | mcphub            | YOUR_MCPHUB_IP | MCPHub Gateway            |
| 200 | skills-hub        | YOUR_SKILLS_IP | Skills Hub                |
| ...  | ...               | ...            | Weitere nach Bedarf       |

---

## 🔌 MCPHub Gateway

**URL:** `http://YOUR_MCPHUB_IP:3000`  
**Health:** `http://YOUR_MCPHUB_IP:3000/health`  
**Auth:** Web UI Login (USER / PASS) + API Key

### MCP Server verwalte

```bash
# Server registriere
curl -X POST http://YOUR_MCPHUB_IP:3000/api/servers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "skills-hub",
    "type": "sse",
    "url": "http://YOUR_SKILLS_IP:PORT"
  }'
```

---

## 📦 Skills Hub

**URL:** `http://YOUR_SKILLS_IP:PORT`  
**Service:** skills-hub.service (systemd)  
**Git Repo:** `https://github.com/YOUR_USER/YOUR_REPO`  
**Frontend Login:** YOUR_USER / YOUR_PASS

### MCP Tools (POST /)

| Tool               | Beschreibung                        |
|--------------------|-------------------------------------|
| list_skills        | Alli Skills useliste                |
| get_categories     | Kategorie mit Skill-Count           |
| get_skill          | Detail zu eme Skill                 |
| pull_from_github   | Git pull vom Repo                   |
| upload_skill       | (via /api/upload) Neie Skill        |

---

## 🔐 Vaultwarden

**URL:** `https://pass.YOUR_DOMAIN`  
**Intern:** `http://vaultwarden:80` (Docker DNS)  
**Admin:** `https://pass.YOUR_DOMAIN/admin`

### API Auth (OAuth2)

```bash
# Token holen
curl -X POST http://vaultwarden:80/identity/connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=api" \
  -d "device_identifier=my-script" \
  -d "device_name=My+Script" \
  -d "device_type=2"

# Ciphers abrufen
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://vaultwarden:80/api/ciphers
```

### Python-Beispiel

```python
import urllib.request, urllib.parse, json

# Token holen
data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "scope": "api",
    "device_identifier": "my-script-001",
    "device_name": "My+Script",
    "device_type": "2"
}).encode()
req = urllib.request.Request(
    "http://vaultwarden:80/identity/connect/token",
    data=data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]

# Ciphers abrufen
req = urllib.request.Request("http://vaultwarden:80/api/ciphers")
req.add_header("Authorization", f"Bearer {token}")
resp = urllib.request.urlopen(req)
ciphers = json.loads(resp.read())
print(f"Found {len(ciphers['data'])} entries")
```

### Docker Compose (Deployment)

```yaml
version: '3.8'
services:
  vaultwarden:
    image: vaultwarden/server:latest
    restart: unless-stopped
    volumes:
      - vaultwarden-data:/data
    environment:
      - SIGNUPS_ALLOWED=false
      - DOMAIN=https://pass.YOUR_DOMAIN
      - ADMIN_TOKEN=YOUR_ADMIN_TOKEN
  vaultwarden-ssl:
    image: nginx:alpine
    ports:
      - "443:443"
      - "8100:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - vaultwarden
```

---

## 🔧 Credential Workflow

### Für Agenten: Credential abfrage
1. **MCPHub prüfe**: Git's en Vaultwarden-MCP Server?
2. Wänn ja: Tool `vaultwarden_list_ciphers` / `vaultwarden_get_credential`
3. Wänn nöd: User frage oder Confluence-Credential-Seite luege

### Credential speichere
1. Prüfe ob bereits in Vaultwarden
2. Wänn nöd: User frage obs gspiechert werde söll
3. **NIE** in Memory oder Code speichere — Vaultwarden isch Source of Truth

### Credential anzeige
- Niemals Credentials in Chats/Output zeige
- Nur bestätige "vorhanden" oder "nicht vorhanden"
- User-Credentials wo de User sälber git: zum *benutze*, nöd zum *dokumentiere*

---

## 🌐 GitHub MCP Server

Eigenständige MCP-Server für GitHub Repos/PRs/Issues.

### Tools
| Tool               | Beschreibung                      |
|--------------------|-----------------------------------|
| github_list_repos  | Repositories aufliste             |
| github_get_repo    | Repository Details                |
| github_list_prs    | Pull Requests aufliste            |
| github_get_pr      | PR Details                        |
| github_create_pr   | Pull Request erstelle             |
| github_list_issues | Issues aufliste (exkl. PRs)       |
| github_create_issue| Issue erstelle                     |

### Token aktualisiere (im MCP-Server Container)

```bash
# 1. Token als Hex codiere (voi: `echo -n "ghp_xxxx" | xxd -p`)
# 2. Im Container usfüehre:
python3 -c "
import codecs
h = 'YOUR_TOKEN_HEX'
token = codecs.decode(h, 'hex').decode()
with open('/path/to/github-mcp.py') as f:
    lines = f.readlines()
lines[3] = f'GITHUB_TOKEN=\"{token}\"\n'
with open('/path/to/github-mcp.py', 'w') as f:
    f.writelines(lines)
"
# 3. Container neustarte
docker restart YOUR_CONTAINER
```

---

## 🔑 Passwort-Schema (NUR als Referenz)

| System          | Schema               | Notiz                     |
|-----------------|----------------------|---------------------------|
| Proxmox         | Riotstar_*           | Main Server               |
| LXC/Docker      | Louis_one_13         | Standard LXC              |
| Agent-Mail      | ApolloHermes**       | Mailboxen                 |
| Web-Apps        | Admin_2026!          | Admin-Bereich             |
| Confluence      | Riotstar_*           | Wiki                      |

---

## ✅ Was du mache muesch für dini Version

1. **IPs ersetz:** Alli `YOUR_*` Platzhalter
2. **Credentials ersetz:** Vaultwarden-Login, API Keys
3. **Domains:** Deine Domain (wänn vorhande)
4. **Services:** Nur das verwende was du hesch
5. **MCP Server:** Eigeni Server z'MCPHub registriere
6. **GitHub Repo:** Falls du es chasch, miteme GitHub Actions Sync

---

## 🩺 Quick Checks

```bash
# Skills Hub
curl http://YOUR_SKILLS_IP:PORT/api/

# MCPHub
curl http://YOUR_MCPHUB_IP:3000/health

# Vaultwarden (Docker intern)
curl http://vaultwarden:80/alive

# Proxmox Host
ssh root@YOUR_PROXMOX_IP 'pct list'
```

---

## 📖 Wie ich de Skill verwende

**Empfehlig:** Chlonsch der s'GitHub Repo `GoetschiM/skills` und **kopiersch de Skill is din lokals Skills-Verzeichnis**:

```bash
# Lokal installiere
mkdir -p ~/.hermes/skills/knowledge-management/goetschi-infra-reference
cp /path/to/SKILL.md ~/.hermes/skills/knowledge-management/goetschi-infra-reference/

# Oder via Skills Hub (wänn erne verbunde):
curl -X POST http://localhost:PORT/ -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_skill",
      "arguments": {"name": "goetschi-infra-reference"}
    }
  }'
```

Dänn chasch de Skill lade über:
```
skill_view("goetschi-infra-reference")
```

# Google MCP Server — Vollständiger Deployment-Guide (Stand 07.06.2026)

Dieses Dokument beschreibt den **kompletten Prozess** von der OAuth-Authorisierung bis zum Deployment des Google Gmail MCP Servers auf MCPHub (CT107) sowie die Sicherheitsentscheidung: Gmail MCP nur via N8N, nicht via MCPHub API.

---

## 1. Die Google Cloud Credentials

Das Gmail MCP verwendet Michels Google-Konto (`michelgoetschi@gmail.com`). Das Google Cloud Project ist **"hermes-agent"** (Project ID: `hermes-agent`).

| Parameter | Wert |
|-----------|------|
| **Client ID** | `<GOOGLE_CLIENT_ID>.apps.googleusercontent.com` |
| **Client Secret** | `<GOOGLE_CLIENT_SECRET>` |
| **Project ID** | `hermes-agent` |
| **Token URI** | `https://oauth2.googleapis.com/token` |

Die `client_secret.json` liegt auf CT100 unter `/data/client_secret.json`.

---

## 2. Neuen OAuth-Token generieren (Browser-Flow)

Der alte Token war expired/revoked. Der **einzige funktionierende Weg** ist ein Direct-Browser-Link mit `redirect_uri=http://localhost`.

### Schritte

1. **OAuth-URL generieren** (Python):
   ```python
   import urllib.parse
   client_id = "<GOOGLE_CLIENT_ID>.apps.googleusercontent.com"
   scopes = [
       "https://www.googleapis.com/auth/gmail.readonly",
       "https://www.googleapis.com/auth/gmail.send",
       "https://www.googleapis.com/auth/gmail.modify",
       "https://www.googleapis.com/auth/calendar.readonly",
       "https://www.googleapis.com/auth/calendar.events",
       "https://www.googleapis.com/auth/drive.readonly",
       "https://www.googleapis.com/auth/drive.file",
   ]
   params = {
       "client_id": client_id,
       "redirect_uri": "http://localhost",
       "response_type": "code",
       "scope": " ".join(scopes),
       "access_type": "offline",
       "prompt": "consent"
   }
   url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(params)}"
   print(url)
   ```

2. **Link an User senden** (z.B. via Telegram). User klickt im Browser (Handy geht auch).

3. **⚠️ Wichtige Fallstricke:**
   - **Keine privaten IPs als redirect_uri:** Google blockt `10.x.x.x` mit `"device_id and device_name are required for private IP"`
   - **Kein OAuth Playground mehr nötig:** Der Direct-Link ist einfacher und funktioniert
   - **Telegram darf den Link nicht modifizieren:** Wenn Telegram eigene Parameter anhängt, kann Google `access_type` doppelt sehen → `"OAuth 2 parameters can only have a single value: access_type"`. Lösung: User lässt den Link kopieren und in den Browser einfügen (nicht im In-App-Browser öffnen).
   - **Kein `&` URL-Encoding Problem:** Wenn der Link zu lang ist, schreib ihn als Plain-Text (ohne Telegram-Markdown-Interferenz)

4. **Nach Consent:** User landet auf `http://localhost/?code=4/0A...&scope=...` (leere Seite, "Connection refused" — erwartet!). Aus der Browser-URL den `code` Parameter kopieren.

5. **Token eintauschen:**
   ```python
   import requests
   r = requests.post("https://oauth2.googleapis.com/token", data={
       "code": "<CODE_AUS_URL>",
       "client_id": "983053334079-...",
       "client_secret": "GOCSPX-...",
       "redirect_uri": "http://localhost",
       "grant_type": "authorization_code"
   }, timeout=15)
   tok = r.json()
   # tok hat: access_token, refresh_token, scope, expires_in
   ```

6. **Token persistieren** (z.B. als JSON in `/data/token.json`):
   ```json
   {
     "token": "ya29.a...",
     "refresh_token": "1//03I...bJAk",
     "token_uri": "https://oauth2.googleapis.com/token",
     "client_id": "983053334079-...",
     "client_secret": "GOCSPX-...",
     "scopes": ["https://...gmail.readonly", "..."],
     "expiry": "2026-06-08T18:00:00.000Z"
   }
   ```

---

## 3. Diagnose: Restart-Loop erkennen

**Symptom:** Docker-Container restartet dauernd (1.961+ Restarts).

**Diagnose:**
```bash
docker ps --filter "name=google-mcp" --format "table {{.Names}}\t{{.Status}}"
# Status: "restarting" — RestartCount im inspect zeigt 1961
docker logs google-mcp-server --tail 20
# Fehler: google.auth.exceptions.RefreshError: invalid_grant
```

**Ursache:** OAuth-Refresh-Token ist expired oder wurde revoked (z.B. wenn User den Zugriff in Google Security Settings entzogen hat).

**Fix:** Siehe Schritt 2 (neuer OAuth-Flow).

**Stoppen des Restart-Loops:**
```bash
docker stop google-mcp-server && docker rm google-mcp-server
```
Container läuft als Teil eines Dokploy-Stacks → ggf. auch im Dokploy-Dashboard deaktivieren.

---

## 4. stdio MCP-Server bauen (hand-crafted, kein Framework)

Der Google MCP Server wird als **reiner stdio-JSON-RPC-Server** gebaut (kein FastMCP, kein MCP-SDK). Läuft im MCPHub Docker-Container mit `python3`.

### Abhängigkeiten (im Container installieren)
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Server-Struktur (minimal)
```python
#!/usr/bin/env python3
"""Google Gmail MCP Server - stdio hand-crafted"""
import sys, os, json, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = "/data/token.json"

def get_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tok = json.load(f)
        creds = Credentials.from_authorized_user_info(tok)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

# Init
creds = get_creds()
service = build("gmail", "v1", credentials=creds, cache_discovery=False)

def handle_request(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "tools/list":
        return {"jsonrpc":"2.0","id":rid,"result":{"tools":[
            {"name":"gmail_search","description":"Search Gmail messages","inputSchema":{...}},
            {"name":"gmail_get_message", ...},
            {"name":"gmail_list_labels", ...},
            {"name":"gmail_send", ...},
            {"name":"gmail_modify_labels", ...},
            {"name":"gmail_trash", ...}
        ]}}

    elif method == "tools/call":
        tool = params.get("name","")
        args = params.get("arguments",{})
        # ... Gmail API calls via googleapiclient ...

    elif method == "initialize":
        return {"jsonrpc":"2.0","id":rid,"result":{
            "protocolVersion":"2024-11-05",
            "capabilities":{"tools":{}},
            "serverInfo":{"name":"google-gmail-mcp","version":"1.0.0"}
        }}

    elif method == "notifications/initialized":
        return {"jsonrpc":"2.0","id":rid,"result":{}}

# stdio loop
for line in sys.stdin:
    try:
        req = json.loads(line.strip())
        resp = handle_request(req)
        print(json.dumps(resp), flush=True)
    except json.JSONDecodeError:
        pass
```

**CRITICAL initialization order:** `initialize` → `notifications/initialized` → `tools/list` → `tools/call`. MCPHub sends them in this order.

**protocolVersion MUSS `"2024-11-05"` sein** — MCPHub v1.29.0 akzeptiert nichts anderes (weder "1.0" noch "0.1.0").

---

## 5. Deployment auf MCPHub (CT107)

### Script in Container kopieren
```bash
# Direkt via cat-pipe (docker cp scheitert oft bei Volume-Mounts)
cat /path/to/goetschi-gmail-mcp.py | docker exec -i mcphub bash -c \
  "cat > /root/mcp-servers/goetschi-gmail-mcp.py && chmod +x /root/mcp-servers/goetschi-gmail-mcp.py"
```

### Token in Container kopieren
```bash
# Token von Quelle holen und in Container schreiben
cat /data/token.json | docker exec -i mcphub bash -c \
  "mkdir -p /data && cat > /data/token.json"
```

### Config in MCPHub eintragen
Das MCPHub Config-File liegt im Container unter `/app/mcp_settings.json` (via Volume-Mount vom Host: `/opt/mcphub/mcp_settings.json`).

```python
cfg["mcpServers"]["goetschi-gmail"] = {
    "description": "Google Gmail API - Search, Read, Send, Label, Trash",
    "transport": "stdio",
    "command": "/usr/bin/python3",
    "args": ["/root/mcp-servers/goetschi-gmail-mcp.py"],
    "enabled": True   # oder False wenn nur via N8N
}
```

**Wichtig:** Der MCPHub liest Config nur **beim Start**. `docker restart mcphub` ist nötig nach Config-Änderungen. SIGHUP (kill -HUP 1) wird vom Container nicht verarbeitet.

### Verifikation
```bash
# Stdio-Direkt-Test (MCPHub-unabhängig)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  docker exec -i mcphub timeout 15 python3 /root/mcp-servers/goetschi-gmail-mcp.py

# MCPHub Health (12 statt 11 Server = Gmail MCP registriert)
curl -s http://10.0.60.170:3000/health
# total:12 = success
```

---

## 6. Sicherheit: Nur via N8N, nicht via MCPHub API

**Entscheidung (Michel, 07.06.2026):** Der Gmail MCP ist **nicht im MCPHub aktiv**. `enabled: false` in der Config.

**Begründung:** Der Refresh-Token hat volle Gmail/Calendar/Drive-Rechte auf Michels Konto. MCPHub hat nur einen einzigen Bearer-Token für alle Agenten — zu breit.

**Zugriff nur über N8N Workflow** (`http://10.0.60.121:5678`):
1. N8N pollt Gmail via eigenem Google OAuth oder via MCP-Tools
2. N8N hat eigene User-Auth (Michel legt Account an)
3. LLM-Entscheidung via LiteLLM (CT112:4000)
4. Telegram-Benachrichtigung an Michel

**Künftig:** Wenn andere Agenten Gmail-Zugriff brauchen, einen **eigenen Service-Account** (Google Workspace) erstellen, nicht Michels persönliches Konto teilen.

---

## 7. Gmail Tools (6)

| Tool | Beschreibung |
|------|-------------|
| `gmail_search(query, maxResults)` | Gmail-Nachrichten durchsuchen |
| `gmail_get_message(id)` | Einzelne Nachricht mit Headers + Body (Base64-decodiert) |
| `gmail_list_labels()` | Alle Labels auflisten |
| `gmail_send(to, subject, body)` | E-Mail senden |
| `gmail_modify_labels(id, addLabels, removeLabels)` | Labels hinzufügen/entfernen |
| `gmail_trash(id)` | In Papierkorb verschieben |

---

## 8. Ablauf (komplette Session vom 07.06.2026)

1. **Diagnose:** Google MCP Server auf CT100/Dokploy crasht (1.961 Restarts) → `RefreshError: invalid_grant`
2. **Container gestoppt & gelöscht** auf CT100 (war falscher Ort)
3. **Neuer OAuth-Flow:** Direct-Link-Methode mit `redirect_uri=http://localhost` → Code erhalten → Token generiert
4. **Gmail-only Token** (beim ersten Mal) → später mit allen Scopes neu authorisiert
5. **Stdio MCP-Server** (6.920 Bytes) hand-crafted geschrieben
6. **In MCPHub Container deployt** via `docker exec -i ... cat >`
7. **Pakete installiert:** 24 Google-Pakete im Container (pip install)
8. **Token in Container kopiert** (nach `/data/token.json`)
9. **MCPHub restart:** `docker restart mcphub` (SIGHUP funktioniert nicht)
10. **Verifiziert:** `tools/list` liefert 6 Tools ✅, `total:12` im Health-Endpoint ✅
11. **Sicherheit:** `enabled: false` gesetzt → nur N8N hat Zugriff
12. **Anleitung geschrieben:** `/root/MCPHub_Agenten_Zugriff.md`

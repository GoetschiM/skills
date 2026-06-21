# Google Workspace MCP v2 — Gmail, Calendar, Drive, Sheets, Docs

## Overview

Der Google Workspace MCP wurde am 07.06.2026 von 5 Tools (Docs/Sheets) auf **12 Tools** erweitert:
Gmail (6), Calendar (2), Drive (1), Sheets (2), Docs (1).

**Wichtigster Architektur-Regel:** ALLE MCPs gehören auf den MCPHub (CT107). N8N und andere Agenten verbinden sich **via MCPHub-API**, nicht direkt via OAuth-Token. Der MCPHub ist die Source of Truth.

## Deployment-Status

| Aspekt | Wert |
|--------|------|
| **Server-Name** | `google-workspace` (im MCPHub als `google-workspace` registriert) |
| **Script** | `/root/mcp-servers/goetschi-google-workspace.py` im Docker-Container |
| **Container** | CT107 (10.0.60.170:3000), MCPHub Docker |
| **Token-Datei** | `/data/token.json` im Container — OAuth2 Refresh-Token |
| **Dependencies** | `google-auth`, `google-api-python-client`, `google-auth-oauthlib` |
| **API-Scopes** | gmail.readonly, gmail.send, gmail.modify, calendar.readonly, calendar.events, drive.readonly, drive.file, spreadsheets.readonly, spreadsheets, documents.readonly |

## Script-Struktur

Das Script ist **hand-crafted stdio MCP** (kein MCP SDK, kein FastMCP) — ~11.335 Bytes, 160 Zeilen.
Es verwendet `googleapiclient.discovery.build()` für 5 Services.

### Tools (12)

| Tool | Service | Beschreibung |
|------|---------|-------------|
| `gmail_search` | Gmail | Nachrichten suchen (query, maxResults) |
| `gmail_get_message` | Gmail | Einzelne Nachricht mit Body |
| `gmail_list_labels` | Gmail | Labels auflisten |
| `gmail_send` | Gmail | Email senden (to, subject, body) |
| `gmail_modify_labels` | Gmail | Labels hinzufügen/entfernen |
| `gmail_trash` | Gmail | In Papierkorb verschieben |
| `calendar_list` | Calendar | Events auflisten (timeMin, timeMax) |
| `calendar_create_event` | Calendar | Event erstellen (summary, start, end) |
| `drive_list_files` | Drive | Dateien auflisten (query) |
| `sheets_read` | Sheets | Daten lesen (spreadsheetId, range) |
| `sheets_write` | Sheets | Daten schreiben (spreadsheetId, range, values) |
| `docs_get` | Docs | Dokument-Inhalt lesen (documentId) |

## OAuth Token Management

Der Token wird beim Start aus `/data/token.json` geladen. Falls expired:
```python
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
```

**Refresh-Token ist persistent** — wird automatisch erneuert, solange der initiale Consent gültig ist.

## Token-Deployment

Der Token gehört auf **alle** MCPHub Docker Container, die Google nutzen:

```bash
# Token in Container kopieren (als base64)
echo '<BASE64_TOKEN>' | pct exec 107 -- docker exec -i mcphub bash -c \
  "base64 -d > /data/token.json"

# Verify
pct exec 107 -- docker exec mcphub python3 -c "import json; tok=json.load(open('/data/token.json')); print('Has refresh_token:', bool(tok.get('refresh_token')))"
```

## OAuth-Flow (für neue Token) — **refined 07.06.2026**

Google erlaubt KEINE Redirects zu privaten IPs (10.x, 192.168.x). **Drei erfahrene Fallbacks:**

### ✅ Variante 1: `http://localhost` (empfohlen, funktioniert vom Handy)
```python
auth_url = (
    f"https://accounts.google.com/o/oauth2/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri=http://localhost"  # ONLY localhost works!
    f"&response_type=code"
    f"&scope={'+'.join(SCOPES)}"
    f"&access_type=offline"
    f"&prompt=consent"  # CRITICAL: ohne consent kein refresh_token
)
```

**Ablauf:**
1. User klickt Link → autorisiert in Google Browser (auch vom Handy via Telegram)
2. Wird zu `http://localhost/?code=...` weitergeleitet (Seite zeigt "Verbindung abgelehnt" = OK)
3. User kopiert `code=` Parameter aus der Browser-Adresszeile
4. Server tauscht Code gegen Token (access + refresh)

### ❌ Variante 2: Private IP (10.x.x.x) — BLOCKIERT
```
redirect_uri=http://10.0.60.10:8888
→ Error: "device_id and device_name are required for private IP"
→ Google erlaubt private IPs nur mit Mobile Device Management — nicht praktikabel
```

### ❌ Variante 3: Public IP — meist BLOCKIERT
Google OAuth erwartet dass die redirect_uri exakt mit der Authorized Redirect URI in der Google Cloud Console übereinstimmt. Ohne Konfiguration dort (nur `http://localhost` vorkonfiguriert) schlägt alles andere fehl.

### Folgefalle: Token-Gültigkeit

Der Authorization Code ist **nur 1 Stunde gültig**. Wenn der User nicht rechtzeitig antwortet:
```
error: invalid_grant, error_description: Bad Request
```
→ **Lösung:** User muss neuen Code authorisieren. Nach Erhalt des Codes SOFORT gegen Token tauschen.

## Config im MCPHub

MCP Eintrag in `/app/mcp_settings.json`:

```json
{
  "google-workspace": {
    "transport": "stdio",
    "command": "python3",
    "args": ["/root/mcp-servers/goetschi-google-workspace.py"],
    "enabled": true
  }
}
```

Achtung: Der Container hat `/app/mcp_settings.json` als Volume-Mount von `/opt/mcphub/mcp_settings.json` auf dem Host (inside LXC). Config-Änderungen werden nur nach `docker restart mcphub` wirksam.

## Pitfalls

1. **Token Location**: Der MCP sucht `/data/token.json` — nach `docker restart` ist das Verzeichnis leer (Container-Dateisystem reset). Token muss nach jedem Build neu deployed werden, es sei denn man baut ein custom Image.
2. **Pip packages are ephemeral**: `google-auth`, `google-api-python-client`, `google-auth-oauthlib` gehen nach `docker restart` verloren. Zwei Optionen: (a) nach jedem Restart neu installieren, oder (b) custom Docker-Image bauen.
3. **ModuleNotFoundError**: Das Script startet SOFORT nach `docker restart` — noch bevor jemand pip installieren konnte. Initialize fängt das mit `try/except ImportError` nicht ab (Script crashed). Lösung: Script muss robust sein gegen fehlende Pakete.
4. **rateLimitExceeded**: Bei `gmail_search` ohne Filter (query="") triggert Google Rate-Limits schnell. Immer mit `maxResults` und `query` arbeiten.
5. **calendar_list ohne timeMin**: Holt ALLE zukünftigen Events — bei vollem Kalender kann das 30+ Sekunden dauern. Immer `timeMin` setzen.

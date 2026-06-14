# PKCE OAuth Flow Fix (29.05.2026)

## Problem

`google_auth_exchange` schlug wiederholt fehl mit:
```
Error executing tool: (invalid_grant) Missing code verifier.
```

## Ursache

Google OAuth 2.0 verwendet seit 2024 PKCE (Proof Key for Code Exchange) als Pflicht.
Jeder `InstalledAppFlow` generiert beim Aufruf von `authorization_url()` einen zufälligen
`code_verifier` und speichert den dazugehörigen `code_challenge` in die Auth-URL.

Wenn `auth_url()` und `auth_exchange()` **separate** `InstalledAppFlow`-Instanzen
erstellen, haben sie unterschiedliche `code_verifier`:

```python
# ❌ FALSCH: Zwei unabhängige Flows
def auth_url():
    flow = InstalledAppFlow.from_client_secrets_file(...)  # Flow A
    url, _ = flow.authorization_url(...)  # challenge von Flow A in URL
    return url

def auth_exchange(code):
    flow = InstalledAppFlow.from_client_secrets_file(...)  # Flow B → ANDERER verifier!
    flow.fetch_token(code=code)  # ❌ verifier von Flow B passt nid zu challenge von Flow A
```

## Fix Option A: File-basierter PKCE State

PKCE Verifier in Datei speichern (`pkce_state.json`) und bim Code-Ischick us dere Datei lese:

```python
import json as _json, os as _os
_PKCE_FILE = "/data/pkce_state.json"

def auth_url():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    auth_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent",
    )
    with open(_PKCE_FILE, "w") as f:
        _json.dump({"code_verifier": flow.code_verifier}, f)
    return auth_url

def auth_exchange(code):
    if not _os.path.exists(_PKCE_FILE):
        return "Fehler: Kein PKCE State. Fuehre zuerst google_auth_url() aus."
    with open(_PKCE_FILE) as f:
        state = _json.load(f)
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    flow.code_verifier = state["code_verifier"]  # ✅ Explizit setze!
    flow.fetch_token(code=code)
    _save_credentials(flow.credentials)
    if _os.path.exists(_PKCE_FILE):
        _os.remove(_PKCE_FILE)
```

**Wichtig:** `flow.code_verifier = state["code_verifier"]` MUSS explizit gsetzt werde
VOR `fetch_token()`. S' `from_client_secrets_file` generiert automatisch en NEUE
code_verifier wo ignoriert wird.

## Fix Option B: Global-Variable Ansatz ✅ (aktuell deployed)

Die aktuell deployed Version verwendet einen **globalen `_AUTH_FLOW`**:

```python
# ── PKCE state (shared between auth_url and auth_exchange) ──────────────────
_AUTH_FLOW = None

def auth_url() -> str:
    global _AUTH_FLOW
    _AUTH_FLOW = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    _AUTH_FLOW.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    auth_url, _ = _AUTH_FLOW.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent",
    )
    return auth_url

def auth_exchange(code: str) -> str:
    global _AUTH_FLOW
    if _AUTH_FLOW is None:
        return "Fehler: Kein Auth-Flow. Fuehre zuerst google_auth_url() aus."
    try:
        _AUTH_FLOW.fetch_token(code=code)
        _save_credentials(_AUTH_FLOW.credentials)
        _AUTH_FLOW = None
        return "Google OAuth erfolgreich! Token gespeichert."
    except Exception as e:
        return "Fehler: " + str(e)
```

Beide Ansätze funktionieren — der globale ist einfacher.

### Warum globale Variable gescheitert SCHIEN (Debug-History)

In der Session vom 29.05.2026 wurde der globale Ansatz MEHRFACH getestet und
schien zu scheitern. Der wahre Grund war NIE die globale Variable selbst,
sondern **Deployment-Fehler**:

1. **`docker exec python3 -c` ≠ uvicorn-Prozess.** `docker exec` erzeugt
   einen SEPARATEN Python-Prozess. `patch` oder `global` in diesem Kontext
   modifiziert NICHT die Server-Module. Teste Änderungen immer via **curl**
   (echter HTTP Request), nie via `docker exec python3`.
2. **Datei-Edits via `docker exec -i python3` werden nicht persistiert**
   wenn das Python-Script einen Fehler hat (langer heredoc wird als
   daemon-detected blockiert).
3. **`docker cp` ist zuverlässiger** als `docker exec python3` für
   Datei-Manipulation in laufenden/stoppten Containern.
4. **Syntax Errors führen zu Restart-Schleife** — siehe Abschnitt unten.

## Container Restart-Schleife beheben

Wenn server.py einen Syntax Error hat, crasht der Container beim Start und
Docker restartet ihn automatisch. Der Container ist nur kurz "Up" — zu kurz
für `docker exec`.

**Recovery:**
```bash
docker stop google-mcp-server                        # Stop den Container
docker cp google-mcp-server:/app/server.py /tmp/     # Kopiere die kaputte Datei raus
# Fixe /tmp/server.py (z.B. Syntax-Fehler korrigieren)
docker cp /tmp/server.py google-mcp-server:/app/     # Kopiere die gefixte Datei rein
docker start google-mcp-server                        # Start neu
```

Schneller wenn du die Datei direkt aus der Source überschreibst:
```bash
docker stop google-mcp-server
docker cp /tmp/google-mcp-server/server.py google-mcp-server:/app/server.py
docker start google-mcp-server
```

## Deployment-Workflow für Code-Änderungen

**NIE per `docker exec python3` patchen!** Immer via rebuild oder docker cp:

**Mit Rebuild (empfohlen):**
```bash
# 1. Source-File ändere
vim /tmp/google-mcp-server/server.py

# 2. Bauen + Starten
docker stop google-mcp-server && docker rm google-mcp-server
docker build --no-cache -t google-mcp-server:latest /tmp/google-mcp-server
docker run -d --name google-mcp-server --restart unless-stopped \
  -p 8002:8002 -v /opt/data/google-mcp-server/data:/data \
  google-mcp-server:latest
```

**Ohne Rebuild (schnell, für kleine Fixes):**
```bash
# 1. Source-File ändere
vim /tmp/google-mcp-server/server.py

# 2. Kopiere + Restart (CAVE: docker build überschreibt)
docker cp /tmp/google-mcp-server/server.py google-mcp-server:/app/server.py
docker restart google-mcp-server

# 3. Verifiziere
docker logs google-mcp-server --tail 5  # Kein SyntaxError = OK
curl -s http://10.0.60.121:8002/mcp \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | head -c 200
```

## Test nach PKCE-Fix

```bash
# Schritt 1: Auth-URL holen
curl -s http://10.0.60.121:8002/mcp \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_auth_url","arguments":{}}}'

# Schritt 2: Code eintauschen
curl -s http://10.0.60.121:8002/mcp \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_auth_exchange","arguments":{"code":"4/xxx..."}}}'
# → "Google OAuth erfolgreich! Token gespeichert."

# Schritt 3: Health-Check
curl -s http://10.0.60.121:8002/mcp \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_health","arguments":{}}}'
```

## Fehler-Symptome

| Fehler | Ursache | Fix |
|--------|---------|-----|
| `(invalid_grant) Missing code verifier` | PKCE Verifier nid richtig übergeh | Gleichen Flow für auth_url + auth_exchange verwenden (global oder file) |
| `(invalid_grant) Bad Request` | Code abgelaufen (>5 Min) | Neuen auth_url generieren |
| `Kein gültiger Google Token` | token.json fehlt oder ungültig | OAuth wiederholen |
| `Token: NONE` beim Start | Volume nicht gemounted | `docker run -v /opt/data/google-mcp-server/data:/data` prüfe |
| `NameError: 'auth_url_with_pkce'` | Import aus externem Modul schlägt fehl | Funktion DIREKT in server.py definiere (kei Import) |
| `SyntaxError` nach Edit → Restart Loop | Syntax-Fehler in server.py | `docker stop` → `docker cp` fixte Datei → `docker start` |
| `406 Not Acceptable` | `Accept: application/json` fehlt | Header mitschicken |
| 14 statt 16 Tools via docker-proxy | Ungelöst (29.05.2026) | tools/call direkt verwenden statt tools/list |

## Referenz

- Google OAuth PKCE: https://developers.google.com/identity/protocols/oauth2/native-app#authorization-code-flow
- google_auth_oauthlib: https://google-auth-oauthlib.readthedocs.io/

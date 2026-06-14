# Coolify CT118 (10.0.60.139) — MT5 Deployment Target

**Entdeckt:** 13.06.2026 via Magos Goetschicus (Voice-Message)

## Übersicht

| Eigenschaft | Wert |
|-------------|------|
| Hostname | coolify |
| IP | 10.0.60.139 |
| LXC ID | CT118 |
| Host Machine | pve01 (10.0.60.10) |
| OS | Ubuntu/Debian LXC |
| Disk | 32GB (8.8G used, 21G frei) |
| RAM | 2GB (784MB used) |
| Docker | ✅ Läuft auf Host |

## Coolify Dashboard

| Eigenschaft | Wert |
|-------------|------|
| URL | `http://10.0.60.139:8000` |
| Dashboard Login | ✅ Browser-UI erreichbar (jetzt Login-Seite) |
| API | `http://10.0.60.139:8000/api/v1/` — benötigt API-Token |
| API Auth | 401 ohne Token |

**Zugriff von Hermes (Apollo, 10.0.60.156):**
- 🔴 **Kein SSH-Zugriff** — SSH Key von Apollo ist nicht auf CT118 hinterlegt. Confluence sagt root/Louis_one_13 aber SSH verweigert den Zugriff (Permission denied).
- 🔴 **Kein Coolify API Token** — muss aus Coolify-UI generiert werden (Settings → API Tokens). Nicht in Confluence, Notion, Session-Search, oder Memory gefunden.
- ✅ **MT5 Container API** ist direkt erreichbar: Port 3007

> **⚠️ Stand 13.06.2026 22:20:** Louis_one_13 **funktioniert NICHT** für SSH root@10.0.60.139 (Permission denied). Confluence sagt root/Louis_one_13 aber der SSH-Zugang ist nicht möglich. Kein API-Token in Confluence/Notion/Session-Search/Memory/Config gefunden. **Vorsicht beim Bauen:** Ohne SSH-Zugang kein Code-Deploy auf diesen Host. Alternativ: Coolify API Token nötig (via Coolify UI 10.0.60.139:8000).

## MT5 Container

| Eigenschaft | Wert |
|-------------|------|
| Image | `goetschi-labs-mt5-tradingbot:latest` |
| Container Name | MT5 (oder `goetschi-labs-mt5-tradingbot`) |
| Interner Port | 8080 |
| Host Port | **3007** |
| Läuft seit | ca. 07.06.2026 (6 Tage am 13.06.) |
| Status | ✅ Up & Healthy |
| API Response | `{"service":"MT5 Trading Bot","status":"migrated"}` |
| `/health` | `{"status":"ok"}` |

**Die aktuelle api.py ist NUR ein Dummy/Platzhalter:**

```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'service': 'MT5 Trading Bot', 'status': 'migrated'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## Single-Container Regel

**KRITISCH:** MT5, das API-Gateway (FastAPI) und Hermes MÜSSEN **alle im selben Docker-Container** laufen (User-Vorgabe). Keine Netzwerk-Verteilung! Kein separates LXC für MT5 + separater API-Container.

**Grund:** Nur so hat das Gateway direkten Zugriff auf das lokale MT5-Terminal (Wine/Desktop).

## Phase 1 — MT5 Gateway (Geplant)

Siehe `references/coolify-ct118-mt5-gateway.md` für den detaillierten Bauplan.

## Zugriff herstellen

Um Coolify CT118 von Hermes (Apollo) aus zu verwalten:

1. **Coolify API Token generieren:** In der Coolify UI (http://10.0.60.139:8000) → Settings → API Tokens
2. **Token in Hermes .env speichern** (oder über Confluence Credential-Seite)
3. **SSH Key hinterlegen:** Apollo's Public Key (`/root/.ssh/id_rsa.pub`) auf CT118 in `~/.ssh/authorized_keys` eintragen

## Deployment-Workflow (Phase 1)

1. Code auf Coolify-Host deployen via:
   - Coolify API (wenn Token vorhanden)
   - Oder direkt auf CT118 via SSH (wenn Key hinterlegt)
   - Oder Docker-Volume/Config-Management
2. FastAPI Gateway + MT5 + Hermes im gleichen Container
3. Container neu bauen: `cd /opt/mt5/ && docker compose build --no-cache && docker compose up -d`
4. Verifizieren: `curl http://10.0.60.139:3007/api/v1/health`

# Dokploy MCP / API — Notes (Stand 06.06.2026)

## @dokploy/mcp — NPM Package

Dokploy bietet ein offizielles MCP-Package: `@dokploy/mcp`

**Installation & Nutzung:**
```bash
# Setup via npx (einmalig authentifizieren)
npx @dokploy/mcp --setup

# Start als MCP Server (für MCPHub oder Hermes native-mcp)
DOKPLOY_API_KEY="..." npx @dokploy/mcp --stdio
```

**Konfiguration in MCPHub (`mcp_settings.json`):**
```json
{
  "dokploy": {
    "command": "npx",
    "args": ["-y", "@dokploy/mcp", "--stdio"],
    "env": {
      "DOKPLOY_API_KEY": "..."
    }
  }
}
```

## DOKPLOY_API_KEY generieren

**Kann NICHT via CLI oder REST-API erzeugt werden.** Nur via Web-UI:

1. Im Browser zu Dokploy WebUI öffnen
2. Settings → API Keys → "Create API Key"
3. API Key kopieren (wird nur einmal angezeigt!)
4. In `DOKPLOY_API_KEY` env var setzen

**Aktuelle Instanzen & Zugang:**

| Instanz | URL | Login | Status |
|---------|-----|-------|--------|
| Production | http://10.0.60.121:3000 | ??? | ❌ Port 3000 antwortet nicht (Container vermutlich down) |
| Production (Fallback) | http://10.0.60.121:8080 | — | ⚠️ Das ist **Nextcloud**, nicht Dokploy! |
| Sandbox | http://10.0.60.136:3000 | hermes@radislione.net / braucht Passwort | ✅ Erreichbar, Login erforderlich |

**⚠️ Production Dokploy:** Port 3000 antwortet nicht (Connection refused / timeout). Der Port auf dem Docker-Host ist entweder nicht gemappt oder der Container läuft nicht. Port 8080 zeigt Nextcloud (LXC 100), nicht Dokploy.

## REST API — nicht öffentlich

Dokploy v0.29.5 hat **keine öffentliche REST API** für Automation:
- `/api/auth/login` → 404 (nicht implementiert)
- `/api/login` → 401 (erwartet Session-Cookie, kein REST-Endpoint)
- `/api/compose/*`, `/api/application/*` → 401 ohne gültiges Session-Cookie
- `/docs`, `/openapi.json`, `/api` → 404 oder nützliches

**Workaround für API-Lücken:**
- **Compose-Content per DB editieren** (siehe dokploy-lxc-setup Skill, Pitfall #8)
- **Direkt per Docker Compose auf dem LXC deployen** (wenn SSH-Zugang vorhanden)
- **@dokploy/mcp** via npx im Studio-Mode (einmalig --setup für OAuth, dann persistenter Token)

## Sandbox-Login-Status

Sandbox auf 10.0.60.136:3000:
- `npx @dokploy/mcp --setup` sollte OAuth-Flow starten (braucht Browser)
- Ohne --setup: POST /api/login mit email+password → 401 (nicht implementiert oder andere URL)
- Vermutlich Session-basiert (Cookie aus WebUI-Login)

**Für Automatisierung:** Besser den API-Key im WebUI generieren lassen (Settings → API Keys), sobald das Sandbox-Passwort bekannt ist.

## Port-Kontext

| Host | Port | Service | 
|------|------|---------|
| 10.0.60.121 | 3000 | Dokploy Production (❌ down) |
| 10.0.60.121 | 8080 | Nextcloud (LXC 100) |
| 10.0.60.136 | 3000 | Dokploy Sandbox ✅ |

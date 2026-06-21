# MCPHub Setup & Debugging (Goetschi Labs)

## Server
- **Container:** CT107 (10.0.60.170:3000)
- **Image:** `samanhappy/mcphub:latest`
- **Config:** `/opt/mcphub/mcp_settings.json`
- **Docker:** `docker restart mcphub` (auf CT107)
- **Health:** `curl http://localhost:3000/health`
- **API Tools:** `curl http://localhost:3000/api/tools -H "Authorization: Bearer <TOKEN>"`

## Auth-Methoden (MCPHub v0.x)
MCPHub hat drei Auth-Mechanismen:
1. **Users/Password** (bcrypt Hash in `mcp_settings.json` — Hash via Python bcrypt generieren)
2. **Bearer Keys** (`bearerKeys: ["<key>"]` in Config)
3. **OAuth Server** (`systemConfig.oauthServer.enabled: true/false`)

**Aktueller Status (07.06.2026):** Auth funktioniert nicht. BearerKeys geben 401, Login gibt "Internal Server Error" oder "Invalid credentials". Ursache unklar — vermutlich bcrypt Hash-Format oder MCPHub Bug.

**Workaround:** Direkt auf CT107 per `docker exec mcphub` arbeiten, kein Fernzugriff via API möglich.

## Support-Formate
MCPHub unterstützt:
- **`stdio`** — lokale Prozesse via `npx`, `uvx`, `python`
- **`sse`** — Server-Sent Events (Remote MCPs)
- **`streamable-http`** — Streamable HTTP
- **`openapi`** — REST APIs als MCP (via OpenAPI Spec)
- **OAuth** — für Auth-basierte MCPs

## npm Pakete — Verfügbarkeit
Folgende MCP-Pakete wurden **getestet** (Stand 07.06.2026):

| Paket | Status | Beschreibung |
|-------|--------|-------------|
| `@notionhq/notion-mcp-server` | ✅ **Funktioniert** | 22 Tools, Notion API |
| `@modelcontextprotocol/server-filesystem` | ❓ Nicht getestet | Dateisystem-Zugriff |
| `@modelcontextprotocol/server-puppeteer` | ❓ Nicht getestet | Headless Browser |
| `@modelcontextprotocol/server-github` | ❓ Nicht getestet | GitHub API |
| `@kovi/mcp-confluence` | ❌ **EXISTIERT NICHT** | 404 auf npm |
| `@kovi/mcp-jira` | ❌ **EXISTIERT NICHT** | 404 auf npm |
| `@kovi/jira-mcp-server` | ❌ **EXISTIERT NICHT** | 404 auf npm |
| `qdrant-mcp` | ❌ **EXISTIERT NICHT** | 404 auf npm |
| `atlassian-mcp` | ❌ **EXISTIERT NICHT** | 404 auf npm |
| `@anthropic/workspace-mcp-server` | ❌ **EXISTIERT NICHT** | 404 auf npm |
| `home-assistant-mcp` | ❓ Ungetestet | Existiert vielleicht |
| `@chenglou/pretext` | ❓ Ungetestet | Existiert |

## OpenAPI $ref Problem
MCPHub's OpenAPI-Client kann **keine externen $ref-Referenzen** auflösen:
```
Failed to load OpenAPI specification: Unable to resolve $ref pointer "http://10.0.60.121:6333/openapi.json"
```

Betrifft: Qdrant, Home Assistant, Asterisk ARI, Proxmox — alle mit OpenAPI-Specs die lokale $ref-Referenzen enthalten.

**Workaround:** Statt OpenAPI-MCPs die stdio-MCPs nutzen, falls verfügbar. Oder eine lokale Kopie der OpenAPI-Spec bereitstellen die keine $refs hat.

## Konfigurierte MCPs (07.06.2026)
Aktuell läuft nur **Notion** (22 Tools, connected). Alle anderen sind deaktiviert weil:
- npm-Pakete existieren nicht (Jira, Qdrant)
- OpenAPI $ref-Probleme (Home Assistant, Asterisk, Proxmox)
- Keine Tokens/Credentials (Google, GitHub)

## Tipps für neue MCPs
1. **Immer zuerst testen ob das Paket existiert:** `docker exec mcphub npx --yes <package> --help`
2. **OpenAPI-MCPs nur wenn die Spec lokal ist und keine $refs hat**
3. **Nach jeder Config-Änderung:** `docker restart mcphub` + 8s warten
4. **Health danach prüfen:** `curl localhost:3000/health` → "connected" Count
5. **Logs:** `docker logs mcphub --tail 40 | grep -E "Success|Error|connect|ready"`

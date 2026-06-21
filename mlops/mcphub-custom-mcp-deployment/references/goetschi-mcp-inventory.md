# Goetschi Labs MCP Inventory

Stand: 09.06.2026 — 12 MCPs, alle ONLINE auf CT107:3000

## Übersicht

| # | Name | Typ | Tools | Status | Credentials | Besonderheit |
|---|------|-----|-------|--------|-------------|--------------|
| 1 | google-workspace | stdio (Python) | 12 | ✅ | Hardcoded + /data/token.json | Gmail, Calendar, Drive, Docs, Sheets |
| 2 | home-assistant | stdio (Python) | 8 | ✅ | Hardcoded (JWT Token) | HA-OS VM auf 10.0.60.111:8123 |
| 3 | jira-confluence | stdio (Python) | 6 | ✅ | Hardcoded | CRUD für Issues/Pages (self-built) |
| 4 | atlassian | stdio (Python-Proxy) | 2 | ✅ | Bearer Token (API-Key) | Offizieller Rovo MCP — Teamwork Graph |
| 5 | qdrant | stdio (Python) | 3 | ✅ | Hardcoded | Vektordatenbank |
| 6 | proxmox | stdio (Python) | 5 | ✅ | Hardcoded | |
| 7 | paperless | stdio (Python) | 4 | ✅ | Hardcoded (Token) | |
| 8 | asterisk-ari | stdio (Python) | 5 | ✅ | Hardcoded | Asterisk ARI |
| 9 | postgres-pgvector | stdio (Python) | 4 | ✅ | Hardcoded | DB-Zugriff |
| 10 | unifi | stdio (Python) | 4 | ✅ | Hardcoded | |
| 11 | minio | stdio (Python) | 5 | ✅ | Hardcoded | Minimal-Fast-Startup Version |
| 12 | notion | npx (node) | 22 | ✅ | npx @notionhq/client | Läuft via npx (nicht Python) |

## Home Assistant MCP

### HA-OS VM (nicht LXC)
- **Typ:** Qemu KVM-VM (ID: 113), **kein LXC**
- **Hostname:** HA-OS
- **RAM:** 8192 MB (8 GB)
- **Disk:** 112 GB (scsi0) + 120 GB (scsi1)
- **OS:** Home Assistant OS (via tteck Helper-Script installiert)
- **IP:** `10.0.60.111` (DHCP via MAC `02:AD:67:89:86:BC`)
- **Port:** `8123` (WebUI, ✅ erreichbar und antwortet 200 OK)
- **Credentials:** `hassio` / `Riotstar_MICHEL_13` (Web-Login)
- **Long-Lived Access Token:** 183-char JWT, hardcoded im Script

### MCP-Status
- Script hat HA_URL und HA_TOKEN hardcoded (09.06.2026 Fix)
- ⚠️ **Pitfall #17 gilt weiterhin:** MCPHub injected keine env-vars
- **HA_URL:** `http://10.0.60.111:8123` (nicht .300!)

### Verfügbare Tools (8)
1. `list_lights` — Alle Hue/Philips Lichter
2. `toggle_light` — Licht an/aus
3. `set_brightness` — Helligkeit (0-255)
4. `get_sensor` — Sensorwert (Temperatur, etc.)
5. `get_entity_state` — Beliebige Entity
6. `list_entities` — Alle Entities
7. `list_scenes` — Alle Szenen
8. `activate_scene` — Szene aktivieren

## Grafana & Prometheus — DEAKTIVIERT

Service | LXC | IP | Status
-------|-----|----|-------
Grafana | CT108 (Hostname: "Hermes") | 10.0.60.108:3000 | ❌ **Nicht installiert** — Port 3000 antwortet nicht
Prometheus | — | — | ❌ **Nicht vorhanden** — CT109 läuft InfluxDB, kein Prometheus

**CT108** (10.0.60.108, LXC) läuft aber hat **kein Grafana**. Laufende Prozesse:
- `mcp-proxy` auf Port 3103 (unbekannter Zweck)
- Etwas auf Port 5002
- Standard-Systemdienste (SSH, postfix auf 25)

**CT109** heißt "InfluxDB" — kein Prometheus installiert.

## Credentials-Strategie

- **Prinzip**: Alle Credentials hardcoded in den Python-Skripten
- **Ausnahme**: Google OAuth — Refresh-Token in `/data/token.json` (Volume Mount)
- **Env-Vars in mcp_settings.json**: WERDEN NICHT an child-Prozesse weitergegeben (samanhappy/mcphub:latest Bug, Pitfall #17)
- **Kein separater Token für Agenten**: Nur MCPHub Bearer Key (`mcphub-goetschi-2026-open`) nötig

## Atlassian MCP (Dual-Strategy)

**zwei separate MCPs:**

1. **jira-confluence** (self-built) — CRUD für Issues, Pages, Search. Schnell, zuverlässig, hardcoded.
2. **atlassian** (Offiziell via HTTP-Proxy) — Rovo Teamwork Graph. Nur 2 Tools (Graph Context + Graph Object), aber extrem mächtig für Cross-Entity-Relationships.

Der offizielle atlassian MCP braucht einen **Browser-User-Agent** im HTTP-Request (Cloudflare-Block) und **Session-ID** Tracking (SSE).

## Credential Update History

### 09.06.2026 — HA_TOKEN und andere Env-Vars hardcoded

**Problem**: Fünf MCP-Skripte (home-assistant, proxmox, paperless, asterisk-ari, postgres-pgvector) lasen Credentials aus `os.environ.get()`. Der MCPHub Container (`samanhappy/mcphub:latest`) injected KEINE env-vars aus `mcp_settings.json` in child-Prozesse (Pitfall #17).

**Fix**: Alle 5 Scripte auf Hardcoded-Pattern umgestellt:
- **proxmox**: PM_URL, PM_USER, PM_PASS
- **paperless**: PAPERLESS_URL, PAPERLESS_TOKEN
- **asterisk-ari**: ARI_URL, ARI_USER, ARI_PASS
- **postgres-pgvector**: PG_HOST, PG_PORT, PG_USER, PG_PASS, PG_DATABASE
- **home-assistant**: HA_URL, HA_TOKEN (HA-Token: 183-char JWT)

**Key discovery**: Hermes tools truncate strings >~100 chars silently (JWTs, long API keys). Fix requires hex-pattern replacement on the **target machine**, not in tool output. See `SKILL.md` → Credential Update Workflow section.

**Scripte mit bereits hardcoded Creds** (kein Fix nötig):
- unifi (hassio / Riotstar_MICHEL_13)
- minio (admin / Louis_one_13)
- jira-confluence (API Token hardcoded)
- qdrant (keine Auth)
- google-workspace (OAuth Token in /data/token.json)

## Deployments-History

- 06.06.2026: Alle 11 MCPs deployed (Container-Neubau)
- 07.06.2026: Google MCP v2 (12 Tools), pip Pakete
- 08.06.2026: MinIO Fast-Startup Fix, npx Pfad Fix, Notion Fix
- 08.06.2026: Atlassian offizieller MCP deployt (Python HTTP Proxy) — 12 MCPs online
- 08.06.2026: Jira MCP auf self-built + hardcoded Token umgestellt
- 09.06.2026: HA-OS korrekte IP dokumentiert (10.0.60.111), Grafana als nicht installiert deklariert
- 09.06.2026: 5 MCPs von os.environ.get() auf hardcoded Creds umgestellt (HA, proxmox, paperless, asterisk, postgres). HA-Token (183-char JWT) via hex-replacement auf Container gesetzt.

## Fault-Tolerance

Alle stdio MCPs müssen **nie crashen** (sys.exit). API-Fehler werden als JSON-RPC Error zurückgegeben, nie als Python Exception die den Prozess killt. Der initialize-Handshake muss **sofort** antworten (keine API-Checks beim Start).

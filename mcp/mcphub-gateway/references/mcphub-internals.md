# MCPHub Node/NPM Setup & SDK Kompatibilität

## Node im LXC 107

MCPHub läuft als Docker Container uf LXC 107 (nöd direkt als systemd). D'Config isch under `/opt/mcphub/mcp_settings.json` gmountet als **read-only Volume** (`:ro`).

De LXC 107 selber het **Node 18.19.1** installiert (ohni npm). Für npm:
```bash
apt-get install -y npm
# git npm 9.2.0
```

## Config updaten

D'Config `/opt/mcphub/mcp_settings.json` isch **read-only** im Container — nach em Update vo de Datei muess de Container **neigstartet** werde:

```bash
docker restart mcphub
```

## SDK Inkompatibilität (Zod v3 vs v4)

`samanhappy/mcphub:latest` nutzt **Zod v4** -> erwartet `protocolVersion` als **string** im MCP Initialize Response.

Enigi MCP Server (mcp-all-inkl@1.0.6) sendet e **falsche/z'wenig Information** im Initialize — MCPHub loggt denn:
```
[ERROR] Failed to connect client for server
ZodError: [
  {"expected": "string", "code": "invalid_type",
   "path": ["protocolVersion"],
   "message": "Invalid input: expected string, received undefined"}
]
```

**Workarounds:**
1. Docker-Weg (Weg 2 im deploy-mcp-server skill)
2. mcp-proxy zwischen MCPHub und MCP schalte
3. Neueri Version vom MCP-Package abwarte

## Auth

MCPHub Config het im Moment **User-Auth deaktiviert** (Admin-Login mit BCrypt-Hash wird nöd über /api/login akzeptiert). Stattdesse git's en **Bearer Token** in `bearerKeys`. De aktuelli Token funktioniert nöd (wahrschinlich uralt/gänderet).

## Installierti MCPs (Stand 07.06.2026)

12 MCPs, alli als Python stdio type:
- home-assistant, jira-confluence, qdrant, proxmox, paperless
- asterisk-ari, postgres-pgvector, unifi, minio, google-workspace
- notion (npx), all-inkl (mcp-all-inkl global)

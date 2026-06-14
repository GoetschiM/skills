# Token Persistence — Google MCP Server

## History

**29.05.2026 — Erster Token-Verlust beim Rebuild**

Beim ersten Deploy wurde der Token im Docker-Container-Writable-Layer gespeichert, nicht im Volume.
Bei `docker rm` + `docker run` war der Token weg → Michel musste neu autorisieren.

**Fix:** Volume-Pfad auf `/opt/data/google-mcp-server/data` geändert (langlebiger Proxmox-Datastore).
Token wird jetzt nach `/data/token.json` geschrieben → überlebt Neustarts und Rebuilds.

## Prüf-Befehl

```bash
# Prüfe ob Token persistiert
docker exec google-mcp-server ls -la /data/token.json
```

## Sollte Token verloren gehen

1. Google-auth_url aufrufen
2. Michel gibt Auth-Code
3. auth_exchange mit Code
4. Token liegt im Volume → nie wieder verlieren

## Volume-Pfad

Host: `/opt/data/google-mcp-server/data`
Container: `/data` (gemountet via `-v`)

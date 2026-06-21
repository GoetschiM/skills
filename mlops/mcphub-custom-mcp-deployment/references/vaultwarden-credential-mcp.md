# Vaultwarden Credential Management MCP

**Standort**: http://10.0.60.121:8100
**Admin**: http://10.0.60.121:8100/admin (Token: `goetschi-vault-admin-2026`)
**Betrieb**: Docker-Container auf Dokploy-Host (CT100, 10.0.60.121)
**Daten**: Persistentes Docker-Volume `vaultwarden-data`

## Überblick

Vaultwarden dient als **zentraler Credential-Store** für alle Goetschi Labs Agenten (Hermes, Orion, Magos, etc.). Jeder Agent fragt Passwörter via MCP ab statt sie in Memory/Skills zu hardcoden.

## Deployment (von CT135 via sshpass)

```bash
# SSH zum Dokploy-Host
sshpass -p 'Louis_one_13' ssh -o StrictHostKeyChecking=no root@10.0.60.121

# Vaultwarden starten
docker run -d \
  --name vaultwarden \
  --restart unless-stopped \
  -p 8100:80 \
  -v vaultwarden-data:/data \
  -e SIGNUPS_ALLOWED=true \
  -e DOMAIN=http://10.0.60.121:8100 \
  -e ADMIN_TOKEN=goetschi-vault-admin-2026 \
  vaultwarden/server:latest
```

## Ersteinrichtung

1. Gehe zu http://10.0.60.121:8100
2. "Create Account" mit einer Email + Master-Passwort (erster User = Admin)
3. Nach erfolgreicher Registrierung: `SIGNUPS_ALLOWED=false` setzen
4. Admin-Panel unter http://10.0.60.121:8100/admin mit Token `goetschi-vault-admin-2026`
5. API-Key generieren: Einstellungen → Sicherheit → API-Key

## MCP-Server

Läuft auf dem Dokploy-Host unter `/opt/vaultwarden-mcp/server.py`.

### Tool: vaultwarden_get

```json
{
  "name": "vaultwarden",
  "description": "Ruft Credentials aus Vaultwarden ab nach Suchbegriff",
  "parameters": {"query": {"type": "string"}}
}
```

### Usage von Hermes/Agenten

```python
# Aus Python execute_code
result = vaultwarden_get(query="Proxmox")
# → {"credentials": [{"name": "Proxmox pve01", "username": "root", "password": "...", "uri": "https://10.0.60.10:8006"}], "count": 1}
```

### CLI (vom Dokploy-Host)

```bash
python3 /opt/vaultwarden-mcp/server.py --mcp        # Tool-Definition
python3 /opt/vaultwarden-mcp/server.py Proxmox       # Suche
python3 /opt/vaultwarden-mcp/server.py Grafana       # Suche
```

## In MCPHub integrieren

MCP-Server ist aktuell **direkt auf dem Dokploy-Host** (nicht via MCPHub). Für MCPHub-Integration:

1. Docker-Container auf CT107 braucht Zugriff auf Vaultwarden (HTTP reicht)
2. Einen neuen stdio MCP-Server deployen der den vaultwarden-mcp aufruft
3. Oder: `mcp_settings.json` Eintrag mit `command: "python3 /opt/vaultwarden-mcp/server.py --mcp"` wenn via Volume gemountet

## Migrierte Credentials

Folgende Einträge sollten in Vaultwarden landen:
- Dokploy Admin (michelgoetschi@gmail.com / Michel2026_Dokploy)
- Coolify Admin (michelgoetschi@gmail.com / Michel2026_Coolify)
- Proxmox pve01 (root / Riotstar_PROXMOX_13)
- Grafana CT110 (admin / Louis_one_13)
- InfluxDB CT140 (kein Auth)
- HomeAssistant CT300 (hassio / Riotstar_MICHEL_13)
- UniFi Dream Router (hassio / Riotstar_MICHEL_13)
- Asterisk ARI (henryari / HermesVB2026)
- MinIO CT106 (admin / Louis_one_13)
- Nextcloud VM201 (michel / Louis_one_14)
- MCPHub Admin / Bearer
- Paperless CT103 (API Token)
- Confluence Cloud (API Token)
- LiteLLM CT112 (Admin Key)
- PostgreSQL CT105
- etc.

## Skill/Agent Prompt

Für andere Agenten (Orion, Magos, Nova):

```
Du hast Zugriff auf Vaultwarden, den zentralen Passwort-Manager
unter http://10.0.60.121:8100 (MCP-Tool: vaultwarden_get).

WENN du Credentials brauchst, rufe vaultwarden_get(query="Suchbegriff") auf.
Credentials NIEMALS hardcoden oder im Klartext zeigen.
Immer via Vaultwarden abrufen.
```

## Warum Vaultwarden statt Memory/Skills

- **Memory** (2.200 Zeichen Limit) kann nicht alle ~15 Credentials fassen
- **Skills** sind für Workflows, nicht für geheime Daten
- **Vaultwarden** hat API, UI, Mobile App, Backup, Versionsgeschichte
- **Agenten** können via MCP automatisiert abfragen

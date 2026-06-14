# all-inkl MCP — Integration i MCPHub (Session 07.06.2026)

## Setup-Versuech

De **mcp-all-inkl** (@1.0.6) isch als Subprozess im MCPHub registriert worde:

```json
{
  "all-inkl": {
    "type": "stdio",
    "command": "mcp-all-inkl",
    "args": [],
    "env": {
      "KAS_LOGIN": "w019000a",
      "KAS_PASSWORD": "Se%^O9yS%PiZdw!@840hr"
    }
  }
}
```

## Status

- **Config geschriebe:** ✅ `/opt/mcphub/mcp_settings.json` updated (12 MCPs total)
- **Container neigstartet:** ✅ `docker restart mcphub`
- **Health:** 12 total, 8 connected, 4 disconnected — **all-inkl isch disconnected**

## Fehler (MCPHub Logs)

```
MCP error -32001: Request timed out
```

De MCPHub cha de mcp-all-inkl nid initialize wills **z'lang brucht** (20+ Sekunde). De Login-Init muess wahrschi z'erscht e KAS-Session via SOAP hole, was z'langsam isch für MCPHub.

## Fehler (direkti müessig — KasAuth)

Direkti Login-Versuech mit SOAP XML an `https://kasapi.kasserver.com/soap/KasAuth.php` ergäbed **immer**:

```
<faultstring>kas_password_incorrect</faultstring>
```

Au mit **exaktem Node-Code nochebaut** (buildSoap, JSON.stringify, &-escape, separators, Namespace `urn:KasAuth`).

## Mögligi Ursache

1. **Passwort falsch**: S'Passwort `Se%^O9yS%PiZdw!@840hr` isch vlt. so nid gsetzt worde im KAS (Sonderzeiche-problem bim Setze)
2. **Flood-Protection**: `lastFloodDelay` im mcp-all-inkl blockiert Login nach z'vilne schnelle Versüech
3. **KasAuth Endpoint gänderet**: Vlt. bruuchts en andere Pfad oder HTTPS-Version
4. **I18n Sonderzeiche**: `%^` im Passwort wird vlt. vom SOAP-XML-Parser vom KAS falsch interpretiert

## Nöchsti Schriitä

- **Option A:** Docker-Weg (MCP als eigenständige Container deploye, als URL-MCP registriere)
- **Option B:** Passwort ohni Sonderzeiche setze (`a-zA-Z0-9` nume)
- **Option C:** mcp-proxy Zwüscheschicht (mcp-all-inkl via Python mcp-proxy als HTTP wrappe)

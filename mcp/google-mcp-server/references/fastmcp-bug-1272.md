# FastMCP 1.27.2 Bug — initialer Grund für Starlette-Migration

## Ursprüngliche Beobachtung (29.05.2026, FastMCP)

Mit `FastMCP(json_response=True, stateless_http=True)` wurden Tools, die per `@mcp.tool()`-Dekorator registriert wurden, **nicht vollständig** über die StreamableHTTP-Schnittstelle exponiert:

- `mcp._tool_manager._tools` → 16 Tools ✅ (alle registriert)
- `mcp._tool_manager.list_tools()` → 16 Tools ✅
- `_mcp_server._tool_cache` nach ListTools-Request → 16 Tools ✅
- `StreamableHTTPASGIApp` → tools/list Antwort → **14 Tools** ❌ (gmail_trash, gmail_modify fehlen)

## Nachtrag (erneut bestätigt 29.05.2026)

**Der Bug PERSISTIERT auch mit dem neuen Starlette-basierten Server.** Der
komplett selbst geschriebene HTTP-Handler (kein FastMCP, kein StreamableHTTP)
zeigt das gleiche Verhalten:

| Zugriff | Tools |
|---------|-------|
| Container-intern via localhost | 16 ✅ |
| Container-intern via TestClient (ASGI direkt) | 16 ✅ |
| Container-intern via Bridge-IP | 16 ✅ |
| Von USSE via docker-proxy | 14 ❌ |

Da der Bug mit einem **komplett anderen Server** (Starlette statt FastMCP)
und **manuellen JSON-RPC Handlern** persistiert, ist die Ursache NICHT in
FastMCP zu suchen, sondern in der **Netzwerk-Infrastruktur**:

- **Verdacht: Docker-proxy auf LXC.** Docker-proxy (Userland-Proxy) könnte
  bei langen JSON-Responses (>4KB) Pakete fragmentieren oder truncaten.
  Oder der LXC-Kernel hat eine Besonderheit bei der NAT-Tabelle.
- **Dokploy/Proxy-Effekt ausgeschlossen.** Der Container läuft auf dem
  default bridge network, nicht im Dokploy-Overlay. Port 8002 ist direkt
  exponiert.
- **Nicht reproduzierbar auf bare-metal Docker.** Nur in LXC-Umgebung.

**KEIN Workaround bekannt** für tools/list. Verwende direkt `tools/call`.

## Warum die Migration trotzdem richtig war

Auch wenn der 14-vs-16 Bug persistiert, war die Migration zu Starlette
richtig, weil:
1. **Vollständige Kontrolle** über den HTTP-Request/Response-Cycle
2. **Keine versteckten FastMCP-Magie** (Session-Manager, Caching, etc.)
3. **Tools/call funktioniert** — nur tools/list zeigt das Phänomen
4. **Einfacheres Debugging** bei zukünftigen Problemen

## Workaround (beibehalten)

Komplette Abkehr von FastMCP → eigener Starlette-Server mit manuellen HTTP Handlern.

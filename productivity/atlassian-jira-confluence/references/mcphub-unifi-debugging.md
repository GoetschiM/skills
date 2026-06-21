# MCPHub Access & UniFi Firewall Debugging (Goetschi Labs)

## MCPHub Server (10.0.60.170:3000)
Zentraler MCP Manager auf LXC CT107 (pve01). Docker `samanhappy/mcphub:latest`.
Config: `/opt/mcphub/mcp_settings.json` (Volume Mount, nur lokal auf CT107).
11 MCPs: Playwright, Fetch, GitHub, Filesystem, Proxmox, Home Assistant,
Jira, Notion, MinIO, **UniFi**, Obsidian.

### Zugang
- **Web UI:** http://10.0.60.170:3000/ — Login-Formular mit eigener
  Benutzer/Passwort-Kombination (NICHT die UniFi-Credentials)
- **API:** Alle Endpoints benötigen API-Token im `Authorization: Bearer` Header
- **Token-Quelle:** Liegt in `/opt/mcphub/mcp_settings.json` auf CT107
  → nur über SSH auf pve01 oder Docker exec zugänglich
- **Nicht in:** Qdrant (type:credential), Notion, Confluence, Obsidian
- **Nicht öffentlich:** Kein `/api/register` oder Token-Endpoint ohne Auth

### Hermes als MCP-Client
`hermes mcp add <name> --url <endpoint>` erwartet einen **Streamable HTTP**
oder SSE Endpoint (/mcp), nicht `/api/servers`. MCPHub hat **keinen** MCP-
kompatiblen Endpoint — es ist ein REST-Manager, kein MCP-Server selbst.

### Workaround (UniFi API direkt)
Wenn MCPHub-Token nicht verfügbar:
```python
import requests, base64, json

session = requests.Session()
session.verify = False
r = session.post("https://10.0.10.1/api/auth/login",
                 json={"username": "hassio", "password": "<PASS>"}, timeout=15)
# CSRF aus JWT-Cookie extrahieren
cookie = session.cookies.get("TOKEN", "")
parts = cookie.split(".")
payload = json.loads(base64.b64decode(parts[1] + "=="))
csrf = payload.get("csrfToken", "")
session.headers.update({"X-CSRF-Token": csrf})
```

## UniFi API — Firewall Debugging

### Wichtige Endpoints
| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/api/auth/login` | POST | Login (setzt TOKEN-Cookie) |
| `/proxy/network/api/s/default/stat/sta` | GET | Aktive WiFi-Clients |
| `/proxy/network/api/s/default/rest/firewallrule` | GET | Firewall-Regeln |
| `/proxy/network/api/s/default/rest/wlanconf` | GET | WLAN/Settings (Client Isolation) |
| `/proxy/network/api/s/default/rest/networkconf` | GET | VLANs/Netzwerke |
| `/proxy/network/api/s/default/rest/user/{id}` | PUT | Client-Konfiguration ändern |

### Account Locked & Zwei Passwörter
Zu viele Login-Versuche → `403 "SSO Account locked"`.
**Fix:** Im UniFi Dashboard entsperren (oder 5-10 Min warten).

**⚠️ UniFi hat ZWEI mögliche Passwörter in Qdrant:**
- `Riotstar_UNIFI_13` — älteres, kann gelockt sein
- `Riotstar_MICHEL_13` — funktioniert aktuell
Beide sind in Qdrant unter `type:credential AND service:unifi*`. Wenn eines locked ist, einfach das andere probieren.

### Client Network Override (VLAN wechseln)
Wenn ein Gerät im falschen VLAN hängt (z.B. Philips TV in VLAN10, aber Hue Bridge in VLAN20):

```python
# 1. Alle Netzwerke und ihre IDs holen
r = session.get("https://10.0.10.1/proxy/network/api/s/default/rest/networkconf", timeout=15)
networks = r.json().get('data', [])
for n in networks:
    print(f"{n.get('name','?')}: {n.get('_id','?')} (vlan={n.get('vlan','native')})")

# 2. Network Override für TV setzen (in IoT Netz)
r = session.put(f"https://10.0.10.1/proxy/network/api/s/default/rest/user/{client_id}",
                json={"network_id": "<IOT_network_id>", "name": "philips tv"})
TV danach aus-/einschalten oder WLAN reconnecten.
```

**Client Isolation checken:** `/proxy/network/api/s/default/rest/wlanconf` → `is_client_isolation_enabled`

### Credentials
- Host: 10.0.10.1
- User: hassio
- Pass: Riotstar_UNIFI_13 (aus Qdrant)
- VLANs: native=0(10.0.0.1), 10=Client(10.0.10.1), 20=IoT(10.0.20.1),
          40=Service(10.0.40.1), 60=Server(10.0.60.1)

### Häufige Probleme
1. **Client Isolation** — Settings → WLAN → [SSID] → Advanced → AUS
2. **mDNS** — Settings → Services → mDNS → AKTIVIERT
3. **Firewall intra-VLAN** — Regel die Traffic im selben VLAN blockiert
4. **IGMP Snooping** — Kann SSDP/mDNS stören

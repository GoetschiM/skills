# All-Inkl KAS API — Technischi Detail (v2)

## SOAP API Endpoints

```
# AUTH (Login — Session-Token hole)
POST https://kasapi.kasserver.com/soap/KasAuth.php
Namespace: urn:KasAuth
Method: KasAuth

# API (Operatione usfüehre)
POST https://kasapi.kasserver.com/soap/KasApi.php
Namespace: urn:KasApi
Method: KasApi
```

**NICHT `?wsdl`** — das git nu d'WSDL-Beschriebig, kei API-Call.

## Auth-Mechanismus (2-Phase)

### Phase 1: Login → Session-Token

XML SOAP-Request:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
 xmlns:ns1="urn:KasAuth">
<SOAP-ENV:Body>
<ns1:KasAuth>
<Params>{"kas_login":"w019000a","kas_auth_type":"plain",
"kas_auth_data":"Se%^O9yS%PiZdw!@840hr",
"session_lifetime":3600,"session_update_lifetime":"Y"}</Params>
</ns1:KasAuth>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

**Kritisch:** `<Params>`-Inhalt ist **JSON.stringify'd und &-escaped** (nit `<KAS_PARAMETER>` mit XML-Direct-Values!). De Node Source code:
```javascript
function buildSoap(ns, method, params) {
    const p = JSON.stringify(params);
    return `<Params>${p.replace(/&/g, "&amp;")}</Params>`;
}
```

### Phase 2: API-Call mit Session-Token

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope ... xmlns:ns1="urn:KasApi">
<SOAP-ENV:Body>
<ns1:KasApi>
<Params>{"kas_login":"w019000a","kas_auth_type":"session",
"kas_auth_data":"[TOKEN]","kas_action":"kas_mail",
"KasRequestParams":{"list":{"KAS_HEADER":{},"KAS_DATA":{}}}}</Params>
</ns1:KasApi>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

Session-Token läuft nach 60 Minute ab (wird im mcp-all-inkl gecached).

## Flood-Protection

De KAS Server het en **Flood-Protection** (`KasFloodDelay`). Noch z'vilne Calls in chürzer Ziit blockiert de Server IP-temporary für die Action.
```javascript
const flood = req?.['KasFloodDelay'];
if (typeof flood === 'number' && flood > 0)
    lastFloodDelay[action] = Date.now() + flood * 1000;
```
**Pitfall:** Meh als 3-5 Login-Versuche pro Minute chönd zunere **temporäre IP-Sperri** füehre.

## KAS Login via Python (exakt wie Node)

```python
import http.client, json, re

LOGIN = "w019000a"
PASS = "..."  # us .env

def build_soap(ns, method, params_dict):
    p = json.dumps(params_dict, ensure_ascii=False, separators=(',', ':'))
    p = p.replace("&", "&amp;")
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"'
            f' xmlns:ns1="{ns}">'
            f'<SOAP-ENV:Body><ns1:{method}><Params>{p}</Params></ns1:{method}>'
            f'</SOAP-ENV:Body></SOAP-ENV:Envelope>')

def soap_post(url, ns, method, params_dict):
    xml = build_soap(ns, method, params_dict)
    conn = http.client.HTTPSConnection("kasapi.kasserver.com", 443, timeout=20)
    conn.request("POST", url, body=xml.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8", "User-Agent": "mcp-all-inkl/1.0.6"})
    resp = conn.getresponse()
    return resp.read().decode("utf-8")
```

## LXC 107 MCPHub Spezifisch

- MCPHub lauft als Docker-Container uf LXC 107 (10.0.60.170:3000)
- Config: `/opt/mcphub/mcp_settings.json`, mountet in Container via `:ro`
- **Container-Neustart nötig** (`docker restart mcphub`)
- Docker: 29.5.3 uf Proxmox Host (10.0.60.10)
- Node: 18.19.1 + npm via apt
- mcp-all-inkl: `npm install -g mcp-all-inkl` (v1.0.6)
- **MCP SDK Inkompatibilität:** mcp-all-inkl@1.0.6 sendet kei `protocolVersion`-string im Initialize Response. MCPHub (SDK 1.29.0/Zod v4) erwartet das und wirft `ZodError`. Workaround: Python mcp-proxy wrapper oder Docker-eigeständig.

## Env-Vars: weli für weli Tool?

| Tool | Brucht | Opt. Alias |
|------|--------|-----------|
| mcp-all-inkl (npm) | `KAS_LOGIN`, `KAS_PASSWORD` | — |
| Python MCP (all-inkl-mcp.py) | `KAS_LOGIN` oder `ALLINKL_KAS_LOGIN` | beidi |
| Hermes .env | `ALLINKL_KAS_LOGIN`, `ALLINKL_KAS_PASSWORD` | — |

**Regle:** immer beidi Setze — `KAS_LOGIN`/`KAS_PASSWORD` UND `ALLINKL_KAS_LOGIN`/`ALLINKL_KAS_PASSWORD`.

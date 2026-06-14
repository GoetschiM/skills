# KAS SOAP Email Creation — Working Pattern

**Last verified: 08.06.2026** — Successfully created 5 mailboxes on goetschi-labs.ch.

## The Two-Step SOAP Flow

All-Inkl KAS uses **two separate SOAP endpoints**:

### Step 1: KasAuth (Login) → Session Token

```
POST https://kasapi.kasserver.com/soap/KasAuth.php
SOAPAction: "urn:KasAuth"
Namespace: "urn:KasAuth"
```

**Request body:**
```xml
<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP-ENV:Header/>
  <SOAP-ENV:Body>
    <ns1:KasAuth xmlns:ns1="urn:KasAuth">
      <Params>{"kas_login":"w019000a","kas_auth_type":"plain","kas_auth_data":"PASSWORD_HERE","session_lifetime":3600,"session_refresh":"false"}</Params>
    </ns1:KasAuth>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

**Response** — XML with `kas_session_id` and `kas_session_expires`.

### Step 2: KasApi (Operation) → Use Session Token

```
POST https://kasapi.kasserver.com/soap/KasApi.php
SOAPAction: "urn:KasApi"
Namespace: "urn:KasApi"
```

**Request body (pattern):**
```xml
<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP-ENV:Header/>
  <SOAP-ENV:Body>
    <ns1:KasApi xmlns:ns1="urn:KasApi">
      <Params>{"kas_login":"w019000a","kas_auth_type":"session","kas_auth_data":"SESSION_TOKEN","kas_action":"ACTION_NAME","KasRequestParams":{...}}</Params>
    </ns1:KasApi>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

## ⭐ Critical: Action Names

The `kas_action` field **MUST** match the KAS-internal action name, NOT the mcp-all-inkl tool name:

| mcp-all-inkl tool | User-visible action | KAS internal `kas_action` |
|-------------------|--------------------|---------------------------|
| `kas_mail` | `list` | `get_mailaccounts` |
| `kas_mail` | `create` | `add_mailaccount` |
| `kas_mail` | `delete` | `delete_mailaccount` |
| `kas_mail` | `update` | `update_mailaccount` |

**NEVER use `kas_mail` as the `kas_action` value** — that's the MCP tool name, not the KAS action. Using it gives `unkown_action` (with typo as spelled — not "unknown").

## Working Python Example (create-mail)

```python
import http.client

# Step 1: Login
conn = http.client.HTTPSConnection("kasapi.kasserver.com", timeout=10)
auth_xml = f'<?xml version="1.0"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Header/><SOAP-ENV:Body><ns1:KasAuth xmlns:ns1="urn:KasAuth"><Params>{{"kas_login":"w019000a","kas_auth_type":"plain","kas_auth_data":"{PASSWORD}","session_lifetime":3600}}</Params></ns1:KasAuth></SOAP-ENV:Body></SOAP-ENV:Envelope>'
conn.request("POST", "/soap/KasAuth.php", auth_xml, {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "urn:KasAuth"})
resp = conn.getresponse()
body = resp.read().decode()

# Extract session token
import re
m = re.search(r'kas_session_id["\']?\s*[:=]\s*["\']([^"\']+)', body)
token = m.group(1)

# Step 2: Create mailbox (add_mailaccount!)
params = json.dumps({
    "kas_login": "w019000a",
    "kas_auth_type": "session",
    "kas_auth_data": token,
    "kas_action": "add_mailaccount",  # ← THIS IS THE KEY!
    "KasRequestParams": {
        "local_part": username,
        "domain_part": domain,
        "mail_password": password,
        "mail_forward": 0,
        "mail_quota": 1024
    }
})
api_xml = f'<?xml version="1.0"?><SOAP-ENV:Envelope ...><ns1:KasApi xmlns:ns1="urn:KasApi"><Params>{params}</Params></ns1:KasApi></SOAP-ENV:Body></SOAP-ENV:Envelope>'
conn.request("POST", "/soap/KasApi.php", api_xml, {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "urn:KasApi"})
```

## Pitfalls

1. **`kas_action` MUST be `add_mailaccount`, NOT `kas_mail`!** Using `kas_mail` gives `unkown_action`.
2. **JSON inside `<Params>`** — the KAS SOAP endpoint expects a single JSON string inside the `<Params>` tag, NOT nested XML elements.
3. **Password in JSON** — use single quotes around the heredoc or escape `$` `!` `%` `^` characters.
4. **Session Token** — valid for `session_lifetime` seconds (default 3600). Must be passed as `kas_auth_data` in Step 2.
5. **`kas_mail` create uses params keys: `["local_part", "domain_part", "mail_password"]`** — NOT `mail_login`, NOT `email`. Checked in mcp-all-inkl server.ts source.

## Verification

After creating, verify by listing:
```python
params = json.dumps({
    "kas_login": "w019000a",
    "kas_auth_type": "session",
    "kas_auth_data": token,
    "kas_action": "get_mailaccounts",
    "KasRequestParams": {}
})
```

## 5 Mailboxes Created 08.06.2026

Each on goetschi-labs.ch, all with password `ApolloHermes2026!`:
- info@goetschi-labs.ch (Allgemein)
- hermes@goetschi-labs.ch (Hermes)
- nova@goetschi-labs.ch (NOVA)
- magos@goetschi-labs.ch (MAGOS)
- orion@goetschi-labs.ch (Orion)

IMAP/SMTP: `w019000a.kasserver.com:993/465`

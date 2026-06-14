# KAS SOAP API — Direct Call Reference

Reverse-engineered from `mcp-all-inkl@1.0.6` source code
(https://github.com/hl9020/mcp-all-inkl)

## Endpoints

| Step | URL | Method | Namespace |
|------|-----|--------|-----------|
| Login | `https://kasapi.kasserver.com/soap/KasAuth.php` | `KasAuth` | `urn:KasAuth` |
| Action | `https://kasapi.kasserver.com/soap/KasApi.php` | `KasApi` | `urn:KasApi` |

## SOAP XML Schema

```xml
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:ns1="urn:KasAuth">
  <SOAP-ENV:Body>
    <ns1:KasAuth>
      <Params>{JSON_PARAMS}</Params>
    </ns1:KasAuth>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

## Login (KasAuth)

```python
params = {
    "kas_login": "w019000a",           # KAS Account
    "kas_auth_type": "plain",          # auth method
    "kas_auth_data": "PASSWORD",       # KAS password
    "session_lifetime": 3600,          # 1 hour
    "session_update_lifetime": "Y",    # auto-renew
}
```

Response contains `<return>` tag with session token.

## Actions (KasApi)

```python
params = {
    "kas_login": "w019000a",
    "kas_auth_type": "session",
    "kas_auth_data": "SESSION_TOKEN",   # from login
    "kas_action": "add_mailaccount",    # KAS-internal action!
    "KasRequestParams": {               # action-specific params
        "local_part": "info",
        "domain_part": "goetschi-labs.ch",
        "mail_password": "...",
    },
}
```

## Action Mapping (Tool Name → KAS Action)

From `src/tools/mail.ts`:

| Tool Action | KAS Action | Required Params |
|-------------|-----------|-----------------|
| `list` | `get_mailaccounts` | none |
| `create` | `add_mailaccount` | mail_password, local_part, domain_part |
| `update` | `update_mailaccount` | mail_login |
| `delete` | `delete_mailaccount` | mail_login |
| `list_forwards` | `get_mailforwards` | none |
| `create_forward` | `add_mailforward` | local_part, domain_part |
| `update_forward` | `update_mailforward` | mail_forward |
| `delete_forward` | `delete_mailforward` | mail_forward |
| `list_lists` | `get_mailinglists` | none |
| `create_list` | `add_mailinglist` | mailinglist_name, mailinglist_domain, mailinglist_password |
| `update_list` | `update_mailinglist` | mailinglist_name |
| `delete_list` | `delete_mailinglist` | mailinglist_name |
| `add_filter` | `add_mailstandardfilter` | mail_login, filter |
| `delete_filter` | `delete_mailstandardfilter` | mail_login |

From `src/tools/domain.ts`:

| Tool Action | KAS Action |
|-------------|-----------|
| `list` | `get_domain` |
| `create` | `add_domain` |
| `update` | `update_domain` |
| `delete` | `delete_domain` |
| `move` | `move_domain` |
| `list_tlds` | `get_domain_tld` |

From `src/tools/dns.ts`: `add_dns_record`, `update_dns_record`, `delete_dns_record`, `reset_dns_zone`, `get_dns_zone`

From `src/tools/database.ts`: `get_database`, `add_database`, `update_database`, `delete_database`

From `src/tools/cronjob.ts`: `get_cronjob`, `add_cronjob`, `update_cronjob`, `delete_cronjob`

From `src/tools/subdomain.ts`: `get_subdomain`, `add_subdomain`, `update_subdomain`, `delete_subdomain`, `move_subdomain`

## Python Example

```python
import http.client, json, re

def kas_call(endpoint, ns, method, params):
    p = json.dumps(params).replace("&", "&amp;")
    xml = f'<?xml version="1.0" encoding="UTF-8"?>'
    xml += f'<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="{ns}">'
    xml += f'<SOAP-ENV:Body><ns1:{method}><Params>{p}</Params></ns1:{method}></SOAP-ENV:Body>'
    xml += f'</SOAP-ENV:Envelope>'
    path = "/soap/KasAuth.php" if method == "KasAuth" else "/soap/KasApi.php"
    conn = http.client.HTTPSConnection("kasapi.kasserver.com", timeout=30)
    conn.request("POST", path, xml.encode(), {"Content-Type": "text/xml"})
    data = conn.getresponse().read().decode()
    conn.close()
    return data

# Login
r = kas_call("KasAuth", "urn:KasAuth", "KasAuth", {
    "kas_login": "w019000a",
    "kas_auth_type": "plain",
    "kas_auth_data": "PASSWORD",
    "session_lifetime": 3600,
    "session_update_lifetime": "Y",
})
token = re.search(r'<return[^>]*>(.*?)</return>', r, re.DOTALL).group(1).strip()

# Create mailbox
r = kas_call("KasApi", "urn:KasApi", "KasApi", {
    "kas_login": "w019000a",
    "kas_auth_type": "session",
    "kas_auth_data": token,
    "kas_action": "add_mailaccount",
    "KasRequestParams": {
        "local_part": "info",
        "domain_part": "goetschi-labs.ch",
        "mail_password": "ApolloHermes2026!",
    },
})
```

## Pitfalls

1. **XML escaping:** JSON.stringify() → replace `&` with `&amp;` — exactly like Node source.
2. **Session reuse:** Session token is cached for 1 hour. Subsequent calls use same token.
3. **Flood protection:** KAS throttles after >3 failed logins in 60s. Wait 30 min.
4. **`unkown_action`:** Means wrong `kas_action` value (not MCP tool name!)
5. **HTTP 405:** Wrong endpoint (KasAuth.php vs KasApi.php)

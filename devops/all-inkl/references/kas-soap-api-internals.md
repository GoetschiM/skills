# KAS SOAP API Internals (mcp-all-inkl)
Erstellt: 08.06.2026

## API Endpoints

| Endpoint | URL |
|----------|-----|
| KasAuth | `https://kasapi.kasserver.com/soap/KasAuth.php` |
| KasApi | `https://kasapi.kasserver.com/soap/KasApi.php` |

**Login und API sind verschiedene Endpoints!**

## Login (Session holen)

```xml
POST /soap/KasAuth.php
Content-Type: text/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:ns1="urn:KasAuth">
<SOAP-ENV:Body>
<ns1:KasAuth>
<Params>{"kas_login":"w019000a","kas_auth_type":"plain","kas_auth_data":"PASSWORT","session_lifetime":3600,"session_update_lifetime":"Y"}</Params>
</ns1:KasAuth>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

**Response:** `<return>049c047a0ff551cb529e...</return>` (Session-Token)

## API Call (mit Session)

```xml
POST /soap/KasApi.php
Content-Type: text/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:ns1="urn:KasApi">
<SOAP-ENV:Body>
<ns1:KasApi>
<Params>{"kas_login":"w019000a","kas_auth_type":"session","kas_auth_data":"SESSION_TOKEN","kas_action":"kas_mail","KasRequestParams":{"local_part":"info","domain_part":"goetschi-labs.ch","mail_password":"ApolloHermes2026!"}}</Params>
</ns1:KasApi>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

> **Bekanntes Problem:** `unkown_action` Fehler bei KasApi-Endpoint

## mcp-all-inkl@1.0.6 Source-Code

**SOAP Builder (kas-client.js L6):**
```js
return `<SOAP-ENV:Envelope xmlns:ns1="${ns}">
<SOAP-ENV:Body><ns1:${method}><Params>${p.replace(/&/g, "&amp;")}</Params></ns1:${method}>
</SOAP-ENV:Body></SOAP-ENV:Envelope>`
```

**Login (L143-149):**
```js
const xml = await soapPost(AUTH_URL, "urn:KasAuth", "KasAuth", {
    kas_login: user, kas_auth_type: "plain", kas_auth_data: pwd,
    session_lifetime: 3600, session_update_lifetime: "Y",
});
```

**API Call (L164-166):**
```js
const doCall = async (tok) => soapPost(API_URL, "urn:KasApi", "KasApi", {
    kas_login: user, kas_auth_type: "session", kas_auth_data: tok,
    kas_action: action, KasRequestParams: params,
});
```

### Session-Caching
```js
let session = null;  // Modul-Scope: 1 Prozess = 1 Session
```

Jede neui npx-Start = neui Session = Flood-Risiko!

## Env-Variable
- `KAS_LOGIN=w019000a` (zwingend)
- `KAS_PASSWORD=...` (zwingend)
- `ALLINKL_KAS_LOGIN`, `ALLINKL_KAS_PASSWORD` (Alias, optional)

## Fehler-Matrix

| Fehler | Grund | Lösig |
|--------|-------|-------|
| `kas_password_incorrect` | Flood-Protection (>3/min) | 30 Min. warte |
| `unkown_action` | KasApi XML falsch | Villicht muess SOAP-Method anders heisse |
| `HTTP 405` | Endpoint falsch | Login: KasAuth.php, API: KasApi.php |
| `HTTP 500` | KasApi akzeptiert form-urlencoded nüd | Nur XML (`text/xml; charset=utf-8`) |
| MCPHub disconnected | Zod v4 Inkompatibilität | Docker-eigeständig deploye |

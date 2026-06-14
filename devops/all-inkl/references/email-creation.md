# E-Mail-Adressen (@goetschi-labs.ch)
Geplant/Session: 07.06.2026 (SUP-??)

## Geplanti Credentials

| Adresse | Status | Notiz |
|---------|--------|-------|
| info@goetschi-labs.ch | ❌ Nöd erstellt | KAS API akzeptiert Login nid |
| hermes@goetschi-labs.ch | ❌ Nöd erstellt | KAS API: kas_password_incorrect |
| nova@goetschi-labs.ch | ❌ Nöd erstellt | KAS API: kas_password_incorrect |
| magos@goetschi-labs.ch | ❌ Nöd erstellt | KAS API: kas_password_incorrect |
| orion@goetschi-labs.ch | ❌ Nöd erstellt | KAS API: kas_password_incorrect |

## Erstelligsversuech

**Endpoints (uss mcp-all-inkl source):**
- **KasAuth:** https://kasapi.kasserver.com/soap/KasAuth.php (Login → Session-Token)
- **KasApi:** https://kasapi.kasserver.com/soap/KasApi.php (API-Calls mit Token)

**SOAP-Struktur (exakt nochebaut us mcp-all-inkl@1.0.6 kas-client.js):**
```xml
<!-- Login -->
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:ns1="urn:KasAuth">
<SOAP-ENV:Body><ns1:KasAuth>
  <Params>{"kas_login":"w019000a","kas_auth_type":"plain","kas_auth_data":"Se%^...","session_lifetime":3600,"session_update_lifetime":"Y"}</Params>
</ns1:KasAuth></SOAP-ENV:Body></SOAP-ENV:Envelope>
```

**Error:** Immer `kas_password_incorrect` — au mit Node-exaktem SOAP XML.
**Mögligi Ursach:** Passwort `Se%^O9yS%PiZdw!@840hr` het Sonderzeiche wo d'KAS-SOAP-Parsing störe.

## IMAP/SMTP Config (wenn erstellt)
- **IMAP:** w019000a.kasserver.com Port 993 (SSL/TLS)
- **SMTP:** w019000a.kasserver.com Port 465 (SSL/TLS)
- **Login:** Volle Adresse, Passwort: ApolloHermes2026!

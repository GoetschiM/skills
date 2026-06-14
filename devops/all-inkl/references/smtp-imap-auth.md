# All-Inkl SMTP/IMAP Authentication — Debugging Notes

**Stand:** 23.05.2026  
**Getestet:** hermes/nova/apollo@radislione.net + michel@radislione.net  
**Resultat:** ❌ Authentication schlaht für ALLI Mailboxe fähl

## Servers

| Protokoll | Host | Port | TLS |
|-----------|------|------|-----|
| IMAP | imap.all-inkl.com | 993 | SSL |
| IMAP (alternativ) | imap.all-inkl.com | 143 | STARTTLS |
| SMTP (Submission) | smtp.all-inkl.com | 465 | SSL |
| SMTP (alternativ) | smtp.all-inkl.com | 587 | STARTTLS |
| SMTP (direct - blockiert) | w019000a.kasserver.com | 25 | - |
| MX | w019000a.kasserver.com | - | - |

## Getesteti Login-Formate

Alli gschiteret mit gliiche Credentials (KAS-API zeigt korrektes Passwort):

| Format | User | SMTP | IMAP |
|--------|------|------|------|
| Volli Email | hermes@radislione.net | ❌ 535 | ❌ AUTHENTICATIONFAILED |
| mail_login | m07f3b09 | ❌ 535 | ❌ |
| mail_login@domain | m07f3b09@radislione.net | ❌ 535 | ❌ |
| mail_login@server | m07f3b09@dd28302.kasserver.com | ❌ 535 | ❌ |
| KAS login | w019000a | ❌ Timeout | ❌ |
| KAS@domain | w019000a@radislione.net | ❌ Timeout | ❌ |

## Sasl-Mechanisms

Server bietet: **AUTH PLAIN LOGIN**  
Error mit AUTH LOGIN: `535 5.7.8 Error: authentication failed: UGFzc3dvcmQ6`

## Postfix Relay Workaround

Funktioniert für **Bounces** (from=<>), schlaht fähl für **Auth**:

```bash
postconf -e "relayhost = [smtp.all-inkl.com]:587"
postconf -e "smtp_sasl_auth_enable = yes"
postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
postconf -e "smtp_sasl_security_options = noanonymous"
postconf -e "smtp_tls_security_level = encrypt"
echo "[smtp.all-inkl.com]:587 hermes@radislione.net:Passwort" > /etc/postfix/sasl_passwd
postmap hash:/etc/postfix/sasl_passwd
```

Dependencies:
- `libsasl2-modules` (PLAIN-Modul für SASL — NUR `libsasl2-modules-db` isch nöd gnueg!)

SASL-Fehler «No worthy mechs found» = libsasl2-modules fählt.

## Vermuetigi Ursache

1. KAS-API `mail_password` = MySQL/KAS-eigeni Passwort-DB
2. Dovecot/Postfix für IMAP/SMTP brucht **eigeni Passwort-DB** (separat gsyncet via KAS Web-Interface)
3. API-Create `mail_password` setzt NUR KAS-DB, aber syncet nöd zu Dovecot
4. **Fix:** via KAS Web-Interface (kasserver.com) → Email → Mailboxe → Passwort zrüggsetze
5. Oder: All-Inkl Support anfragen obs en API-Endpoint für Dovecot-Sync git

## Alternativ-Lösige

- **Webmail:** Nutzer chönd via Webmail uf radislione.net (All-Inkl Roundcube) lese/schribe
- **Mailgun/Sendgrid:** Externi SMTP-Provider als Relay, fall All-Inkl SMTP nie funktioniert
- **Gmail API:** Falls d'Mails ohni All-Inkl wösch, über Gmail-API (für GMX/Gmail-Accounts)

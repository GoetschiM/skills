# All-Inkl Email Connectivity

## IMAP / SMTP Server

**CRITICAL:** Verwende NIEMALS `imap.all-inkl.com` oder `smtp.all-inkl.com`!
Die generische Load-Balancer akzeptieren KEINE SMTP/IMAP AUTH (535 Error).

**Der korrekte Server ist:** `<KAS-Login>.kasserver.com`
- Hermes KAS Login: `w019000a`
- **Server:** `w019000a.kasserver.com`

| Protokoll | Host | Port | Verschlüsselung |
|-----------|------|------|-----------------|
| IMAP | `w019000a.kasserver.com` | 993 | SSL/TLS |
| SMTP | `w019000a.kasserver.com` | 465 | SSL/TLS (Wrappermode) |
| SMTP (alt) | `w019000a.kasserver.com` | 587 | STARTTLS |

**Login-Format:** Volle E-Mail-Adresse (z.B. `hermes@radislione.net`)
**Passwort:** Das via KAS-API gsetzt Mailbox-Passwort

## Agent-Mailboxen (Stand 23.05.2026)

| Adresse | Mail-ID | Passwort | Status |
|---------|---------|----------|--------|
| hermes@radislione.net | m07f3b09 | ApolloHermes2026! | ✅ IMAP+SMTP getestet |
| nova@radislione.net | m07f3b0a | ApolloHermes2026! | ✅ aagleit |
| apollo@radislione.net | m07f3b0b | ApolloHermes2026! | ✅ aagleit |

## Postfix Relay (Hermes 10.0.60.156)

Postfix ist als SMTP-Relay konfiguriert. Verwendet SASL PLAIN auth.

### Konfiguration
```
relayhost = [w019000a.kasserver.com]:465
smtp_tls_wrappermode = yes           # WICHTIG für Port 465!
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_sasl_mechanism_filter = plain, login
```

### SASL Module
NUR `libsasl2-modules-db` reicht NICHT! Es braucht:
```bash
apt-get install -y libsasl2-modules
```
Enthält `libplain.so` und `liblogin.so` für sasl2.

### Sendmail benutzen
```bash
echo "From: hermes@radislione.net
To: ziel@domain.ch
Subject: Test
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Body" | sendmail -f hermes@radislione.net ziel@domain.ch
```

### Port 25 outbound
Ist vom Hosting-Provider blockiert (`Network is unreachable`).
Nur Port 465/587 via Relay funktionieren.

## Bekannte Fehler

### "SMTPUTF8 is required, but was not offered"
All-Inkl SMTP unterstützt KEIN SMTPUTF8. Emoji/Unicode im Subject → Bounce.
**Lösung:** Kein Emoji im Subject. Nur im Body verwenden.

### "SASL authentication failed: no mechanism available"
Fehlende `libsasl2-modules`. Installieren:
```bash
apt-get install -y libsasl2-modules
```
Dann Postfix reload.

### "SMTPS wrappermode requires setting smtp_tls_wrappermode = yes"
Postfix-Konfiguration für Port 465 vergessen.
```bash
postconf -e "smtp_tls_wrappermode = yes"
postfix reload
```

## Verifikation

```bash
# IMAP Login
python3 -c "import imaplib; m=imaplib.IMAP4_SSL('w019000a.kasserver.com',993); m.login('hermes@radislione.net','ApolloHermes2026!'); m.select('INBOX'); print(f'{len(m.search(None,\"ALL\")[1][0].split())} Mails'); m.logout()"

# SMTP Login
python3 -c "import smtplib; s=smtplib.SMTP_SSL('w019000a.kasserver.com',465); s.login('hermes@radislione.net','ApolloHermes2026!'); print('SMTP OK'); s.quit()"

# Postfix Queue
mailq
tail /var/log/syslog | grep postfix/smtp
```

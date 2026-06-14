---
name: hermes-email-client
description: "Sende und lese E-Mails via hermes@goetschi-labs.ch (All-Inkl IMAP/SMTP). Python-Script als Wrapper, kein Gateway-Neustart. Direct IMAP/SMTP via Python imaplib+smtplib. Migriert von hermes@radislione.net am 08.06.2026."
version: 1.1.0
---

# Hermes Email-Client Skill

**Account:** hermes@goetschi-labs.ch  
**IMAP:** w019000a.kasserver.com:993 (SSL/TLS)  
**SMTP:** w019000a.kasserver.com:465 (SSL/TLS, Wrappermode!)  
**Login:** Volle E-Mail-Adresse (z.B. hermes@goetschi-labs.ch)  
**Credentials in .env:** `HERMES_EMAIL_USER`, `HERMES_EMAIL_PASS`

## ⚠️ TRIGGER-WARNING: DAS IST DAS SYSTEM-POSTFACH

Dieses Postfach (hermes@goetschi-labs.ch) ist das Hermes-**System**-Postfach für automatisierte Dispatch: Statusberichte, Alarme, System-Mails. Es ist NICHT Michels persönliches Postfach.

**Wenn Michel sagt "email check" / "Mails checken" / "prüf mal d'Mails", meint er SEIN Gmail (michelgoetschi@gmail.com), abrufbar via Google MCP (mcp_google_gmail_search / mcp_google_gmail_get).** Dieses IMAP-Postfach enthält nur automatisierte System-Mails. Nie ohne explizite Aufforderung dieses Postfach für "Michels Mails" checken — das führt zu irrelevantem System-Spam.

## Tools

### Script: `scripts/hermes-email.py`

Ein Python-Script für alle Email-Operationen:

```bash
# Status bericht sende
python3 ~/.hermes/skills/email/hermes-email-client/scripts/hermes-email.py send \
  --to michelgoetschi@gmail.com \
  --subject "Statusbericht" \
  --body "Hier der Bericht..."

# Neuesti 5 Mails lese
python3 ~/.hermes/skills/email/hermes-email-client/scripts/hermes-email.py read \
  --limit 5

# Mails vo bestimmem Absender suche
python3 ~/.hermes/skills/email/hermes-email/scripts/hermes-email.py search "betreff"
```

## Credentials (.env)
```bash
HERMES_EMAIL_USER=hermes@goetschi-labs.ch
HERMES_EMAIL_PASS=ApolloHermes2026!
```

## Source of Truth
- **Jira:** GL-72 → GL-141 (Migration zu goetschi-labs.ch)
- **Confluence:** Goetschi Labs Space (Seite 44892161 — Agent-Mailboxen)
- **GitHub:** hermes-agent-skills/hermes-email-client

### Postfix (auf Hermes/156 installiert)

Postfix isch uf Hermes (156) als SMTP-Relay konfiguriert. Sendmail brucht das automatisch. **IMPORTANT:** De Server isch `<KAS-Login>.kasserver.com` (NICHT `smtp.all-inkl.com` oder `imap.all-inkl.com`!).

#### Dpkg-Fix (falls apt-get failt)
Wenn apt-get mit `Sub-process /usr/bin/dpkg returned an error code (1)` failt:
```bash
# Broken packages force-remove
dpkg --purge --force-all libjs-mathjax 2>/dev/null
dpkg --configure -a
# Denn erst libsasl2-modules installiere
apt-get install -y libsasl2-modules
```

### Setup (einmalig)
```bash
# 1. SASL PLAIN Modul (libsasl2-modules, NUR -db isch nöd gnueg!)
apt-get install -y libsasl2-modules

# 2. Postfix konfiguriere (Port 465 = SMTPS wrappermode!)
postconf -e "relayhost = [w019000a.kasserver.com]:465"
postconf -e "smtp_sasl_auth_enable = yes"
postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
postconf -e "smtp_sasl_security_options = noanonymous"
postconf -e "smtp_sasl_mechanism_filter = plain, login"
postconf -e "smtp_tls_wrappermode = yes"
postconf -e "smtp_tls_security_level = encrypt"
postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"

# 3. Credentials
echo "[w019000a.kasserver.com]:465 hermes@goetschi-labs.ch:ApolloHermes2026!" > /etc/postfix/sasl_passwd
postmap hash:/etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db

# 4. Reload
postfix reload
```

### Test-Mail sende
```bash
echo "From: hermes@goetschi-labs.ch
To: michelgoetschi@gmail.com
Subject: Test vo Hermes
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Test vo Hermes via All-Inkl Relay.
Gruss
Hermes" | sendmail -f hermes@goetschi-labs.ch michelgoetschi@gmail.com
```

### Verifikation
```bash
mailq  # Queue leer = delivered
tail /var/log/syslog | grep postfix/smtp  # Zeigt relay w019000a.kasserver.com[..]:465
```

## Pitfalls

### FALSCH: `imap.all-inkl.com` / `smtp.all-inkl.com`
Das sind die generische All-Inkl Load-Balancer. IMAP/SMTP AUTH schlaht dört FIX fähl (535 Error). De korrekt Server isch `<KAS-Login>.kasserver.com` = `w019000a.kasserver.com`.

### Postfix Port 465 bruucht wrappermode
`postconf -e "smtp_tls_wrappermode = yes"` — ohni das seit Postfix "SMTPS wrappermode requires setting smtp_tls_wrappermode = yes"

### KEI Emoji im Subject
All-Inkl SMTP unterstützt **kai SMTPUTF8**. Mail mit `✅`/`🎯`/Emoji im Subject → bounce (SMTPUTF8 required, but not offered). Emoji nur im Body verwende, nie im Subject.

### Port 25 outbound blockiert
Direkti Zustellig zu Gmail MX schlaht fähl (`Network is unreachable`). Nur Relay via Port 465/587 möglich.

### `subprocess.run(input=payload)` mit npx funktioniert nöd
Email-Create/Tools mit mcp-all-inkl müend via heredoc, nöd via stdin-pipe.

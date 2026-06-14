# All-Inkl SMTP/IMAP Konfiguration

**Stand:** 23.05.2026  
**Author:** Hermes Agent  
**Source:** Michels Anleitung + Live-Test

## Server (WICHTIG!)

**Falsch (gibt AUTH-Fehler):**
- `imap.all-inkl.com` / `smtp.all-inkl.com` — das sind Generic Load-Balancer
- AUTH schlaht mit "535 5.7.8 authentication failed" fähl

**Richtig (funktioniert):**
- `w019000a.kasserver.com` — <KAS-Login>.kasserver.com

| | Server | Port | Verschlüsselung |
|--|--------|------|-----------------|
| IMAP | w019000a.kasserver.com | 993 | SSL/TLS |
| SMTP | w019000a.kasserver.com | 465 | SSL/TLS (SMTPS Wrappermode) |

## Credentials

- **Login:** Volle E-Mail-Adresse (z.B. hermes@radislione.net)
- **Passwort:** ApolloHermes2026! (alle 3 Agent-Mailboxen identisch)

## Postfix Relay Setup (für Hermes oder NOVA)

```bash
# Installiere SASL PLAIN Modul (NUR -db reicht nöd!)
apt-get install -y libsasl2-modules

# Postfix konfiguriere
postconf -e "relayhost = [w019000a.kasserver.com]:465"
postconf -e "smtp_sasl_auth_enable = yes"
postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
postconf -e "smtp_sasl_security_options = noanonymous"
postconf -e "smtp_sasl_mechanism_filter = plain, login"
postconf -e "smtp_tls_wrappermode = yes"        # WICHTIG für Port 465!
postconf -e "smtp_tls_security_level = encrypt"
postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"

# Credentials-Datei
echo "[w019000a.kasserver.com]:465 hermes@radislione.net:ApolloHermes2026!" > /etc/postfix/sasl_passwd
postmap hash:/etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db

# Postfix neu starte
postfix reload
```

## Python Script (für IMAP LESE / SMTP SEND ohni Postfix)

```python
import smtplib, imaplib

# SMTP SENDEN
s = smtplib.SMTP_SSL('w019000a.kasserver.com', 465, timeout=15)
s.login('hermes@radislione.net', 'ApolloHermes2026!')
s.send_message(msg)
s.quit()

# IMAP LESE
s = imaplib.IMAP4_SSL('w019000a.kasserver.com', 993, timeout=15)
s.login('hermes@radislione.net', 'ApolloHermes2026!')
s.select('INBOX')
typ, data = s.search(None, 'ALL')
s.logout()
```

## Fehlerbehebung

### "535 authentication failed"
**Ursach:** Falscher Server brucht (`imap.all-inkl.com` oder `smtp.all-inkl.com`)  
**Fix:** `<KAS-Login>.kasserver.com` verwende

### "SASL authentication failed: no mechanism available"
**Ursach:** `libsasl2-modules-db` isch installiert, aber `libsasl2-modules` (mit PLAIN) fehlt  
**Fix:** `apt-get install -y libsasl2-modules`

### "SMTPS wrappermode requires setting smtp_tls_wrappermode = yes"
**Ursach:** Port 465 bruucht SMTPS (Wrapper Mode), nöd STARTTLS  
**Fix:** `postconf -e "smtp_tls_wrappermode = yes"`

### "SMTPUTF8 is required, but was not offered by host"
**Ursach:** Emoji im Subject (All-Inkl unterstützt kein SMTPUTF8)  
**Fix:** Emoji nur im Body, nöd im Subject

### "Network is unreachable" / "Connection timed out" (Port 25)
**Ursach:** Hosting Provider blockiert Port 25 outbound  
**Fix:** Relay via Port 465 oder 587 verwende

### "mail_password update: nothing_to_do"
**Ursach:** KAS-API erkennt kein Unterschied zum gspiicherete Passwort  
**Fix:** Zuerscht älteres Passwort setze, denn s'neue — oder via KAS Web-Interface

## Test

```bash
# SMTP via Python
python3 -c "
import smtplib
s = smtplib.SMTP_SSL('w019000a.kasserver.com', 465, timeout=15)
s.login('hermes@radislione.net', 'ApolloHermes2026!')
print('✅ SMTP Login OK')
s.quit()
"

# IMAP via Python
python3 -c "
import imaplib
s = imaplib.IMAP4_SSL('w019000a.kasserver.com', 993, timeout=15)
s.login('hermes@radislione.net', 'ApolloHermes2026!')
s.select('INBOX')
typ, data = s.search(None, 'ALL')
print(f'✅ IMAP Login OK — {len(data[0].split()) if data[0] else 0} Mails')
s.logout()
"

# Postfix Test
echo 'From: hermes@radislione.net
To: michelgoetschi@gmail.com
Subject: SMTP Test
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Test vo Hermes
Gruss' | sendmail -f hermes@radislione.net michelgoetschi@gmail.com
tail -5 /var/log/syslog | grep status=sent
```

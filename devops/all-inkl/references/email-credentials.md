# Agent-E-Mail-Adressen (@radislione.net)
Erstellt: 23.05.2026 durch Hermes (SUP-33)

## Credentials

| Adresse | Mail-ID | Passwort | Nutzer |
|---------|---------|----------|--------|
| hermes@radislione.net | m07f3b09 | ApolloHermes2026! | Hermes Agent (Logins, Services) |
| nova@radislione.net | m07f3b0a | ApolloHermes2026! | NOVA Agent (Logins, Services) |
| apollo@radislione.net | m07f3b0b | ApolloHermes2026! | Apollo/System (Reserve) |

## Erstellungs-Befehl (Referenz)

```bash
KAS_LOGIN="w019000a" KAS_PASSWORD="***" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_mail","arguments":{"action":"create","params":{"local_part":"hermes","domain_part":"radislione.net","mail_password":"ApolloHermes2026!"}}}}
EOF
```

Response: `m07f3b09` (hermes), `m07f3b0a` (nova), `m07f3b0b` (apollo)

## Sicherheit
- Alle 3 teilen sich dasselbe Passwort (einfacher für Agent-Setup)
- Sollten nur für Service-Logins genutzt werden (keine persönlichen Mails)
- Konfiguriert in: .env, Jira-Attachments (SUP-33), Confluence

---

## Goetschi Labs Agent-Mailboxen (@goetschi-labs.ch)
Erstellt: 08.06.2026 durch Hermes (GL-141, Mail-Migration von radislione.net)

### Credentials

| Adresse | Mail-ID | Passwort | Nutzer |
|---------|---------|----------|--------|
| hermes@goetschi-labs.ch | m07f3b0f | ApolloHermes2026! | Hermes Agent (System-Mail, Dispatch) |
| nova@goetschi-labs.ch | m07f3b10 | ApolloHermes2026! | NOVA Agent (Logins, Services) |
| apollo@goetschi-labs.ch | m07f3b11 | ApolloHermes2026! | Apollo/System (Reserve) |
| orion@goetschi-labs.ch | m07f3b12 | ApolloHermes2026! | ORION Agent |
| info@goetschi-labs.ch | m07f3b0e | ApolloHermes2026! | Info/Eingang |

### Erstellungs-Befehl (Referenz)

```bash
KAS_LOGIN="w019000a" KAS_PASSWORD="***" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_mail","arguments":{"action":"create","params":{"local_part":"hermes","domain_part":"goetschi-labs.ch","mail_password":"ApolloHermes2026!"}}}}
EOF
```

Responses: m07f3b0e (info), m07f3b0f (hermes), m07f3b10 (nova), m07f3b11 (apollo), m07f3b12 (orion)

### Migration-Status (Stand 08.06.2026)

| Alte Adresse (radislione.net) | Neue Adresse (goetschi-labs.ch) | Status |
|------|------|--------|
| hermes@radislione.net (m07f3b09) | hermes@goetschi-labs.ch (m07f3b0f) | ✅ Hermes-Client migriert, alte noch nicht gelöscht |
| nova@radislione.net (m07f3b0a) | nova@goetschi-labs.ch (m07f3b10) | ❌ Nicht migriert |
| apollo@radislione.net (m07f3b0b) | apollo@goetschi-labs.ch (m07f3b11) | ❌ Nicht migriert |

**Bekanntes Problem:** Löschen der alten radislione.net-Mailboxen über mcp-all-inkl@1.0.6 `delete`-Action schlägt fehl (Parameter-Bug — siehe SKILL.md Fehler-Tabelle). Workaround via SSH → LXC 107 → lxc-attach ist möglich (siehe `scripts/create-mails.py`).

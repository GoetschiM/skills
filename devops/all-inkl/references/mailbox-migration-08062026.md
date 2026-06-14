# Mailbox Migration radislione.net → goetschi-labs.ch (08.06.2026)

## Background
Radislione.net war der ursprüngliche Provider für Hermes-Agent-Mailboxen. Mit GL-141 wurde beschlossen, alle Agent-Mailboxen auf goetschi-labs.ch zu migrieren — die Domain des eigentlichen Projekts.

## Mailboxes auf goetschi-labs.ch (erstellt)
| Adresse | Mail-ID | Erstellt | Passwort |
|---------|---------|----------|----------|
| info@goetschi-labs.ch | m07f3b0e | 08.06.2026 | ApolloHermes2026! |
| hermes@goetschi-labs.ch | m07f3b0f | 08.06.2026 | ApolloHermes2026! |
| nova@goetschi-labs.ch | m07f3b10 | 08.06.2026 | ApolloHermes2026! |
| apollo@goetschi-labs.ch | m07f3b11 | 08.06.2026 | ApolloHermes2026! |
| orion@goetschi-labs.ch | m07f3b12 | 08.06.2026 | ApolloHermes2026! |

## Alte radislione.net Mailboxes (zu löschend)
| Adresse | Mail-ID | Status |
|---------|---------|--------|
| hermes@radislione.net | m07f3b09 | ❌ Delete blocked (mcp-all-inkl@1.0.6 bug) |
| nova@radislione.net | m07f3b0a | ❌ Noch nicht migriert |
| apollo@radislione.net | m07f3b0b | ❌ Noch nicht migriert |
| user45@radislione.net | — | ❌ Nicht angetastet |
| user97@radislione.net | — | ❌ Nicht angetastet |
| user99@radislione.net | — | ❌ Nicht angetastet |

## Migration Steps (pro Agent)

1. **Neue Mailbox erstellen** auf goetschi-labs.ch via mcp-all-inkl `kas_mail create`
2. **Email-Client umstellen** — Patch .env + Script defaults
3. **Qdrant-Knowledge aktualisieren** — Neue Adresse/Werte im Wissensspeicher
4. **Confluence-Seite updaten** — Seite 44892161 (Agent-Mailboxen)
5. **Jira-Ticket schliessen** — GL-141: Status-Update + Kommentar
6. **Alte Mailbox löschen** — Von radislione.net (siehe Bug unten)

## Bekannte Fehler/Lösungen

### 🐛 mcp-all-inkl@1.0.6 Delete-Bug
- **Problem:** `kas_mail delete` mit `params.mail_login="m07f3b09"` gibt immer "Pflichtfeld fehlt: mail_login" zurück
- **Ursache:** Node-Wrapper übergibt Parameter nicht korrekt an die SOAP-API
- **Workaround 1 — SSH → LXC 107:** 
  ```bash
  sshpass -p 'PASS' ssh root@10.0.60.10 \
    "lxc-attach -n 107 -- sh -c 'KAS_LOGIN=w019000a KAS_PASSWORD=*** mcp-all-inkl' << 'INNEREOF'
  {\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"kas_mail\",\"arguments\":{\"action\":\"delete\",\"params\":{\"mail_login\":\"m07f3b09\"}}}}
  INNEREOF"
  ```
- **Workaround 2 — Direct KAS SOAP:** Siehe `references/kas-soap-direct.md` für Python-Code
- **Hinweis:** `create` funktioniert ohne Probleme via normalem npx-Aufruf

### 🐛 KasAuth SOAP-Endpoint
- **Problem:** Direkter SOAP-Call an KasAuth.php für Login schlägt fehl
- **Ursache:** Der Endpoint akzeptiert nur das spezifische XML-Format von mcp-all-inkl (urn:KasAuth Namespace + KasAuth-Method)
- **Lösung:** Immer mcp-all-inkl verwenden, nicht direkt SOAP

## TODO (nach Bugfix)
- [ ] Delete hermes@radislione.net (m07f3b09)
- [ ] Migrate NOVA-MAIL-CLIENT to nova@goetschi-labs.ch
- [ ] Migrate APOLLO-MAIL-CLIENT to apollo@goetschi-labs.ch
- [ ] Delete nova@radislione.net (m07f3b0a)
- [ ] Delete apollo@radislione.net (m07f3b0b)

# mcp-all-inkl — All-Inkl.com Hosting Admin via MCP

**SUP-33** — Integriert 23.05.2026

## Überblick

`mcp-all-inkl` (npm: `hl9020/mcp-all-inkl`) verbindet Hermes mit em All-Inkl.com KAS SOAP API.
9 Tools, 53 Aktionen: DNS, Domains, Subdomains, MySQL-DBs, Email, Cronjobs, SSL, Account, System.

GitHub: https://github.com/hl9020/mcp-all-inkl

## Config (config.yaml)

```yaml
mcp_servers:
  all-inkl:
    command: "npx"
    args: ["-y", "mcp-all-inkl"]
    env:
      KAS_LOGIN: "w019000a"
      KAS_PASSWORD: "***"
    timeout: 30
    connect_timeout: 15
```

## Zugriffsregle (Michel, per SUP-33)

| Bereich | Rächt | Grund |
|---------|-------|-------|
| DNS, Domains, DBs, SSL, Cronjobs | READ ONLY | Live-Pages mit SLA |
| E-Mail (Mailboxe, Forwards, Liste) | FULL | Michel erlaubt |
| Account-Management | NONE | Sicherheit |

## Getesteti Tools

| Tool | Test | Resultat |
|------|------|----------|
| `kas_domain(list)` | ✅ | 10 Domains |
| `kas_mail(list)` | ✅ | 336 Mail-Entries |
| `kas_system(get_space)` | Testbereit | Speicherplatz |

## Domains (Stand 23.05.2026)

radislione.net, darklake.uk, smarthausautomation.ch, moto-poschung.ch, grow-pro.ch, darksoul.ch, besorgsdir.ch, motoposchung.ch, rebelone.ch, darklake.ch

## Agent-Emails (@radislione.net)

| Adresse | Mail-ID | Passwort | Nutzer |
|---------|---------|----------|--------|
| hermes@radislione.net | m07f3b09 | ApolloHermes2026! | Hermes Agent |
| nova@radislione.net | m07f3b0a | ApolloHermes2026! | NOVA Agent |
| apollo@radislione.net | m07f3b0b | ApolloHermes2026! | Apollo/System |

## Direkter MCP-Call (ohne Gateway-Config, Skill-Nutzung)

Skill `devops/all-inkl` (`scripts/hermes-all-inkl.sh`) bi dir installiert:
```bash
bash /path/to/hermes-all-inkl.sh kas_domain list
bash /path/to/hermes-all-inkl.sh kas_mail list
```

Oder pur via heredoc (für NOVA/andere Agents):
```bash
KAS_LOGIN="w019000a" KAS_PASSWORD="***" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_domain","arguments":{"action":"list"}}}
EOF
```

## Pitfalls

- **KAS Flood Protection:** Bei schnelle sukzessive Calls wird automatisch gwarted (KasFloodDelay)
- **DNS zone_host:** Muess mit emene trailing dot enden: `"example.com."` nöd `"example.com"` (Server fixts auto, aber lieber korrekt)
- **36px Mail-Entries** — bi `list`-Befuhl chunnt alli, kei Pagination
- **Credentials im .env** — NIE hardcoded i Config, immer via `env:` Block
- **SLA-Risiko** — Wäge Live-Pages (BN 602127PW Riotstar_ALLINKL_13) nüt schriibe ohni Michels OK!
- **SSL tool:** Nur `update` (installiere), kei `list` oder `delete`

---
name: all-inkl
description: "All-Inkl.com Webhosting MCP — Verwaltet Domains, DNS, E-Mail, DBs via KAS-SOAP-API. Nutzt entweder direkt CLI (Skill-Modus) oder MCPHub (Server-Modus). Zwei Modi: Skill (für Hermes) und MCP-Server (für ALLI Agents via Gateway)."
version: 2.1.0
author: Hermes Agent
platforms: [linux, macos]
scripts:
  - scripts/hermes-all-inkl.sh
references:
  - references/email-credentials.md
  - references/smtp-imap-auth.md
  - references/email-connectivity.md
category: devops
platforms: [linux, macos]
scripts:
  - scripts/hermes-all-inkl.sh
references:
  - references/email-credentials.md
  - references/smtp-imap-auth.md
  - references/email-connectivity.md
---

# All-Inkl MCP — Skill & MCP-Server Dokumentation

**Version 2.0.0** — Komplett überarbeitet mit zwei Nutzungsmodi:
- **Skill-Modus:** Hermes-only, direkt via CLI (füe existierendi Hermes-Session)
- **MCP-Server-Modus:** Zentral übe MCPHub für ALLI Agents (NOVA, ORION, MAGOS G., etc.)

---

## 🔧 Grundwüsse: Was ist All-Inkl?

All-Inkl.com isch en deutsche Webhoster. Mir hend dört:

- **Account:** `w019000a` (KAS-Login)
- **BN (Kundennummer):** 602127PW
- **Vertragspartner:** Riotstar GmbH
- **Domains:** 10 Stück (radislione.net, darklake.uk, smarthausautomation.ch, moto-poschung.ch, grow-pro.ch, darksoul.ch, besorgsdir.ch, motoposchung.ch, rebelone.ch, darklake.ch)
- **Mailboxen:** ~336 Stück
- **Webspace:** MySQL-DB, Cronjobs, SSL-Zertifikate, Subdomains

**KAS API** = d'SOAP-basierti Management-API vo All-Inkl. De MCP Server (`mcp-all-inkl`) kapslet das i einfachi JSON-RPC Calls.

---

## 🗝️ Credentials

| Variable | Wert | Beschrieb |
|----------|------|-----------|
| `ALLINKL_KAS_LOGIN` | `w019000a` | KAS-Benutzername (Account-ID) |
| `ALLINKL_KAS_PASSWORD` | _im .env_ | KAS-Passwort (vom Kundenkonto!) |
| `KAS_LOGIN` | `w019000a` | Alias (optional, unterstützt) |
| `KAS_PASSWORD` | _im .env_ | Alias (optional, unterstützt) |

**Wo gspüchert:** `/root/.hermes/.env`

**Passwort-Setze (sicher):**
```bash
# IMMER Single Quotes verwende! Sonderzeiche ($, !, %, ^) würded suscht expandiert!
echo 'ALLINKL_KAS_LOGIN="w019000a"' >> ~/.hermes/.env
echo 'ALLINKL_KAS_PASSWORD="DeinPasswort!"' >> ~/.hermes/.env
```

---

## 📦 Modus A: Skill-Modus (direkt via CLI für Hermes)

### Voraussetzig

```bash
node --version  # Node.js 22+ nötig
# mcp-all-inkl wird via npx automatisch useglade
```

### Nutzig via Wrapper-Script

```bash
cd /root/.hermes/skills/devops/all-inkl/scripts
chmod +x hermes-all-inkl.sh

# Syntax
hermes-all-inkl <tool> [action] [params-json]

# Beispiele:
hermes-all-inkl kas_domain list
hermes-all-inkl kas_mail list
hermes-all-inkl kas_mail list_forwards
hermes-all-inkl kas_system get_space
hermes-all-inkl kas_dns list '{"params":{"zone_host":"radislione.net."}}'

# E-Mail erstelle (nu mit Bestätigung!)
hermes-all-inkl kas_mail create '{"local_part":"hermes","domain_part":"radislione.net","mail_password":"SicheresPasswort!"}'
```

### Direkter JSON-RPC Call (ohne Wrapper)

```bash
KAS_LOGIN="w019000a" KAS_PASSWORD="DeinPasswort" npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_mail","arguments":{"action":"list"}}}
EOF
```

**⚠️ Wichtig:** `<< 'EOF'` (single-quoted!) — verhindert Passwort-Expansion

---

## 🔄 MCP-Server mit mcp-proxy starte (eigenständig)

Falls du en eigene MCP-Server-Prozess wetsch starte (ohni MCPHub), nutz `mcp-proxy`:

```bash
# Python Script (falls vorhande — lueg /usr/local/bin/all-inkl-mcp.py)
mcp-proxy --port 3103 --host 0.0.0.0 \
  -e ALLINKL_KAS_LOGIN w019000a \
  -e KAS_LOGIN w019000a \
  -e ALLINKL_KAS_PASSWORD "DEIN_PASSWORT" \
  -e KAS_PASSWORD "DEIN_PASSWORT" \
  /usr/local/bin/all-inkl-mcp.py

# Oder via npx (Standard)
mcp-proxy --port 3103 --host 0.0.0.0 \
  -e KAS_LOGIN w019000a \
  -e KAS_PASSWORD "DEIN_PASSWORT" \
  -- npx -y mcp-all-inkl
```

**⚠️ Wichtig:** 
- `-e KEY VALUE` **mit Leerschlag** (nit mit `=`!) — sunsch `expected 2 arguments`
- `--port` / `--host` VOR de `-e` Flags setze
- De Command (Python Script oder npx) ganz AM ENDI

**Systemd-Service (optional, für dauerhafte Betrieb):**
```bash
cat > /etc/systemd/system/all-inkl-mcp.service << 'EOF'
[Unit]
Description=All-Inkl MCP Server
After=network.target

[Service]
Type=simple
User=root
Environment=ALLINKL_KAS_LOGIN=w019000a
Environment=ALLINKL_KAS_PASSWORD=DEIN_PASSWORT
Environment=KAS_LOGIN=w019000a
Environment=KAS_PASSWORD=DEIN_PASSWORT
ExecStart=/usr/local/bin/mcp-proxy --port 3103 --host 0.0.0.0 /usr/local/bin/all-inkl-mcp.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now all-inkl-mcp.service
```

**Test ob de Server lauft:**
```bash
# SSE-Endpoint prüefe
curl -s http://localhost:3103/sse | head -5
# Sött usgäh: event: endpoint\ndata: /messages/?session_id=...

# Tools liste (SSE asynchron — Response chunnt über de SSE-Stream)
curl -s -X POST "http://localhost:3103/messages/?session_id=test123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## 🖥️ Modus B: MCP-Server-Modus (zentral übe MCPHub)

### Ziel

Statt dass jede Agent sini eigene Credentials setzt, lauft **mcp-all-inkl** als dauerhafte MCP-Server im **MCPHub** (LXC 107). Alli Agents froged nur nomol über de Gateway aa.

### Setup im MCPHub

**Schritt 1:** Config `/opt/mcphub/mcp_settings.json` update:

```json
{
  "mcpServers": {
    "all-inkl": {
      "type": "npx",
      "name": "all-inkl",
      "command": "npx",
      "args": ["-y", "mcp-all-inkl"],
      "env": {
        "KAS_LOGIN": "w019000a",
        "KAS_PASSWORD": "DeinPasswort"
      }
    }
  }
}
```

**Schritt 2:** MCPHub neustarte oder Config neu lade:

```bash
docker restart mcphub
# oder: Config hot-reload (falls unterstützt)
curl -X POST http://10.0.60.170:3000/api/reload
```

**⚠️ Quote-Escaping beim Config-Deploy via SSH:**
Wenn du d'Config uf LXC 107 via ssh/lxc-attach update wetsch, gits heavy Quote-Conflicts (SSH → lxc-attach → Python heredoc → JSON). **Bewährti Methode:** Config als Python-File uf LXC 107 erstelle, det ausfüehre:

```bash
# Arbeitet zueverlässig — kein Quote-Hell
sshpass -p 'PASS' ssh root@10.0.60.10 "lxc-attach -n 107 -- python3 -c '
import json, os
f = \"/opt/mcphub/mcp_settings.json\"
c = json.load(open(f)) if os.path.exists(f) else {\"mcpServers\": {}}
c[\"mcpServers\"][\"all-inkl\"] = {\"type\":\"npx\",\"name\":\"all-inkl\",\"command\":\"npx\",\"args\":[\"-y\",\"mcp-all-inkl\"],\"env\":{\"KAS_LOGIN\":\"w019000a\",\"KAS_PASSWORD\":\"DEIN_PASSWORT\"}}
json.dump(c, open(f, \"w\"), indent=2)
print(f\"OK: {len(c[\"mcpServers\"])} MCPs\")
'"

# Dänn Docker restart
sshpass -p 'PASS' ssh root@10.0.60.10 "lxc-attach -n 107 -- docker restart mcphub"
```

**NIE** `sed` über SSH mit Sonderzeiche (`%`, `^`, `!`) im Passwort — das verursacht unvorhersehbare Shell-Expansion.

**Schritt 3:** Verifikation:

```bash
# Health-Check
curl -s http://10.0.60.170:3000/health | jq '.["all-inkl"]'

# Agent-Call via Gateway
curl -s http://10.0.60.170:3000/api/call   -H "X-Auth-Token: $TOKEN"   -H "Content-Type: application/json"   -d '{
    "server": "all-inkl",
    "tool": "kas_domain",
    "arguments": {"action": "list"}
  }'
```

### Alternative: Docker-eigeständig (User-Präferenz 06.06.2026)

Gemäss User-Präferenz sött MCP-Server lieber als **eigeständige Docker-Container** uf LXC 107 laufe, statt als npx-Subprozess:

```
Dockerfile:
FROM node:22-alpine
RUN npm install -g mcp-all-inkl
ENV KAS_LOGIN=w019000a
ENV KAS_PASSWORD=DeinPasswort
EXPOSE 3103
CMD ["mcp-all-inkl"]
```

Denn im MCPHub als `"type": "url"` registriere:

```json
{
  "all-inkl": {
    "type": "url",
    "url": "http://10.0.60.170:3103"
  }
}
```

---

## 🧰 Tools & Actions (9 Tools, 53 Actions)

### kas_domain — Domains
| Action | Beschrieb | Parameter |
|--------|-----------|-----------|
| `list` | Alli Domains | — |
| `list_tlds` | Verfüegbare TLDs | — |
| `create` | Neui Domain registriere | domain_name, domain_tld |
| `update` | Domain-Einstellige ännere | domain_name, ... |
| `delete` | Domain lösche ❌ | domain_name |
| `move` | Domain transferiere ❌ | domain_name, source_account, target_account |

### kas_dns — DNS Records
| Action | Beschrieb |
|--------|-----------|
| `list` | DNS-Records vo ere Zone |
| `create` | Neje Record ahläge |
| `update` | Record bearbeite |
| `delete` | Record lösche ❌ |
| `reset` | Ganci Zone zurücksetze ❌ |

### kas_mail — E-Mail ✅ **Schriibrächt!**
| Action | Beschrieb | Spezielle Parameter |
|--------|-----------|-------------------|
| `list` | Alli Mailboxe | — |
| `create` | Mailbox ahläge | local_part, domain_part, mail_password |
| `update` | Mailbox bearbeite | mail_login, ... |
| `delete` | Mailbox lösche ❌ | mail_login |
| `list_forwards` | Forwards ahzeige | — |
| `create_forward` | Forward ahläge ❌ | local_part, domain_part |
| `delete_forward` | Forward lösche ❌ | mail_forward |
| `list_lists` | Mailingliste | — |
| `create_list` | Mailingliste ahläge ❌ | mailinglist_name, mailinglist_domain, mailinglist_password |

### kas_database — MySQL/PostgreSQL
| Action | Beschrieb |
|--------|-----------|
| `list` | Alli Datebanke mit Grösse |
| `create` | Datebank ahläge ❌ |
| `update` | Passwort/Kommentar |
| `delete` | Datebank lösche ❌ |

### kas_subdomain — Subdomains
| Action | Beschrieb |
|--------|-----------|
| `list` | Alli Subdomains |
| `create` | Neji ahläge ❌ |
| `delete` | Lösche ❌ |
| `move` | Verschiebe ❌ |

### kas_cronjob — Cronjobs
| Action | Beschrieb |
|--------|-----------|
| `list` | Alli Cronjobs |
| `create` | Neje ahläge ❌ |
| `update` | Bearbeite ❌ |
| `delete` | Lösche ❌ |

### kas_ssl — SSL Zertifikat
| Action | Beschrieb |
|--------|-----------|
| `update` | Zertifikat installiere ❌ |

### kas_account — Account
| Action | Beschrieb |
|--------|-----------|
| `list` | Alli Sub-Accounts |
| `get_resources` | Resource-Limite |
| `get_settings` | Account-Settings |
| `get_server_info` | Server-Info (PHP, MySQL, OS) |
| `create/update/delete` | Sub-Accounts ❌ |

### kas_system — System
| Action | Beschrieb |
|--------|-----------|
| `get_space` | Speicherplatz |
| `get_traffic` | Traffic-Statistike |
| `get_space_usage` | Detailierte Speicherplatz |

> ❌ = **Destruktiv/Schriibrächtig** — Bruucht User-Bestätigung!

---

## 📧 IMAP/SMTP Zugriff

Für E-Mail-Clients (Hermes, Himalaya, Thunderbird, etc.):

| Dienst | Server | Port | Verschlüsselig |
|--------|--------|------|----------------|
| **IMAP** | `w019000a.kasserver.com` | 993 | SSL/TLS |
| **SMTP** | `w019000a.kasserver.com` | 465 | SSL/TLS (Wrappermode) |
| **Login** | Voli E-Mail-Adresse (z.B. `hermes@radislione.net`) | | |

Agent-Mailboxe (goetschi-labs.ch, all **ApolloHermes2026!**):
| Adresse | Agent | Status |
|---------|-------|--------|
| `info@goetschi-labs.ch` | Allgemein | ✅ Erstellt 08.06.2026 |
| `hermes@goetschi-labs.ch` | Hermes | ✅ Erstellt 08.06.2026, aktiv |
| `nova@goetschi-labs.ch` | NOVA | ✅ Erstellt 08.06.2026 |
| `magos@goetschi-labs.ch` | MAGOS | ✅ Erstellt 08.06.2026 |
| `orion@goetschi-labs.ch` | Orion | ✅ Erstellt 08.06.2026 |

Alti Mail hermes@radislione.net → **soll gelöscht werde** (radislione.net-Account nüüt me). Alti NOVA-Mail nova@radislione.net wird nüme bruucht (NOVA chunt neu uf goetschi-labs.ch).

**Aktueller Stand (11.06.2026):** MCPHub all-inkl Verbindig isch **disconnected** — Zod v4 SDK-Inkompatibilität. Workaround: Skill-Modus via `hermes-all-inkl <tool> <action>` oder direkti Python-SOAP-Calls.

> **Wichtig:** Kei Emoji im Subject (All-Inkl unterstützt kei SMTPUTF8!)

---

## ⚠️ Sicherheitsregle (MÜSSE immer befolgt werde!)

1. **READ ONLY** für Domains, DNS, Datebanke, SSL — nüt lösche/ändere ohni Michels OK!
2. **E-Mail** darf VERVOLLSTÄNDIG verwaltet werde (Michels Erlaubnis)
3. **Grundsätzlich:** Alles usser `list` brucht User-Bestätigung
4. **NIE** Passwort im Chatoutput hardcoded aazeige — us `.env` lese, mit `***` maskiere
5. **NIE** Pages/Domains aalänge (SLA-Vertrag!)
6. **Credentials us `.env` lese**, nie hardcoded i Chats/Code

---

## 🐛 Häufigi Fehler & Lösige

| Fehler | Ursach | Lösig |
|--------|--------|-------|
| `kas_password_incorrect` | *(1) Passwort falsch. (2) Falschi Env-Var. (3) KAS Account gspärrt. (4) Flood-Protection / IP temporär blockiert.* | `KAS_LOGIN` UND `KAS_PASSWORD` setze (2 Varianten). >3 Login-Versuche/Minute → Flood-Sperri. Im All-Inkl Webadmin luege. |
| `HTTP 405/500` | API-Endpoint falsch (KasAuth vs KasApi) | Login: `/soap/KasAuth.php` (urn:KasAuth). API: `/soap/KasApi.php` (urn:KasApi). |
| `MessageParseException` | `<Params>`-Inhalt het unescapti Zeiche | `p.replace("&", "&amp;")` nach JSON.stringify() — exakt wie Node source |
| `flood delay` | Z'vilni Calls pro Minute | 3–5 Sek. Pause; Flood Delay us Response lese |
| `kas_password_incorrect` trotz korrektem Passwort (Version 1.0.4) | mcp-all-inkl 1.0.4 het e Login-Bug (Session Handling) | `npm install -g mcp-all-inkl@1.0.6` — Version 1.0.6 het korrekte Session-Timeout und Login. Check: `node -e \"console.log(require('/usr/lib/node_modules/mcp-all-inkl/package.json').version)\"` |
| `Command timeout` | npx ladt Package zemme erste Mol | Einfach nomol usfüehre |
| `Pflichtfeld fehlt: mail_login` (delete) | mcp-all-inkl@1.0.6 Bug: `delete`-Action übergibt `mail_login` im `KasRequestParams` nöd korrekt ans SOAP — `mail_login` wird immer als fehlend gmeldet, obwohl er korrekt gsetzt isch | **Lösig:** Direkti SOAP via Python (ohni mcp-all-inkl) für delete (siig `references/kas-soap-email-creation.md`). NIE `delete_mailaccount` via npx/mcp-all-inkl — nur via directe SOAP mit Session-Token. |
```bash
sshpass -p 'PASS' ssh root@10.0.60.10 \
  "lxc-attach -n 107 -- sh -c 'KAS_LOGIN=w019000a KAS_PASSWORD=\"PASS\" mcp-all-inkl' << 'INNEREOF'
{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"kas_mail\",\"arguments\":{\"action\":\"delete\",\"params\":{\"mail_login\":\"m07f3b09\"}}}}
INNEREOF"` |
| `mcp-proxy: Expected string, received undefined` | mcp-all-inkl@1.0.6 Sendet kei protocolVersion im Initialize — MCPHub Zod v4 erwartet string | Workaround: Python mcp-proxy (mit `--pass-environment`) oder Docker-eigeständig deploye |
| `module not found` | Node < 22 | `node -v` prüefe, Upgrade |
| Empty stdout (Exit 0) | Heredoc ohne `'EOF'` (Passwort-Zeiche expandiert) oder falsche JSON-Body | `<< 'EOF'` (single-quoted!) verwende; oder JSON via `/dev/stdin` pipe mit `printf` |
| Sonderzeiche im Passwort expandiert | Bash expandiert `$`, `!`, `%`, `^` in Doppel-aafüerigszeiche | IMMER single quotes (`'EOF'`) verwende; NIE doppelt! |
| `tool: ${AL...}`-Platzhalter werden im Befehl ersetzt | Tool ersetzi `ALLINKL_KAS_PASSWORD` oder `PASSWORD=***` automatisch mit `AL...`-Platzhalter | Schriib e Script-File und füehr det us. Verwänd `source .hermes/.env` im Script. Nie `${ALLINKL_KAS_...}` nackt im Befehl schriibe. |
| MCP-proxy: `Accepted` aber kei JSON-Response | SSE-Asynchronität — Response chunnt über SSE-Event, nöd per HTTP-Rückgab | SSE stream lese (`curl -s -N /sse`), det chömmed d'JSON-RPC-Responses |
| `ConnectionError` bim mcp-proxy / Python MCP | `--pass-environment` vergässe oder env via `-e` falsch gsetzt | Env mit `-e KEY VALUE` (mit Leerschlag!) setze ODER `--pass-environment` |
| MCPHub disconnected für all-inkl | Zod v4 SDK Inkompatibilität: mcp-all-inkl@1.0.6 het veralteti Initialize Response (fählt `protocolVersion` string) | **Debug:** Docker logs luege: `docker logs mcphub 2>&1 | grep -i \"all-inkl\\|error\\|ZodError\"`. Wenn `ZodError: expected string` — SDK-Bug. **Lösig:** mcp-all-inkl als eigenständige Docker-Container deploye und als URL-MCP im MCPHub registriere (Weg 2). Alternativ mcp-proxy Zwüscheschicht. |
| MCP-Hub – Config deploy über SSH | Quote-Escaping-Hölle: SSH → lxc-attach → Python/JSON mit Sonderzeiche | Verwänd **Python-einzylig über SSH** (bewährt!): `ssh host \"lxc-attach -n 107 -- python3 -c '...'\"`. Never sed over SSH mit Sonderzeiche. |

---

## 📚 Referenze

- **GitHub Repo:** https://github.com/hl9020/mcp-all-inkl
- **All-Inkl KAS Doku:** https://all-inkl.com/kas
- **Confluence Doku:** [Confluence All-Inkl Page](https://nextcloud.rebelone.ch/confluence)
- **Credentials:** `/root/.hermes/.env` und `/opt/data/home/.hermes/.env`
- **Email Credentials & Migration:** `references/email-credentials.md`, `references/mailbox-migration-08062026.md`
- **MCPHub-Deployment:** `/root/.hermes/skills/devops/all-inkl/references/mcphub-deployment.md`
- **KAS SOAP API Internals:** `references/kas-soap-api-internals.md` (reverse-engineered XML-Strukture, mcp-all-inkl Source-Code, Fehlermatrix)
- **KAS SOAP Direct API:** `references/kas-soap-direct.md` (Python-Cheat-Sheet für directe SOAP-Calls, Action-Mapping-Tabelle)
- **KAS SOAP Email Creation:** `references/kas-soap-email-creation.md` (Python-Cheat-Sheet speziell für Email-Create/Delete — funktioniert zuverlässiger als mcp-all-inkl)
- **Weitere Referenze:** In diesem Skill-Ordner under `references/`

---

## 🚀 Quick-Start Cheat Sheet

```bash
# Hermes-Skill-Modus
hermes-all-inkl kas_domain list                          # Domains
hermes-all-inkl kas_mail list                            # Mailboxe
hermes-all-inkl kas_system get_space                     # Speicher
hermes-all-inkl kas_dns list '{"params":{"zone_host":"radislione.net."}}'
hermes-all-inkl kas_mail list_forwards                   # Forwards

# MCPHub-Modus (via Agent Gateway)
# all-inkl.tool("kas_mail", {"action": "list"})

# Direkter JSON-RPC
KAS_LOGIN="w019000a" KAS_PASSWORD="..." npx -y mcp-all-inkl << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kas_domain","arguments":{"action":"list"}}}
EOF
```

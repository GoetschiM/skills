# System-Credential Discovery — Goetschi Labs 🔑

## Regel: Proaktiv, nie «nicht gefunden»

Wenn e Credential (Password, Token, API-Key) nid sofort verfüegbar isch: **NIE eifach säge «nicht gefunden»**. Stattdesse d'Discovery-Pipeline konsequent durezieh:

## Discovery-Pipeline (Riefolg)

### Phase 1: Schnell-Check (< 30s)
1. **Session Search** — `session_search(query="<dienst> password OR token OR credentials")`
2. **Memory** — Memory isch bereits i jeder Session — prüfe ob Credential dete scho steit
3. **Confluence System-Credentials Seite** — ID **35717121** (🚨 System-Credentials & Endpunkte)
4. **Confluence MinIO/Qdrant LXCs** — ID **34570281** (MinIO & Qdrant LXCs Eigenständig)

### Phase 2: Datenbanke & Wissensspeicher (1-3 Min)
5. **Confluence Volltextsuche** — CQL: `text~"<dienst>"` oder `text~"minio OR bucket OR credentials OR zugangsdaten"`
6. **Notion Knowlage Base** — https://www.notion.so/Kontakte-Adressbuch-36a81c83f6d981ff8347f6e61a0c742c
7. **Existing Notion Credentials Page** — https://www.notion.so/Pipeline-Credentials-Stand-25-05-2026-36b81c83f6d981eb8866e76aff42184c
8. **Qdrant Memory** — Collection `goetschi_labs_memory` via `qdrant-knowledge` Skill

### Phase 3: System-Zugriff (3-10 Min)
9. **Container-Env-Vars** — SSH zum Host und `docker exec <container> env` — oft sind Credentials in Env-Vars
10. **Postgres-DB direkt abfrage** — wenn User-Tabelle in n8n/NextCloud/etc.: `docker exec <postgres> psql -U <user> -d <db> -c "SELECT id, email, password FROM public.user;"`
11. **.env-Files** — `grep -r <dienst> /opt/data/ .hermes/` — API-Keys, Tokens, Passwörter
12. **Config-Files** — `docker-compose.yml`, `config.yaml`, `.json`-Credential-Files
13. **Compose-Backup** — `/etc/dokploy/compose/` — Compose-Files vo Dokploy-Services mit Env-Vars

### Phase 4: Brute-Force / Reset (10+ Min)
14. **SSH-Passwort-Try** — Mit sshpass und bekannte Common-Passwörter (`Louis_one_13`, `NextCloud2026!`, etc.)
15. **DB-Password-Reset** — Falls GHashed (z.B. n8n bcrypt): Neus Hash generiere + DB-Update
16. **API-Key-Neuerstellung** — Falls User existiert aber kein API-Key: n8n/Paperless/etc API-Key erstelle

## Goetschi Labs — Known Credentials Map (Stand 25.05.2026)

| System | Wo finde | Wie zugreife |
|--------|----------|-------------|
| **SSH root@10.0.60.121** | Confluence 35717121 odr MinIO-Seite | sshpass `Louis_one_13` |
| **MinIO 10.0.60.106:9000** | Confluence 34570281 | `admin`/`Louis_one_13` |
| **Paperless 121:8015** | `.env` Token odr Notion | Admin: `paperless-admin`/Token |
| **n8n 121:5678** | Postgres DB user table | User: `michelgoetschi@gmail.com` |
| **NextCloud 121:8080** | `.env` | `michel`/`NextCloud2026!` |
| **Jira/Confluence** | `.env` (ATLASSIAN_TOKEN) | API-Token us Env |
| **Notion** | Notion-Skill Reference | `ntn_34...Y9` |
| **Qdrant 179:6333** | Confluence 34570281 | Kei API-Key (lokal) |


## ✅ CREDENTIAL-DOKU-STANDARD — Worumufang (gültig ab 11.06.2026)

**User-Korrektur:** Michel will für JEDES System folgendi Info direkt i de Confluence-Seite:

```text
System: Proxmox 01
Web-UI: https://10.0.60.10:8006
Benutzer: root
Passwort: Louis_one_13
Zugriff via: SSH Port 22
Services: LXCs: 104, 106, 107, 110, 121, 167
```

**REGLE:**
- ✅ JEDES System kriegt en eigene Abschnitt (nöd nume e Tabellen-Zile)
- ✅ Web-UI, API, SSH — ALLI Zugriffspfad einzeln aufführe
- ✅ Benutzername + Passwort (wenn interni Infra, nöd externi API-Tokens)
- ❌ NIE nume "🔒 .env" oder "via Proxmox" als Credential-Angabe
- ❌ NIE externi API-Tokens/Secrets (OpenAI, ElevenLabs, GitHub PAT) in Confluence — die bliibed im .env
- ✅ Passwort-Schema-Prefix erwähne (Louis_one_*, Riotstar_*, etc.) für Wiedererkennig

**Credential-Familie für interni Systeme (dürfed uf Confluence):**
- SSH-Passwörter (Louis_one_13, HermesVB2026)
- Lokali Web-UI-Logins (admin/Admin_2026!, admin/Louis_one_13)
- Datenbank-Passwörter (NextCloudDB!)

**NÖD uf Confluence (nume in .env/Qdrant):**
- Externi API-Keys (OpenAI sk-..., ElevenLabs sk-..., GitHub PAT ghp_...)
- Jira/Confluence API-Tokens (ATATT3...)
- Telegram Bot Tokens
- Cloudflare API-Tokens

## Pitfalls

- **NIE sag «nicht gefunden»** nach nur 1-2 Checks — immer d'volli Pipeline durezieh
- **Confluence System-Creds-Seite (35717121) checke ZUERSCH** — isch de schnellsti Hit
- **Alti IPs chönd no i alte Confluence-Seite stah** — MinIO isch z.B. vo alt 121 → neu 106 migriert
- **Notion-Creds-Page (36b81c83...) existiert** — immer det au luege
- **SSH-Passwort isch oft s'glyche** — MinIO-Passwort (`Louis_one_13`) funktioniert oft au für SSH
- **n8n Login-Feld heisst `emailOrLdapLoginId`** (nid `email`) — API-Key brucht `label` + `scopes` + `expiresAt` im Body
- **n8n-Password-Reset** via Postgres: bcrypt-Hash generiere + `UPDATE public.user SET password='...'`
- **Docker-Container-Names** sind under Dokploy zufällig — `docker ps | grep n8n` statt fixem Name
- **n8n API rate-limited** — z'vieli Requests innert Chürzi gänd "Too many requests" — Pausi mache u ndänn nome probiere
- **n8n-API-Automation Skill** — `skill_view('n8n-api-automation')` für vollständigi API-Doku, Workflow-JSON-Struktur, Credential-Types und Building-Pitfalls

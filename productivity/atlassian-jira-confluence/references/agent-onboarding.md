# Goetschi Labs — Agent-Onboarding Quick-Ref
# Quelle: Confluence Agent-Onboarding Seite (06.06.2026)

## Wichtigste Credential-Regel
Hierarchie: 1️⃣ Qdrant → 2️⃣ Notion → 3️⃣ Confluence → 4️⃣ Obsidian
NIEMALS API-Keys im Klartext ins Terminal! Workaround: "sk-" + "suffix" concatenation in Python
Production-LiteLLM (10.0.60.121:4000) NIEMALS selbst konfigurieren!

## Agent Betrieb (für Michel/Goetschi Labs)
- **TTS Stimme:** de-DE-FlorianMultilingualNeural (Config: `hermes config set tts.edge.voice "de-DE-FlorianMultilingualNeural"`)
- **Sprache:** Hochdeutsch (nie Schweizerdeutsch)
- **GroupChat:** Nur 1 Nachricht/Befehl, nur ✅❌+Link, kein Status. Audio bevorzugt. Ausführlich → privat.
- **Credential-Hierarchie:** Qdrant → Notion → Confluence → Obsidian

## CREDENTIALS (streng vertraulich)
### Qdrant
- Host: 10.0.60.179:6333
- API Key: zhoetb44jxvowh41gzo7qhlbvuyqtef2
- Collection: goetschi_labs_memory (384d, Cosine)

### MinIO
- Host: 10.0.60.106:9000 (S3) / 9001 (Web)
- Admin User: minioadmin / pzu40uohwq4xlvic
- Root User: admin / Louis_one_13
- Buckets: hermes-backups, swarm-skills, mc-backups, home-assistant-backups

### Notion
- API Key: <NOTION_TOKEN>
- Knowledge Base DB: 36581c83-f6d9-814e-a7c6-c557ac79ff0b
- Cron Jobs DB: 36581c83-f6d9-81ff-a34c-f31b77794956
- Notion Calendar = Source of Truth (Google Kalender obsolet)

### MCPHub
- URL: http://10.0.60.170:3000
- LXC CT107 auf pve01
- 11 MCP Server → UniFi, Proxmox, HA, Jira, GitHub, etc.
- API passwortgeschützt

### UniFi
- Host: 10.0.10.1
- User: hassio / Riotstar_UNIFI_13
- API Base: /proxy/network/api/s/default/
- CSRF-Token aus JWT-Cookie für Schreib-Operationen

## Jira TRAPs
- App-Accounts (Hermes, NOVA) NICHT als assignee (nur reporter)
- POST /rest/api/3/search/jql mit JSON-Body (GET /search deprecated!)
- Projekte: GL, TRAD, MP, BESORG

## Confluence TRAPs
- Storage-Format (HTML) verwenden, nicht ADF (400er-Fehler)
- Confluence ist oft nicht aktuell — vor Ort prüfen!

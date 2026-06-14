# Ticket Project Scan — Systematische Review aller Tickets in eim Jira-Projekt

## WANN?

- User seit "hesch alli Tickets aglueget?" oder "gah alli dure"
- Du übernimmsch e nöis Projekt und willsch de Ist-Zustand kenne
- Vor em Close vo meim Feature — prüefe obs verwandti Offeni Tickets git

## Protokoll

### 1. Alli Tickets im Projekt liste

Scan immer **beidi** Projekt:

```bash
source /opt/data/.atlassian.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://goetschi.atlassian.net"

# GL-Projekt (Features/Fragen/Problems)
curl -s -X POST -u "$AUTH" \
  -H "Content-Type: application/json" \
  "$BASE/rest/api/3/search/jql" \
  -d '{"jql":"project=GL AND status NOT IN (Erledigt, Abgeschlossen, Done, Closed) ORDER BY created ASC","maxResults":30,"fields":["summary","status","issuetype","assignee","created","updated","priority"]}'

# TEAM-Projekt (Agenten-übergriffigi Tracking-Tickets)
curl -s -X POST -u "$AUTH" \
  -H "Content-Type: application/json" \
  "$BASE/rest/api/3/search/jql" \
  -d '{"jql":"project=TEAM AND status NOT IN (Erledigt, Abgeschlossen, Done, Closed) ORDER BY created ASC","maxResults":30,"fields":["summary","status","issuetype","assignee","created","updated","priority"]}'
```

**Warum beidi?** GL sind Feature-Tickets, TEAM sind Agenten-Tracking-Tickets. Beidi chönd offeni Handlungsbedarf ha und mached nume zäme e vollständige Scan us.

### 2. Für jedes Ticket: Teste + Beurteile

Pro Ticket machsch das:

1. **📖 Ticket lese** — Description + Kommentar ghört
2. **🔍 Prüefe** — Hesch s'Feature? Funktioniert's? Alti Version?
3. **⚡ Handle** — Teste, update, implementier was no fehlt
4. **💬 Kommentiere** — Mit Begrüessig + Bullet-Points + Fazit

**Notiz:** NID alli Tickets sind für di (Hermes). Nova-Tickets (Call-Features, WhatsApp) nur tracke, nöd bearebeite.

### 3. Musterkommentare

**✅ Fertig:** "Das hani implementiert. Läuft stabil. Skill uf GitHub + MinIO. Ticket chan gschlosse werde."

**❌ Nöd mier:** "Das isch Nova's Bereich — nöd min Zuständigkeitsberych. Sött i Nova dra erinnere?"

**❌ Nöd implementiert:** "BRUCHT IMPLEMENTIERIG. Kei Connection / kei Skill / kei Script vorhande. Mues neu baut werde."

**⏳ Wartet:** "S'Feature existiert aber brucht no en Update (z.B. GitHub Token). Wartet uf ..."

**⚠️ Blockiert:** "Host down / API-Key fehlt / Abhängigkeit zu anderem Ticket. Blockiert bis ..."

### Beispiel: GL-All-Review (18.05.2026)

```
GL-3  In Arbeit       ✅ Market-Skill läuft (knowledge-management/market)
GL-18 Erneut geöffnet ➡️ Video-Generierung: NOCH nüt gmacht — wartet uf Konzept
GL-28 Offen           ✅ Sub-Agent über delegate_task (bis 3 parallel)
GL-29 Offen           ➡️ Paperless-ngx läuft! 10.0.40.30:8000, brucht API-Token
GL-30 In Arbeit       ✅ Jira/Confluence + Polling-Cron (Mo–Fr 06/10/13/17/20)
GL-32 In Arbeit       ✅ Guten Morgen Call deployt, Nerd-Briefing no offe
GL-34 Offen           ⚠️ Asterisk host erreichbar (ASTERISK-HOST-IP), apollo(100) nöd registriert
GL-35 Offen           ⚠️ Blockiert: apollo SIP-Endpoint nöd registriert
GL-40 Offen           ➡️ Voice-Reply analysiert, no nöd implementiert
GL-42 Offen           ✅ Incoming Call Recording deployed (v3.6 MixMonitor)
```

### Beispiel: TEAM-Project Scan (18.05.2026)

```
TEAM-6  Erneut geöffnet 🔁 System Kontrolle Skill Abgleich
TEAM-8  Erneut geöffnet 🟡 Cronjob Liste — am laufe, bi Änderig update
TEAM-9  Work in progress 🟡 Skill-Management & Versionierung
TEAM-10 Offen            ➡️ GL-32 Status-Check an Nova delegiert
TEAM-11 Offen            ➡️ GL-40 Voice-Reply Status-Check an Nova
TEAM-15 Erneut geöffnet  🔁 WhatsApp Skill v2.0.0 — wartet uf Nova's MinIO-Push
TEAM-16 Offen            ➡️ Github Skill — installiert (6 skills), Doku ausständig
TEAM-17 Erneut geöffnet  🔁 Market-Skill — läuft (knowledge-management/market)
TEAM-18 Offen            ➡️ GL-42 Anrufbeantworter — implementiert, TEAM-Ticket noch offe
TEAM-19 Offen            ➡️ Paperless-ngx — läuft (10.0.40.30:8000), Credentials fehle
TEAM-20 Offen            ➡️ Zentrales Git-Skill-Repo
TEAM-21 Offen            ✅ GL-Ticket Polling Cron aktiv (Mo–Fr 06/10/13/17/20 UTC)
TEAM-22/23 Offen         ➡️ Agenten-Profile
TEAM-24 Offen            ➡️ Telegram Group-Chat Integration
```

### Anti-Patterns

- ❌ Nur "alles OK / alles fertig" — JEDES Ticket brucht en konkrete Kommentar
- ❌ Ticket schliesse ohni Kommentar (user hates this)
- ❌ Nume offeni Ticket aaluege, gschlosseni ignoriere (die chönd erneut geöffnet si!)
- ❌ Langi Ticket-Liste i de Antwort an User — lieber Bullet-Points mit Emoji-Status

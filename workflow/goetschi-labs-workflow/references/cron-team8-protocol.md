# TEAM-8: Cron Job Update Protocol

## WANN?
Bi JEDEM erstelle/lösche/ändere von Cronjobs — sofort, automatisch, proaktiv.

## WAS?
Vollständigi Liste ALLER aktive Cronjobs uf TEAM-8 poste. Immer ALLI, nöd nume de gändereti!

## WIE?

### 1. Aktuelli Liste hole

```bash
cronjob action=list
```

Dänn die 6 Jobs i TEAM-8-Kommentar iisetze.

### 2. TEAM-8 Kommentar poste — aktuell gültigi Liste (Stand 17.05.2026)

```bash
source /opt/data/home/.hermes/.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"

curl -s -u "$AUTH" -X POST -H "Content-Type: application/json" \
  "$BASE/rest/api/3/issue/TEAM-8/comment" \
  -d '{"body":{"type":"doc","version":1,"content":[
    {"type":"paragraph","content":[{"type":"text","text":"HERMES: Cron-Liste Stand 17.05.2026","marks":[{"type":"strong"}]}]},
    {"type":"bulletList","content":[
      {"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"🔄 GitHub Skill-Sync — 04:00 UTC — no_agent — skill-sync.sh (git pull+push)"}]}]},
      {"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"🔍 GL-Ticket Polling — Mo–Fr 06/10/13/17/20 UTC — agent — offene Tickets prüfe + antworte"}]}]},
      {"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"📦 MinIO Backup — 03:00 UTC — no_agent — minio-backup.py"}]}]},
      {"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"🔄 Schwarm Skill-Sync — 02:00 UTC — no_agent — swarm-skills-sync.py"}]}]},
      {"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"💾 Qdrant Snapshot — So 03:00 UTC — no_agent — qdrant-backup.py"}]}]},
      {"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"📞 Asterisk Backup — 04:00 UTC — no_agent — asterisk-backup.py"}]}]}
    ]},
    {"type":"paragraph","content":[{"type":"text","text":"GitHub Sync und Asterisk Backup beide um 04:00 (kein Konflikt — no_agent Scripts, laufe sequenziell)."}]}
  ]}}'
```

### 3. UPDATE statt NEU (User-Correction 17.05.2026)

**Kei neue Kommentar wenn bereits en HERMES-Kommentar existiert — immer den bestehende UPDATE!** TEAM-8 sött möglichscht wenig Kommentar ha.

- `GET /rest/api/3/issue/TEAM-8/comment` → noch HERMES-Kommentar sueche (am body-Text)
- `PUT /rest/api/3/issue/TEAM-8/comment/{id}` → bestehende HERMES-Kommentar update
- `DELETE /rest/api/3/issue/TEAM-8/comment/{alti_id}` → altti HERMES-Kommentar lösche (nume 1 soll aktiv si)
- **Falls KEIN HERMES-Kommentar existiert** → `POST` en neue (das isch de erschti, oder es sind nume User-Kommentar det). User-Kommentar NIE lösche/überschribe.

**Vorteil:** Kei Spam, immer die einzig aktuelli Liste uf TEAM-8.

### 4. MERKMAL

Kei Memory-Duplikat — TEAM-8 isch verbindlich. S'Memory erinneret dich an d'Regle, nöd a d'Liste.

## Beispiel: Neje Cron hinzue — Vollständig

```bash
# 1. Cron erstelle
cronjob action=create name="Xyz-Check" schedule="0 6 * * *" no_agent=true script="xyz.sh"

# 2. Aktuelli Liste hole
CRONS=$(cronjob action=list)

# 3. TEAM-8 update — ALLI Crons inkl. Neue
#    → Siehe curl-Kommando Punkt 2, ergänzt um Xyz-Check
```

## Beispiel: GitHub Skill-Sync von stündlich auf täglich ändere (17.05.)

```bash
# 1. Cron update
cronjob action=update job_id=e48d1bf65b6d schedule="0 4 * * *"

# 2. TEAM-8 update — GitHub Skill-Sync jetzt "04:00 UTC (war stündlich)"
#    Restliche Crons unverändert, aber ALLI trotzdem aufführe
```

Im TEAM-8-Kommentar: Änderig markiere z.B. als:
- `🔄 GitHub Skill-Sync — 04:00 UTC (war stündlich) — no_agent`

## Aktuelli Cron-Liste

**TEAM-8 (Jira) isch verbindlichi Quelle.** Alli Änderige det dokumentiere, nöd hie.
Stand: 18.05.2026 — Total 10 aktivi Crons.

### Hermes Daily/Weekly Standup Calls (3 Stück, agent-gesteuert)

| Job | Schedule | Beschrieb |
|-----|----------|-----------|
| Hermes Tagesbeginn | Mo–Fr 05:00 UTC | Tagesplan + Learnings + Ideen → Call Michel |
| Hermes Tagesabschluss | Mo–Fr 18:00 UTC | Erledigt + Gelernt + Verbessert → Call Michel |
| Hermes Wochenrückblick | So 18:00 UTC | Weekly Review → Call Michel |

### System-Crons (6 Stück, no_agent)

| Job | Schedule | Script |
|-----|----------|--------|
| Schwarm Skill-Sync | tägl. 02:00 UTC | swarm-skills-sync.py |
| MinIO Backup | tägl. 03:00 UTC | minio-backup.py |
| Paperless Pipeline | tägl. 03:00 UTC | paperless-pipeline.py |
| GitHub Skill-Sync | tägl. 04:00 UTC | skill-sync.sh |
| Asterisk Backup | tägl. 04:00 UTC | asterisk-backup.py |
| Qdrant Snapshot | So 03:00 UTC | qdrant-backup.py |

### Agent-Crons (1 Stück)

| Job | Schedule | Beschrieb |
|-----|----------|-----------|
| GL-Ticket Polling | Mo–Fr 06/10/13/17/20 UTC | Offene Tickets prüfen + Neues melden |

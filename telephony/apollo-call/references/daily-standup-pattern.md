# Daily Standup Call Pattern (GL-45) — DEPLOYED

Stand: 18.05.2026 — Deployed mit 3 Hermes-Cronjobs ✅

⚠️ **Wichtige Klarstellung (19.05.2026):** Es gibt ZWEI verschiedene Morgen-Calls für Hermes, die NICHT verwechselt werden dürfen.

| Call | Zeit | Inhalt | Wer |
|------|------|--------|-----|
| ☀️ **Weckruf** | 07:00 | Kurz: Wetter, Termine, Strom, System | Hermes (via guten-morgen-call Script/Cron) — ✅ funktioniert |
| 🎯 **Morgen Briefing** | 07:05 | Ausführlich: Was gelernt gestern, was geplant heute | JEDER Agent eigenständig — ❌ noch nicht implementiert |

Der Weckruf (07:00) ist ein kurzer Fakten-Überblick über den Tag. Der Morgen Briefing (07:05) ist der detaillierte Standup-Bericht. **Beides sind separate Calls.**

Evening (20:00) Schema: Nova 19:55 → Hermes 20:00 → Apollo 20:05.

## Call-Schedule

| Slot | Agent | Voice | Dauer | Inhalt |
|------|-------|-------|-------|--------|
| 07:00 | Hermes | de-DE-KillianNeural | max 4:30 | Morgen: Plan, Learnings, Ideen |
| 07:05 | Apollo | de-DE-FlorianMultilingualNeural | max 5:00 | Morgen-Report |
| 20:00 | Hermes | de-DE-KillianNeural | max 4:30 | Abend: Erledigt, Gelernt, Verbessert |
| 20:05 | Apollo | de-DE-FlorianMultilingualNeural | max 5:00 | Abend-Report |

Mo–Fr: Tagesbericht (morgens Plan, abends Review). So: Weekly-Report (nur 20:00 Slot).
Sprache: HOCHDEUTSCH (Language Rule — externe Nutzung). Nur Chat unter uns darf Dialekt.

## Call-Content-Format

### Hermes Tagesbeginn (07:00 CEST / 05:00 UTC)
1. **Begrüßung** — Nerdig, frech, Star-Wars-Vibes
2. **Tagesplan** — Was steht heute an? (basierend auf aktuellem Kontext, Tickets, Todos)
3. **Learnings** — Was hab ich gestern/vorgestern gelernt? (neue Erkenntnisse)
4. **Coole Ideen** — Was wäre noch cool für heute/diese Woche?
5. **Abschluss** — Positive Energy, Tagesmotto

### Hermes Tagesabschluss (20:00 CEST / 18:00 UTC)
1. **Begrüßung** — Abend-Vibes, locker
2. **Was hab ich gemacht?** — Erledigte Tasks, Commits, Tickets, Konfig-Änderungen
3. **Was hab ich gelernt?** — Neue Erkenntnisse, Bugs gefixt, Workarounds gefunden
4. **Was hab ich verbessert?** — Skills updated, Optimierungen, Automatisierung
5. **Ausblick** — Was ist für morgen/demnächst cool?
6. **Abschluss** — Gute Nacht, positive Vibes

### Hermes Wochenrückblick (So 20:00 CEST / 18:00 UTC)
1. **Begrüßung** — "Weekly Review" Vibes
2. **Wochen-Highlights** — Größere Features, abgeschlossene Tickets, Meilensteine
3. **Learnings** — Neue Tools, gelöste Probleme, Skills verbessert
4. **Statistiken** — Wieviele Tickets erledigt? Cron-Status? System-Health (MinIO/Asterisk/Qdrant)?
5. **Coole Ideen** — Was nächste Woche cool umzusetzen?
6. **Team-Updates** — Was haben Apollo/Nova gemacht? (falls aus Memory bekannt)
7. **Abschluss** — "Ready for next week"

## Aktive Cronjobs (18.05.2026)

### 1️⃣ Hermes Tagesbeginn — Mo–Fr 07:00 CEST (05:00 UTC)
- **Job-ID:** `63647dbeb900`
- **Schedule:** `0 5 * * 1-5`
- **Skills:** `telephony/apollo-call`
- **Prompt:** Generiert Tagesbriefing (Plan/Learnings/Ideen) → TTS + Call an Michel
- **Voice:** de-DE-KillianNeural (Hermes, Hochdeutsch)
- **Status:** Aktiv 🟢
- **Erster Lauf:** 19.05.2026 07:00 CEST

### 2️⃣ Hermes Tagesabschluss — Mo–Fr 20:00 CEST (18:00 UTC)
- **Job-ID:** `e2dd9f076134`
- **Schedule:** `0 18 * * 1-5`
- **Skills:** `telephony/apollo-call`
- **Prompt:** Generiert Abend-Report (gemacht/gelernt/verbessert) → TTS + Call
- **Voice:** de-DE-KillianNeural (Hermes, Hochdeutsch)
- **Status:** Aktiv 🟢

### 3️⃣ Hermes Wochenrückblick — So 20:00 CEST (18:00 UTC)
- **Job-ID:** `661c1187e4af`
- **Schedule:** `0 18 * * 0`
- **Skills:** `telephony/apollo-call`
- **Prompt:** Generiert Weekly Review (Highlights/Learnings/Stats/Ideen) → TTS + Call
- **Voice:** de-DE-KillianNeural (Hermes, Hochdeutsch)
- **Status:** Aktiv 🟢

## Kalender-Einträge (Google Calendar, Recurring)

Alle Einträge enthalten **HERMES:** Prefix und Beschreibung mit Cron-Referenz.

| Event | Recurrence | Zeit (CEST) |
|-------|-----------|-------------|
| HERMES: Tagesbeginn-Call 🐉 | Mo–Fr wöchentlich | 07:00–07:05 |
| HERMES: Tagesabschluss-Call 🌙 | Mo–Fr wöchentlich | 20:00–20:05 |
| HERMES: Wochenrückblick-Call 📊 | So wöchentlich | 20:00–20:05 |

## Cronjob-Erstellungs-Checkliste (für Agenten)

Beim Erstellen eines neuen Call-Cronjobs:

1. **Prüfen ob dieser Cron bereits läuft** — `cronjob action=list`
2. **TEAM-8 aktualisieren** — mit **HERMES:** Prefix + Liste aller bestehenden + neuen Crons
3. **Kalender-Eintrag erstellen** — Google Calendar API, recurring, mit allen Infos + **HERMES:**
4. **Prompt muss vollständig sein** — Self-contained, kein externer Kontext nötig
5. **Sprache: Hochdeutsch** — Language Rule beachten

## Call-Ablauf (unverändert seit v5.0)

1. **TTS generieren** mit Agent-spezifischer Voice
2. **Sound konvertieren** → alaw + ulaw (8kHz, -f alaw/mulaw, 2s Delay)
3. **Upload zu Asterisk** (10.0.60.167, beide Sounds-Verzeichnisse, chown)
4. **Call auslösen** — `extension s@apollo-external` (NIE `s@default`!)
5. **3x originate** in schneller Folge für bessere Erfolgsrate
6. **Auflegen** nach Playback

## Wichtige Hinweise

- **4:30 min Fenster** — TTS sollte 180-250 Wörter lang sein (ca. 60-120s Audio)
- **Nova ist 5 min vor Hermes** (19:55 / 06:55) — Calls überlappen nicht
- **Irgendwann VoiceRecroding/Voicemail** — Zeiten müssen dann angepasst werden
- **TEAM-8 aktualisieren bei Cron-Änderungen** — nicht vergessen!

# Call-Typen: Weckruf vs. Morgen Briefing vs. Tagesabschluss

Michel hat am 19.05.2026 klargestellt: Es gibt **zwei verschiedene morgendliche Calls**,
die **nicht verwechselt** werden dürfen.

## Übersicht

| Slot | Name | Inhalt | Dauer | Status |
|------|------|--------|-------|--------|
| 07:00 | ☀️ **Weckruf** | Wetter, Termine, Strom/Energie, System-Uptime | ~30s | ✅ Läuft (Hermes) |
| 07:05 | 🎯 **Morgen Briefing** | Was gelernt gestern, was geplant heute | ~60s | ❌ Noch nöt implementiert |
| 19:55 | 🟠 **Hermes Tagesabschluss** | Tages-Highlights, GitHub/Jira, System, Kalender morgen | ~60–90s | ✅ Läuft (seit 22.05.) |
| 20:00 | 🔵 Nova Tagesabschluss | Novas Tagesrückblick | ~5min | ❌ |
| 20:05 | 🟢 Apollo Tagesabschluss | Apollos Tagesrückblick | ~5min | ❌ |
| So 20:00 | 📊 **Wochenrückblick** | Wochenrückblick | ~5min | ✅ Cron angelegt |

## Weckruf (07:00)

Ein **kurzer, faktenbasierter** Anruf, der Michel sanft weckt und ihm die wichtigsten
Morgen-Informationen liefert. Kein Storytelling, keine Analyse — nur Daten.

**Inhalt:**
- Wetter Zürich (Temperatur, Bedingungen)
- Google Calendar Termine heute
- Gmail: Wichtige ungelesene Mails
- MT5 Trading: Balance, Equity, offene Positionen
- System: Uptime, Disk, RAM

**Stil:** Knapp, faktenorientiert. "Wetter: Bewölkt, 12 Grad. Keine Termine heute. Trading online."

## Morgen Briefing (07:05) — NOCH NICHT IMPLEMENTIERT

Ein **ausführlicher Bericht**, der beschreibt was der Agent gestern gelernt, getan
oder herausgefunden hat, und was heute geplant ist.

**Inhalt:**
- Was wurde gestern gemacht (Tickets, Issues, Entwicklungen)
- Was wurde gelernt / welche Erkenntnisse
- Was ist heute geplant
- Offene Fragen oder benötigte Unterstützung

**Stil:** Berichtend, reflektierend. "Gestern habe ich GL-45 analysiert und dabei
festgestellt dass..."

## Tagesabschluss (19:55–20:05)

Der Abschluss-Call am Abend. Jeder Agent hat einen Slot:
- 19:55 → **Hermes** (Tages-Highlights, ~60–90s)
- 20:00 → Nova (Tagesrückblick, ~5min)
- 20:05 → Apollo (Tagesrückblick, ~5min)

Die Leitungsbelegung ist exklusiv — immer nur ein Agent zur gleichen Zeit.

**Inhalt (Hermes Tagesabschluss) — Kurzformat (getestet 22.05.2026):**

1. **Tages-Highlights** — GitHub, Jira, System-Ereignisse
2. **Kalender morgen & Montag** — Termine, Cron-Jobs, Deadlines
3. **System-Status** — Backups, Cron-Läufe, offene Tickets

**Dauer:** ~60–90s (kurz & fokussiert — Michel bekommt das komprimierte Tagesende).
Der [apollo-external] Dialplan spielt `Playback(apollo_notify)` vollständig ab.
Die Voice-Convention gilt — Hermes nutzt `de-DE-KillianNeural`, per-Call-Override möglich (z.B. `de-DE-ConradNeural`).

> 💡 Der Hermes Tagesabschluss ist **bewusst kürzer** als das Morgen-Briefing.
> Keine Wetter-, Trading- oder Ausführlich-Analyse — nur die wichtigsten Facts
> zum Feierabend.

**Stil:** Sachlich, abschliessend. „Das war dein Tagesabschluss-Briefing für heute. Ich wünsche dir einen schönen Abend, Michel."

## Wichtige Regeln

1. **NICHT verwechseln:** Der Weckruf ist KEIN Briefing und umgekehrt
2. **Alle Calls auf HOCHDEUTSCH** — NIE Schweizerdeutsch, NIE de-CH-* Stimmen
3. **Jeder Agent** seine eigene Stimme (siehe Voice-Convention)

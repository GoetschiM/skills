---
name: status-call
description: "Umfassender Status Call Skill — sammelt Daten von MT5 Trading Bots, Home Assistant, Tesla, Jira, Wetter, News und Home Lab und ruft Michel per TTS mit Soundeffekten an (3-4 Min)."
version: 1.3.1
updated: 2026-05-28
changes:
  - "Syntax-Fix: Fehlendes Komma nach `deepseek-v4-flash` im Script gefixt"
  - "Modell `deepseek-v4-flash` → `deepseek-v4-flash` wäge API-Key-Restriktion"
  - "Pitfall-Sektion ergänzt: Modell-Konfiguration, Jira-Projekt leer, News-Fallback"
  - "Reference: session-2026-05-26-model-fix.md"
tags: [status, call, briefing, tts, trading, home-assistant, tesla, jira]
triggers:
  - "status call"
  - "statusbericht"
  - "Mach mir en Status Call"
  - "Briefing"
  - "mach Status"
---

# Status Call Skill — Kompletter Live-Report per TTS-Anruf 📞

## Auslöser
- Michel sagt: **"Mach mir en Status Call"** oder **"Gibt mir mal en Status Call"**
- Cron: Kann als Cron-Job für regelmässige Briefings konfiguriert werden

## Funktionsweise

Wenn getriggert, führt Hermes folgende Schritte aus:

### 1. Datensammlung (parallele Queries)
- **MT5 Trading Bots** — Status, PNL, Win Rate, Drawdown, offene Positionen
- **Home Assistant** — Stromproduktion (Solar), PV-Status, Hausverbrauch
- **Tesla** — Kilometerstand, Batteriestatus (via HA)
- **Jira** — Heute geschlossene Tickets, offene Tickets
- **Wetter** — Aktuelle Temperatur, Vorhersage
- **Weltnachrichten** — Top 3 Nachrichten
- **Home Lab / Goetschi Lab** — Server-Status, Uptime

### 2. Narrative Generierung (LLM-basiert — dynamisch!)
- Das Script sammelt alle Rohdaten und übergibt sie als JSON an den **LiteLLM** (via lokalen API-Call)
- Ein LLM (deepseek-v4-flash) generiert **jedes Mal einen FRISCHEN, NATÜRLICHEN Text**
- **Kein Template mehr!** Der LLM entscheidet dynamisch über:
  - Reihenfolge der Themen (mal Wetter zuerst, mal Trading)
  - Detailtiefe (mal kurz, mal ausführlich)
  - Tonfall (locker, sachlich, begeistert — je nach Situation)
  - Formulierungen — nie die gleichen Sätze wie beim letzten Mal
- **Keine Roboter-Erklärungen** — Drawdown, SOC und Margin-Level werden nicht jedes Mal erklärt
- **Keine Rubriken** — keine "--- BEGINN ... ---" oder "--- ENDE ---" Marker
- **Natürliche Sprache** — wie ein Kollege der kurz anruft
- Geschrieben in **Hochdeutsch** (für TTS)
- **Keine Soundeffekte** ❌
- **Textlänge:** max. 2500 Zeichen (ca. 3 Minuten)
### 3. TTS-Anruf
- POST an `http://10.0.60.156:5002/call` mit `voice: "hermes"` (→ de-DE-ConradNeural, Michels Preference)
- **Geschwindigkeit:** Standard (1.2x via edge-tts)
- **NUR Hochdeutsch! Kein Schweizerdeutsch!**
- **Keine Soundeffekte mehr** (vom User abgelehnt)
- **Call-API v1.1** mit Call-Lock gegen parallele Anrufe

## Datenquellen

| Quelle | Endpunkt | Auth |
|--------|----------|------|
| MT5 Bot04 (LIVE) | `http://10.0.60.104:8080/api/status` | JWT: michel/Louis_one_13 |
| MT5 Bot01 (TEST) | `http://10.0.60.101:8080/api/status` | JWT: michel/Louis_one_13 |
| Home Assistant | `http://10.0.60.111:8123/api/states` | Bearer Token (via Nova SSH) |
| Jira | `rest/api/3/search/jql` | Basic Auth (ENV) |
| Wetter | Open-Meteo API (kostenlos, kein Key) | — |
| Hermes Call API | `http://10.0.60.156:5002/call` | — |

## Skript

Das Hauptskript liegt unter `scripts/status-call.py` und führt alle Schritte aus:

```bash
cd ~/.hermes/skills/telephony/status-call
python3 scripts/status-call.py
```

### Output-Modi
- `--dry-run`: Nur Text generieren, keinen Anruf tätigen
- `--only-data`: Nur Daten sammeln, keinen Text/Narrativ generieren
- `--speed 1.15`: TTS-Geschwindigkeit (Default: 1.15 = 115%)

### Datenfluss
```
status-call.py
  ├── collect_mt5() → dict(bot04, bot01)
  ├── collect_ha() → dict(solar, pv, power, tesla)
  ├── collect_jira() → dict(closed_today, open_count)
  ├── collect_weather() → dict(temp, condition, forecast)
  ├── collect_news() → list(top_3_headlines)
  ├── generate_narrative(data) → str(text)
  └── make_call(text) → POST /call
```

## TTS-Parameter
- Voice: `hermes` → de-DE-ConradNeural (Michels Preference)
- **Geschwindigkeit:** edge-tts Standard (~1.0x) — der `speed`-Parameter wird von der Call API derzeit ignoriert (Einbau serverseitig nötig)
- **Sprache:** NUR Hochdeutsch! Niemals Schweizerdeutsch!
  - Falsch: "isch", "hörsch", "bisch", "bi", "chli", "nöd"
  - Richtig: "ist", "hörst", "bist", "bin", "ein wenig", "nicht"
- **Soundeffekte:** ❌ Gestrichen (User: 'scheiße auf die Soundeffekte')
- **Zwei-Wege-Audio:** ❌ Vom User explizit verboten
- **Max Länge:** ~3000 Zeichen (3 Minuten bei ~150 Wörtern/min)

## Referenzen
- `references/test-call-20260523.md` — Test-Protokoll des ersten Echt-Anrufs (21:58, 23.05.2026)
- `references/llm-narrative-architecture.md` — Architektur der LLM-basierten Narrativ-Generierung (ab v1.2.0)

## Installation & Setup

### Voraussetzungen
- Hermes Call API läuft (`http://10.0.60.156:5002/health`)
- Jira Credentials in `.env` (`ATLASSIAN_EMAIL`, `ATLASSIAN_TOKEN`)
- Home Assistant Token via Nova SSH
- MT5 Bots erreichbar

### Test
```bash
# Dry-Run (kein Anruf)
python3 scripts/status-call.py --dry-run

# Echter Anruf
python3 scripts/status-call.py
```

## Pitfalls
- **MT5 Bot01 (TEST)** zeigt "online" obwohl MT5 disconnected (mt5_status=0). Script prüft jetzt `mt5_status == 0` → korrekter Offline-Status.
- **Tesla-Modus** wird über Entity-Namen-Suche gefunden (`modus`/`mode` im Namen). Falls kein passender Eintrag, zeigt das Script "?".
- **HA Token** liegt auf Nova → SSH nötig (Louis_one_13). Script nutzt subprocess SSH für Extraktion.
- **Jira Token** muss in `/opt/data/home/.hermes/.env` als `ATLASSIAN_TOKEN` oder `JIRA_TOKEN` gespeichert sein. Ohne Token → Jira-Sektion wird übersprungen (kein Fehler).
- **Jira .env ohne `export`** — Python-Script sieht die Token nicht via `os.environ`. Script nutzt `set -a` im Bash-Subprocess für korrekte Extraktion.
- **TTS-Text** muss Hochdeutsch, nie Dialekt.
- **Textlänge** max ~3000 Zeichen (3-4 Min). Text darüber wird trotzdem gesendet, aber die Call-Dauer steigt.
- **Kein Emoji** im Subject bei Jira-Updates (SMTPUTF8).
- **LLM-Modell-Konfiguration:** Das Script nutzt `deepseek-v4-flash` für's LLM-Narrativ. Falls de API-Key nur uf bestimmti Modell beschränkt isch, muess de Wert i `generate_narrative()` i de Script-Konstante `"model"` aapasst werde. Lüüt vo 401-Fehler i de Konsol lönd druf schlüsse, dass Modell nid erlaubt isch.
- **Jira GL-Projekt leer:** S'Goetschi-Lab-Jira-Projekt het 0 Issues (Stand Mai 2026). D'Jira-Sektion im Narrativ chunnt drum immer mit 0 gschlossnige/offene Tickets zrück. Falls wider Tickets da sind, funktioniert d'Query normal.
- **News-API-Fallback:** `newsapi.org` mit `apiKey=demo` schlägt oft fehl. Fallback uf `tagesschau.de/api2u/news/` lauft stabil.

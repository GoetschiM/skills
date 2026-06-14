# Multi-Channel Delivery: Telegram Text + Audio + Phone Call

Stand: 13.06.2026 — Erster Live-Test mit GitHub Awesome Reporter

## Use Case

Nach dem Verarbeiten eines YouTube-Videos (Transkript → Zusammenfassung)
soll das Ergebnis mehrkanalig ausgeliefert werden:

1. **Telegram Text** — Zusammenfassung zum Lesen
2. **Telegram Audio** — TTS-generiertes MP3 zum später Abhören (Fallback falls Anruf verpasst)
3. **Telefonanruf** — TTS-Ansage live auf Michels Handy

## Workflow

```
1. Transkript holen (youtube-transcript-api / fetch_transcript.py)
2. LLM analysiert & fasst zusammen
3. TTS generieren (edge-tts) → /tmp/summary.mp3
4. MEDIA:-Marker für Telegram-Audio in Antwort einfügen
5. Telefonanruf via Nova Call API tätigen
6. Text-Zusammenfassung + Audio im Chat ausliefern
```

## Dependencies

```bash
# Bereits installiert:
pip install --break-system-packages youtube-transcript-api edge-tts requests
```

## TTS generieren

```bash
edge-tts --voice de-DE-ConradNeural --text "Hochdeutscher Text..." --write-media /tmp/summary.mp3
```

**WICHTIG:** Nur Hochdeutsch im TTS-Text! Kein Schwiizerdütsch.
Die TTS-Stimme wird auf Hochdeutsch trainiert — Dialekt tönt unnatürlich.

## Telegram Audio ausliefern

In der Antwort `MEDIA:/tmp/summary.mp3` einfügen. Das System erkennt
das MEDIA:-Prefix und sendet die Datei als native Audio-Nachricht.

```python
# Der Pfad muss existieren und ein MP3 sein
MEDIA_PATH = "/tmp/summary.mp3"
```

## Telefonanruf tätigen

Via Nova Call API (10.0.60.60:5050/call), getestet 13.06.2026 ✅:

```bash
curl -X POST http://10.0.60.60:5050/call \
  -H "Content-Type: application/json" \
  -d '{
    "number": "0796459743",
    "message": "Hochdeutsche Zusammenfassung...",
    "playback_file": "nova_welcome"
  }'
```

Response bei Erfolg:
```json
{"status":"call_initiated","phone":"0796459743","call_file":"nova_api_call_....call","timestamp":"..."}
```

**Parameter:** Der Endpoint erwartet `"message"` (nicht `"text"`) und `"playback_file"`.

## Timing & Reihenfolge

Empfohlene Reihenfolge:
1. **TTS generieren** (dauert ~5s für kurze Texte)
2. **Anruf initiieren** (Call wird in Hintergrund gestellt)
3. **Telegram ausliefern** (Text + MEDIA:) — User sieht alles sofort
4. **Fertig** ✅ — Anruf kommt parallel an, Audio liegt im Chat

## Pitfalls

| Problem | Lösung |
|---------|--------|
| TTS zu lang für Call | Zusammenfassung auf 3-5 Sätze kürzen für Phone; ausführlicher Text nur im Chat |
| Call API timeout | Call ist async — POST gibt sofort `call_initiated` zurück, kein Wait nötig |
| MEDIA: wird nicht gesendet | Pfad muss absolut sein und existieren; MP3 muss valide sein |
| TTS klingt roboterhaft | Text in kurze Sätze aufteilen, natürliche Pausen einbauen |
| Video hat 35+ Projekte | Nicht alle auflisten — Top 5-6 Highlights reichen für den Call |

## Voice Convention

| Delivery-Kanal | Voice | Hinweis |
|---------------|-------|---------|
| Telegram Audio | `de-DE-ConradNeural` | edge-tts, gleicher Text wie Call |
| Telefonanruf | via Nova API | TTS wird serverseitig generiert |

Immer `de-DE-ConradNeural` (mit **C**!). `de-DE-KonradNeural` (mit K)
existiert nicht — führt zu edge-tts Fehler.

## Beispiel (Live-Test 13.06.2026)

**Video:** Hacker News Show #8 (TFRXkUECTcM) — 35 Open-Source-Projekte
**Call-Status:** ✅ Call initiated erfolgreich
**Audio:** 323KB MP3, Telegram zugestellt
**Skill:** `github-awesome-reporter` mit Trigger `!ga`

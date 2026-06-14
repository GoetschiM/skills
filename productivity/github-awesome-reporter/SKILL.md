---
name: github-awesome-reporter
description: >
  Trigger-Wort "!ga" / "!github-awesome": Holt das neueste Video von GitHub
  Awesome (@GithubAwesome), extrahiert Transkript, identifiziert das vorgestellte
  GitHub-Repository, fasst es zusammen, und liefert parallel per Telegram (Text +
  Audio) + Telefonanruf aus.
tags: [youtube, github, summary, call, tts, telegram]
---

# GitHub Awesome Reporter 🚀

## Trigger

- **`!ga`** — Schnell: News vom GitHub Awesome YouTube-Kanal holen
- **`!github-awesome`** — Alternative

## Was passiert

```
1. Neuestes Video vom @GithubAwesome Kanal abrufen
2. Transkript extrahieren
3. LLM analysiert: Welches GitHub-Repo wird vorgestellt? Was kann es?
4. Zusammenfassung generieren (Kernfeatures, Use-Cases, Link)
5. Parallel ausliefern:
   a) Telegram-Chat: Text-Zusammenfassung
   b) Telefonanruf: TTS-Audio-Zusammenfassung (via Nova Call API)
   c) Telegram-Audio: Als MP3/Audio-Fallback (zum später Abhören)
```

## Abhängigkeiten

```bash
pip install --break-system-packages youtube-transcript-api edge-tts requests
```

Bereits installiert ✅: `youtube-transcript-api`, `edge-tts`, `requests`

## Neuestes Video finden

Der Kanal ist `@GithubAwesome`. Die Channel-ID lässt sich via yt-dlp oder
YouTube oEmbed API ermitteln. Alternativ RSS-Feed:

```bash
# Channel-Videos via oEmbed (kein API-Key nötig)
curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/@GithubAwesome&format=json"

# Neueste Videos via yt-dlp (Video-IDs)
yt-dlp --print id,title,upload_date "https://www.youtube.com/@GithubAwesome" 2>/dev/null

# Wenn yt-dlp ohne JS-Runtime hängt: Invidious-Instanz versuchen
curl -s "https://inv.vern.cc/api/v1/channels/UC_GITHUBAWESOME_ID/videos?sort=newest"
```

## Transkript extrahieren

```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
segments = api.fetch(video_id, languages=['de', 'en'])
transcript = " ".join(seg.text for seg in segments)
```

## Zusammenfassung generieren

Das Transkript + der LLM-Kontext identifizieren:
- Repository-Name + URL (`https://github.com/author/repo`)
- Hauptfunktion / Use-Case
- Technologie-Stack (Sprache, Framework)
- Warum es trending ist (falls ersichtlich)
- 3-5 Sätze Zusammenfassung

## Parallel-Auslieferung

### a) Telegram Text
Einfach die Zusammenfassung in die Antwort schreiben.

### b) Telefonanruf
Via Nova Call API (10.0.60.60:5050/call):

```python
import requests
requests.post("http://10.0.60.60:5050/call",
    json={
        "number": "0796459743",
        "message": "Hochdeutsche Zusammenfassung...",
        "playback_file": "nova_welcome"
    }, timeout=30)
```

**WICHTIG:** Nur Hochdeutsch im TTS-Text! Kein Schwiizerdütsch.
TTS-Stimme: `de-DE-ConradNeural`

### c) Telegram Audio
Via edge-tts generieren, MP3 speichern, als MEDIA:-Pfad ausliefern:

```bash
edge-tts --voice de-DE-ConradNeural --text "Hochdeutscher Text..." --write-media /tmp/ga_summary.mp3
```

Dann in der Antwort `MEDIA:/tmp/ga_summary.mp3` einfügen.

## Voice-Konvention

| Rolle | Voice | Sprache |
|-------|-------|---------|
| Hermes (Default) | `de-DE-ConradNeural` | Hochdeutsch, männlich |
| Anruf | via Nova API (10.0.60.60:5050) | Nur Hochdeutsch! |

## Workflow (vollständig)
## Workflow (vollständig)

1. **Neuestes Video finden**
   - `yt-dlp --print id,title,upload_date "https://www.youtube.com/@GithubAwesome" 2>/dev/null | head -1`
   - Falls kein yt-dlp: Manuell Channel-Seite scrapen (siehe channel-metadata reference)

2. **Transkript holen**
   - `python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; ..."`

3. **Repository identifizieren**
   - LLM analysiert Transkript → Repo-URL + Beschreibung

4. **Zusammenfassung schreiben**
   - Kurz (3-5 Sätze), Fokus auf: Was macht das Repo? Für wen? Link

5. **Telegram senden**
   - Zusammenfassung als Text
   - MEDIA:/tmp/ga_summary.mp3

6. **Anruf tätigen**
   - POST http://10.0.60.60:5050/call
   - JSON: `{"message": "Hochdeutscher Text...", "number": "0796459743", "playback_file": "nova_welcome"}`
   - Parameter-Name ist **`message`**, nicht `text`!
   - TTS wird serverseitig auf CT117 via edge-tts generiert (im venv /opt/nova-call-api/venv/)
   - Falls edge-tts fehlt: via Proxmox Host (10.0.60.10, root/Riotstar_PROXMOX_13) → `pct enter 117` → `pip install edge-tts --break-system-packages`
   - Falls TTS trotzdem fehlschlägt: `systemctl restart nova-call-api` auf CT117

7. **Fertig** ✅

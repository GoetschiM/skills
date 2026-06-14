---
name: hermes-call-api
description: "REST API for outgoing calls — any agent can call Michel via TTS + Asterisk"
category: telephony
version: 1.1.0
tags: [call, phone, asterisk, tts, notification, outgoing]
---

# Hermes Call API — Agent Call Skill 📞

❗ **VOICE MIGRATION 07.06.2026 — ALLE ALTE ENDPUNKTE SIND TOT!**
Alti Hosts: ~~10.0.60.156:5002~~ (tot), ~~10.0.60.167~~ (tot).
**Neuer Host: Nova Call API unter http://10.0.60.60:5050/call**
Siehe `apollo-call` Skill für de aktuelle Weg.

**⚠️ PARAMETER CHANGE (Nova API, getestet 09.06.2026):** Die neue Nova Call API (10.0.60.60:5050) erwartet `"message"` statt `"text"` als Feldname. `"text"` git en 400-Fehler ("Field required"). 
- **Alt (Hermes API, EOL):** `{"text": "...", "number": "...", "voice": "..."}`
- **Neu (Nova API):** `{"message": "...", "number": "...", "playback_file": "nova_welcome"}

D'Beispiel unten sind für de **alte, tote** Endpoint — nur als Referenz.

A REST API on **Hermes (10.0.60.156:5002)** — ⚠️ **END OF LIFE!** Siehe Migration oben.

## Endpoints

### POST /call — Make a call
```bash
curl -X POST http://10.0.60.156:5002/call \
  -H "Content-Type: application/json" \
  -d '{"text": "Hallo Michel, hier ist ...", "voice": "hermes"}'
```

### GET /health — Status
```bash
curl http://10.0.60.156:5002/health
```

### GET /voices — Available voices
```bash
curl http://10.0.60.156:5002/voices
```

### GET /history — Call history
```bash
curl http://10.0.60.156:5002/history
```

## Voice Convention (CRITICAL)
| Agent | Voice | Style |
|-------|-------|-------|
| Hermes | de-DE-ConradNeural (C!) | Male, warm, Hochdeutsch — Michels Favorit |
| Apollo | de-DE-FlorianMultilingualNeural | Male, Hochdeutsch |
| Nova | de-DE-SeraphinaMultilingualNeural | Female, Hochdeutsch |
| Fallback | de-DE-KillianNeural | Male, Hochdeutsch |

**ALL calls MUST be Hochdeutsch. NEVER de-CH voices!**
**⚠️ AUCH Test-Texte müssen Hochdeutsch sein!** Kein "isch", "hörsch", "bisch", "bi", "nöd" — immer "ist", "hörst", "bist", "bin", "nicht". Die TTS-Stimme wird auf Hochdeutsch trainiert; Schweizer Text tönt unnatürlich und führt zu massiver Frustration beim User.

💡 **Schreibfalle:** edge-tts verwendet `de-DE-ConradNeural` (mit **C**), nicht `de-DE-KonradNeural` (mit K). Bei Tippfehler schlägt TTS fehl (non-zero exit status 1).

## Parameters
- `text` (required): TTS message in Hochdeutsch
- `voice` (optional): hermes/apollo/nova/conrad (default: hermes)
- `number` (optional): Swiss format (default: 0796459743)
- `retries` (optional): Default 3

### Known parameter gaps (v1.0.0 — 23.05.2026)
- **`speed`** — parameter is accepted but silently **ignored**. The TTS engine always renders at default speed (~1.0x). For custom speed, pre-process the audio server-side or re-generate with speed injected into the TTS provider call.
- **`sfx` / sound effects** — NOT supported. There is no SFX pipeline. Any SFX (portal-gun, sci-fi, beep) must be pre-mixed into the audio file before the TTS generator call, or added via a post-processing step on the generated WAV.
- **`format`** — output is always μ-law WAV for Asterisk. No format switching available.

## For Agent Devs (Python)
```python
import requests
resp = requests.post("http://10.0.60.156:5002/call",
    json={"text": "Dein Text hier", "voice": "nova"}, timeout=30)
```
Check health first:
```python
r = requests.get("http://10.0.60.156:5002/health", timeout=5)
if r.json()["status"] == "ok": ...
```

## System
- Service: `hermes-call-api.service`
- Logs: `journalctl -u hermes-call-api -n 50`
- Restart: `systemctl restart hermes-call-api`
- Source: `/opt/call-api/hermes-call-api.py`
- Host: 10.0.60.156 (Apollo) Port 5002

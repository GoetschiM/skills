---
name: text-to-speech
description: "TTS-Audio-Generierung für Nachrichten — ElevenLabs (primär) / Piper (Fallback). User-Preferences: NUR männlich, 1.15x Speed, Hochdeutsch, SFX."
version: 1.2.0
tags: [tts, audio, elevenlabs, piper, german, voice]
---

# Text-to-Speech (TTS)

Generiert Sprach-Audio für Nachrichten via **ElevenLabs** (Premium-Cloud-TTS) oder **Piper** (lokal, Fallback). Dient als Begleit-Audio für längeri Textnachrichte.

## ⚠️ Provider-Update (09.06.2026)
TTS wurde von **Piper** auf **ElevenLabs** umgestellt. ElevenLabs ist jetzt der primäre Provider. Piper bleibt als Fallback erhalten.

## ElevenLabs-Konfiguration

**Voice ID:** `5KvpaGteYkNayiswuX2h`
**Model:** `eleven_multilingual_v2` (mehrsprachig, unterstützt Deutsch)
**API Key:** in `/root/.hermes/.env` (oder `hermes config set tts.elevenlabs.api_key "sk_..."`)

**Config (via `hermes config set` gesetzt):**
```yaml
tts:
  provider: elevenlabs
  elevenlabs:
    api_key: sk_...           # in config gespeichert
    voice_id: 5KvpaGteYkNayiswuX2h
    model_id: eleven_multilingual_v2
```

**Wichtig:** Bei einem Gateway-Neustart wird der neue Provider aktiv. Der `text_to_speech` Tool im Gateway läd die Config nur beim Gate-Start — falls der Tool noch Piper verwendet, den Gateway neustarten (`systemctl restart hermes-gateway` oder per `hermes gateway restart`).

## CRITICAL: User-Preferences (NIE vergesse!)

### ⚠️ Agent-spezifisch — NIE global setze!
Die TTS-Estellige gälted NUR für Hermes, NID für Nova oder anderi Agent!
Keini globali Config-Setzige vorneh. Was i däm Skill stoht, isch Hermes-spezifisch.
Wenn Nova sini eigene TTS-Estellige brucht, macht Nova das selber — mir überschriibe nüt!

Die folgende Regle sind ABSOLUT und gälted für ALLI Hermes-TTS-Nutzige:

| Regel | Wert | Begründig |
|-------|------|-----------|
| **Stimm** | `5KvpaGteYkNayiswuX2h` (ElevenLabs, männlich) ElevenLabs-Stimme | User hät sich mehrmols beschwert über Frauestimme |
| **NIEMALS** Frauestimm | gTTS / Edge Default / irgendöppis mit female | User: "nie eine Frau und Stimme" |
| **Sprach** | NUR Hochdeutsch | NIE Schwiizerdütsch |
| **Gschwindigkeit** | 1.15x | User: "x15 prozent schneller" |
| **SFX** | Am Afang + am Endi (sofern verfügbar) | Soundeffekt zum I/Usblende |
| **Wänn Audio?** | Bi allne **längere Nachrichte** (3+ Sätz / strukturiert) | User will underwegs zuelose |

## Setup (einmalig)

ElevenLabs isch via `hermes config set` konfiguriert. **Kein manueller Konfigurationseingriff nötig.**

### Config überprüfen

```bash
hermes config get tts.provider                    # sollte "elevenlabs" zeigen
hermes config get tts.elevenlabs.voice_id         # sollte "5KvpaGteYkNayiswuX2h" zeigen
hermes config get tts.elevenlabs.model_id         # sollte "eleven_multilingual_v2" zeigen
hermes config get tts.elevenlabs.api_key          # sollte den API Key zeigen
```

### Piper (Fallback, weiterhin verfügbar)
Piper mit Thorsten-Model isch installiert uf Apollo (10.0.60.156):

```bash
# Model location
/usr/local/share/piper-voices/de_DE-thorsten-medium.onnx (63 MB)
/usr/local/share/piper-voices/de_DE-thorsten-medium.onnx.json
```

Helper-Script `/usr/local/bin/piper_tts.py`:
```python
Usage: python3 piper_tts.py "Text" /output/path.mp3
```

**Hinweis:** De built-in `text_to_speech` Tool vom Hermes Gateway läd d Config nume bim Gateway-Start. Wenn de TTS-Tool no d alti Piper-Stimm brucht, muess de Gateway neigstartet werde.

## Tool: text_to_speech

De Hermes-Gateway het en integrierte `text_to_speech` Tool. Wenn'er nid funktioniert (z.B. "No TTS provider available"), lueg:

1. Isch `provider: elevenlabs` i de Config gsetzt? (`hermes config get tts.provider`)
2. Falls nid: `hermes config set tts.provider elevenlabs`
3. Gateway-Neustart falls nötig (beachte: User mag kein Restart für MCPs, aber für TTS ist OK)
4. Fallback: immer manuell via Piper + MEDIA (`python3 /usr/local/bin/piper_tts.py "Text" /tmp/audio.mp3`)

## Workflow: Audio bi langer Nachricht

1. Text verfasse (Hochdeutsch, männlich adressiert)
2. Prüfe: isch d Nachricht länger als 2-3 Sätz?
3. Wenn ja: TTS generiere
   - Priorität: `text_to_speech` Tool (ElevenLabs, falls verfügbar)
   - Fallback: `python3 /usr/local/bin/piper_tts.py "{{TEXT}}" /tmp/tts_output.mp3`
4. MEDIA-Pfad i d Antwort ihbinde: `MEDIA:/tmp/tts_output.mp3`
5. Vor dem sende: no einisch prüefe obs en Frauestimm isch (NIE!)

## Config-Bug (28.05.2026 GEFIXT)

Es het en **zweite `piper:`-Eintrag** i de Config geh (Zeile 253-254: `voice: en_US-lessac-medium` — Frauestimm!). In YAML gwinnt de letzt Block — d.h. de Thorsten isch überschriebe worde und d Frauestimm `en_US-lessac-medium` ohni speed isch verwändet worde.

**Fix:** Zweite piper-Block glöscht. Jetzt isch nume no eine det:
```yaml
tts:
  provider: elevenlabs
  elevenlabs:
    voice_id: 5KvpaGteYkNayiswuX2h
    model_id: eleven_multilingual_v2
    api_key: sk_...
```

**Prüef-Steps falls Problem widerkchunnt:**
1. `grep -n "provider:" ~/.hermes/config.yaml | head -5` — NUR 1x `provider: elevenlabs`
2. `grep -A3 "elevenlabs:" ~/.hermes/config.yaml` — muess `voice_id: 5KvpaGteYkNayiswuX2h` zeige

## Verification Script

E fertigs Verify-Skript prüeft d Config uf alli bekannte Problem:

```bash
bash /root/.hermes/skills/productivity/text-to-speech/scripts/verify_tts_config.sh
```

Lauft **vor jedem TTS-Einsatz** wenn du d Config gänderet hesch oder en Frauestimm vermuetisch.

## References

| Pfad | Inhalt |
|------|--------|
| `scripts/verify_tts_config.sh` | Verifikations-Skript für TTS-Config (prüft ElevenLabs) |
| `scripts/piper_tts.py` | Piper TTS Helper (manuelli Generierig, Fallback) |
| `references/yaml-duplicate-key-pitfall.md` | YAML Duplicate-Key Bug: Erkennig + Prävention (allgemein, nid nume TTS) |

## Known Working Config

`/root/.hermes/config.yaml`:
```yaml
tts:
  provider: elevenlabs
  elevenlabs:
    api_key: sk_fb5...              # gesetzt via hermes config set
    voice_id: 5KvpaGteYkNayiswuX2h
    model_id: eleven_multilingual_v2
```

## Trigger Conditions

- User schickt en längeri Nachricht / Voi
- User erwartet en Antwort wo TTS brucht (vorgängigi Konversation)
- User bittet um en Zämmefassig / Report
- Automatisch bi allne Health-Check / Status-Meldige wo länger sind

## Pitfalls

### gTTS ist VERBOTEN
gTTS (Google TTS) git für Dütsch NUR e Frauestimm. NIE bruuche! Au nid als "schnelli Alternative" — User hät sich explizit und mehrmols beschwert.

### Edge-TTS isch blockiert
De Microsoft Edge TTS-Dienst (`speech.platform.bing.com`) isch vo däm Netzwerk us blockiert. `edge-tts` CLI schlaht immer feh mit "No audio was received". Nid probiere — zuverlässiger isch Piper (Fallback) oder ElevenLabs (primär).

### Stimme-Check VOR em Sende
Bevor e TTS-Datei gschickt wird, PRÜEFE:
- Isches e Männerstimm (ElevenLabs Voice ID `5KvpaGteYkNayiswuX2h`)?
- Falls nid: nid schicke, Alternative finde
- Falls ElevenLabs-API mal down: auf Piper Fallback wechseln (mit `hermes config set tts.provider piper`)

### ElevenLabs API Key Exposure
Der API Key wird in der Config im Klartext gespeichert. Niemals in Chat/Antworten ausgeben! `hermes config get tts.elevenlabs.api_key` zeigt ihn an — nicht in User-Antworten kopieren.

### Memory isch nid gnueg
D TTS-Präferenz isch au im Memory (USER.md) gspicheret, ABER es het scho mehrmols Failures geh — d Skill werd glade BEVOR de User d Nachricht list. D Skill isch d primär Quelle für die Regle, Memory isch nume Backup.

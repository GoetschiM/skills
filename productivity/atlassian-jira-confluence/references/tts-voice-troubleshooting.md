# TTS Voice Configuration Troubleshooting
## (For Michel / Goetschi Labs — de-DE-FlorianMultilingualNeural)

### The Problem (recurring)
When asked to speak, the agent calls `text_to_speech()` but gets the **wrong voice**
(e.g. female instead of male, wrong language). The user corrects it, the agent
calls `text_to_speech()` again with the same wrong voice.

### Root Cause
The `text_to_speech` tool **respects `tts.edge.voice` from `config.yaml`** —
it does NOT have a voice parameter. Calling `text_to_speech()` repeatedly
without fixing the config produces the same voice every time.

### The Fix
```bash
# 1. Check current setting
grep "voice" ~/.hermes/config.yaml

# 2. Set correctly (permanent)
hermes config set tts.edge.voice "de-DE-FlorianMultilingualNeural"

# 3. Verify in config.yaml (must be under `tts.edge.voice:`, not somewhere else)
```

### Common Mistakes
- **Mistake:** Calling `text_to_speech()` repeatedly, hoping the voice changes.
  The tool has no voice parameter — it always reads from config.
- **Mistake:** Only checking whether edge-tts is installed, not what voice
  the config is set to.
- **Mistake:** Remembering to set config in memory ("Michel wants Florian")
  but not actually running `hermes config set`.

### Verification
After fixing config, call `text_to_speech()` once with a short test phrase.
If correct, the fix is permanent — no need to repeat each session.

### Available German Male Voices (Edge TTS)
- `de-DE-FlorianMultilingualNeural` — empfohlen, natürlich
- `de-DE-KillianNeural` — aktuell gesetzt
- `de-DE-ConradNeural` — Alternative
- `de-AT-JonasNeural` — Österreichisch
- `de-CH-JanNeural` — Schweizer Akzent
- `de-DE-AmalaNeural` (female — avoid)
- `de-DE-SeraphinaMultilingualNeural` (female — avoid, was default)
- `de-DE-KatjaNeural` (female — avoid)

### Piper TTS (lokal, offline)

Piper ist vorinstalliert (Teil von Hermes). Bietet **komplett lokale TTS** — kein Internet, kein API Key.

**Setup einer deutschen Stimme (Thorsten):**

```bash
# 1. Modell runterladen und Config
mkdir -p /root/.local/share/piper/voices/de_DE/thorsten/medium
cd /tmp
curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx" -o thorsten.onnx
curl -sL "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json" -o thorsten.onnx.json
mv thorsten.onnx.json thorsten.onnx.json  # Name muss .onnx.json enden!
cp /tmp/thorsten* /root/.local/share/piper/voices/de_DE/thorsten/medium/
```

**Konfiguration in Hermes:**
```bash
hermes config set tts.provider piper
hermes config set tts.piper.voice de_DE-thorsten-medium
```

**Verfügbare deutsche Piper Modelle:**
- `thorsten` (männlich, medium quality) ✅ empfohlen
- `thorsten_emotional` (männlich, emotionaler — klingt natürlicher)
- `karlsson` (männlich)
- `eva_k` (weiblich)
- `kerstin` (weiblich)
- `ramona` (weiblich)
- `mls` (gemischt)
- `pavoque` (gemischt)

**Pitfall:** Config muss mit `hermes config set` geändert werden, nicht per `patch` auf config.yaml (wird durch security-Guard blockt).

**Pitfall:** `de-DE-RalfNeural` existiert NICHT in der Edge-TTS Liste. Nicht verwechseln mit Piper Thorsten.

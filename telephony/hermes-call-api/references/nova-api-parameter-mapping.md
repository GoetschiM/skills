# Parameter-Mapping: Hermes API → Nova API (09.06.2026)

Die alte Hermes Call API (10.0.60.156:5002, EOL) und die neue Nova Call API (10.0.60.60:5050)
haben **unterschiedliche Parameter-Namen**.

## Mapping

| Zweck | Alt (Hermes, tot) | Neu (Nova, 10.0.60.60:5050) |
|-------|-------------------|------------------------------|
| TTS-Text | `text` | **`message`** |
| Zielnummer | `number` | `number` |
| Stimme | `voice` (Wert: "hermes"/"apollo"/etc.) | `playback_file` (Wert: "nova_welcome") |
| Retries | `retries` | nöd unterstützt |

## Beispiel-Request (Nova API, funktionierend)

```json
{
  "message": "Hallo Martin, das ist ein Test.",
  "number": "0797507151",
  "playback_file": "nova_welcome"
}
```

## Bekannti Fehler (09.06.2026)

- **`"text"` verwende** → 400: `{"detail":[{"type":"missing","loc":["body","message"],"msg":"Field required"}]}`
- **edge-tts fählt uf CT117** → API nimmt Request a, aber TTS schlaht fähl: `{"detail":"TTS-Generierung fehlgeschlagen (edge-tts auf CT117 installiert?)"}`
- Der Call wird in dem Fall *trotzdem* initiiert (Asterisk ruft d'Nummer a), aber es wird nüt vorgspielt → User hört Stille

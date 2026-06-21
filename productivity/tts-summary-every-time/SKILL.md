---
name: tts-summary-every-time
description: "Pflicht: Am Ende jeder längeren Antwort ein TTS-Audio generieren und als MEDIA: anhängen. Keine Ausnahme. Der User erwartet das standardmässig, nicht als Angebot."
---

# TTS-Summary am Ende jeder Antwort

## Trigger
Immer wenn die Antwort länger als 3-4 Sätze ist oder ein komplexes Thema behandelt (MCPHub-Status, Infrastruktur, Zusammenfassungen, Reparaturanleitungen, etc.).

## Pflicht-Schritte
1. **text_to_speech(text, output_path)** aufrufen mit einer knackigen Zusammenfassung
   - Max 200 Wörter
   - Deutsch (wie der User spricht)
   - Freundlicher, informativer Ton
   - "Grüessli" oder ähnlich als Abschluss
2. **MEDIA:/pfad/zur/ogg** in der Antwort anhängen
3. **Zuletzt (nach MEDIA):** nochmal gedanklich checken ob Audio wirklich angehängt wurde

## Wichtige Details
- **Edge TTS** = Standard-Provider (kein API-Key nötig)
- Output Format: `.ogg` (Telegram native voice)
- Stimme: vom User konfiguriert (aktuell de-DE-SeraphinaMultilingualNeural — weiblich, User wünscht männlich)
- Nicht fragen "Soll ich TTS machen?" — einfach machen
- Bei Fehlschlag: sag's dem User, aber lös das Problem (anderen Provider versuchen)

## Beispiel-Struktur für TTS-Text
"Hallo Michel, hier die Zusammenfassung: [2-3 Kernpunkte]. [Was wurde gemacht]. [Was ist noch offen/next steps]. Grüssli!"

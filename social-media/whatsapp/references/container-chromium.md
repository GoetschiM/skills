# Chromium im Docker-Container (Dokploy)

## Gefundener Chromium-Pfad (14.05.2026)

```
/opt/data/home/.cache/puppeteer/chrome/linux-148.0.7778.97/chrome-linux64/chrome
```

**Pruefung:**
```bash
ls -la ~/.cache/puppeteer/chrome/*/chrome-linux64/chrome
```

## Benoetigte Shared Libraries

Chromium im Container braucht diese libs:
```bash
ldd /opt/data/home/.cache/puppeteer/chrome/linux-148.0.7778.97/chrome-linux64/chrome | grep "not found"
```

Auf Debian 13 (trixie) sind alle libs vorhanden.

## Puppeteer Args fuer Container

MANDATORY fuer jeden whatsapp-web.js Client im Container:
```js
puppeteer: {
    executablePath: '<path-from-above>',
    headless: true,
    args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--single-process'
    ]
}
```

Ohne `--no-sandbox` startet Chromium nicht. Ohne `--single-process` gibts Speicherprobleme.

## Fehlerbehebung

### "Navigating frame was detached"
- **Ursache:** whatsapp-web.js nutzt eigene puppeteer-core Version (24.38.0), die nach Chromium im falschen Path sucht.
- **Loesung:** Immer `executablePath` explizit setzen!

### "Failed to launch the browser process"
- **Ursache:** Chromium fehlen Shared Libraries oder `--no-sandbox` fehlt.
- **Pruefung:** `ldd` ausfuehren, sandbox-flag checken.

### Chromium findet sich nicht
- **Loesung:** `npx puppeteer browsers list` ausfuehren oder manuell `~/.cache/puppeteer/chrome/*/` durchsuchen.
- Der Cache-Pfad enthaelt die Chromium-Version im Namen (z.B. `linux-148.0.7778.97`).

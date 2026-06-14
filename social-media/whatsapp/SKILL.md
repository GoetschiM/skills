---
name: whatsapp
category: social-media
description: "WhatsApp-Integration für Apollo — Zwei-Wege: Nachrichten lesen, senden, überwachen via Michels WhatsApp-Account. Primär whatsapp-web.js + Chromium, Fallback Baileys v7."
---

# WhatsApp Skill

Verbinde Apollo mit Michels persoenlichem WhatsApp-Konto (`+41796459743`).

## Status ✅ (14.05.2026)

**whatsapp-web.js + Chromium** laeuft stabil unter pm2.
- Session: `/opt/data/home/.wa-wweb-session/` (LocalAuth)
- Script: `/opt/data/skills/social-media/whatsapp/scripts/wa-wweb.js`
- PM2: `whatsapp` (PID 6115, uptime 55s, 86MB)
- Health: `/tmp/.wa-health` (30s Heartbeat)
- Auth: `/tmp/.wa-authenticated`

## Setup (einmalig)

```bash
cd /opt/data/home
npm install whatsapp-web.js qrcode
# Chromium ist automatisch via puppeteer da
```

## Login (nur bei Erstverbindung)

```bash
# Alte Session loeschen (nur wenn Neu-Registrierung)
rm -rf /opt/data/home/.wa-wweb-session /tmp/.wa-authenticated

# Via pm2 starten
cd /opt/data/home && npx pm2 start /opt/data/skills/social-media/whatsapp/scripts/wa-wweb.js --name whatsapp

# QR ist unter /tmp/wa-qr.png -> ALS MEDIA-BILD an Michel senden!
# Michel scannt: WhatsApp -> Einstellungen -> Verknuepfte Geraete -> Geraet verknuepfen
```

**Wichtig:** QR-Code immer als MEDIA-Bild senden, niemals als ASCII!

## Dauerbetrieb (pm2)

```bash
# Status
cd /opt/data/home && npx pm2 status

# Logs
cd /opt/data/home && npx pm2 logs whatsapp --lines 20

# Neustart
cd /opt/data/home && npx pm2 restart whatsapp

# Stop
cd /opt/data/home && npx pm2 stop whatsapp

# Nach Aenderungen am Script
cd /opt/data/home && npx pm2 restart whatsapp

# pm2 dump speichern (nach jeder Aenderung)
cd /opt/data/home && npx pm2 save
```

**Auto-Restart:** pm2 startet automatisch bei Container-Neustart via `pm2 save` + `pm2 resurrect`.

## Scripts & Templates

- `scripts/wa-wweb.js` — Haupt-Script: WhatsApp-Client mit Chromium
  - Session wird automatisch aus `/opt/data/home/.wa-wweb-session/` wiederhergestellt
  - Bei Verbindungsabbruch: 5s warten, dann exit(1) -> pm2 restart
  - Health-Heartbeat alle 30s nach `/tmp/.wa-health`
- `scripts/wa-simple.js` — Fallback: Baileys Minimal-Login (deprecated)
- `templates/ecosystem.config.js` — PM2-Ecosystem-Konfiguration
  - Start: `cd /opt/data/home && npx pm2 start /opt/data/skills/social-media/whatsapp/templates/ecosystem.config.js`
  - Setzt NODE_PATH automatisch auf `/opt/data/home/node_modules`

## Wichtige Config-Parameter

```js
puppeteer: {
    executablePath: '/opt/data/home/.cache/puppeteer/chrome/<version>/chrome-linux64/chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process']
}
```

**WhatsApp-Web-Version fixieren** (wichtig für Stabilität):
```js
webVersionCache: {
    type: 'remote',
    remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html'
}
```
Ohne Cache-Crash bei WA-Web-Update. Diese Version (2.2412.54) wurde getestet (14.05.2026).

**Chromium-Path auto-detektiert** im Script via `fs.readdirSync()` auf `~/.cache/puppeteer/`

## Troubleshooting

### 💥 MODULE_NOT_FOUND trotz installiertem Modul

Wenn pm2 `Error: Cannot find module 'whatsapp-web.js'` zeigt, aber `ls node_modules/whatsapp-web.js` bestätigt, dass es existiert:

**Ursache:** pm2 startet ohne `NODE_PATH`, findet das Modul nicht direkt.

**Fix — Ecosystem Config verwenden (setzt NODE_PATH korrekt):**
```bash
cd /opt/data/home && npx pm2 delete whatsapp
cd /opt/data/home && npx pm2 start \
  /opt/data/skills/social-media/whatsapp/templates/ecosystem.config.js --only whatsapp
npx pm2 save
```

Das ecosystem.config.js setzt `NODE_PATH: '/opt/data/home/node_modules'`. Danach läuft WhatsApp wieder.

**Prüfung (vorher/nachher):**
```bash
# Vor Fix: pm2 zeigt MODULE_NOT_FOUND
# Nach Fix: pm2 status zeigt "online"
# Health: cat /tmp/.wa-health (nach 30s da)
# Auth: cat /tmp/.wa-authenticated (nach QR-Scan da)
```

### Session Recovery nach QR-Neuscan

Wenn pm2 online ist aber `/tmp/.wa-authenticated` fehlt → Michel muss QR scannen:
1. `/tmp/wa-qr.png` prüfen (wird vom Script generiert)
2. Als MEDIA-Bild an Michel senden
3. Er scannt: WhatsApp → Einstellungen → Verknüpfte Geräte → Gerät verknüpfen

## Pitfalls

- **Niemals Session-Verzeichnis ohne Grund loeschen** — Session ist wertvoll! Nur bei Neu-Registrierung.
- **Chromium-Path nicht hardcoden** — haengt von Puppeteer-Version ab. Check: `ls ~/.cache/puppeteer/chrome/*/chrome-linux64/chrome`
- **whatsapp-web.js braucht `--no-sandbox`** im Container. Ohne startet Chromium nicht.
- **Qr immer als MEDIA-Bild senden** — ASCII-QR im Terminal bringt nichts.
- **pm2 NODE_PATH** setzen: `NODE_PATH=/opt/data/home/node_modules` im ecosystem.config.js
- **Nach pm2 save immer pm2 resurrect testen** — dump.pm2 muss gueltigen Pfad haben.

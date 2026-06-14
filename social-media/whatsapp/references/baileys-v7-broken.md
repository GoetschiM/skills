# Baileys v7.0.0-rc11 API-Einschraenkungen

Stand: 14.05.2026, Container Hermes auf Dokploy.

## Ueberblick

Baileys v7 verbindet sich erfolgreich (QR-Login, connection.update), aber die Chat-Listing API ist **broken**. Zusaetzlich: WhatsApp verweigerte mehrfach die Verknuepfung trotz gueltigem QR.

## Was funktioniert

- QR-Login als PNG via qrcode.toFile()
- Verbindung (connection.update -> connection: 'open')
- messages.upsert Event (eingehende Nachrichten)
- Session persistieren via useMultiFileAuthState()

## Was NICHT funktioniert

- sock.chats -> undefined (kein Store mehr in v7)
- chats.set Event -> wird nie gefeuert
- chats.upsert Event -> wird nie gefeuert
- makeInMemoryStore() -> not a function (aus core entfernt)
- Browsers-Export -> nicht definiert
- Login-Verweigerung -> WhatsApp akzeptiert den QR nicht (mehrere Versuche, frischer Session jedes Mal)

## Workaround fuer Chat-Listing

Braucht separates Store-Package (gibt es noch nicht auf npm).

## Prioritaet

**whatsapp-web.js + Chromium bevorzugen** - hat volle Chat-API, kein Broken-Channel-Problem.

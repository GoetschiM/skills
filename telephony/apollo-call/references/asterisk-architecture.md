# Asterisk Architecture (10.0.60.167)

## Channel Drivers / Endpoints

| Endpoint | Type | Extension | Status | Auth |
|----------|------|-----------|--------|------|
| `PJSIP/apollo` | PJSIP | 100 | offline | `100` / `HenrySipPass13!` |
| `PJSIP/101` | PJSIP | 101 | offline | `101` / `Louis_one_13!` |
| `PJSIP/salt-trunk` | PJSIP | — | online | Salt.ch Trunk |

- **Endpoint 100** = Apollo (Nova/Apollo-Hermes shared): Context `[from-internal]`
- **Endpoint 101** = Michel: Context `[from-internal]`
- **salt-trunk** = Externer SIP-Trunk zu sipvoice.salt.ch: Context `[from-salt-inbound]`

## Sound Formats

Asterisk Playback benötigt zwingend **alaw (.alaw)** oder **ulaw (.ulaw)**.
WAV funktioniert NICHT direkt via Playback.

Sound-Datei-Namen sind fest codiert im Dialplan: `apollo_notify`
→ Jeder Anruf überschreibt `apollo_notify.alaw` + `apollo_notify.ulaw` + `.wav`

## ARI (Asterisk REST Interface)

- **Port:** 8088 (localhost only, kein externes Binding)
- **User:** `henryari` / `DEIN_STARKES_AMI_PASSWORT`
- **REST API:** `http://localhost:8088/ari/`
- **WebSocket:** `ws://localhost:8088/ari/events?app=...` (Stasis)
- ARI benötigt eine aktive Stasis-App (WebSocket) für `channels.create` — sonst wird der Channel sofort geräumt
- Ohne App: **ARI allein nicht nutzbar für Calls** (Nova hat eine solche App)

## Dialplan Contexts

### [apollo-out]
Outbound Notification Calls. Erwartet Swiss-Format (079...):
```
exten => _.,1,Dial(PJSIP/salt-trunk/sip:+41${EXTEN:1}@sipvoice.salt.ch,120)
```
→ Stripped die erste Ziffer, ersetzt mit +41.
→ Salt Trunk liefert oft NO ANSWER (siehe Troubleshooting)

### [apollo-external] — Post-Answer Context (EMPFEHLUNG für Hermes)
Wird nach erfolgreichem Answer via `extension s@apollo-external` aktiviert.
Playback läuft **vollständig ab** (kein Timeout während Playback), dann folgt eine 60s-Wartezeit vor Hangup:
```
exten => s,1,Answer()
 same => n,Playback(apollo_notify)
 same => n,Wait(60)
 same => n,Hangup()
```
→ **Playback-Order:** Playback → Wait(60) → Hangup. Die 60s-Pause kommt NACH der Ansage.
→ TTS-Dauer ist nicht begrenzt durch die Wait-Zeit — auch 2:18+ lange Ansagen (wie beim Tagesabschluss-Briefing) werden vollständig abgespielt.
→ Die 60s sind eine Wartezeit für Michel, falls er etwas notieren möchte, bevor der Kanal geschlossen wird.

### [nova-local] — Post-Answer Context (Alternative für Nova)
```
exten => s,1,Answer()
 same => n,Wait(1)
 same => n,Playback(apollo_notify)
 same => n,Hangup()
```
→ Wartet nur 1s nach Answer, dann Playback, dann sofort Hangup.
→ KEINE 60s Wartezeit — für kurze Benachrichtigungen geeignet.

### [from-internal]
Test / Internal extensions:
```
exten => apollo,1,Answer()
 same => n,Playback(apollo_notify)
 same => n,Hangup()
```

### [from-salt-inbound]
Eingehende Anrufe vom Salt-Trunk → Playback(apollo_notify) → Hangup.

### [default]
Fallback → Playback(demo-congrats) → Hangup.
**⚠️ NIE `extension s@default` für Post-Answer verwenden!** Spielt `demo-congrats` statt `apollo_notify`.

## SIP-Trunk (Salt)

- **Registriert:** ✅ (`pjsip show registrations` → Registered)
- **Kontakt:** Avail, 6ms RTT
- **DNS:** `sipvoice.salt.ch` → 213.55.128.83 / 213.55.128.211
- **Rufnummer:** `+413****7977` (ausgehende CLI)
- **Auth:** `+413****7977` / `RiotstarSIPCALL13`

**Bekanntes Problem:** Der Salt-Trunk ist registered + online, aber ausgehende Calls kommen nicht an
(CDR zeigt konsistent NO ANSWER). Grund unbekannt — möglicherweise Carrier-Routing-Problem.

## SSH

```bash
ssh root@10.0.60.167  # Pass: Louis_one_13
```

Nützliche CLI-Befehle:
```bash
asterisk -rx 'pjsip show endpoints'
asterisk -rx 'pjsip show registrations'
asterisk -rx 'pjsip show contacts'
asterisk -rx 'core show channels'
asterisk -rx 'core show channels verbose'
tail -20 /var/log/asterisk/cdr-csv/Master.csv   # Call Detail Records
cat /etc/asterisk/extensions.conf                # Dialplan
cat /etc/asterisk/pjsip.conf                     # SIP-Konfiguration
cat /etc/asterisk/ari.conf                       # ARI-Konfiguration
```

# Salt-Trunk Retry-Pattern — Erfahrungswerte

## Problem
Salt-Trunk (PJSIP/salt-trunk auf sipvoice.salt.ch) liefert beim ersten `channel originate` oft NO ANSWER innerhalb von 0 Sekunden. Der Trunk IST registered und online, DNS funktioniert — aber der Call kommt nicht durch.

## Lösung
**3 parallele originate-Versuche in schneller Folge** (0.5s Abstand):

```python
for i in range(3):
    client.exec_command(
        "asterisk -rx 'channel originate Local/0796459743@apollo-out extension s@default'"
    )
    time.sleep(0.5)
```

## Warum?
Erfahrungsgemäss klappt der 2. oder 3. Versuch, während der 1. oft direkt NO ANSWER returned. Vermutlich SIP-Timing-Problem beim Salt-Trunk (SIP-Proxy braucht "Aufwärmrunde").

## Getestet
- 17.05.2026: 3 Versuche → 1x connect, Michel hat "Hammer höre ich" gsait ✅
- Vorher: Einzelversuche → ausnahmslos NO ANSWER (CDR zeigt 0s Dauer)

## Rufnummernformat
**Zwingend Swiss-Format:** `0796459743`
(NICHT `+41796459743` — der apollo-out Dialplan macht `+41${EXTEN:1}`)

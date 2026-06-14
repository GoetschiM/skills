# Teichpumpe Session 23.05.2026 — Komplett-Sanierung

## Kontext
Michels Pumpe het ständig ON/OFF zyklieret. User immer frustrierter ("Da stimmt was nicht", "immer das Gleiche"). Drei kritische Sessions.

## Root Causes

### 1. Falsche Switch-Referenz in A3
A3 het `switch.teich_pumpe` (mit Underscore) referenziert statt `switch.teichpumpe` (ohni).
- `switch.teich_pumpe` = existiert nid → A3 cha nüt schalte
- `switch.teichpumpe` = korrekte Shelly-Switch (via Shelly HTTP/CoIoT)
- **Fix:** A3-Variable umgstellt + A3 stüüret jetz direkt `switch.teichpumpe`

## Finale Architektur (nach Cron-Bridge-Einführung)
```
A3 → switch.teichpumpe (Soll-Zuestand direkt gschribbe) → Cron-Bridge (1min) → Shelly HTTP
```

- A3 steuert **`switch.teichpumpe`** direkt — immer verfüegbar, nie unavailable
- Cron-Bridge liist switch.teichpumpe + Shelly-Relay → synct bi Abwiichig
- **`input_boolean.teichpumpe_soll` existiert DOCH in HA** — isch `off` — aber isch nöd mit em Shelly verbunde. A3 stüüret jetz direkt `switch.teichpumpe`
- Cron-Job-Protokoll: wenn switch.teichpumpe ≠ Shelly-Relay → Shelly via POST Form-Data schalte + HA-State aktualisiere

### 4. Kei Min ON-Time
A3 het `min_on_time` nid definiert gha → Pump sofort usgschaltet nach ihschalte
- **Fix:** `min_on_time: 39` in A3-Variable + alli "Turn OFF"-Branches checke `pump_on_since > min_on_time`

### 5. Kaputts Notify
`notify.mobile_app_samsung_michel` existiert nüme (Handy ersetzt worde?)
- **Fix:** Uf `notify.sm_s25_ultra` gänderet

## Lösig (final) — siehe SKILL.md für aktuelle Architektur
```
A3 → switch.teichpumpe (Soll-Zuestand) → Cron-Bridge (1min) → Shelly HTTP
```
- A3 steuert **switch.teichpumpe** (nie unavailable)
- Cron-Bridge synct minütlich mit Shelly-HTTP-API
- HA-State wird via Cron-Bridge aktualisiert (POST /api/states/switch.teichpumpe)

## Überspring des Final Fixes
1. Cron-Bridge erstellt (`cronjob create teichpumpe-bridge`)
2. A3 uf direkti `switch.teichpumpe`-Steuerig umgstellt (statt `teich_pumpe`)
3. `min_on_time = 39` in A3-Variable
4. Fehlendi Sensore nöi erstellt
5. Notify-Name korrigiert
6. Alles in Qdrant gspycheret

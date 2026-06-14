# Teichpumpe Automation System

Last updated: 25.05.2026 00:10 (Session: PC-Adaption automation created, cron bridge deleted)

## 0. Current State (25.05.)

| Entity | Wert | Bewertung |
|--------|------|-----------|
| switch.teichpumpe (real) | OFF | 18:48 UTC (02:00 CH) |
| automation.teichpumpe_pv_optimierung_v2_3_003 (A3) | ON | ⭐ Alleiniger Controller — direkt an switch.teichpumpe |
| automation.teichpumpe_switch_bridge | ON | **⚠️ Überschrieben!** Enthält jetzt **"Teichpumpe PC-Adaption"** (s.u.) |
| automation.teich_darf_nur_3_30_stunden_laufen (A1) | OFF | Deaktiviert |
| automation.teich_pumpe_einschalten_solar_soc_optimiert (A2) | OFF | Deaktiviert |
| automation.teich_abend_tagesbilanz (A4) | ON | Harmlos, Reporting |
| input_boolean.eigenverbrauchsoptimierung_aktiv | ON | ✅ KRITISCH — muss ON si |
| input_boolean.teichpumpe_rush_mode | OFF | Override |
| input_number.min_daily_run | 240 (180 wenn PC ON 14-21h) | ✅ Dynamisch via PC-Adaption |
| input_number.soc_schwelle_fur_verlangerung | 84 | ✅ |

### Neue Automation: Teichpumpe PC-Adaption (25.05.)

**Entity:** `automation.teichpumpe_switch_bridge` (HA slug so generiert — der Name im UI is "Teichpumpe PC-Adaption")
**Config ID:** `new`
**Status:** ✅ ON

**Logik:**
- **Trigger:** `switch.strom_prox03` state change + Timer um 14:00
- **Condition:** Nur 14:00–21:00 Uhr aktiv
- **PC ON:** → `input_number.min_daily_run` = **180** (3h Grundlauf)
- **PC OFF:** → `input_number.min_daily_run` = **240** (4h Grundlauf)
- A3 verlängert immerno bis 6h wenn SOC ≥ 84% + PV-Überschuss
- Der 14:00-Timer stellt sicher, dass auch PC der schon am Morgen läuft, adaptiert wird

**Warum:** PC + TV am Abend = höherer Hausverbrauch → Batterie wird stärker entladen. Pump kürzer laufen lassen = mehr Batterie-Reserve für den Abend. Batterie sollte ideal um 18:00 bei ~100% sein.

### Cron-Bridge (d2b55a0e2f2a): GELÖSCHT (25.05.)

Der Cron-Bridge-Job (alle 60s) wurde gelöscht. A3 steuert switch.teichpumpe direkt via HA-native Shelly-Integration. Die PC-Adaption-Automation übernimmt die dynamische Runtime-Anpassung.

**Konsequenz:** Kein externer Bridge-Prozess mehr nötig. HA + A3 regeln alles nativ.

## 1. System Architecture

Solar (2 strings je ~220W)
  -> Ecoflow PowerStream
    -> Ecoflow DeltaMax Battery (SOC optimiert via PC-Adaption)
      -> Jelly/Grid-Meter -> Grid (zielt auf 0)
        -> Teichpumpe 177W via switch.teichpumpe (Shelly PM)

KEY: Jelly/Grid-Meter hält Netzbezug auf 0. Überschuss -> Batterie.

## 2. The evcc Problem (RESOLVED)

evcc misst Grid-Export-Surplus. Ecoflow+Jelly halten Grid auf 0.
-> evcc sieht nie Surplus.
-> **evcc aus Pumpen-Loop entfernt.** `select.evcc_teich_pumpe_mode = off`

## 3. A3 Variables & Dynamic Runtime

A3 liest `input_number.min_daily_run` als **runtime_goal**:
```yaml
"runtime_goal": "{{ states('input_number.min_daily_run')|float(240) }}",
```

Dynamik:
- **Default:** 240 Min (4h)
- **PC ON 14-21h:** 180 Min (3h) — via PC-Adaption Automation
- **A3 Extend-Logik:** +15 Min Schritte via `input_number.extend_step` bis max 360 Min (6h), nur bei SOC ≥ 84% + PV-Überschuss ≥ 1 kWh

### Alle Bugs & Fixes (23.05.)

Siehe vorherige Session-Doku für Bug 1–9. Kurzfassung:
- Bug 1-4: Fehlende Sensoren via POST /api/states erstellt
- Bug 5: `input_boolean.eigenverbrauchsoptimierung_aktiv` war OFF
- Bug 6: Entity name mismatch (switch.teich_pumpe → switch.teichpumpe)
- Bug 7: `notify_target` blockierte gesamte Automation
- Bug 8: ON/OFF-Cycling durch fehlenden pv_uberschuss Sensor
- Bug 9: min_on_time=39 eingeführt (Anti-Cycling)

## 4. Michel's Requirements (23.05. + 25.05.)

| Bedingung | Min | Max | PC-Adaption |
|-----------|-----|-----|-------------|
| Schlechtes Wetter | 3h | - | 180 Min wenn PC ON |
| Gutes Wetter + SOC ≥ 84% | - | 6h | A3 Extend |
| PC läuft (14-21h) | 3h | ~5h | min_daily_run=180 |
| PC läuft nicht (14-21h) | 4h | 6h | min_daily_run=240 |
| Batterie-Priorität am Abend | SOC ≥ 32% | - | Stoppt Pumpe |

## 5. Quick Fix (Fish Emergency)

```bash
# Rush Mode aktivieren (überbrückt ALLE Limits)
curl -s -X POST "$HOMEASSISTANT_HOST/api/services/input_boolean/turn_on" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "input_boolean.teichpumpe_rush_mode"}'
```

## 6. Related

- **GL-73**: System-Überholung — alle Änderungen dokumentiert
- **Qdrant**: search "teichpumpe automation soc cutoff"
- **Skill**: `skill_view(name='teichpumpe-bridge')` für Bridge-Referenz
- **Skill**: `skill_view(name='home-assistant')` für API-Referenz

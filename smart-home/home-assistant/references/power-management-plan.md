# Power Management Plan — Michel's Home (Kriegstetten)

> Status: **DEPLOYED** ✅ (21.05.2026) — `automation.strommodus_optimiert_v2_0` isch am Laufen
> Nächst: Wenn Michel neui Wünsch het, patches an däre Automation vorneh.

## Problem

Michel has multiple **Strom (power) switches** throughout the house. When he leaves home, the presence sensor sets HA to **Abwesen** (away) mode. When he returns, the mode switches back to **Normal** — and **all Strom switches turn on**, even appliances that don't need power (TV, sofa lamps, dishwasher, washing machine, printer, bedroom, etc.). This wastes electricity.

## Goal

1. When Michel leaves home → switch off non-essential Strom switches
2. When Michel returns → do NOT auto-switch them on (let him decide)
3. Exceptions: certain circuits must stay on always

## Entities (actual IDs, verified 20.05.2026)

| Michel's Name | Entity ID | Aktuell | Soll bei Abwesenheit |
|---|---|---|---|
| **Stromwohnzimmer** | `switch.zw_strom_wohnzimmer` | off | OFF (schon richtig) |
| **Stromwohnzimmer-TV** | `switch.zw_strom_wohnzimmer_tv` | on | OFF |
| **Stromwohnzimmer-Sofa** | `switch.zw_strom_wohnzimmer_sofa` | on | OFF |
| **Stromschlafzimmer** | `switch.zw_strom_schlafzimmer` | on | OFF nur wenn Tesla NICHT ladet! |
| **Strombüro** | `switch.zw_strom_buro` | on | < 50W sofort OFF, ≥ 50W 60min Timer, BEI Heimkehr nüt auto aa |
| **Stromküche** | `switch.zw_strom_kuche` | on | **Immer ON** (Kühlschrank, Grundlast) |
| **Stromküche-Ecke** | `switch.zw_strom_kuche_ecke` | on | OFF |
| **Strom-ESbereich/Esszimmer** | `switch.strom_esszimmer` | off | **Nie OFF** (Staubsauger-Akku-Ladestation!) |
| **Strom Geschirrspülmaschine** | `switch.zw_strom_geschirrspulmaschine` | on | OFF |
| **Strom Tesla** | `switch.zw_strom_tesla` | on | Separates Lademanagement (nicht hier) |
| **Strom Prox03** | `switch.strom_prox03` | off | Darf off bleibe

### Additional devices that can stay OFF when away
- Drucker (printer)
- Waschmaschine (washing machine)
- Geschirrspüler (dishwasher)
- Alle nicht-aktiven Küchengeräte

## Suspected Automation Issue

Michel mentioned the house has an **Abwesen** (away) mode. The hypothesis is:
- Presence automation: `person.michel_goetschi` changes to `not_home`
- This triggers a scene/mode change
- The mode change has unintended side-effects: it powers up ALL Strom switches instead of leaving them OFF
- On return: mode flips back and switches power ON again

**Fix approach:** The current mode-based automation likely uses a "restore" or "on" action. Need to:
1. Find the existing presence/absence automation(s) in HA
2. Change what gets turned on/off — only turn OFF non-essential switches on absence, do NOT turn them back on on arrival
3. Create a separate manual action (button/script/scene) for "I'm home, power up everything"

## Automation Architecture (discovered 20.05.2026)

### Status Chain
```
person.michel_goetschi (home/not_home)
  -> input_select.michel_status (anwesend/abwesend/ankommend/bettfertig/schlaeft/im urlaub/wakeup)
    -> input_select.wohnungsstatus (normalbetrieb/nachtmodus/urlaub/alarm_scharf/...)
      -> input_select.strommodus (Normal/Abwesend/Eco/Nacht)
```

### Key Automations (all active unless noted)

| Automation | Status | Purpose |
|---|---|---|
| michel_status_trigger_automation | on | Triggers when Michel status changes |
| status_wohnung_sync_mit_status_michel | on | Syncs Wohnungsstatus with Michels presence |
| strommodus_globaler_wechsler | on | Switches Strommodus based on Wohnungsstatus |
| wohnunngsstatus_trigger_automationn_v1_0_001 | on | Triggers actions on Wohnungsstatus change |
| alarmnlage_schaltet_nach_status_michel | on | Alarm system follows Michels status |
| eco_modus_bewegung_pro_raum_steuern | on | Eco motion-based room control |
| tesla_steckdose_bei_an_abwesenheit_schalten | **unavailable** | Defunct -- Tesla socket control |

## Proposed Solution

### When leaving (strommodus → Abwesend)

**Always OFF (switch.turn_off):**
- `switch.zw_strom_wohnzimmer` (bereits off)
- `switch.zw_strom_wohnzimmer_tv` → OFF
- `switch.zw_strom_wohnzimmer_sofa` → OFF
- `switch.zw_strom_kuche_ecke` → OFF
- `switch.zw_strom_geschirrspulmaschine` → OFF

**Conditional OFF — Schlafzimmer:**
- Check if `sensor.zw_strom_tesla_w` (Tesla power draw) > ~500W
- If Tesla is charging → DO NOT turn off Schlafzimmer (interrupts charging!)
- If not charging → turn OFF `switch.zw_strom_schlafzimmer`
- ⚠️ The Tesla is physically plugged into the Schlafzimmer circuit

**Conditional OFF — Büro (60min timer):**
- Check `sensor.zw_strom_buro_electric_consumption_w`
- If < 50W → turn OFF immediately (`switch.turn_off`)
- If ≥ 50W (computer running, printer active) → wait 60 minutes, then check again & turn OFF
- On arrival home → DO NOT auto-turn ON

**NICHT antasten:**
- `switch.zw_strom_kuche` — immer ON (Kühlschrank + Alexa Cube für Sprachbefehle)
- `switch.strom_esszimmer` — nie OFF (Staubsauger-Akku!)
- `switch.zw_strom_tesla` — Lade-Strategie bleibt (separates evcc-Lademanagement)

### When arriving home (strommodus → Normal)

- ✅ `switch.zw_strom_kuche` → **ON** (Alexa Cube für Sprachbefehle beim Iiträte)
- ✅ **Licht** → soll funktioniere (nüt kabutt mache)
- ❌ **Alles andere** → nüt automatisch aa
- 👆 TV, Sofa, Büro, etc. → nur manuell dur Michel

### Key Principle
When Michel is away, the washing machine, dishwasher, dryer, printer, TV, sofa, Simrig, and most kitchen appliances don't need power. Only the fridge (Stromküche) and vacuum battery charger (Strom Esszimmer) must stay on. The bedroom circuit needs special handling because the EVSE for the Tesla is wired into it — if you cut power while the car is charging, it stops the charge session.

### Implementation (Option B — new automation via REST API)

**Deployed 21.05.2026** ✅ via `POST /api/config/automation/config/new` (see SKILL.md "Automation Management via REST API").

**Results:**
| Automation | Entity ID | Config ID | Status |
|---|---|---|---|
| Strom optimiert | `automation.strommodus_optimiert_v2_0` | `1779384040353` | **on** ✅ |
| Lichter us bim Wegfaare | `automation.lichter_us_bim_wegfaare` | auto | **on** ✅ |
| Lichter a bim Heicho | `automation.lichter_a_bim_heicho` | auto | **on** ✅ |
| Strom alt (globaler) | `automation.strommodus_globaler_wechsler` | `1748967085801` | off |

**Live test (21.05.):**
- strommodus → Abwesend → Wohnzimmer/TV/Sofa/Gschirrspüler/Küche-Ecke/Büro/Schlafzimmer OFF ✅, Küche ON ✅
- strommodus → Normal → nüt wider aa (usser Küche wo schon a war) ✅
- Büro-Check: sensor 25.04W < 50W → sofort OFF ✅
- Schlafzimmer-Check: sensor 4.539W < 250W (Tesla nid am lade) → OFF ✅
- **Licht us bim Wegfaare:** testet via strommodus → Abwesend: `light.alle_lichter` + `light.lichter_hue` + `light.vorderer_bereich_hue` turned off ✅
- **Hinwi:** `automation.lichter_us_bim_wegfaare` und `automation.lichter_a_bim_heicho` sind eigenständigi Automatione — triggers glich wie Strom-Auto, aber separat (cleaner Pattern).

### Known issue (still open)

`light.lichter_wohnzimmer` (room group) = **UNAVAILABLE** — this breaks the `alle_lichter` bulk-off for the living room. The individual bulbs (via `licht.lichter_hue` group) still get turned off by the dedicated light automation, but a room-level group fix is pending. Create Support ticket if Michel asks about it.

### Verification
✅ Deployed and tested. All switches behave correctly at both Abwesend and Normal modes.

## Related

- Home Assistant skill: `skill_view(name='home-assistant')`
- Presence entity: `person.michel_goetschi` (returns `home` or `not_home`)

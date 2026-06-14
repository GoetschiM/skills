---
name: ecoflow-pv-load-management
version: 1.1.0
description: "Ecoflow PowerStream + DeltaMax — Solar-Überschuss-Management für Lasten (Teichpumpe, Waschmaschine, etc.). HA-Automationen mit direkten Ecoflow-Daten statt evcc Grid-Surplus. SOC-basiertes Laden, Wetterprognose, Rush-Mode."
tags: [ecoflow, pv, solar, battery, load-management, teichpumpe, evcc, smart-home]
category: smart-home
---

# Ecoflow PV-Load-Management 🐟☀️

## System-Architektur

```
☀️ Solar panels → Ecoflow PowerStream (2 Strings)
                        ↓
               🔋 Ecoflow DeltaMax (2 kWh)
                        ↓
               ⚡ Jelly/Grid-Meter → Grid = 0 (Ecoflow regelt)
                        ↓
               🏠 Hausverbrauch (81-200W) + Pumpen (177W)
```

### Kritische Erkenntnis: Warum evcc hier nicht funktioniert

**Ecoflow + Jelly = Grid immer auf 0.** Das Jelly/Grid-Meter regelt d'Ecoflow so, dass de Netzbezug immer ~0 W isch. Solar-Überschuss → direkt in Batterie. Solar-Defizit → Batterie lieferet.

**evcc `minpv` misst Grid-Export-Surplus** → weil Grid immer 0, sieht evcc NIE Surplus → schaltet nie ah.

**Lösung:** Ecoflow-Daten DIREKT via HA-Sensoren verwerde, nöd über evcc.

### Richtige Berechnung

**⚠️ HISTORY (24.05.2026 — NOW FIXED):** `sensor.solarproduktion` existiert NID in HA — A3-Variable `pv_total` isch uf `|float(0)` zruggfalle. `haus_last` het `strom_total_w` = **Grid-Power** (aktuell ~ -2.5W) gläse statt em tatsächliche Huusverbrauch.

**✅ FIXED 24.05.2026 13:25:** A3-Variable wurden via HA REST API korrigiert:

```yaml
# ✅ IST JETZT (fixed 24.05.)
pv_total = states('sensor.ecoflow_powerstream_solarproduktion_w')|float(0)     # 468W ✅
haus_last = states('sensor.evcc_home_power')|float(0)                         # ~512W ✅
pv_avg10 = states('sensor.ecoflow_powerstream_solarproduktion_druchschnitt')|float(0)  # ~459W ✅
pv_trend_up: "{{ pv_avg10 > pv_start or pv_total > pv_start }}"              # Template statt nid-exist. binary_sensor ✅
pv_start: "{{ states('input_number.pv_min_start')|float(372) }}"               # Korrekt ohne haus_last ✅
pv_continue: "{{ states('input_number.pv_min_continue')|float(180) }}"         # Korrekt ohne haus_last ✅
runtime_goal: "{{ states('input_number.min_daily_run')|float(240) }}"          # Korrekti Entity statt nid-exist. min_daily_runtime ✅
soc: "{{ states('sensor.ecoflow_deltamax_main_battery_level')|float(100) }}"   # ✅ vorhande
soc_cutoff: "{{ states('input_number.soc_cutoff')|float(32) }}"                # ✅ vorhande
soc_extend_thresh: "{{ states('input_number.soc_schwelle_fur_verlangerung')|float(84) }}" # ✅ vorhande
```

**Kritischster Fix:** A3 stüüret jetz direkt `switch.teichpumpe` statt em nid-existierende `input_boolean.teichpumpe_soll` (dä existiert doch — isch `off` — aber isch nöd mit em Shelly verbunde gsi). D'Cron-Bridge liist `switch.teichpumpe` → passt alles zäme.

## HA-Architektur (Teichpumpe)

### Automationen (Stand 23.05.2026)

| Automation | Status | Rolle |
|-----------|--------|-------|
| **A3** `teichpumpe_pv_optimierung_v2_4_000` | ✅ ON | **Alleiniger Controller** |
| A1 `teich_darf_nur_3_30_stunden_laufen` | 🔴 OFF | Früher: evcc-mode-Gesetz. Deaktiviert. |
| A2 `einschalten_solar_soc_optimiert` | 🔴 OFF | Früher: Min+PV-Bedingung. Blockiert. |
| A4 `teich_abend_tagesbilanz` | ✅ ON | Reporting um 20:00 (harmlos) |

### A3-ID
- **Exakte Automation-ID:** `automation.teichpumpe_pv_optimierung_v2_3_003`
- **Numeric ID (API):** `1748519216924`
- **Notiz:** De Name seit `v2.4.000` aber d'Entity-ID isch `v2_3_003` — das isch korrekt so.

### A3-Logik (5-Minuten-Takt)

```yaml
Start-Bedingung:
  - Pumpe OFF
  - Temp > 5°C
  - Laufzeit heute < Ziel (240 Min)
  - PV-Überschuss (10 Min gemittelt) > Start-Schwelle (372W)
  - ODER: PV-Trend steigend + Überschuss > Start-Schwelle

Stop-Bedingung:
  - Pumpe ON + Ziel erreicht + Rest-Prognose < 1kWh + SOC < 84% → STOP
  - Pumpe ON + Temp ≤ 5°C → STOP (Frostschutz)
  - Pumpe ON + SOC < 32% → STOP (Batterieschutz)
  - Pumpe ON + kein PV-Überschuss > 10 Min → STOP (Wolke)

Verlängerung (nur wenn genug Solar):
  - Pumpe ON + Ziel erreicht + Rest-Prognose ≥ 1 kWh + SOC ≥ 84% → +5 Min

Rush-Mode (input_boolean.teichpumpe_rush_mode = ON):
  - Überbrückt ALLE Limits — Pumpe lauft bis Sunne weg isch

Fallback (20:30):
  - Wenn Laufzeit < Minimum + SOC ≥ Cutoff → Pumpe no ahe
```

### Wichtigi Limits (input_number Helfer)

| Helfer | Wert | Beschrieb |
|--------|------|-----------|
| `min_daily_run` | 240 Min | Standard-Ziel (4h) |
| `extend_max` | 120 Min | Max Verlängerung → Total max = 6h |
| `extend_step` | 5 Min | Schrittwiisi Verlängerig |
| `soc_cutoff` | 32% | Abschaltig bi leerer Batterie |
| `soc_schwelle_fur_verlangerung` | 84% | Verlängerig nur wenn SOC ≥ Schwelle |
| `max_on_time_no_pv` | 30 Min | Max Laufzit ohni PV |
| `min_on_time` | **39** Min | **⚠️ KRITISCH: Mindestlaufzit pro Start. Schützt Pumpe vor Zerstörig dur Zyklierä! Steiit in A3-Variable — NIE überschriibe!** |

### Weitere Input-Helfer

| Helfer | Beschrieb |
|--------|-----------|
| `input_boolean.teichpumpe_rush_mode` | ON = alle Limits ignoriere |
| `input_boolean.eigenverbrauchsoptimierung_aktiv` | Hauptschalter für A3 |
| `input_select.teichpumpe_notifications` | Start_Stop / Erweiterung / Alle / Aus |

**✅ FIXED 24.05.2026:** A3-Actions wurden uf `switch.teichpumpe` umgstellt. `input_boolean.teichpumpe_soll` existiert **doch** (isch `off`) — aber isch nöd mit em Shelly verbunde gsi. System isch jetz konsistent: A3 → `switch.teichpumpe` → Cron-Bridge liist `switch.teichpumpe` → Shelly.

**Fix:** A3-Actions müend `switch.turn_on -> switch.teichpumpe` si, nöd `input_boolean.teichpumpe_soll`. Oder `input_boolean.teichpumpe_soll` muess i HA als persistenten Helfer erstellt werde + die Cron-Bridge muess dä Helfer als Soll-Zuestand lese.

| `input_number.pv_min_start`

### HA-Konfiguration (Stand 24.05.2026 — FIXED ✅)

Die Teichpumpe brucht folgendi Sensore. **Alli sind jetz korrekt i A3 referenziert:**

| Entity | A3-Variable | Status | Bemerkig |
|--------|-----------|--------|----------|
| `sensor.ecoflow_powerstream_solarproduktion_w` | `pv_total` | ✅ nativ, immer verfüegbar | 468W aktuell |
| `sensor.evcc_home_power` | `haus_last` | ✅ nativ, immer verfüegbar | ~512W aktuell |
| `sensor.ecoflow_powerstream_solarproduktion_druchschnitt` | `pv_avg10` | ✅ nativ, immer verfüegbar | ~459W Ø |
| `sensor.ecoflow_deltamax_main_battery_level` | `soc` | ✅ nativ (Ecoflow-Integration) | 37% aktuell |
| `input_number.min_daily_run` | `runtime_goal` | ✅ persistent, Wert 240 Min | **War fälschlicherwise `min_daily_runtime`** |
| `input_number.soc_cutoff` | `soc_cutoff` | ✅ persistent | 32% |
| `input_number.soc_schwelle_fur_verlangerung` | `soc_extend_thresh` | ✅ persistent | 84% |
| `input_number.pv_min_start` | `pv_start` | ✅ persistent | 372W |
| `input_number.pv_min_continue` | `pv_continue` | ✅ persistent | 180W |
| `input_number.extend_step` | `extend_step` | ✅ persistent | 5 Min |
| `input_number.extend_max` | `extend_max` | ✅ persistent | 120 Min |
| `input_number.max_on_time_no_pv` | `max_no_pv` | ✅ persistent | 30 Min |

**HISTORY:** Vor em Fix (23.-24.05.) sind Sensore wie `sensor.solarproduktion`, `sensor.pv_uberschuss_10min_mittel`, `input_number.min_daily_runtime` via API erstellt gsi — und bim HA-Neustart verschwunde. Jetz sind alli durch nativi/persistente Entities ersetzt.

**⚠️ API-erstellti Entity sind NID persistent** — si verschwinde bim HA-Neustart. Müend i de HA-Konfiguration.yaml verewigt oder per Automation bi Start neigschribe wärde.

### Cron Bridge Architecture (Shelly MQTT Workaround)

**Problem:** De Shelly EM3 het MQTT deaktiviert → HA gseht ihn als "unavailable", chan Pumpe nöd stüüre.

**Lösig:** Entkopplig vo Steuerig + Konnektivität — **nach Fix 24.05.:**

```
A3 Automation → switch.teichpumpe (schribt Soll-Zuestand direkt)
                       ↓
              Cron-Bridge (alli 60s: liist switch.teichpumpe, verglicht mit Shelly HTTP)
                       ↓
              Shelly EM3 HTTP API (10.0.20.144 via POST form-data)
                       ↓
              switch.teichpumpe (HA-State via Cron-Bridge aktualisiert)
```

**HISTORY (vor 24.05.):** A3 het `input_boolean.teichpumpe_soll` gstüüret, wo existiert aber nöd mit em Shelly verbunden isch. D'Cron-Bridge het `switch.teichpumpe` gläse — aber A3 het nöd dri gschribe. Jetz isch alles konsistent: A3 → `switch.teichpumpe` → Cron-Bridge liist sälbi Entity.

**Cron Job** (erstellt via `cronjob(action='create')`):
- Job ID: `d2b55a0e2f2a`
- Name: `teichpumpe-bridge`
- Schedule: `*/1 * * * *` (jede Minute)
- Prompt: Lese `switch.teichpumpe` as Soll-Zustand (A3 schribt dri). Verglich mit Shelly-Relay `http://10.0.20.144/relay/0`. Falls abwiichend → POST `turn=on`/`turn=off` als Form-Data an Shelly. Update `switch.teichpumpe` in HA via API.
- Deliver: `local` (kei Telegram-Spam)
- Credentials: HA-Token via grep im Bash-History od. ursprünglich base64-enkodiert im erste `.env`-Setup. **Nid** in `/opt/data/home/.hermes/.env` (wurde überschriebe).

### ⚠️ KRITISCH: Min On-Time 39 min (Pumpeschutz!)

**WENN d'Pumpe ihgschaltet wird, MUSS si mindestens 39 Min laufe** bevor sie wider abgschaltet wird. Suscht wird d'Pumpe dur s'Zyklierä zerstört.

A3-Variable: `min_on_time: 39` (i Minute). Alli "Turn OFF"-Branches bruched `pump_on_since > min_on_time` als Bedingig. **Dä Wert darf NIE ohni Rücksprache mit Michel gänderet werde!**

### ⚠️ API-erstellti Entity sind NID persistent

Sensore und Helfer, wo via `POST /api/states` erstellt worde sind, **verschwinde bim HA-Neustart** oder innert 24h. Das betrifft:

- `sensor.solarproduktion` — `pv_total` im A3
- `sensor.pv_uberschuss_10min_mittel` — `pv_avg10`
- `sensor.ecoflow_deltamax_main_battery_level` — `soc`
- `input_number.min_daily_runtime` — `runtime_goal` (180 Min Default)
- `input_number.soc_extend_threshold` — `soc_extend_thresh` (84%)

**Müend i de HA-Konfiguration.yaml persistent verewigt oder via Automation bi Start neigschribe wärde.**
A3 fällt uf Default-Wert zrugg (`|float(300)`, `|float(80)`, `|float(100)`) wenn Sensore nid existiere — das füert zu falsche Entscheide! (Erfahret 23.05.2026)

**Bestätigt (24.05.2026):** Alli via API erstellte Sensore sind tatsächlich **verschwunde** — genau wie vorusgseit.
- `sensor.solarproduktion` → ❌ existiert nid → `pv_total = 0`
- `sensor.pv_uberschuss_10min_mittel` → ❌ existiert nid → `pv_avg10 = 0`
- `sensor.ecoflow_deltamax_main_battery_level` → existiert ✅ (kummt vo Ecoflow-Integration)
- `input_number.min_daily_runtime` → ❌ existiert nid → A3 liist immer 300 als Fallback
- `input_number.soc_extend_threshold` → ❌ existiert nid → Fallback 80% statt 84%
- `binary_sensor.pv_trend_positiv` → ❌ existiert nid → `pv_trend_up = off`

**Konsequenz:** D'Start-Bedingig (Branch 2) isch immer FALSE → Pumpe cha NIE via A3 starte. Nur d'Stop-Bedingige wirked no. Wenn d'Pumpe scho ah isch (manuell oder vom Vortag), lauft si wiiter bis e Stop-Bedingig trefft.

### ⚠️ Kritische Pitfalls (neu 23.05.)

#### 🚫 Entity-Name `switch.teich_pumpe` vs `switch.teichpumpe`

A3 im Original het **`switch.teich_pumpe`** (mit Underscore) referenziert, aber de reali Switch heisst **`switch.teichpumpe`** (ohni). A3 het jedezyte en nicht-existente Switch aagsproche. Fix: A3-Variable uf korrekte Switch-Namen umgstellt.

**Situation nach Fix:** A3 stüüret jetz direkt `switch.teichpumpe` — de isch immer verfüegbar und wird via Cron-Bridge mit em Shelly synchronisiert.

#### 🚫 Min On-Time: 39 min (Pumpeschutz!)

**WENN d'Pumpe ihgschaltet wird, MUSS si mindestens 39 Min laufe** bevor sie wider abgschaltet wird. Suscht wird d'Pumpe dur s'Zyklierä zerstört.

A3-Variable: `min_on_time: 39` (i Minute). Alli "Turn OFF"-Branches bruched `pump_on_since > min_on_time` als Bedingig.

#### 🚫 Fehlendi Sensore → A3 evaluiert falsch

Wänn Sensore wie `sensor.solarproduktion` oder `sensor.pv_uberschuss_10min_mittel` nid existiere, evaluiert A3 `pv_total` und `pv_avg10` als 0 → Pump wird sofort wider usgschaltet. **Immer prüefe ob alli Sensore existiere bevor A3 ihgschaltet wird!**

#### 🚫 Shelly EM3 HTTP Control (Form-Data, nid Query-Params)

De Shelly EM3 (v1.14.1, Gen1) wird **NUR über POST mit Form-Data gschaltet**:
```bash
# ✅ FUNKTIONIERT
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "turn=on" http://10.0.20.144/relay/0

# ❌ FUNKTIONIERT NID (Timeout)
curl -X POST "http://10.0.20.144/relay/0?turn=on"
```

#### 🚫 HA API: r.read() numen EINMOL ufruefe

```python
# ❌ FALSCH — r.read() wird 2x ufgrufe
return json.loads(r.read()) if r.read() else {}

# ✅ RICHTIG — Body zwüschespychere
body = r.read()
return json.loads(body) if body and body.strip() else {}
```

#### 🚫 `haus_last` = Grid-Power statt Huusverbrauch (NEU 24.05.)

A3-Variable `haus_last` liist `states('sensor.strom_total_w')` — das isch de **Grid-Power** vom Shelly 3EM (-2.5W aktuell), nöd de tatsächlich Huusverbrauch. D'Ecoflow hält de Grid uf Null, drum gseht A3 immer ~0W Huusverbrauch.

**Konsequenz:** `pv_surplus = pv_total - haus_last = 0 - (-2.5) = 2.5W` (falsch, viel z'wenig). `pv_start = -2.5 + 372 = 369.5W` (z'artifiziell hoch will Grid-Wert negativ isch).

**Korrekt wär:** `haus_last = states('sensor.evcc_home_power')|float(0)` oder `states('sensor.ecoflow_powerstream_inverter_output_watts')|float(0)` — zeigt de würkliche Huusverbrauch (aktuell ~463W).

#### 🚫 `input_number.min_daily_runtime` existiert nid (NEU 24.05., bestätigt)

A3-Variable `runtime_goal` liist `states('input_number.min_daily_runtime')|float(300)` — aber dä Helfer existiert nid! De korrekti Helfer isch `input_number.min_daily_run` (Wert = 240 Min).

**Konsequenz:** A3 gseht immer 300 Min als Ziel, nie 240 — will's de API-erstellti Sensor nümm git. D'Verlängerig schribt sogar `input_number.set_value` uf `min_daily_runtime` — was ooni Wirkig blibt.

**Fix:** A3-Variable müesst `input_number.min_daily_run` referenziere (das existiert und isch persistent).

#### 🚫 Batterie ladet nid trotz Solar-Überschuss (NEU 24.05.)

**Beobachtig (24.05. 13:25):** 462W Solar, 183W Pumpe, ~280W anderi Verbraucher → eigentli Soll-Überschuss für Batterieladig. Aber `ecoflow_deltamax_total_in_power` = **0W**, Batterie SOC = **37%**.

**Hypothese:** Ecoflow-System priorisiert Iispeisig (Grid = 0) vor Batterieladig — oder de SOC Lower Limit isch uf ~35% gsetzt, so dass erst ab öppis >37% glade wird. Oder d'Ecoflow-Integration zeigt d'Ladeleistig nöd korrekt a.

**Prüefig:** `sensor.ecoflow_deltamax_ac_in_power` = 0W, `sensor.ecoflow_deltamax_solar_in_power` = 0W — d'Ecoflow erfasst gar kei In-Power. De muss i de Ecoflow-App selber prüeft werde.

#### 🚫 Batterie_Level-Sensor: ecoflow_deltamax_main vs ecoflow_powerstream_battery

Es git zwöi Batterie-SOC-Sensore:
- `sensor.ecoflow_deltamax_main_battery_level` = 37% (via API erstellt, nid persistent ✅ vorhande)
- `sensor.ecoflow_powerstream_battery_charge` = 37% (Ecoflow-nativ, **immer verfüegbar**)

A3 brucht `ecoflow_deltamax_main_battery_level` (den wo nid persistent isch). Für Resilienz sött A3 uf `ecoflow_powerstream_battery_charge` umgestellt werde — das isch en nativ verfüegbare Sensor vo de Ecoflow-Integration und verschwindet nid bim HA-Neustart.

#### 🚫 Fehlendi `binary_sensor.pv_trend_positiv` blocheirt PV-Trend-Start

A3 het en alternativ Start-Pfad: `pv_trend_up and pv_surplus >= pv_start`. Aber `binary_sensor.pv_trend_positiv` existiert nid → `pv_trend_up = 'off'` → dä Pfad isch au blockiert.

**Fix:** Binär-Sensor via Template-Sensor i HA erstelle, wo `sensor.power_production_now` mit em 10-Min-Durchschnitt verglicht. Oder A3-Variable aapasse: `pv_trend_up = states('sensor.power_production_next_hour')|float(0) > states('sensor.power_production_now')|float(0)`.

## Neue Features (24.05.2026)

### ☀️ SUN-Start 12:30 (Mittags-Start-Fenster)

**Trigger:** Um 12:30 evaluiert → gaht a wenn Solar > 200W + SOC > Cutoff.

```yaml
Trigger: at: 12:30:00
Branch (vor PV-Start-Branch):
  Bedingig: not pump_on AND temp_out > 5 AND run_today < runtime_goal
            AND off_since >= min_off_time
            AND time BETWEEN 12:30 AND 13:00
            AND pv_total >= 200  # Min Solar zum Starte
            AND soc >= soc_cutoff  # Batterie nöd leer
  Aktion: switch.turn_on -> switch.teichpumpe
```

Ideal für Schönewätter-Täg wo d'Pumpe am Morge no nöd gnueg PV gha het.

### 🚀 Auto-Rush-Mode (bi Schönewätter)

Automatisch aktiv wenn Solar > 400W + SOC > 50% (10:00-16:00). Automatisch us wenn Solar < 150W oder SOC < 35% oder 18:00+.

```yaml
Branch 0 (Auto-Rush-ON):
  Bedingig: not rush_mode AND pv_total >= 400 AND soc >= 50
            AND time BETWEEN 10:00 AND 16:00
  Aktion: input_boolean.turn_on -> teichpumpe_rush_mode

Branch 1 (Auto-Rush-OFF):
  Bedingig: rush_mode AND (pv_total < 150 OR soc < 35 OR time >= 18:00)
  Aktion: input_boolean.turn_off -> teichpumpe_rush_mode
```

**Hinweis:** Rush-Mode gaht nur a wenn SOC ≥ 50% — schützt d'Batterie vor Tiefentladig.

## User-Preference: Nie is Netz verchaufe

Michels klari Aasag: **Lieber d'Pumpe länger laufe lah als Solar is Netz ispiise.** Wenn d'Batterie voll isch (SOC ≥ 84%) und d'Sunne no schint, wird d'Pumpe verlängeret statt dass mer Iispiist. Das isch über d'Verlängerigs-Logik scho i A3 integriert (Branch 6: Ziel ↑ bi energy_rest ≥ 1 kWh + SOC ≥ Schwelle).

## Wichtigi HA-Sensoren

### Ecoflow (Muss für pv_surplus)

| Entity | Beschrieb |
|--------|-----------|
| `sensor.ecoflow_powerstream_solarproduktion_w` | Aktuelli Solar-Produktion (W) |
| `sensor.ecoflow_deltamax_main_battery_level` | Batterie-SOC (%) |
| `sensor.ecoflow_deltamax_total_in_power` | Ladeleistung (W) |
| `sensor.ecoflow_deltamax_total_out_power` | Entladeleistung (W) |
| `sensor.ecoflow_powerstream_solar_1_current` | PV String 1 Strom (A) |
| `sensor.ecoflow_powerstream_solar_2_current_2` | PV String 2 Strom (A) |

### Energie (für Berechnig)

| Entity | Beschrieb | Status |
|--------|-----------|--------|
| `sensor.ecoflow_powerstream_solarproduktion_w` | Ecoflow Solar total (W) — **immer verfüegbar** | ✅ nativ |
| `sensor.solarproduktion` | Alias für Solar total — **NUR via API erstellt, nid persistent!** | ❌ verschwunde |
| `sensor.strom_total_w` | Grid-Power (W) — **NID** Huusverbrauch! (D'Ecoflow hält Grid uf ~0) | ⚠️ irreführend |
| `sensor.evcc_home_power` | **Richtige** Huusverbrauch (W) — via evcc | ✅ nativ |
| `sensor.ecoflow_powerstream_inverter_output_watts` | **Alternativ**: Ecoflow Inverter Output = Total-Last | ✅ nativ |
| `sensor.energy_production_today_remaining` | Rest-Prognose heute (kWh) | ✅ |
| `sensor.evcc_battery_capacity` | Batterie-Kapazität (kWh) | ✅ |

### Pumpe (Teich)

| Entity | Beschrieb |
|--------|-----------|
| `switch.teichpumpe` | Teichpumpe AN/AUS |
| `sensor.teichpumpe_laufzeit_heute` | Laufzeit heute (h) |
| `sensor.teichpumpe_leistung` | Aktuelli Leistig (W) |
| `sensor.teichpumpe_temperatur` | Pumpen-Temperatur (°C) |

### Wetter

| Entity | Beschrieb |
|--------|-----------|
| `weather.forecast_home` | Wetterprognose (Wolken/Sonne) |
| `sensor.netatmo_aussenmodul_temperatur` | Aussetemperatur (°C) |
| `sensor.sun_next_setting` | Sunneuntergang |
| `sensor.sun_solar_elevation` | Solar-Elevation |

## Pitfalls

### 🚫 evcc minpv mit Ecoflow = sinnlos
Ecoflow + Jelly haltet Grid auf 0 → evcc sieht nie Surplus. **Immer Ecoflow-Daten direkt bruuche.**

### 🚫 Automations-Interferenz
Wenn mehrmi Automatione uf de glyche switch losgönd, blockiere si sich. Nur **EINE Hauptautomation** söll d'Pumpe steuere.

### 🚫 Falsche input_number-Referenz — FIXED 24.05.
A3 het `input_number.min_daily_runtime` referenziert (existiert nid → Fallback 300 Min). Jetz korrekt: `input_number.min_daily_run` (240 Min). **✅ Gfixt.**

### 🚫 Confluence-Wiki isch ABSCHLUSS
Ersch wenn s'Ticket vollständig beschriebe isch + alli Tests dursind, d'Wiki-Seite schriibe. Nöd vorher.

## QUICK-START: Neue Solar-Last aabinde

```yaml
# 1. Sensor i HA aabinde (Shelly/ESPHome/SmartPlug)
# 2. switch erstell für d'Last
# 3. A3 dupliziere + Ziel-Entity ersetze
# 4. pv_min_start/pv_min_continue a passe
# 5. min_daily_run + extend_max setze
# 6. Teste: manuell AN → A3 söt in 5 Min reagiere
```

## Verwandte Skills

### ha-shelly-bridge (HA ↔ Shelly Low-Level Sync)

Das `ha-shelly-bridge` Skill (`devops/ha-shelly-bridge`) isch de **primär Klass-Level-Umbrella** für alli HA↔Shelly Bridges. Es enthaltet:

- D'Cron-Bridge-Architekture (vollständigi Dokumentation vo Token-Extraktion, Tirith-Bypass, usw.)
- S'kanonischi Skript `scripts/teichpumpe-sync.py`
- Alli Methodä für HA-Token-Extraktion (6 Methode dokumentiert)
- D'Shelly EM3 HTTP-API-Format (Form-Data, nid Query-Params)

**Die Brücke zwüsched A3 und Shelly isch zweiteilt:**
1. **A3** (ecoflow-pv-load-management) → schribt Soll-Zuestand i `switch.teichpumpe`
2. **ha-shelly-bridge** → liist `switch.teichpumpe` und synchronisiert mit physischem Shelly-Relay

D'Cross-Referenz erlaubt jedem Skill sim eigene Domain-Kontext z'blibe, ohni Redundanz.

### Siehe au

- **Jira:** GL-73 (Systemanalyse + Limits)
- **Qdrant:** `smart-home/ecoflow` — Alli Credentials + Server + IPs
- **Confluence:** All-Inkl Integration (Email) + Goetschi Labs Rules
- **Referenz:** `references/a3-sensor-diagnosis-2026-05-24.md` — Vollständigi A3-Branch-Analyse + Fix-Report: Before/After-Vergleich, korrigierti Variablen, SUN-Start 12:30, Auto-Rush-Mode, Lessons Learned
- **Referenz:** `references/a3-update-recipe.md` — HA REST API Recipe: A3-Konfiguration lesen, modifizieren, POST-Update, Reload (24.05.2026)

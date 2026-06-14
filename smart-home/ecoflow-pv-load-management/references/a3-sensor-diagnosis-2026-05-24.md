# A3 Sensor Diagnosis + Fix Report (24.05.2026)

## Before → After: Variable Fixes

| A3 Variable | ❌ VOR Fix | ✅ NACH Fix | Korrekt? |
|-------------|-----------|------------|----------|
| `pv_total` | `states('sensor.solarproduktion')` → ❌ 0W | `states('sensor.ecoflow_powerstream_solarproduktion_w')` → ✅ 468W | ✅ |
| `haus_last` | `states('sensor.strom_total_w')` → ⚠️ -2.5W (Grid!) | `states('sensor.evcc_home_power')` → ✅ 512W | ✅ |
| `pv_avg10` | `states('sensor.pv_uberschuss_10min_mittel')` → ❌ 0W | `states('sensor.ecoflow_powerstream_solarproduktion_druchschnitt')` → ✅ ~459W | ✅ |
| `pv_trend_up` | `is_state('binary_sensor.pv_trend_positiv','on')` → ❌ `off` | `{{ pv_avg10 > pv_start or pv_total > pv_start }}` → ✅ dynamisch | ✅ |
| `runtime_goal` | `states('input_number.min_daily_runtime')` → ❌ 300 (existiert nid) | `states('input_number.min_daily_run')` → ✅ 240 Min | ✅ |
| `soc_extend_thresh` | `states('input_number.soc_extend_threshold')` → ⚠️ 80% (existiert nid) | `states('input_number.soc_schwelle_fur_verlangerung')` → ✅ 84% | ✅ |
| Target Entity | `input_boolean.teichpumpe_soll` → existiert aber nöd verbunde | `switch.teichpumpe` → ✅ direkti Steuerig | ✅ |

## Entity-Validierung (POST-FIX, verified)

| Entity | Existiert? | Wert | Quelle |
|--------|-----------|------|--------|
| `sensor.ecoflow_powerstream_solarproduktion_w` | ✅ nativ | 462W | Ecoflow-Integration |
| `sensor.evcc_home_power` | ✅ nativ | 463W | evcc |
| `sensor.ecoflow_powerstream_solarproduktion_druchschnitt` | ✅ nativ | ~459W | Ecoflow-Integration |
| `sensor.ecoflow_deltamax_main_battery_level` | ✅ nativ | 37% | Ecoflow-Integration |
| `input_number.min_daily_run` | ✅ persistent | 240 | HA-Konfiguration |
| `input_number.soc_cutoff` | ✅ persistent | 32 | HA-Konfiguration |
| `input_number.soc_schwelle_fur_verlangerung` | ✅ persistent | 84 | HA-Konfiguration |
| `input_number.pv_min_start` | ✅ persistent | 372 | HA-Konfiguration |
| `input_number.pv_min_continue` | ✅ persistent | 180 | HA-Konfiguration |
| `input_number.extend_step` | ✅ persistent | 5.0 | HA-Konfiguration |
| `input_number.extend_max` | ✅ persistent | 120.0 | HA-Konfiguration |
| `input_number.max_on_time_no_pv` | ✅ persistent | 30 | HA-Konfiguration |
| `input_boolean.teichpumpe_soll` | ✅ existiert (off) | off | HA — aber **NID** mit Shelly verbunde |
| `switch.teichpumpe` | ✅ nativ | on | Shelly via Cron-Bridge |

## Live State NACH Fix (verified 24.05. 14:00+)

| Messpunkt | Wert |
|-----------|------|
| Solar Total | 468W |
| Hausverbrauch (evcc) | 512W |
| Batterie SOC | 37% |
| Pumpe | ON (via A3) |
| Pumpe Leistung | 183W |
| Grid | ~0W (Ecoflow regelt) |
| Runtime Today | ~90+ Min |

## A3-Config NACH Fix (Struktur)

### Variables (korrigiert)

```yaml
pv_total: "{{ states('sensor.ecoflow_powerstream_solarproduktion_w')|float(0) }}"
haus_last: "{{ states('sensor.evcc_home_power')|float(0) }}"
pv_surplus: "{{ (pv_total - haus_last)|abs }}"
pv_avg10: "{{ states('sensor.ecoflow_powerstream_solarproduktion_druchschnitt')|float(0) }}"
pv_trend_up: "{{ pv_avg10 > pv_start or pv_total > pv_start }}"
pv_start: "{{ states('input_number.pv_min_start')|float(372) }}"
pv_continue: "{{ states('input_number.pv_min_continue')|float(180) }}"
runtime_goal: "{{ states('input_number.min_daily_run')|float(240) }}"
soc: "{{ states('sensor.ecoflow_deltamax_main_battery_level')|float(100) }}"
soc_cutoff: "{{ states('input_number.soc_cutoff')|float(32) }}"
soc_extend_thresh: "{{ states('input_number.soc_schwelle_fur_verlangerung')|float(84) }}"
energy_rest: "{{ states('sensor.energy_production_today_remaining')|float(0) }}"
run_today: "{{ (states('sensor.teichpumpe_laufzeit_heute')|float(0)) * 60 }}"
temp_out: "{{ state_attr('weather.forecast_home', 'temperature')|float(5) }}"
pump_on: "{{ is_state('switch.teichpumpe', 'on') }}"
rush_mode: "{{ is_state('input_boolean.teichpumpe_rush_mode', 'on') }}"
min_on_time: "{{ 39 }}"
min_off_time: "{{ 5 }}"
max_no_pv: "{{ states('input_number.max_on_time_no_pv')|float(30) }}"
extend_step: "{{ states('input_number.extend_step')|float(5.0) }}"
extend_max: "{{ states('input_number.extend_max')|float(120.0) }}"
pump_on_since: "{{ (as_timestamp(now()) - as_timestamp(state_attr('switch.teichpumpe', 'since')|default(now()))|int) // 60 }}"
off_since: "{{ (as_timestamp(now()) - as_timestamp(state_attr('switch.teichpumpe', 'off_since')|default(now()))|int) // 60 }}"
```

### Triggers

```yaml
triggers:
  - trigger: time_pattern
    minutes: "/5"        # Alle 5 Minuten evaluiere
  - trigger: time
    at: "12:30:00"       # NEW: Mittags-Start-Fenster
  - trigger: time
    at: "20:30:00"       # Fallback am Abe
  - trigger: template     # Notfall wenn SOC unter Cutoff fallt
    value_template: "{{ soc < soc_cutoff and pump_on }}"
```

### Choose-Branches (Reihenfolge = Priorität)

```
[NEW] Branch 0a: Auto-Rush ON  → wenn Solar≥400W + SOC≥50% + 10-16 Uhr
[NEW] Branch 0b: Auto-Rush OFF → wenn Solar<150W + SOC<35% + 18+ Uhr
Branch 0: Stop bei Ziel erreicht → run_today ≥ goal + kein Rest
Branch 1: Stop bei Frost/leerer Batterie → temp≤5°C oder SOC<cutoff
[NEW] Branch 1b: SUN-Start 12:30 → Solar≥200W + SOC≥cutoff + 12:30-13:00
Branch 2: Start PV-Überschuss → pv_avg10 ≥ pv_start
Branch 3: Weiterlaufen → gnueg PV
Branch 4: Stop bei kein PV → pv < continue + >30 Min
Branch 5: Start Fallback 20:30 → run_today < min + SOC ≥ cutoff
Branch 6: Verlängerung → Ziel erreicht + Rest ≥ 1kWh + SOC ≥ 84%
```

### Conditions (Guard)

```yaml
condition: "{{ is_state('input_boolean.eigenverbrauchsoptimierung_aktiv', 'on') }}"
```

## Auto-Rush-Mode

**Aktivierung (Branch 0a, vor alle andere):**
```yaml
condition: rush_mode == off AND pv_total >= 400 AND soc >= 50
           AND time BETWEEN 10:00 AND 16:00
action: input_boolean.turn_on → teichpumpe_rush_mode
```

**Deaktivierung (Branch 0b):**
```yaml
condition: rush_mode == on AND (pv_total < 150 OR soc < 35 OR time >= 18:00)
action: input_boolean.turn_off → teichpumpe_rush_mode
```

**Effekt:** Rush-Mode überbrückt alli Stop-Limits — Pumpe lauft bis Sunne weg.

## SUN-Start 12:30 (Branch 1b)

```yaml
condition: pump_on == off AND temp_out > 5
           AND run_today < runtime_goal AND off_since >= min_off_time
           AND time BETWEEN 12:30 AND 13:00
           AND pv_total >= 200 AND soc >= soc_cutoff
action: switch.turn_on → switch.teichpumpe
```

Ideal für Schönewätter-Täg wo d'Pumpe am Morge wäge SOC < cutoff no nöd ane isch.

## Lessons Learned

1. **API-erstellti Sensore sind NIE persistent** — verschwinde bim HA-Neustart. Immer nativi/persistenti Entities verwende.
2. **`strom_total_w` isch GRID-Power**, nöd Huusverbrauch — bei Ecoflow isch das immer ~0W und irreführend.
3. **`input_boolean.teichpumpe_soll` existiert doch** — isch aber nöd mit em Shelly verbunde. A3 söll direkt `switch.teichpumpe` schriibe.
4. **`min_daily_runtime` vs `min_daily_run`** — en kline Typo het zur Folg gha, dass d'Pumpe immer 300 Min statt 240 Min als Ziel gha het.
5. **Binary-Sensor `pv_trend_positiv`** existiert nid — besser Template-basiert via Variablen.
6. **HA `choose`-Branches evaluiere vo OBEN nach UNTE** — ersti passendi Bedingig gwinnt. Reihenfolg isch kritisch.

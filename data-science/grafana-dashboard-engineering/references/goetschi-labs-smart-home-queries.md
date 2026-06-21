# Goetschi Labs Smart Home & Tesla – InfluxDB Queries for Grafana

Verified working InfluxDB V1 queries for HomeAssistant data on 10.0.60.140:8086.
All queries tested with actual data — not theoretical.

## DATA VERIFICATION WORKFLOW (CRITICAL!)

Before building ANY dashboard, always verify which measurements actually log data:

```python
INF = "http://10.0.60.140:8086"
import urllib.request, json, urllib.parse
def iq(db, q):
    req = urllib.request.Request(f"{INF}/query?db={urllib.parse.quote(db)}&q={urllib.parse.quote(q)}")
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

# 1) Show ALL measurements with data in last 24h
r = iq("homeassistant", "SHOW MEASUREMENTS")
all_meas = [v[0] for s in r["results"][0].get("series",[]) for v in s["values"]]
print(f"Total measurements: {len(all_meas)}")

recent = []
for m in all_meas:
    r2 = iq("homeassistant", f'SELECT * FROM "{m}" WHERE time > now() - 24h LIMIT 1')
    if r2["results"][0].get("series"):
        recent.append(m)
print(f"With data in 24h: {len(recent)}")

# 2) Check field structure of a specific measurement
r = iq("homeassistant", 'SHOW FIELD KEYS FROM "sensor.strom_wohnung"')
for s in r["results"][0]["series"]:
    for f in s["values"]:
        print(f"  Field: {f[0]} ({f[1]})")
```

## KEY INSIGHT: Not All HA Sensors Log to InfluxDB

Many Z-Wave sensors (`electric_consumption_w`, power sensors) exist as HomeAssistant entities but are **NOT** logged to InfluxDB. They only exist as real-time state in HA.

Check with `SHOW SERIES` before assuming data exists:
```sql
SHOW SERIES FROM "sensor.zw_strom_wohnzimmer_electric_consumption_w"
-- If empty → sensor is NOT in InfluxDB
```

## HomeAssistant Numeric Value Pattern

HA logs the actual value in the `value` field. String states in `state`. Metadata in `*_str` fields.

```sql
-- ✅ Numeric data
SELECT last("value") FROM "sensor.strom_wohnung"

-- ✅ String state  
SELECT last("state") FROM "sensor.tesla_ladestatus"

-- ❌ Avoid: returns ALL metadata fields
SELECT last(*) FROM "sensor.X"
```

## Strom/PV Queries

### Aktueller Gesamtverbrauch (Stat Panel)
```sql
SELECT last("value") FROM "sensor.strom_wohnung"
```
Unit: `watt`, decimals: 0
→ Aktuell: ~208W

### Aktueller Küchenverbrauch (Stat Panel)
```sql
SELECT last("value") FROM "sensor.strom_kuche_w"
```
Unit: `watt`, decimals: 0

### Strom Wohnung – 24h Verlauf (Timeseries)
```sql
SELECT "value" FROM "sensor.strom_wohnung" WHERE $timeFilter
```
Unit: `watt`

### Strom Küche – 24h Verlauf (Timeseries)
```sql
SELECT "value" FROM "sensor.strom_kuche_w" WHERE $timeFilter
```
Unit: `watt`

### Shelly 3EM Power Factor – Aktuell (Stat, one per Phase)
```sql
SELECT last("value") FROM "sensor.shelly3em_channel_a_power_factor"
SELECT last("value") FROM "sensor.shelly3em_channel_b_power_factor"
SELECT last("value") FROM "sensor.shelly3em_channel_c_power_factor"
```
Unit: `percent`, decimals: 2
→ Measurement names: `shelly3em_channel_a_power_factor`, etc.
→ Device: `shellyem3-483FDAC38E46`

### Shelly 3EM Power Factor – 24h Verlauf (Timeseries)
```sql
SELECT "value" FROM "sensor.shelly3em_channel_a_power_factor" WHERE $timeFilter
SELECT "value" FROM "sensor.shelly3em_channel_b_power_factor" WHERE $timeFilter
SELECT "value" FROM "sensor.shelly3em_channel_c_power_factor" WHERE $timeFilter
```
Legend format: "Phase A", "Phase B", "Phase C"

### EcoFlow DeltaMax Cycles (Stat)
```sql
SELECT last("value") FROM "sensor.ecoflow_deltamax_cycles"
```

### Solar Peak Heute (Stat – string state)
```sql
SELECT last("state") FROM "sensor.power_highest_peak_time_today"
```
→ Returns timestamp string like `2026-06-14T11:00:00+00:00`
→ Measurement: `power_highest_peak_time_today`
→ Also available: `power_highest_peak_time_tomorrow`

### EcoFlow Battery Limits (Stat)
```sql
SELECT last("value") FROM "sensor.ecoflow_powerstream_lower_battery_limit"
SELECT last("value") FROM "sensor.ecoflow_powerstream_upper_battery_limit"
```

### kWh Verbrauch pro Raum (Stat)
```sql
-- Waschküche (aktuell: ~158.8 kWh)
SELECT last("value") FROM "sensor.srom_waschkuche_kwh_energy"
-- Büro (aktuell: ~685.9 kWh)
SELECT last("value") FROM "sensor.strom_buro_kwh_energy"
```
Unit: `kwh`, decimals: 1

## Tesla/EVCC Queries

### Aktueller Ladestatus (Stat – string state)
```sql
SELECT last("state") FROM "sensor.tesla_ladestatus"
```
→ Returns: `disconnected`, `charging`, `stopped`, `complete`, `starting`, `no_power`

### EVCC Ladevorgänge Total (Stat – numeric)
```sql
SELECT last("value") FROM "sensor.evcc_charging_sessions"
```
→ Returns total count (currently: 75)

### Tesla Connected (Stat – binary)
```sql
SELECT last("value") FROM "binary_sensor.evcc_tesla_connected"
```
→ 0 = disconnected, 1 = connected

### Tesla Charging (Stat – binary)
```sql
SELECT last("value") FROM "binary_sensor.evcc_tesla_charging"
```
→ 0 = not charging, 1 = charging

### Tesla Mobil Connector Connected (Stat – binary)
```sql
SELECT last("value") FROM "binary_sensor.evcc_tesla_mobil_connector_connected"
```

### Tesla Mobil Connector Charging (Stat – binary)
```sql
SELECT last("value") FROM "binary_sensor.evcc_tesla_mobil_connector_charging"
```

### Ladevorgänge – Loadpoints (Table – JSON string field)
```sql
SELECT "loadpoints_str", "vehicles_str", "total", "value" 
FROM "sensor.evcc_charging_sessions" WHERE $timeFilter ORDER BY time DESC LIMIT 10
```
→ `loadpoints_str` contains JSON with charging sessions per device:
```json
{
  "Tesla": {"chargeDuration": 120484.0, "chargedEnergy": 26.06, "cost": 8.33},
  "Tesla Mobil Connector": {"chargeDuration": 453223.0, "chargedEnergy": 147.89, "cost": 47.12},
  "Teich Pumpe": {"chargeDuration": 411522.0, "chargedEnergy": 20.51, "cost": 4.59},
  "Wäschetrockner": {"chargeDuration": 41511.0, "chargedEnergy": 7.47, "cost": 2.32},
  "Waschmaschine": {"chargeDuration": 31524.0, "chargedEnergy": 3.07, "cost": 0.95}
}
```
→ Note: The `vehicles_str` field has a DIFFERENT structure from `loadpoints_str` (merges Tesla + Mobil Connector)

### Ladevorgänge – Detail (Table)
```sql
SELECT * FROM "sensor.evcc_charging_sessions_loadpoints" WHERE $timeFilter ORDER BY time DESC LIMIT 10
```
→ Contains individual loadpoint charging data as JSON strings

### Tesla Kosten (Stat – all currently 0, energy cost tracking)
```sql
SELECT last("value") FROM "sensor.tesla_kosten_monat"
SELECT last("value") FROM "sensor.tesla_kosten_tag"
SELECT last("value") FROM "sensor.tesla_kosten_woche"
```
Unit: `currencyEUR`
→ Note: Currently all return 0 (not collecting? or reset?)

## Trading Queries (database: trading01)

### Account Overview (Stat)
```sql
SELECT last("balance") FROM "trading01"."autogen"."account"
SELECT last("equity") FROM "trading01"."autogen"."account"
SELECT last("profit") FROM "trading01"."autogen"."account"
SELECT last("margin_level") FROM "trading01"."autogen"."account"
SELECT last("open_positions") FROM "trading01"."autogen"."account"
SELECT last("login") FROM "trading01"."autogen"."account"
```
Unit: `currencyEUR`, decimals: 2
→ Live data: Balance=61660.16, Equity=60758.79, Profit=-901.37

### Balance/Equity History (Timeseries)
```sql
SELECT "balance" FROM "trading01"."autogen"."account" WHERE $timeFilter
SELECT "equity" FROM "trading01"."autogen"."account" WHERE $timeFilter
```
Unit: `currencyEUR`, decimals: 2

### Letzte Trades (Table)
```sql
SELECT "time","entry_price","exit_price","profit","side","symbol","volume" 
FROM "trading01"."autogen"."trades" WHERE $timeFilter ORDER BY time DESC LIMIT 20
```

### Letzte Positionen (Table)
```sql
SELECT "time","symbol","type","volume","price_open","price_current","profit" 
FROM "trading01"."autogen"."positions" WHERE $timeFilter ORDER BY time DESC LIMIT 20
```

### Trading Signale (Table)
```sql
SELECT "time","action","asset","type","value" 
FROM "trading01"."autogen"."trading_signals" WHERE $timeFilter ORDER BY time DESC LIMIT 20
```

### Performance (Table)
```sql
SELECT "time","profit","trades","wins","losses" 
FROM "trading01"."autogen"."performance" WHERE $timeFilter ORDER BY time DESC LIMIT 20
```

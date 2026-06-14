# Teichpumpe HA Entities

## Switches / Input Booleans
- `switch.teichpumpe` — actual physical state (synced to Shelly)
- `input_boolean.teichpumpe_soll` — desired state (set by PV optimization)
- `input_boolean.teichpumpe_rush_mode`

## Select / Sensors
- `input_select.teichpumpe_notifications`
- `sensor.teichpumpe_leistung`
- `sensor.teichpumpe_temperatur`
- `sensor.teichpumpe_laufzeit_heute`

## Automations
- `automation.teichpumpe_switch_bridge` — handles real-time sync
- `automation.teichpumpe_pv_optimierung_v2_3_003` — sets desired state based on solar surplus

# Goetschi Labs Grafana Environment

## URLs & Zugänge

| System | URL | Zugang |
|--------|-----|--------|
| **Grafana** | http://10.0.60.110:3000 | admin / Louis_one_13 |
| **Prometheus** | http://10.0.60.110:9090 | direkt erreichbar |
| **Loki** | http://10.0.60.110:3100 | direkt erreichbar |
| **InfluxDB** | http://10.0.60.140:8086 | Kein Auth |

## Dashboard Übersicht

| Dashboard | URL | Datenquellen |
|-----------|-----|-------------|
| 🏠 Goetschi Labs – Live Monitor | `/d/d63f5e80/` | Prometheus (12/13 Hosts) |
| 🌞 PV & Strom | `/d/c893f920/` | InfluxDB homeassistant |
| 🚗 Tesla | `/d/2155e090/` | InfluxDB homeassistant |
| 📈 Trading | `/d/e10de26b/` | InfluxDB trading01 |

## Prometheus Targets (13)

| Instance | Job | Status |
|----------|-----|--------|
| localhost:9090 | prometheus | ✅ up |
| 10.0.60.10:9100 | pve01 | ✅ up |
| 10.0.60.60:9100 | docker-lxcs | ✅ up |
| 10.0.60.121:9100 | docker-lxcs | ✅ up |
| 10.0.60.139:9100 | docker-lxcs | ✅ up |
| 10.0.60.167:9100 | docker-lxcs | ✅ up |
| 10.0.60.170:9100 | docker-lxcs | ✅ up |
| 10.0.60.104:9100 | no-docker-lxcs | ✅ up |
| 10.0.60.106:9100 | no-docker-lxcs | ✅ up |
| 10.0.60.140:9100 | no-docker-lxcs | ✅ up |
| 10.0.60.141:9100 | no-docker-lxcs | ✅ up |
| 10.0.60.179:9100 | no-docker-lxcs | ✅ up |
| 10.0.60.30:9100 | no-docker-lxcs | 🔴 down |

## InfluxDB Datenbanken (24)

| Datenbank | Measurements | Beschreibung |
|-----------|-------------|-------------|
| homeassistant | ~1947 | 2 Jahre Smart Home Daten |
| trading01 | 6 | account, positions, trades, ohlcv, performance, trading_signals |
| trading | 565 | Trading Daten |
| Signale | 6 | Trading Signale |
| RL-Bot | 1 | Reinforcement Learning Bot |
| Tradingbot_LIVE01-03 | - | Live Bots |
| Tradingbot_BOT01-08 | - | Bot-Tester |

## Wichtige InfluxDB Felder (homeassistant)

| Measurement | Feld | Typ |
|-------------|------|-----|
| sensor.strom_wohnung | `value` | float (Watt) |
| sensor.strom_kuche_w | `value` | float (Watt) |
| sensor.tesla_ladestatus | `state` | string |
| sensor.evcc_charging_sessions | `total`, `value`, `loadpoints_str`, `vehicles_str` | float/string |
| binary_sensor.evcc_tesla_charging | `value` | float (0/1) |
| binary_sensor.evcc_tesla_connected | `value` | float (0/1) |
| sensor.shelly3em_channel_a_power_factor | `value` | float |
| sensor.ecoflow_deltamax_cycles | `value` | float |
| sensor.ecoflow_powerstream_lower_battery_limit | `value` | float |
| sensor.power_highest_peak_time_today | `state` | timestamp string |

## NOT in InfluxDB (existieren nur in HomeAssistant)

Diese Sensoren sind in HA als Entities vorhanden, werden aber **nicht** in InfluxDB geloggt:
- `sensor.zw_strom_*_electric_consumption_w` (alle Z-Wave power meter)
- `sensor.strom_buro_w`, `sensor.strom_keller_w` (aggregierte Helfer)

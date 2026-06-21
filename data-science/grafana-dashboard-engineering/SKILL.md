---
name: grafana-dashboard-engineering
description: "Build, debug, and iterate Grafana dashboards — Prometheus + InfluxDB data sources, panel types, query verification, and deployment patterns."
version: 1.0.0
author: Hermes Agent
tags: [grafana, dashboard, prometheus, influxdb, homeassistant, monitoring]
---

# Grafana Dashboard Engineering

Building Grafana dashboards for infrastructure, smart home, and trading data. Covers Prometheus (node_exporter) and InfluxDB V1 (HomeAssistant) data sources.

## Prerequisites

- Grafana URL + admin credentials (e.g. `http://10.0.60.110:3000` with `admin / Louis_one_13`)
- Basic Auth works for API access

## CRITICAL: Verify Data FIRST (Pitfall Prevention)

**BEFORE** building any dashboard panels, you MUST verify which data actually exists. This is the #1 mistake that produces empty dashboards.

### For Prometheus:

```python
import urllib.request, json

BASE = "http://10.0.60.110:9090"
def pq(q):
    import urllib.parse
    req = urllib.request.Request(f"{BASE}/api/v1/query?query={urllib.parse.quote(q)}")
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read()).get("data", {}).get("result", [])

# Check what metrics exist and return data
r = pq('100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)')
print(f"CPU: {len(r)} results")
for i in r[:3]:
    print(i.get("metric",{}).get("instance","?"), i.get("value",["","?"])[1])
```

### For InfluxDB (HomeAssistant):

```python
INF = "http://10.0.60.140:8086"
def iq(db, q):
    req = urllib.request.Request(f"{INF}/query?db={db}&q={urllib.parse.quote(q)}")
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

# 1) Check which measurements have data in last 24h
r = iq("homeassistant", "SHOW MEASUREMENTS")
all_meas = [v[0] for s in r.get("results",[{}])[0].get("series",[]) for v in s.get("values",[])]

# 2) Filter to recent data
for m in all_meas:
    r2 = iq("homeassistant", f"SELECT * FROM \"{m}\" WHERE time > now() - 24h LIMIT 1")
    series = r2.get("results",[{}])[0].get("series",[])
    if series and series[0].get("values"):
        print(f"✅ {m}: {series[0].get('values',[[]])[0]}")

# 3) Check field names per measurement
r2 = iq("homeassistant", f"SHOW FIELD KEYS FROM \"{m}\"")
for s2 in r2.get("results",[{}])[0].get("series",[]):
    for f in s2.get("values",[]):
        print(f"  Field: {f[0]} ({f[1]})")

# 4) Check series (tags) 
r3 = iq("homeassistant", f"SHOW SERIES FROM \"{m}\"")
```

## Common Pitfalls

### Pitfall 1: Assuming All HA Sensors Log to InfluxDB
**WRONG:** Many Z-Wave sensors (electric_consumption_w, power sensors) exist as HomeAssistant entities but are **NOT** logged to InfluxDB. They only exist as real-time state in HA.

**RIGHT:** First verify with `SHOW SERIES FROM "sensor.X"`. If it returns no series, the sensor is NOT in InfluxDB.

### Pitfall 2: Wrong Field Name in InfluxDB Queries
HomeAssistant logs sensors with structures like:
- String fields: `friendly_name_str`, `state`, `device_class_str`
- Float fields: `value` (this is what you want for numeric data)
- JSON fields: `loadpoints_str`, `vehicles_str` (complex objects as strings)

For HomeAssistant data, use:
```sql
SELECT last("value") FROM "sensor.strom_wohnung"  -- ✅ numeric
SELECT last("state") FROM "sensor.tesla_ladestatus"  -- ✅ string state
```
NOT:
```sql
SELECT last(*) FROM ...  -- ⚠️ returns all fields, most are metadata strings
```

### Pitfall 3: Grafana Proxy Can't Reach Itself
When creating a Data Source with URL `http://10.0.60.110:9090`, Grafana's internal proxy might fail because it's trying to reach itself. Direct queries from your agent to the Prometheus endpoint work fine.

### Pitfall 4: ReadOnly Data Sources
Provisioned Data Sources (via YAML files in `/etc/grafana/provisioning/datasources/`) are **readOnly** — can't edit or delete via API. Create new ones with different names instead.

## Dashboard Creation via API

```python
import urllib.request, json, base64

BASE = "http://10.0.60.110:3000"
creds = base64.b64encode(b"admin:Louis_one_13").decode()
headers = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

# Get Data Source UIDs
req = urllib.request.Request(f"{BASE}/api/datasources", headers=headers)
resp = urllib.request.urlopen(req)
all_ds = json.loads(resp.read())
prom_uid = [ds["uid"] for ds in all_ds if "Prometheus" in ds["name"]][0]
influx_uid = [ds["uid"] for ds in all_ds if ds["name"] == "InfluxDB"][0]

# Panel gridPos layout:
# (h=height, w=width/24, x=col_offset, y=row)
# 24 units wide. Common: w=6 (4 panels/row), w=12 (2/row)

dashboard = {
    "dashboard": {
        "title": "My Dashboard",
        "tags": ["monitoring"],
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "30s",
        "panels": [
            # Row header
            {"type": "row", "title": "Row Title", "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0}},
            # Stat panel
            {
                "id": 1, "type": "stat", "title": "Value",
                "gridPos": {"h": 4, "w": 6, "x": 0, "y": 1},
                "datasource": {"type": "prometheus", "uid": prom_uid},
                "targets": [{"refId": "A", "expr": "up{job='prometheus'}", "instant": True}]
            },
            # Timeseries
            {
                "id": 2, "type": "timeseries", "title": "CPU",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 5},
                "datasource": {"type": "prometheus", "uid": prom_uid},
                "targets": [{"refId": "A", 
                    "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[2m])) * 100)",
                    "legendFormat": "{{instance}}"}],
                "fieldConfig": {"defaults": {"unit": "percent", "min": 0, "max": 100}}
            },
            # InfluxDB raw query
            {
                "id": 3, "type": "stat", "title": "Balance",
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 1},
                "datasource": {"type": "influxdb", "uid": influx_uid},
                "targets": [{"refId": "A", "rawQuery": True,
                    "query": "SELECT last(\"balance\") FROM \"trading01\".\"autogen\".\"account\""}],
                "fieldConfig": {"defaults": {"unit": "currencyEUR", "decimals": 2}}
            },
        ]
    },
    "overwrite": True
}

req = urllib.request.Request(f"{BASE}/api/dashboards/db",
    data=json.dumps(dashboard).encode(), headers=headers, method="POST")
resp = urllib.request.urlopen(req, timeout=10)
result = json.loads(resp.read())
print(f"URL: {BASE}{result.get('url','?')}")
```

## Helpful Prometheus Queries

```promql
# Host status
count(up == 1)                    # Services online
count(up == 0)                    # Services offline

# CPU per host
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)

# Memory per host
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Disk usage (root partition)
100 - (node_filesystem_avail_bytes{mountpoint="/",fstype!=""} / node_filesystem_size_bytes{mountpoint="/",fstype!=""} * 100)

# Network traffic
rate(node_network_receive_bytes_total{device!="lo"}[5m])
rate(node_network_transmit_bytes_total{device!="lo"}[5m])

# Uptime
(time() - node_boot_time_seconds{instance="10.0.60.10:9100"}) / 86400

# Prometheus metrics
prometheus_tsdb_head_series       # Total time series
prometheus_build_info             # Version info
```

## InfluxDB Query Patterns (HomeAssistant)

```sql
-- Numeric value (current)
SELECT last("value") FROM "sensor.strom_wohnung"

-- String state
SELECT last("state") FROM "sensor.tesla_ladestatus"

-- Time series
SELECT "value" FROM "sensor.strom_wohnung" WHERE $timeFilter

-- From non-default retention policy
SELECT last("balance") FROM "trading01"."autogen"."account"

-- Table with specific columns
SELECT "time","entry_price","exit_price","profit","side","symbol" 
FROM "trading01"."autogen"."trades" 
WHERE $timeFilter 
ORDER BY time DESC LIMIT 20
```

## Data Source Health Checking

```python
# Test via Grafana API
req_h = urllib.request.Request(f"{BASE}/api/datasources/uid/{uid}/health", headers=headers)
resp_h = urllib.request.urlopen(req_h, timeout=10)
h = json.loads(resp_h.read())
print(f"Health: {h.get('status','?')} - {h.get('message','?')[:100]}")
```

## See Also

- `grafana-admin` skill — Admin tasks (password recovery, provisioning)
- `references/goetschi-labs-smart-home-queries.md` — Verified InfluxDB queries for HomeAssistant (Strom, Tesla/EVCC, Solar) and Trading (account, positions, trades, signals)

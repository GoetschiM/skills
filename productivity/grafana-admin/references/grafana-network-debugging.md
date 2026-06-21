# Grafana Network Debugging via Prometheus API

When data sources won't connect and you need to understand the network topology from inside the monitoring stack, Prometheus's API is your best friend.

## Key Prometheus API Endpoints

All accessible on Prometheus port (typically 9090):

### Target Status

```bash
# List all active and dropped targets
curl -s 'http://<PROMETHEUS>:9090/api/v1/targets'

# Active targets show scrape health per endpoint
# Dropped targets show what was configured but not scraped
```

### Query

```bash
# Simple metric query
curl -s 'http://<PROMETHEUS>:9090/api/v1/query?query=up'

# Returns all scraped targets with up/down status
# Values: [timestamp, "1" (up) or "0" (down)]
```

### Configuration

```bash
# Full Prometheus YAML config
curl -s 'http://<PROMETHEUS>:9090/api/v1/status/config'
```

This reveals all scrape jobs, targets, intervals — extremely useful for understanding what services exist and where they're configured.

### Label Values

```bash
# All job names
curl -s 'http://<PROMETHEUS>:9090/api/v1/label/job/values'

# All metric names
curl -s 'http://<PROMETHEUS>:9090/api/v1/label/__name__/values'
```

### Series Count

```bash
# Total time series in TSDB
curl -s 'http://<PROMETHEUS>:9090/api/v1/query?query=prometheus_tsdb_head_series'
```

## Discovering InfluxDB (or other services)

If you know InfluxDB should be running but can't find it:

1. **Check Prometheus targets** — is there a job scraping port 8086?
   ```bash
   curl -s 'http://10.0.60.110:9090/api/v1/query?query=up{instance=~".*8086.*"}'
   ```
   If empty, Prometheus doesn't scrape InfluxDB.

2. **Check all active IPs** — Prometheus shows all reachable hosts:
   ```python
   import urllib.request, json
   data = json.loads(urllib.request.urlopen("http://10.0.60.110:9090/api/v1/query?query=up").read())
   for r in data["data"]["result"]:
       ip = r["metric"]["instance"].split(":")[0]
       val = r["value"][1]
       print(f"{'🟢' if val=='1' else '🔴'} {ip} (job: {r['metric']['job']})")
   ```
   If InfluxDB's IP isn't in the result list, there's no node_exporter there.

3. **Test connectivity from Grafana container** — use Grafana's health check:
   Create a temp Prometheus data source pointing at the target host:port, check its health. The error message tells you if it's `no route to host`, `connection refused`, or `no such host`.

## Goetschi Labs Network Topology (June 2026)

### Alert: IP changes are NOT reflected in infrastructure docs

The old infrastructure documentation (goetschi-labs-infrastruktur-voll.md) contained **stale IPs**:
- CT108/109 existed in the original scan but were replaced by CT110/140
- **InfluxDB** moved from 10.0.60.109 → 10.0.60.140
- **Grafana/Prometheus** moved from 10.0.60.108 → 10.0.60.110

### Accessible Hosts from CT135 (NOVA)

Only reachable via 10.0.60.0/24 subnet:
- 10.0.60.1 (pve01) — SSH is public-key only, no password accepted
- 10.0.60.110 (CT110 — Grafana/Prometheus/Loki) — Grafana API on 3000, Prometheus on 9090
- 10.0.60.140 (CT140 — InfluxDB) — Port 8086, no auth required

### NOT accessible from CT135

- 10.0.60.107 (CT107 — MCPHub) — Different network segment
- Any 10.0.40.x (Paperless) — Different subnet
- 10.0.10.x (UniFi) — Different subnet
- Proxmox API (8006 on pve01) — Connection refused

## Grafana API Quick Reference

```python
BASE = "http://10.0.60.110:3000"
import urllib.request, json, base64
creds = base64.b64encode(b"admin:Louis_one_13").decode()
headers = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}

def grafana_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    return json.loads(urllib.request.urlopen(req).read())

def grafana_post(path, data):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(data).encode(), headers=headers, method="POST")
    return json.loads(urllib.request.urlopen(req).read())

def grafana_delete(path):
    req = urllib.request.Request(f"{BASE}{path}", headers=headers, method="DELETE")
    return json.loads(urllib.request.urlopen(req).read())

# Health check all non-readOnly DS
for ds in grafana_get("/api/datasources"):
    if not ds.get("readOnly"):
        health = grafana_get(f"/api/datasources/uid/{ds['uid']}/health")
        print(f"{ds['name']}: {health.get('status')}")
```

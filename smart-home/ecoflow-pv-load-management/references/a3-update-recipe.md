# A3 Automation Update Recipe (HA REST API)

How to read, modify, and save the Teichpumpe PV-Optimierung automation (A3).

## Prerequisites

- HA token (via Nova SSH: `source /root/hermes-runtime-167/home/.hermes/.env`)
- A3 numeric config ID: `1748519216924`
- Entity ID: `automation.teichpumpe_pv_optimierung_v2_3_003`

## Step 1: Read full config

```python
import json, urllib.request, base64

# Token holen
import subprocess
result = subprocess.run(
    ["sshpass", "-p", "Louis_one_13", "ssh", "-o", "StrictHostKeyChecking=no",
     "root@10.0.60.167",
     "grep HOMEASSISTANT_TOKEN /root/hermes-runtime-167/home/.hermes/.env | cut -d= -f2- | base64 -w0"],
    capture_output=True, text=True, timeout=15)
TOKEN = base64.b64decode(result.stdout.strip()).decode().strip()
HOST = "http://10.0.60.111:8123"

def ha(method, path, body=None):
    url = HOST + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, method=method, data=data,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
        return json.loads(raw) if raw and raw.strip() else {}

a3 = ha("GET", "/api/config/automation/config/1748519216924")
```

## Step 2: Modify

The config has these top-level keys:
- `triggers` — list of trigger objects (time_pattern, time, template)
- `conditions` — guard clause (must be true for any branch to execute)
- `actions[0].choose` — list of choose-branch dicts (evaluated in order, first match wins)
- `variables` — template variables dict

### Common modifications:

**A) Fix sensor references:**
```python
a3["variables"]["pv_total"] = "{{ states('sensor.ecoflow_powerstream_solarproduktion_w')|float(0) }}"
a3["variables"]["haus_last"] = "{{ states('sensor.evcc_home_power')|float(0) }}"
a3["variables"]["pv_avg10"] = "{{ states('sensor.ecoflow_powerstream_solarproduktion_druchschnitt')|float(0) }}"
```

**B) Change target entity (e.g., input_boolean → switch):**
```python
def fix_entity_ids(obj, old, new):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "entity_id" and isinstance(v, str) and v == old:
                obj[k] = new
            else:
                fix_entity_ids(v, old, new)
    elif isinstance(obj, list):
        for item in obj:
            fix_entity_ids(item, old, new)

fix_entity_ids(a3, "input_boolean.teichpumpe_soll", "switch.teichpumpe")
```

**C) Add a new time trigger:**
```python
a3["triggers"].append({"at": "12:30:00", "trigger": "time"})
```

**D) Add a new choose branch:**
```python
new_branch = {
    "alias": "My New Branch",
    "conditions": [{"condition": "template", "value_template": "..."}],
    "sequence": [...]
}
a3["actions"][0]["choose"].insert(0, new_branch)
```

## Step 3: Save via POST

```python
result = ha("POST", f"/api/config/automation/config/1748519216924", a3)
# Expect: {"result": "ok"}
```

## Step 4: Reload + Enable

```python
ha("POST", "/api/services/automation/reload", {})
ha("POST", "/api/services/automation/turn_on", {"entity_id": "automation.teichpumpe_pv_optimierung_v2_3_003"})
```

## Step 5: Verify

```python
verify = ha("GET", "/api/states/automation.teichpumpe_pv_optimierung_v2_3_003")
print(verify.get("state"))  # Should be "on"
```

## Known pitfalls

| Issue | Symptom | Fix |
|-------|---------|-----|
| `POST` returns 405 | Using PUT instead of POST | Use `method="POST"` |
| Branch never fires | Condition uses `enabled_condition` | Use `choose` with template conditions instead |
| `{"result": "ok"}` but no effect | Automation not reloaded | Always call `automation.reload` after save |
| Entity not found | Wrong entity ID | Check with `GET /api/states` first |

# HA Automation Debugging — Entity Mismatches

## Pattern: Automation wird nöd aktiv, obwohl Konditione schinbar erfüllet

### Schritt 1: Entität-Existenz prüefe

D'Automation referenziert hüfig Entities, wo nöd existiered. Das fallt nöd uf, wills Template-Engine stumm `0` oder `unknown` retourniert.

```python
# Jede referenzierti Entität prüefe
import json, urllib.request
HOST = "http://10.0.60.111:8123"
TOKEN = "..."

for eid in ["sensor.solarproduktion", "sensor.pv_uberschuss_10min_mittel", 
            "input_number.min_daily_runtime"]:
    req = urllib.request.Request(f"{HOST}/api/states/{eid}", 
        headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=5).read())
        print(f"{eid:45s} = {r.get('state','?')}")
    except urllib.request.HTTPError as e:
        print(f"{eid:45s} = NOT FOUND ({e.code})")
```

### Schritt 2: Entity-Naming-Check

Automation referenziert `entity_id: switch.teich_pumpe` aber de real Switch heisst `switch.teichpumpe` → stumm ignoriert.

```python
# Exakte Entity-ID us Automation Config extrahiere
config_id = "1748519216924"  # A3 Config ID
req = urllib.request.Request(f"http://10.0.60.111:8123/api/config/automation/config/{config_id}",
    headers={"Authorization": f"Bearer {TOKEN}"})
auto = json.loads(urllib.request.urlopen(req).read())
# Actions extrahiere und entity_ids uslese
for action in auto.get('action',[]):
    eid = action.get('entity_id','?')
    print(f"Action referenziert: {eid}")
```

### Schritt 3: Fehlendi Entities erstelle

```python
# Einfachi Entität via POST /api/states erstelle
req = urllib.request.Request(f"{HOST}/api/states/sensor.solarproduktion",
    method="POST",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
req.data = json.dumps({"state": "614", "attributes": {"unit_of_measurement": "W", "friendly_name": "Solarproduktion"}}).encode()
json.loads(urllib.request.urlopen(req).read())
```

### Schritt 4: Template-Sensor via Config Flow

```python
# Config Flow starte für Template Sensor
req = urllib.request.Request(f"{HOST}/api/config/config_entries/flow",
    method="POST",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
req.data = json.dumps({"handler": "template", "show_advanced_options": True}).encode()
flow = json.loads(urllib.request.urlopen(req, timeout=10).read())
flow_id = flow.get('flow_id')
# Flow fortsetze/step...
```

### Schritt 5: Bridge-Automation für Entity-Aliasing

Wenn de Name i de Automation nöd änderbar isch (ke PUT-Recht) aber s'richtige Entity en andere Name het → e **Bridge-Automation** erstelle wo uf State-Change vom falsche Name lost und uf s'richtige schribt.

```python
bridge_auto = {
    "name": "Teichpumpe Switch Bridge",
    "description": "Bridge teich_pumpe → teichpumpe",
    "trigger": [{"platform": "state", "entity_id": "switch.teich_pumpe"}],
    "condition": [],
    "action": [{
        "choose": [
            {"conditions": [{"condition": "state", "entity_id": "switch.teich_pumpe", "state": "on"}],
             "sequence": [{"service": "switch.turn_on", "entity_id": "switch.teichpumpe"}]},
            {"conditions": [{"condition": "state", "entity_id": "switch.teich_pumpe", "state": "off"}],
             "sequence": [{"service": "switch.turn_off", "entity_id": "switch.teichpumpe"}]}
        ]
    }]
}
# POST /api/config/automation/config  → neu erstelle
```

## Notification-Template Debugging (gelernt 26.05.2026)

Wenn en Automation **füt** (triggeret korrekt, sendet Notification) aber d'Ausgab isch kaputt — einzelni Wärt fehled, "unknown" statt Zahle — sind oft Template-Sensore referenziert wo's **nöd git**.

### Symptom
- Automation isch ON, Trigger funktioniert
- Notification chunnt a, aber 7-8 vo 10 Wärt gönd
- HA zeigt kei Fehler — brucht stumm `unknown` oder `0`

### Prozäss

```python
# 1. Automation config uslese
config = ha("GET", "/api/config/automation/config/{config_id}")
# Gseht: actions[0].data.message enthält Template-Stings

# 2. Jede sensor.Template-Eintrag prüefe
for s in extrahierte_Sensor_IDs:
    try:
        r = ha("GET", f"/api/states/{s}")
        print(f"OK: {s} = {r['state']}")
    except HTTPError as e:
        print(f"NOT FOUND: {s}")  # DAS isch de Übeltäter!
```

### Fix

1. Find korrekte Sensor-Name:
   ```
   GET /api/states
   → Filter nach Theme (z.B. "teich") → aka. "sensor.teichpumpe_laufzeit_heute" statt falschem "sensor.teich_laufzeit_heute_min"
   ```

2. Automation aktualisiere (POST, nöd PUT!):
   ```python
   # POST mit config_id → HA aktualisiert
   ha("POST", f"/api/config/automation/config/{config_id}", updated_config)
   # Output: {"result": "ok"}
   
   # Automation neulade
   ha("POST", "/api/services/automation/reload", {})
   ```

3. Test-Trigger:
   ```python
   ha("POST", "/api/services/automation/trigger", {"entity_id": "automation.<slug>"})
   ```

### User Preference: Notification nur an Mobile-App

Michel bechunnt Tagesbericht am **Handy** — `notify.mobile_app_sm_michel`. D'Notification für `notify.notify` (allgemein) chan usbaut werde. Seit 26.05.2026 nur no ein action-Block pro mobile-app.

---

## Bekannti Fallstrick (aktualisiert 26.05.2026)

| Muster | Effekt |
|--------|--------|
| `state_attr('wrong.entity','last_changed')` | `None` → Template default brucht |
| `states('entity')|float(0)` | Falls Entity fehlt → `0` statt Fehler |
| `switch.teich_pumpe` vs `switch.teichpumpe` | Stumm ignoriert, kei Log |
| `PUT /api/config/automation/config/{id}` → 405 | **POST** bruche (mit config_id, vollem Config-Body) → `{"result": "ok"}` |
| Top-Level `condition: state` | **Ganze** Choose-Block wird übersprunge |

## User Preference: Alles nativ i HA

**Nie externi Sync-Cron/Bridge-Scripts uf Hermes/Nova.** Alli Bridges, Syncs, Sensor-Kopien ghöred nativ i HA (Automatione, Template-Sensors, Helper).

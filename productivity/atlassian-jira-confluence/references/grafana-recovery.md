# Grafana Password Recovery & Provisioning (Goetschi Labs CT110)

## Situation
Grafana läuft als Docker-Container auf CT110 (10.0.60.110:3000). Das Admin-Passwort wurde bei Erstanmeldung geändert und nirgends dokumentiert. Der `grafana-cli` Befehl zum Reset existiert im aktuellen grafana/grafana:latest Image **nicht** im PATH.

## Workaround: SQLite-DB + frischer Container

### Schritt 1: Grafana-Container stoppen
```bash
# Auf pve01:
sshpass -p "Riotstar_PROXMOX_13" ssh root@10.0.60.10
pct exec 110 -- docker stop grafana
```

### Schritt 2: DB lokal sichern
```bash
pct exec 110 -- docker cp grafana:/var/lib/grafana/grafana.db /tmp/grafana.db.backup
```

### Schritt 3: Container löschen + neu starten MIT ENV-Passwort
```bash
pct exec 110 -- docker rm grafana
pct exec 110 -- docker run -d \
  --name grafana \
  --restart unless-stopped \
  -p 3000:3000 \
  -e 'GF_SECURITY_ADMIN_USER=admin' \
  -e 'GF_SECURITY_ADMIN_PASSWORD=*** \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana:latest
```

**Wichtig:** Das Volume `grafana-storage` muss existieren (wird automatisch erstellt).  
**⚠️ `GF_SECURITY_ADMIN_PASSWORD`** funktioniert nur beim **ersten Start** eines frischen Containers.  
Wenn das Volume bereits eine `grafana.db` mit User-Tabelle enthält, wird das ENV-Passwort **ignoriert**.

### Schritt 4: Login testen
```bash
# Warten bis Container up ist (~15s)
pct exec 110 -- curl -s -X POST http://localhost:3000/login \
  -H 'Content-Type: application/json' \
  -d '{"user":"admin","password":"admin"}'
# Erwartet: {"message":"Logged in","redirectUrl":"/"}
```

### Schritt 5: Service Account anlegen (API-Key)
```bash
# Login → Cookie holen
pct exec 110 -- curl -s -c /tmp/grafana_cookies.txt -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"admin"}'

# Cookie auslesen
COOKIE=$(grep grafana_session /tmp/grafana_cookies.txt | awk '{print $NF}')

# Service Account erstellen
pct exec 110 -- curl -s -X POST http://localhost:3000/api/serviceaccounts \
  -H "Content-Type: application/json" \
  -b "grafana_session=$COOKIE" \
  -d '{"name":"Hermes-Admin","role":"Admin"}'

# Token für den Service Account generieren
pct exec 110 -- curl -s -X POST "http://localhost:3000/api/serviceaccounts/2/tokens" \
  -H "Content-Type: application/json" \
  -b "grafana_session=$COOKIE" \
  -d '{"name":"Hermes-Admin-Token"}'
# Erwartet: {"id":1,"name":"Hermes-Admin-Token","key":"glsa_XXXX_YYYY"}
```

### Schritt 6: Datasources provisionieren (via API)
```python
import urllib.request, json

TOKEN="glsa_..."  # aus Schritt 5
GRAFANA_URL="http://10.0.60.110:3000"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

datasources = [
    {"name": "Prometheus", "type": "prometheus", "url": "http://localhost:9090", "access": "proxy", "isDefault": True},
    {"name": "Loki", "type": "loki", "url": "http://localhost:3100", "access": "proxy"},
    {"name": "InfluxDB", "type": "influxdb", "url": "http://10.0.60.109:8086", "access": "proxy", "database": "trading", "jsonData": {"httpMode": "GET"}}
]

for ds in datasources:
    req = urllib.request.Request(
        f"{GRAFANA_URL}/api/datasources",
        data=json.dumps(ds).encode(), headers=HEADERS, method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        print(f"✅ {ds['name']}: added")
    except Exception as e:
        print(f"⚠️ {ds['name']}: {e}")
```

## Key Differences from Old Grafana Versions
- **Grafana v11+** verwendet Service Accounts statt API Keys (`/api/auth/keys` → 404/Not Found)
- **`grafana-cli`** ist nicht im PATH des Containers enthalten (kein `grafana-cli admin reset-admin-password`)
- **Service Accounts** werden unter `/api/serviceaccounts` erstellt, **Token** unter `/api/serviceaccounts/{id}/tokens`
- **SQLite-Hash manipuliert funktioniert NICHT** — `attempt to write a readonly database` (Volume-Rechte im Docker-Container)

## Prevention
- Grafana-Credentials SOFORT nach erstem Login in Confluence dokumentieren
- Oder `GF_SECURITY_ADMIN_PASSWORD` in der docker-compose.yml hinterlegen
- Service-Account-Token als Fallback generieren und in Confluence-Seite "System-Credentials & Endpunkte" eintragen

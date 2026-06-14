---
name: unifi-network
description: "UniFi Network Controller API (UDM Pro) — Clients verwalten, VLANs ändern, DNS konfigurieren, mDNS Gateway, Netzwerke abfragen, Security-Incident-Triage."
version: 1.1.0
created_by: agent
status: active
---

# UniFi Network Controller API (UDM Pro)

## Übersicht

Verwaltung der UniFi Network Controller API auf einem UDM Pro (10.0.60.1). Für Client-Management, VLAN-Änderungen, DNS-Konfiguration und Netzwerk-Inspektion.

## Credentials

- **Host:** `https://10.0.60.1` (default gateway, Server-VLAN) — alternativ Manager-VLAN `10.0.10.1` falls nöd erreichbar
- **User:** `hassio`
- **Password:** `Riotstar_MICHEL_13`
- **API Base:** `/proxy/network/api/s/default/`

## Authentifizierung

### Login + CSRF Token

Der UDM Pro braucht CSRF-Token für Schreib-Operationen (PUT/POST/DELETE). Der CSRF-Token steckt im JWT-Cookie:

```bash
# 1. Login → Cookie speichern
curl -sk -X POST "https://10.0.60.1/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"hassio","password":"Riotstar_MICHEL_13"}' \
  -c /tmp/unifi_cookies.txt

# 2. CSRF aus Cookie extrahieren
CSRF=$(cat /tmp/unifi_cookies.txt | grep -oP 'csrftoken":{"([^"]+)"' | sed 's/.*"\(.*\)"/\1/' || \
       python3 -c "import base64,json; import sys; c=open('/tmp/unifi_cookies.txt').read(); t=next(l for l in c.split('\n') if 'TOKEN' in l and 'eyJ' in t.split()[-1]); p=t.split()[-1].split('.')[1]; p+='='*(4-len(p)%4); d=json.loads(base64.b64decode(p)); print(d['csrftoken'])")

# 3. CSRF für Schreib-Operationen mitgeben
curl -sk -X PUT "https://10.0.60.1/proxy/network/api/s/default/rest/user/{id}" \
  -b /tmp/unifi_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{"...": "..."}'
```

**Alternative — CSRF direkt aus Cookie parsen:** Der JWT liegt im TOKEN-Cookie als Base64. Mittelteil dekodieren → `csrftoken`-Feld.

**Alternative 2 — CSRF aus Login-Response-Header:** Der UDM Pro gibt das `X-CSRF-Token` auch direkt im Response-Header des Login-Endpunkts zurück. Damit entfällt das JWT-Parsing:

```bash
CSRF=$(curl -sk -X POST "https://10.0.60.1/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"hassio","password":"Riotstar_MICHEL_13"}' \
  -c /tmp/unifi_cookies.txt \
  -D - 2>/dev/null | grep -i 'x-csrf-token' | tr -d '\r' | cut -d' ' -f2)

# In Python:
r = httpx.post(f"{UNIFI_HOST}/api/auth/login", ...)
csrf = r.headers.get("x-csrf-token", "")
```

## Wichtige API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/api/auth/login` | POST | Login (setzt TOKEN-Cookie + gibt `X-CSRF-Token` im Response-Header) |
| `/proxy/network/api/s/default/stat/sta` | GET | **Aktive (online) Clients** — Live-Verbindungen (nur was gerade aktiv ist) |
| `/proxy/network/api/s/default/stat/alluser` | GET | **Alle bekannten Clients** (auch offline). Liefert `last_ip`, `is_wired`, `last_uplink_name`. Primäre Quelle für Client-Suche `_id` |
| `/proxy/network/api/s/default/rest/user/{id}` | GET/PUT | Client-Konfiguration ändern (Name, Fixed IP, Network Override). ID aus `stat/alluser.data[]._id` |
| `/proxy/network/api/s/default/rest/networkconf` | GET | Alle Netzwerke/VLANs |
| `/proxy/network/api/s/default/rest/networkconf/{id}` | PUT | Netzwerkkonfiguration ändern |
| `/proxy/network/api/s/evtmgr/conf` | GET | mDNS Gateway-Konfiguration |
| `/proxy/network/api/s/evtmgr/conf` | PUT | mDNS Gateway-Konfiguration ändern |
| `/proxy/network/api/s/default/rest/setting/mgmt` | GET | Device-Management Settings |

## Client in anderes VLAN verschieben (Network Override)

Ein Client behält dieselbe SSID, kriegt aber eine IP aus einem anderen VLAN. **Perfekt für: Gerät im falschen VLAN ohne WLAN-Wechsel.**

### Schritt-für-Schritt

```bash
# 1. Client finden (MAC oder IP)
CLIENT_MAC="40:aa:56:05:57:75"
CLIENT=$(curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/alluser" \
  -b /tmp/unifi_cookies.txt | python3 -c "
import sys, json
data = json.load(sys.stdin)
for c in data.get('data',[]):
    if c.get('mac') in ['$CLIENT_MAC']:
        print(json.dumps(c,indent=2))
        break
")

# 2. Ziel-VLAN-ID ermitteln
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/networkconf" \
  -b /tmp/unifi_cookies.txt | python3 -c "
import sys, json
for n in json.load(sys.stdin).get('data',[]):
    print(f\"{n['name']}: ID={n['_id']}, VLAN={n.get('vlan','')}, Subnet={n.get('ip_subnet','')}\")
"

# 3. Client-Override setzen
curl -sk -X PUT "https://10.0.60.1/proxy/network/api/s/default/rest/user/{CLIENT_ID}" \
  -b /tmp/unifi_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{
    "virtual_network_override_enabled": true,
    "virtual_network_override_id": "657a3354269bb2051d3c0b49",
    "fixed_ip": "10.0.10.86",
    "use_fixedip": true,
    "name": "philips tv"
  }'
```

### Wichtige Felder

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `virtual_network_override_enabled` | bool | `true` = Override aktivieren |
| `virtual_network_override_id` | string | ID des Ziel-Netzwerks (aus networkconf) |
| `use_fixedip` | bool | Feste IP vergeben (optional) |
| `fixed_ip` | string | IP im Ziel-VLAN (nur wenn use_fixedip=true) |
| `name` | string | Anzeigename im Controller |

### Effekt

- Client bleibt auf **derselben SSID**
- UniFi routet den Traffic ins andere VLAN
- Client kriegt neue IP per DHCP beim nächsten Reconnect
- Kein WLAN-Wechsel nötig!

### ⚠️ Wichtige Einschränkung: Network Override für das Default Corporate Network

**Network Override kann NICHT auf das Default Corporate Network als Ziel setzen.** 

Wenn du versuchst, einen Client via Override in das Default-Netz (`purpose=corporate`, `is_nat=True`, meist Management/Infra) zu verschieben, schlägt der PUT fehl mit:

```
api.err.VirtualNetworkOverrideUnsupportedForDefaultNetwork
```

Das Default-Netz erlaubt keine `virtual_network_override` als Ziel — unabhängig von den API-Credentials. Das gilt sowohl für WiFi- als auch für wired Clients.

**Um einen Client ins Default Corporate Network zu verschieben, Alternativen:**
1. **Separate SSID erstellen** — Ein neues WLAN auf dem Ziel-VLAN aufsetzen und das Gerät dort anmelden
2. **MAC-basierte VLAN-Zuweisung (RADIUS)** — Den Client per MAC-Adresse automatisch in das gewünschte VLAN routen
3. **Wenn der Client wired ist:** Switch-Port-VLAN ändern (auf dem Port das Ziel-VLAN setzen)

**Wichtig:** Network Override VOM Default-Netz WEG (also einen Client der auf dem Default ist in ein anderes VLAN zu schieben) funktioniert problemlos. Das Problem tritt NUR auf, wenn das Default-Netz das ZIEL ist.

### Network Override rückgängig machen

`virtual_network_override_enabled: false` setzen → Client fällt zurück auf SSID-Standard-VLAN.
# 1. Netzwerk-IDs holen
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/networkconf" \
  -b /tmp/unifi_cookies.txt

# 2. DNS ändern (z.B. auf AdGuard 10.0.60.111)
curl -sk -X PUT "https://10.0.60.1/proxy/network/api/s/default/rest/networkconf/{NET_ID}" \
  -b /tmp/unifi_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{
    "dhcpdns": ["10.0.60.111", "1.1.1.1"],
    "dhcpdns_enabled": true,
    "name": "IOT"
  }'
```

**Rollback-Backup:** Vor DNS-Änderungen die aktuelle Config sichern:
```bash
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/networkconf" \
  -b /tmp/unifi_cookies.txt > /tmp/unifi_dns_backup.json
```

## 📡 WLAN-Optimierung (Best Practice nach IT-Ion/UniFi-Experten)

### 🔍 Scan-Cheatsheet (alles uf ei Blick)

```bash
COOKIE=/tmp/unifi_cookies.txt
curl -sk -X POST "https://10.0.60.1/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"hassio","password":"Riotstar_MICHEL_13"}' -c "$COOKIE"

# Alli relevante WLAN-Parameter
curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/device" -b "$COOKIE" \
  | python3 -c "
import sys,json
for ap in json.load(sys.stdin)['data']:
    if 'UAP' in ap.get('model',''):
        n=ap.get('name','?'); print(f'=== {n} ===')
        for r in ap.get('radio_table',[]):
            b=r.get('radio','?'); ch=r.get('channel','?')
            bw=r.get('ht','?'); tx=r.get('tx_power_mode','?')
            ut=r.get('utilization','?'); cl=r.get('sta_count',r.get('user_num','?'))
            print(f'  {b:8s} ch={ch:4s} bw={bw:3s}MHz TX={tx:10s} util={ut}% clients={cl}')
"

# Roaming-Estellige
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/wlanconf" -b "$COOKIE" \
  | python3 -c "
import sys,json
for w in json.load(sys.stdin)['data']:
    if not w.get('enabled'): continue
    print(f'{w.get(\"name\",\"?\"):25s} FastR={w.get(\"fast_roaming_enabled\"):5s} BSST={w.get(\"bss_transition\"):5s} MinRate={w.get(\"min_data_rate\",\"?\")}')
"

# Band-Verteilig
curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/sta" -b "$COOKIE" \
  | python3 -c "
import sys,json
cl=json.load(sys.stdin).get('data',[]); by_band={}
for c in cl: b=c.get('radio','?'); by_band[b]=by_band.get(b,0)+1
print(f'Total: {len(cl)} | ' + ' | '.join(f'{b}: {c}' for b,c in sorted(by_band.items())))
"

# Health
curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/health" -b "$COOKIE" \
  | python3 -c "
import sys,json
for h in json.load(sys.stdin)['data']:
    s=h.get('subsystem','?'); st=h.get('status','?')
    if s in ['wan_1','www','wlan','lan']: print(f'{s:10s} = {st}')
"
```

### Kanalbreite (Channel Width)

| Band | Empfehlig | API-Feld |
|------|-----------|----------|
| **2.4 GHz** | **20 MHz** (fix) | `radio_table[].ht: 20` |
| **5 GHz** | **80 MHz** — freiends Hus | `radio_table[].ht: 80` |
| **5 GHz** | **40 MHz** — dichti Lag/MFH | `radio_table[].ht: 40` |
| **5 GHz 160 MHz** | **NICHT empfohle** | `has_ht160` prüefe |
| **6 GHz** (WiFi 6E/7) | **160-320 MHz** | — |

### Sendeleistung (TX Power)

**⛔ Nie Auto, nie High — immer Medium** bi mehrere APs.

Grund: WLAN isch e **Gegenstrooss** → AP brüellt, Client flüstert. Z'hoche TX füert zu Asymmetrie + Störig zwüsche APs.

| Szenario | Empfehlig | API-Feld |
|----------|-----------|----------|
| **Mehreri APs** (2+) | **Medium** | `tx_power_mode: "medium"` |
| **Einzel-AP, grossi Fläche, kei Nachbere** | **High** | `tx_power_mode: "high"` |
| Default | **Nie Auto** | `tx_power_mode: "auto"` ✗ |

### Kanalauswahl (Channel Selection)

**Immer manuell** — Auto-Algorithmus reagiert z'träg.

- **2.4 GHz** → **1, 6, 11** (nöd überlappend)
- **5 GHz** → **DFS-Kanäle 52-144** bevorzuge (weniger Nachbere). Usnahm: Flughafe-/Radarnächi.

### Roaming (Fast Roaming + BSS Transition)

| Feature | API-Feld | Empfehlig |
|---------|----------|-----------|
| **Fast Roaming (802.11r)** | `fast_roaming_enabled: true` | **ON** |
| **BSS Transition** | `bss_transition: true` | **ON** |

Pitfall: Sehr alti Gerät (vor ~2015) chönd mit 802.11r Problemer ha → für die SSID deaktiviere.

### Minimum Data Rate

Zwängt schwach verbundni Gerät zum nähere AP z'roame.

| Startwert | Beschrieb |
|-----------|-----------|
| **12 Mbps** | Guet für die meiste Setups |
| **24 Mbps** | Nur wenn alli Endgerät modern |

### Wichtigi API-Feldnäme (Radio Config)

| Funktion | Feld | Wert |
|----------|------|------|
| Kanalbreite | `radio_table[].ht` | `20`, `80`, `40` |
| Kanal | `radio_table[].channel` | Kanalnummer |
| TX Power Modus | `radio_table[].tx_power_mode` | `"medium"` (nie auto/high) |
| Auslastig | `radio_table[].utilization` | Prozent (read-only) |
| Max TX | `radio_table[].max_txpower` | dBm (read-only) |
| NSS (MIMO) | `radio_table[].nss` | 2=ng, 4=na (read-only) |

### WLAN Config (wlanconf) Felder

| Funktion | Feld | Wert |
|----------|------|------|
| Fast Roaming | `fast_roaming_enabled` | `true`/`false` |
| BSS Transition | `bss_transition` | `true`/`false` |
| Min Data Rate | `min_data_rate` | `12000` (12 Mbps, in kbps!) |
| PMF | `pmf_mode` | `"disabled"`/`"optional"`/`"required"` |

**⚠️ `min_data_rate` isch in kbps** — 12 Mbps = `12000`, 24 Mbps = `24000`.

### Radio AI (Automatic Channel Optimization)

Der UDM Pro hat en **Radio AI**-Feature wo automatisch Kanäl und Kanalbreite managet:

```bash
# Status prüfe
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/setting/radio_ai" \
  -b "$COOKIE" | python3 -c "
import sys,json
d=json.load(sys.stdin)['data'][0]
print(f\"Enabled: {d.get('enabled')}\")
print(f\"Optimize: {d.get('optimize')}\")
print(f\"Schedule: {d.get('cron_expr')}\")
print(f\"2.4GHz channels: {d.get('channels_ng')} (BW: {d.get('ht_modes_ng')})\")
print(f\"5GHz channels: {d.get('channels_na')} (BW: {d.get('ht_modes_na')})\")
print(f\"Radios: {d.get('radios_configuration')}\")
"
```

**Wichtigi Felder im Radio AI Config:**

| Feld | Bedeutung | Typisch |
|------|-----------|---------|
| `enabled` | Radio AI aktiv | `true`/`false` |
| `optimize` | Was optimiert wird | `["channel"]` (nur Kanal) |
| `channels_ng` | Erlaubti 2.4GHz Kanäl | `["1","6","11"]` |
| `channels_na` | Erlaubti 5GHz Kanäl | `["56","60","64","100","104",...]` (DFS) |
| `ht_modes_ng` | Erlaubti 2.4GHz Breite | `["20"]` |
| `ht_modes_na` | Erlaubti 5GHz Breite | `["20","40","80"]` |
| `channels_blacklist` | Blacklisteti Kanäl pro Band | Liste vo `{channel, channel_width, radio}` |
| `radios_configuration` | Default-Kanalbreite + DFS pro Band | z.B. `[{"radio":"ng","channel_width":20,"dfs":false},...]` |
| `cron_expr` | Schedule | `"0 3 * * *"` (nacht um 3 Uhr) |
| `auto_channel_presets_type` | Optimierungsziel | `"maximum_speed"`/`"minimize_interference"` |

**⚠️ Radio AI überschriebt manuelli Kanäle!** Wenn Radio AI `enabled: true` isch, wärde manuelli `channel`-Setzige im `radio_table` vo `stat/device` ignoriert. Zum manuell chantere: Radio AI deaktiviere (`enabled: false`, `optimize: []`), Config speichere, AP reboote.

**👉 Radio AI grundsätzlich ON LOH!** De Michel het explizit gseit, dass Radio AI blibe söll. Radio AI macht gueti DFS-Kanalwahl + vermeidet au Overlapping. Nur deaktiviere wenn:
- Manuelli Kanalbelegung zwingend nötig isch
- Spezifischi Probleme mit DFS (Radar, Flughafe-Nächi)

**Radio AI deaktiviere:**
```bash
curl -sk -X PUT "https://10.0.60.1/proxy/network/api/s/default/rest/setting/radio_ai" \
  -b "$COOKIE" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -d '{"enabled": false, "optimize": []}'
```

**Radio AI reaktiviere:**
```bash
curl -sk -X PUT "..." -d '{"enabled": true, "optimize": ["channel"]}'
```

### ⚠️ TX Power setze — API-Grenze

De `tx_power_mode` KANN per API gsetzt wärde, ABER d'Änderig wird UDM-seitig nöd immer uf d'APs propagiert:

```bash
# Via setdeviceconfig (cmd/devmgr) — funktioniert z.T.
curl -sk -X POST "https://10.0.60.1/proxy/network/api/s/default/cmd/devmgr" \
  -b "$COOKIE" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -d '{"cmd":"setdeviceconfig","mac":"<MAC>","radio_table":[{"radio":"ng","channel":"6","ht":"20","tx_power_mode":"medium"},{"radio":"na","channel":"100","ht":"80","tx_power_mode":"medium"}]}'

# Via rest/device/{_id} mit radio_table — retourniert rc:ok aber AP ignoriert's oft
curl -sk -X PUT "https://10.0.60.1/proxy/network/api/s/default/rest/device/{_id}" \
  -b "$COOKIE" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -d '{"radio_table":[{"radio":"ng","tx_power_mode":"medium"},{"radio":"na","tx_power_mode":"medium"}]}'
```

**Praktischi Limitation:** Auf däm UDM Pro (UniFi OS) laht sich TX Power via API NUR über d'GUI zverlässig setze. D'API retourniert `rc: ok` aber d'APs ignoriere d'Config. Wenn Michel explizit TX = Medium wot, im GUI: *Radios > Sendeleistung*.

### Client-Band-Verteilig prüfe

Wichtig für Optimierig: Wievili Clients händ sich uf 2.4GHz vs 5GHz verbunde?

```bash
curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/sta" \
  -b "$COOKIE" | python3 -c "
import sys,json
cl=json.load(sys.stdin).get('data',[])
by_band={}
for c in cl:
    b=c.get('radio','?')
    by_band[b]=by_band.get(b,0)+1
print(f'Total: {len(cl)} | ' + ' | '.join(f'{b}: {c}' for b,c in sorted(by_band.items())))
"
```

Optimale Verteilig: **Mindestens 50% uf 5GHz** — 2.4GHz isch überlade (nur 3 non-overlapping Kanäl). Falls z'vili uf 2.4GHz: Band Steering aktiviere oder TX Power uf 5GHz erhöhe.`

### References

- `references/wlan-optimization.md` — Vollständigi Scan-Checkliste

Für **Cross-VLAN Service Discovery** (z.B. Hue Bridge in V10, TV in V20 soll sie finden):

```bash
# Aktuelle Konfiguration
curl -sk "https://10.0.60.1/proxy/network/api/s/evtmgr/conf" \
  -b /tmp/unifi_cookies.txt | python3 -m json.tool

# mDNS Gateway aktivieren für bestimmte VLANs
# Felder: enabled_for_network_ids (Liste der Netzwerk-IDs wo mDNS durchgereicht wird)
```

## Geräte auf Switch-Ports finden (Wired Clients)

Wichtig für: **Hue Bridge im falschen VLAN**, Geräte die physisch an einem bestimmten Switch-Port hängen.

```bash
# Alle aktiven Clients + deren Switch-Port
curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/sta" \
  -b /tmp/unifi_cookies.txt | python3 -c "
import json, sys
data = json.load(sys.stdin)['data']
for s in data:
    if s.get('is_wired'):
        print(f'{s.get(\"mac\",\"?\")} ({s.get(\"hostname\",\"?\")}) → {s.get(\"last_uplink_name\",\"?\")} Port {s.get(\"sw_port\",\"?\")}')
"
```

**Oder für ein spezifisches Gerät:** `.stat/alluser`-Endpoint liefert auch offline Clients mit `last_uplink_mac` und `sw_port`. Damit auch Geräte die aktuell offline sind aber mal verbunden waren.

## Switch-Port-Konfiguration ändern (Port Override)

Wenn ein **verkabeltes** Gerät ein anderes VLAN braucht (z.B. Hue Bridge von Management in Client-VLAN verschieben):

### Port-Override prüfen

```bash
curl -sk "https://10.0.60.1/proxy/network/api/s/default/stat/device" \
  -b /tmp/unifi_cookies.txt | python3 -c "
import json, sys
data = json.load(sys.stdin)
for dev in data.get('data', []):
    if 'US' in dev.get('model','') or 'SW' in dev.get('model',''):
        print(f\"Switch: {dev.get('name','?')} ({dev.get('model','?')})\")
        for po in dev.get('port_overrides', []):
            pidx = po.get('port_idx','?')
            net = po.get('native_networkconf_id','?')
            print(f\"  Port {pidx}: native_networkconf_id={net}\")
"
```

### Port 3 auf Client-VLAN umstellen

```bash
DEVICE_ID="<aus stat/device>"
CLIENT_NET_ID="<aus rest/networkconf>"
CSRF="<aus Cookie/JWT>"

# Port-Override per REST-Device-PUT setzen
curl -sk -X PUT "https://10.0.60.1/proxy/network/api/s/default/rest/device/$DEVICE_ID" \
  -b /tmp/unifi_cookies.txt -b "csrf_token=$CSRF" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{
    "port_overrides": [
      {
        "port_idx": 3,
        "native_networkconf_id": "'"$CLIENT_NET_ID"'",
        "setting_preference": "auto"
      }
    ]
  }'
```

**⚠️ Pitfalls:**
- Der `rest/device/{id}`-Endpoint gibt nach dem PUT `rc: ok` zurück, liefert aber in GET **immer leeres `data: []`** — das ist normal, nicht prüfbar via REST. Verwende `stat/device` für die Laufzeit-Konfiguration (Running State).
- Nach dem Port-Override muss das Gerät **neu verbinden** (Link-Down/Link-Up) → Strom ziehen oder Kabel kurz trennen.
- Für wired Clients **statt Switch-Port-Änderung**: `virtual_network_override` am Client setzen (s.o.) — weniger disruptiv, funktioniert für UniFi-switched VLANs.

## IGMP Snooping & Multicast-Konfiguration (Cross-VLAN Discovery)

Wenn Geräte über VLAN-Grenzen hinweg per **SSDP/UPnP/mDNS** kommunizieren müssen (z.B. Philips TV findet Hue Bridge nicht, weil sie in verschiedenen VLANs sind):

### Aktuelle IGMP-Konfiguration prüfen

```bash
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/setting/igmp_snooping" \
  -b /tmp/unifi_cookies.txt | python3 -c "
import json, sys
d = json.load(sys.stdin)['data'][0]
print(f'forward_unknown_mcast_router_ports: {d.get(\"forward_unknown_mcast_router_ports\")}')
print(f'flood_known_protocols: {d.get(\"flood_known_protocols\")}')
print(f'flood_unknown_multicast: {d.get(\"flood_unknown_multicast_for_network_ids\")}')
"
```

### IGMP Multicast-Flood aktivieren (für SSDP/UPnP über VLANs)

```bash
# Netzwerk-IDs der beteiligten VLANs holen
curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/networkconf" \
  -b /tmp/unifi_cookies.txt | python3 -c "
import json, sys
for n in json.load(sys.stdin).get('data', []):
    print(f\"{n['name']:30s} → _id={n['_id']}, VLAN={n.get('vlan','native')}\")
"

# IGMP-Snooping aktualisieren (SSDP Multicast flooden)
CSRF=\"<aus Cookie/JWT>\"
curl -sk -X PUT \
  "https://10.0.60.1/proxy/network/api/s/default/rest/setting/igmp_snooping" \
  -b /tmp/unifi_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{
    "forward_unknown_mcast_router_ports": true,
    "flood_known_protocols": true,
    "flood_unknown_multicast_for_network_ids": [
      "NET_ID_VLAN_A",
      "NET_ID_VLAN_B"
    ]
  }'
```

**⚠️ Pitfalls (real-world tested):**
- ❌ **IGMP-Flooding allein reicht NICHT** für SSDP-Discovery über VLANs — die IGMP Snooping-Änderungen werden vom UDM propagiert, aber SSDP Multicast kommt trotzdem nicht bei Geräten im anderen VLAN an.
- ❌ `flood_unknown_multicast_for_network_ids` + `forward_unknown_mcast_router_ports: true` haben **keine nachweisbare Wirkung** auf SSDP (239.255.255.250:1900) zwischen VLANs gezeigt.
- ❌ Auch der **mDNS Gateway** im UDM (evtmgr/conf) ist kein Allheilmittel — er reflectiert nur mDNS, nicht SSDP/UPnP.
- ✅ **Zuverlässigste Lösung:** Geräte **ins gleiche VLAN** verschieben (Port-Override am Client oder Switch-Port-Änderung).
- Nach IGMP-Änderungen kann es **bis zu mehreren Minuten** dauern bis der UDM die Config propagiert hat.
- `forward_unknown_mcast_router_ports: true` kann Load auf Switches erhöhen. Auf `false` zurücksetzen wenn nicht mehr benötigt.

### 🏆 SSDP Proxy Workaround (wenn VLAN-Änderung nicht möglich)

Wenn Geräte nicht umziehen können/sollen, aber per SSDP/UPnP über VLANs hinweg kommunizieren müssen, hilft ein **Python SSDP-Proxy** auf einem Host der beide VLANs erreicht (z.B. Hermes-Container mit Zugriff auf alle Netze):

**Ansatz 1 — Passiver SSDP-Proxy** (hört auf M-SEARCH, antwortet als falscher Bridge):
```bash
# Läuft als Background-Prozess: python3 /opt/data/home/ssdp-proxy.py
```

**Ansatz 2 — Aktiver NOTIFY-Broadcaster** (sendet SSDP NOTIFY alive an alle VLANs):
```python
TARGETS = [
    ("10.0.0.255", 1900),    # Management broadcast
    ("10.0.10.255", 1900),   # Client broadcast
    ("10.0.20.255", 1900),   # IoT broadcast
    ("10.0.60.255", 1900),   # Server broadcast
    ("10.0.10.86", 1900),    # Direkt zum TV (altes IP)
    ("239.255.255.250", 1900), # SSDP Multicast
]
```

**⚠️ Hinweise zum SSDP-Proxy:**
- Der Proxy läuft auf **172.18.0.x (Hermes-Container)** — die NOTIFYs gehen über die Host-Netzwerkbrücke, ob sie im Ziel-VLAN ankommen hängt von der Switch-Konfiguration ab
- **Kombiniere beide Ansätze** (Proxy + NOTIFY) für maximale Erfolgschance
- Die Scripts liegen unter `scripts/ssdp-proxy.py` und `scripts/ssdp-notify.py` im Skill-Verzeichnis
- Verwende die **Cron-Job-Funktion** (`cronjob create`) um den NOTIFY-Broadcaster regelmäßig auszuführen (z.B. alle 60 Sekunden): `hermes cron ssdp-notify --schedule '*/1 * * * *'`
- **Letzter Ausweg:** Trotzdem nicht genug? Gerät physisch umstecken (Hue Bridge an Switch-Port im IoT-VLAN) und HA-Hue-Integration neu konfigurieren.

### References

- `references/cross-vlan-troubleshooting.md` — Troubleshooting pattern for devices that can't discover each other across VLANs (Philips TV + Hue Bridge use case)

### Scripts

- `scripts/ssdp-proxy.py` — Passiver SSDP-Proxy: hört auf 0.0.0.0:1900, antwortet auf M-SEARCH mit der Hue Bridge Location (http://10.0.0.190:80/description.xml)
- `scripts/ssdp-notify.py` — Aktiver SSDP-NOTIFY-Broadcaster: sendet unsolicited SSDP alive an alle VLAN-Broadcast-Adressen + TV-Unicast-IPs + SSDP-Multicast

## Nützliche Python-Helfer (für Hermes-Automation)

```python
import httpx, json, base64

UNIFI_HOST = "https://10.0.60.1"
UNIFI_USER = "hassio"
UNIFI_PASS = "Riotstar_MICHEL_13"

def unifi_login():
    """Login und CSRF extrahieren"""
    r = httpx.post(f"{UNIFI_HOST}/api/auth/login",
        json={"username": UNIFI_USER, "password": UNIFI_PASS},
        verify=False)
    
    # CSRF aus JWT extrahieren
    token = r.cookies.get("TOKEN", "")
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.b64decode(payload_b64))
    csrf = payload.get("csrftoken", "")
    
    return r.cookies, csrf

def unifi_get(path, cookies):
    return httpx.get(f"{UNIFI_HOST}/proxy/network/api/s/default/{path}",
        cookies=cookies, verify=False)

def unifi_put(path, data, cookies, csrf):
    return httpx.put(f"{UNIFI_HOST}/proxy/network/api/s/default/{path}",
        json=data, cookies=cookies,
        headers={"X-CSRF-Token": csrf}, verify=False)

def find_client(mac_or_ip, cookies):
    """Client-Details anhand MAC oder IP finden"""
    data = unifi_get("stat/alluser", cookies).json()
    for c in data.get("data", []):
        if c.get("mac") == mac_or_ip or c.get("fixed_ip") == mac_or_ip or c.get("last_ip") == mac_or_ip:
            return c
    return None
```

## 🔐 Security Incident Analysis

Wenn de Michel meldet: **«Angriff», «Attacke», «Hacker»** — das Triage-Protokoll.

### Triage-Workflow

1. **📧 Gmail prüefe** — Such uf Wordfence-Rapport & UDM Pro-Alerts
   - Wordfence weekly report: suche neui Mail vo noreply@wordfence.com
   - UDM Pro alerts: suche `is:unread from:noreply@notifications.ui.com` in Michels Gmail (mich **muesch** Gmail MCP tool bruuche, nid hermes@radislione.net IMAP!)
2. **🔍 UDM Threat-Mail analysiere** — Inhalt genau läse: was isch Source und Destination?
   - **MAC statt IP?** D'Alert-Mail zeigt MAC-Adressen, nid IPs. UDM zeigt nur die letschte 4 Hex-Stelle (z.B. `7b:d7`) — die volli MAC findsch im UDM Pro.
   - **Self-Targeting (gleichi MAC)?** `"from Workstation X to Workstation X"` = False Positive. Source und Destination sind identisch → Broadcast/Loopback, kei echte Angriff.
   - **External IP?** Wenn e externi IP als Source erwähnt wird (z.B. `45.9.168.16`) → echte IPS-Meldig. IP über ipinfo.io prüefe.
   - **Internal IP zu internal IP?** Möglicherweise legitimer Traffic (z.B. HA → Server). Immer prüefe obs e bekannte Service isch.
3. **🔎 UDM Pro-Login + Client identifiziere** (bei MAC-Threats)
   ```bash
   # Login + Client anhand MAC (oder Teil-MAC) in rest/user finde
   curl -sk -X POST "https://10.0.60.1/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"hassio","password":"Riotstar_MICHEL_13"}' \
     -c /tmp/unifi_cookies.txt
   curl -sk "https://10.0.60.1/proxy/network/api/s/default/rest/user" \
     -b /tmp/unifi_cookies.txt | python3 -c "
   import json,sys; d=json.load(sys.stdin)
   for u in d.get('data',[]):
       if '7b:d7' in u.get('mac','').lower():  # Teil-MAC suchen
           print(f'{u[\"mac\"]}  {u.get(\"hostname\",\"?\")}  {u.get(\"fixed_ip\",u.get(\"last_ip\",\"?\"))}')
           print(f'OUI: {u.get(\"oui\",\"?\")}  OS: {u.get(\"os_name\",\"?\")}  WLAN: {u.get(\"last_uplink_name\",\"?\")}')
           print(f'First seen: {u.get(\"first_seen\",\"?\")}  Last seen: {u.get(\"last_seen\",\"?\")}')
   "
   ```
   - OUI (f0:57:a6 = Intel Corporate) → Hersteller vode Netzwerkkarte
   - `dev_cat`, `dev_family`, `os_name` → Gerätetyp (PC, Smartphone, IoT)
   - `is_wired`/`last_uplink_name` → Wo hänge? (WLAN AP oder Switch-Port)
   - `first_seen`/`last_seen` → Timestamps arechene
   - `last_ip` → IP im aktuelle VLAN
4. **🌐 Wordfence-Daten analysiere** (für moto-poschung.ch)
   - Blockierti IPs: IP + Herkunftsland + Blockcount
   - Failed Logins: Username + Count → Brute-Force oder Bots?
   - Security-Updates: Plugins/Themes mit Security-Fix → DRINGEND iispielbar
   - Recently Blocked: Datum + IP + Grund
5. **🌐 UniFi-Netzwerk-Check** (für s'Homelab)
   - Health: `stat/health` → WAN/www/WLAN/LAN Status
   - Firewall: Firewall-Regle prüefe (0 Regle = default)
   - Port-Forwarding: Nur nötigi Ports offe (SIP + RTP)
   - Active Clients: `stat/sta` → suspekti MACs? Alli bekannt?
   - IPS/IDS: Modus prüefe (`ids` vs `ips`)
6. **🧠 Querverbindig mache**
   - Externi Angriff (Wordfence) vs interni (UniFi)
   - moto-poschung.ch isch **extern gehosted** → ghört nöd zum Homelab
   - Homelab isch **sauber** wenn kei suspekti Clients + Port-Forwards minimal

### False-Positive-Heuristik (UDM Pro IPS)

| Muster | Bewertung | Begründig |
|--------|-----------|-----------|
| Source MAC = Destination MAC (gleichi MAC) | **False Positive 🟢** | Self-Targeting = Broadcast/Loopback. UDM IPS interpretiert Windows-Broadcasts fälschlich als Intrusion. |
| External IP (45.x, 185.x, etc.) | **Potenzielle echte Meldung 🟡** | IP via ipinfo.io prüefe. Oft CDN-Scanner oder Shodan-Bots. |
| Internal IP → Internal IP (verschidni VLANs) | **Beobachte 🟠** | Könnt legitimer Traffic si (HA, Monitoring). Nur wenn seltsams Muster → Ticket. |
| 10+ identischi Mails innert Sekunde | **Auto-Trigger / Storm ⚠️** | Burst deutet uf Broadcast-Storm oder Auto-Trigger (Scheduled Scan). Eifach der ganze Thread trashed. |
| External IP bekannt (Shodan, Censys, CDN) | **False Positive 🟢** | Bekannti Scanner/Prober. Nüt alässlich. |

### Report-Struktur

```
HERMES: Deep Analysis [System] ✅

📧 [QUELLE] — [System]
⚠️ Blockierti IPs: [IP] [Herkunft] [Count]
❌ Failed Logins: [Username] [Count]
🔴 Security-Updates: [Plugin] — Update verfügbar

🌐 [NETZWERK]
- Internet: [OK/WARNING] ([Xd Uptime])
- Firewall: [X Regle] / kei suspekte
- Clients: [X] online, alli bekannt
- IPS/IDS: [ids/ips/disabled]

🎯 EMPFEHLIG:
1️⃣ Updates iispiele
2️⃣ … / Nüt alässlich
```

### Security Pitfalls

- **moto-poschung.ch isch extern gehostet** — Wordfence schützt de Webspace, nöd s'Homelab
- **Wordfence-Wochenrapport = kein akuts Problem** — Bot-Aktivität, kei gezielti Attacke
- **ISP-Ausfall:** UDM Pro schickt Email → Gmail sueche. `wan=OK, www=WARNING`
- **Failed Logins mit Standard-Usernames** (admin, 22255, 90452) = Bots, nüt alässlich
- **Security-Updates fällig = handlungsrelevant** — immer i TEAM-Ticket notiere

### WAN vs WWW Status (wichtig für ISP-Probleme!)

Das `stat/health`-Endpoint hat separate Subsysteme:

| Subsystem | Bedeutung | Status-Beispiel |
|-----------|-----------|-----------------|
| `wan_1` | Uplink-Verbindung (Modem/SFP) → `OK` wenn angeschlossen | OK = Uplink physisch da |
| `www` | Internet-Erreichbarkeit (DNS/Ping zu externen Hosts) → `WARNING` bei Störung | WARNING = ISP-Probleme |
| `wlan` | WLAN-Status → `WARNING` bei disconnected APs | WARNING = APs offline |
| `lan` | LAN-Verbindungen | OK = Clients verbunden |

**Bei ISP-Ausfall:** `wan` bleibt OK (Uplink steht), aber `www` zeigt WARNING mit `uptime: 0` und `drops: 1+`. Dieses Muster bestätigt einen Provider-Ausfall (nicht das eigene Netzwerk).

**Primäre Outage-Erkennung via Gmail:** Der UDM Pro sendet Email-Alerts bei WAN-Temporary-Disconnect-Events. Diese landen in Michels Gmail. Bei ISP-Status-Anfragen immer auch Gmail checken (`is:unread from:noreply@notifications.ui.com`) — das ist zuverlässiger als die Event-APIs.

### ⚠️ Bekannte API-Grenzen

- **`stat/event`** — Liefert **immer 0 Events** auf dieser UDM Pro, auch mit `_sort=-time` und breitem Filter. Keine Events über Disconnects, Reconnects, Roaming abrufbar.
- **`stat/alarm`** — Liefert ebenfalls **immer leeres Array** (`data: []`). Keine Alarme abrufbar.
- **`stat/sta` (active clients)** — Feld `ap_name` bleibt leer (`?`) für alle aktiven Clients, obwohl APs im System vorhanden sind.
- **Alternative:** Verwende `stat/alluser` mit `last_seen`-Timestamp für Offline-Erkennung und `stat/health` für Live-Status.

## Troubleshooting

- **403 Forbidden bei PUT/POST:** CSRF-Token fehlt! Immer aus JWT-Cookie extrahieren und als `X-CSRF-Token` Header mitgeben
- **Änderung wirkt erst nach Client-Reconnect:** Der Client muss sich neu verbinden (DHCP-Lease erneuern). Einfach WLAN kurz aus/an oder Gerät neustarten
- **API-Pfad:** UDM Pro nutzt `/proxy/network/api/s/default/...` — NICHT die alten UniFi Controller Pfade (`/api/s/default/...`)
- **Network-Override rückgängig:** `virtual_network_override_enabled: false` setzen → Client fällt zurück auf SSID-Standard-VLAN
- **Event-APIs sind tot:** `stat/event` und `stat/alarm` liefern 0 Ergebnisse → für Outage-Analyse `stat/health` + Gmail-UDM-Alerts verwenden
- **WWW vs WAN:** Bei ISP-Ausfall bleibt `wan` OK, aber `www` zeigt WARNING — das ist das sichere Unterscheidungsmerkmal

# WLAN-Optimierungs-Checkliste

Basierend uf em IT-Ion/UniFi-Experte-Video («UniFi WLAN richtig optimieren») + Scan vo Michel sim Setup.

## 🔴 Muss-Korrekture (sofort)

| # | Check | Soll | Ist | Fix |
|---|-------|------|-----|-----|
| 1 | **TX Power 2.4 GHz** — Wohnzimmer | `medium` | `high` | AP-Radio PUT |
| 2 | **TX Power 5 GHz** — Wohnzimmer | `medium` | `high` | AP-Radio PUT |
| 3 | **TX Power 2.4 GHz** — Keller | `medium` | `auto` | AP-Radio PUT |
| 4 | **TX Power 5 GHz** — Keller | `medium` | `auto` | AP-Radio PUT |
| 5 | **Fast Roaming** — Alice im Wland | `true` | `false` | WLANconf PUT |
| 6 | **Fast Roaming** — Alice im Vland | `true` | `false` | WLANconf PUT |
| 7 | **Fast Roaming** — Alice im IOTland | `true` | `false` | WLANconf PUT |
| 8 | **BSS Transition** — Alice im Vland | `true` | `false` | WLANconf PUT |
| 9 | **BSS Transition** — Alice im IOTland | `true` | `false` | WLANconf PUT |

## 🟡 Optimierig (optional)

| # | Check | Soll | Ist | Fix |
|---|-------|------|-----|-----|
| 10 | **5 GHz Kanal manuell** | DFS-Kanal (z.B. 100) | `auto` | AP-Radio PUT |
| 11 | **2.4 GHz Keller manuell** | ch1 oder ch11 | `auto` | AP-Radio PUT |
| 12 | **Minimum Data Rate** | 12 Mbps | nid gsetzt | WLANconf PUT |
| 13 | **2.4 GHz Wohnzimmer** | ch6 ✅ | ch6 | — |

## 🟢 Bereits optimal

- ✅ Kanalbreite 2.4 GHz = 20 MHz
- ✅ Kanalbreite 5 GHz = 80 MHz
- ✅ U6 Pro 4×4 MIMO (5 GHz)
- ✅ Beidi APs verkabelt (kein Mesh)
- ✅ VLAN-Trennig sauber
- ✅ 2.4 GHz Wohnzimmer uf ch6 (nöd überlappend)

## Befund (Scan 23.05.2026)

**Setup:** 2× U6 Pro (Wohnzimmer + Keller) | UDM Pro | 6 VLANs
**Clients:** 39 total (20× 2.4 GHz / 6× 5 GHz / 13× wired — Band-Steering suboptimal)
**Health:** WLAN=WARNING (APs wohl grad neugstartet), WWW=OK, LAN=OK

### Radio-Tabelle

| AP | Band | Ch | BW | TX Mode | Util |
|----|------|----|----|---------|------|
| U6 Pro Wohnzimmer | 2.4 GHz | 6 | 20 | **HIGH** ❌ | ? |
| U6 Pro Wohnzimmer | 5 GHz | auto | 80 | **HIGH** ❌ | ? |
| U6 Pro Keller | 2.4 GHz | auto | 20 | **auto** ❌ | ? |
| U6 Pro Keller | 5 GHz | auto | 80 | **auto** ❌ | ? |

### Roaming

| SSID | Fast Roam | BSS Trans | Min Rate |
|------|-----------|-----------|----------|
| Alice im Wland | **OFF** ❌ | ON ✅ | ? |
| Alice im Vland | **OFF** ❌ | **OFF** ❌ | ? |
| Alice im IOTland | **OFF** ❌ | **OFF** ❌ | ? |

### VLANs

| Name | VLAN | Subnet | DHCP |
|------|------|--------|------|
| Management | native | 10.0.0.1/24 | ✅ |
| Client | 10 | 10.0.10.1/24 | ✅ |
| IOT | 20 | 10.0.20.1/24 | ✅ |
| Service/DMZ | 40 | 10.0.40.1/27 | ✅ |
| Server | 60 | 10.0.60.1/24 | ✅ |

## Fix-Befehle (Curl)

```bash
COOKIE=/tmp/unifi_cookies.txt
# Login
CSRF=$(curl -sk -X POST "https://10.0.10.1/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"hassio","password":"Riotstar_MICHEL_13"}' \
  -c "$COOKIE" -D - 2>/dev/null | grep -i x-csrf-token | awk '{print $2}' | tr -d '\r')

# AP IDs hole
DEVICES=$(curl -sk "https://10.0.10.1/proxy/network/api/s/default/stat/device" -b "$COOKIE")

# TX Power uf Medium setze (beidi APs)
for AP_ID in $(echo "$DEVICES" | python3 -c "
import sys,json
for ap in json.load(sys.stdin)['data']:
    if 'UAP' in ap.get('model',''): print(ap['_id'])
"); do
  curl -sk -X PUT "https://10.0.10.1/proxy/network/api/s/default/rest/device/$AP_ID" \
    -b "$COOKIE" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
    -d '{"radio_table":[{"radio":"ng","tx_power_mode":"medium"},{"radio":"na","tx_power_mode":"medium"}]}'
done

# Roaming uf allne SSIDs aktiviere
for WLAN_ID in $(curl -sk "https://10.0.10.1/proxy/network/api/s/default/rest/wlanconf" \
  -b "$COOKIE" | python3 -c "
import sys,json
for w in json.load(sys.stdin)['data']:
    if w.get('enabled'): print(w['_id'])
"); do
  curl -sk -X PUT "https://10.0.10.1/proxy/network/api/s/default/rest/wlanconf/$WLAN_ID" \
    -b "$COOKIE" -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
    -d '{"fast_roaming_enabled": true, "bss_transition": true, "min_data_rate": 12}'
done
```

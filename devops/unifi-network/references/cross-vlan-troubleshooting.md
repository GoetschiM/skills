# Cross-VLAN Troubleshooting: Device Discovery (Philips TV + Hue Bridge)

## The Problem
Device A (TV, phone, speaker) in **VLAN X** can't find Device B (Hue Bridge, server, smart device) in **VLAN Y** via mDNS/UPnP/SSDP, even though both networks have `mdns_enabled: True`.

## Root Cause
mDNS (Bonjour/Avahi) and SSDP (UPnP/DIAL) are **link-local** protocols. They work by broadcasting/multicasting on a single subnet. By default, **no router forwards multicast between VLANs** — even with mDNS enabled on both networks individually.

## Analysis Checklist

### 1. Get UniFi API access
```python
import httpx, json, base64
UNIFI_HOST = "https://10.0.10.1"
r = httpx.post(f"{UNIFI_HOST}/api/auth/login",
    json={"username": "hassio", "password": "Riotstar_MICHEL_13"}, verify=False)
token = r.cookies.get("TOKEN", "")
payload_b64 = token.split(".")[1] + "=" * (4 - len(token.split(".")[1]) % 4)
csrf = json.loads(base64.b64decode(payload_b64)).get("csrftoken", "")
cookies = r.cookies
```

### 2. Get all networks (VLANs) from `rest/networkconf`
Key fields: `name`, `vlan` (int/null for native), `ip_subnet`, `_id`, `mdns_enabled`, `network_isolation_enabled`.

### 3. Find both devices in `stat/alluser`
Search by name, OUI, or MAC. Key fields to check:

| Field | What it tells you |
|-------|-------------------|
| `name` / `hostname` | Device name in UniFi |
| `mac` | MAC address |
| `last_ip` / `fixed_ip` | Current IP / reserved IP |
| `network_id` | VLAN it's currently in |
| `virtual_network_override_enabled` | If True, device is per-VLAN via SSID override |
| `virtual_network_override_id` | The VLAN it's forced into |
| `is_wired` | Wired vs WiFi — `false` = WLAN. <br/>⚠️ **Wichtige Unterscheidung:** `rest/user` hat KEIN `is_wired`-Feld! Nur `stat/alluser` und `stat/sta` liefern das. Wenn du checken willsch obs WiFi oder verkabelt isch → `stat/alluser` verwende. |
| `last_uplink_name` | AP or switch it's connected to |
| `is_online` | Currently reachable |
| `last_connection_network_name` | Human-readable network name |

### 4. Compare device locations
Different `network_id` → different VLANs → root cause confirmed.

### 5. Check for Network Override
`virtual_network_override_enabled: True` means the device is **not** on its SSID's native VLAN. The override `_id` tells you where it's actually placed. This can be changed.

## Solution Options

### A) Move device via Network Override (SAFEST, WIRED ONLY)
Change `virtual_network_override_id` on an already-overridden device to point to the other device's network. Device stays on its SSID but gets IP in target VLAN after reconnect.

**⚠️ WIFI LIMITATION:** Network Override funktioniert NUR für wired-Clients oder WiFi-Clients auf NICHT-Default-Netzen. Für WiFi-Clients im Default Corporate Network schlägt es fehl mit `VirtualNetworkOverrideUnsupportedForDefaultNetwork`. In dem Fall: separate SSID auf Ziel-VLAN erstellen.

### B) Move device via Switch Port Override (wired devices)
Change the switch port's native VLAN on the UniFi switch.

### C) SSDP Proxy (workaround)
Run Python SSDP proxy on a host with access to both VLANs (e.g. Hermes). See `scripts/ssdp-proxy.py`.

### D) mDNS Gateway / IGMP Snooping — DO NOT WASTE TIME
UDM Pro `evtmgr/conf` returns `api.err.NoSiteContext`. Even if available: reflects mDNS, NOT SSDP/UPnP. IGMP multicast flood **does not work** for SSDP between VLANs on UDM Pro.

## Real-World Reference Data

**Philips Hue Bridge:** MAC `00:17:88:25:8a:1a`, IP `10.0.0.190` (Management), Wired US24 Port 3, uses **SSDP** (not mDNS)
**Philips TV:** MAC `40:aa:56:05:57:75`, IP `10.0.10.86` (Client VLAN 10), **WiFi** (`is_wired: false`, AP Wintergarten), hat `virtual_network_override_enabled: True` auf Client 10. Lässt sich NICHT per Override ins Management-Netz verschieben (Default Corporate Network).

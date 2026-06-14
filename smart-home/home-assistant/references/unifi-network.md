# UniFi Network Analysis — Goetschi Labs

Access technique for UniFi OS (UDM Pro) Controller API.

## Access

- **Host**: `https://10.0.10.1` (UDM Pro)
- **Auth**: `POST /api/auth/login` with JSON body `{"username": "$UNIFI_USER", "password": "$UNIFI_PASS"}`
- **Credentials**: `UNIFI_USER=hassio`, `UNIFI_PASS=Riotstar_MICHEL_13` (in `~/.hermes/.env`)
- **Cookie**: Save login cookie with `-c /tmp/unifi_cookies.txt`

## API Endpoints (UniFi OS format)

All network queries go through the proxy endpoint:

```
/proxy/network/api/s/default/<endpoint>
```

| Endpoint | Description | Read/Write |
|---|---|---|
| `stat/device` | All network devices (APs, switches, gateway) | Read |
| `stat/sta` | All connected clients (with signal, VLAN, uptime) | Read |
| `stat/health` | System health — WAN, LAN, WLAN status | Read |
| `rest/user` | Known clients (name, MAC, IP, fixed IP) — **not just currently connected** | Read |
| `rest/networkconf` | Network configs (VLANs, DHCP, DNS, subnets, isolation, IGMP, UPnP) | **Read+Write** |
| `rest/setting/mdns` | mDNS Gateway config (cross-VLAN service reflection) | Read+Write |
| `rest/setting/igmp_snooping` | IGMP snooping, querier, multicast forwarding | Read+Write |
| `rest/firewallrule` | Custom firewall rules (empty if none defined) | Read+Write |

## Network Config Quick-Reference (Goetschi Labs)

| Network | VLAN | Subnet | _id |
|---|---|---|---|
| Management / Infra | — | 10.0.0.1/24 | `657844356d610c0744f51649` |
| Client | 10 | 10.0.10.1/24 | `657a3354269bb2051d3c0b49` |
| IOT | 20 | 10.0.20.1/24 | `66b6915b13e5ee2bfab356ab` |
| Server | 60 | 10.0.60.1/24 | `6808d99e5de12d4e3a920e8b` |
| Service / App / DMZ | 40 | 10.0.40.1/27 | `697003effec4b93b2f0099c7` |

## Write Operations (PUT/POST) — CSRF Token Required

UniFi OS (UDM Pro) requires an **X-CSRF-Token** header for write operations (PUT, POST, DELETE). The token is embedded in the login cookie's JWT payload.

### Extracting the CSRF Token

After login, inspect the cookie file. The CSRF token is a JWT claim `csrfToken`:

```bash
# Direct extraction from cookie
grep 'TOKEN' /tmp/unifi_cookies.txt | awk '{print $NF}' | cut -d. -f2 | \
  python3 -c "import sys,json,base64; d=json.loads(base64.urlsafe_b64decode(sys.stdin.read()+'===').decode()); print(d.get('csrfToken','NOT_FOUND'))"
```

Or just copy the hex UUID from the decoded JWT — it's a v4 UUID like `fdccaf76-4725-47d9-...`.

The cookie also works for reads without CSRF; CSRF is only needed for writes.

### Modify a Network (DNS, DHCP, VLAN settings)

**Always backup first!**

```bash
# 1. BACKUP full network config (includes ALL settings for rollback)
curl -sk "https://10.0.10.1/proxy/network/api/s/default/rest/networkconf" \
  -b /tmp/unifi_cookies.txt > /tmp/unifi_network_backup.json

# 2. FIND the network _id
python3 -c "
import json
with open('/tmp/unifi_network_backup.json') as f:
    data = json.load(f)
for n in data.get('data', []):
    if n.get('purpose') == 'corporate':
        v = n.get('vlan', '-')
        print(f\"{n['name']:25s} V{v!s:3s} | _id={n['_id']} | DNS1={n.get('dhcpd_dns_1','-')} DNS2={n.get('dhcpd_dns_2','-')}\")
"

# 3. MODIFY — CSRF + all required fields in body
CSRF="fdccaf76-4725-47d9-8b78-4e70d129e0b4"
curl -sk -X PUT "https://10.0.10.1/proxy/network/api/s/default/rest/networkconf/<_id>" \
  -b /tmp/unifi_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF" \
  -d '{
    "_id": "<_id>",
    "name": "IOT",
    "purpose": "corporate",
    "vlan": 20,
    "dhcpd_enabled": true,
    "enabled": true,
    "ip_subnet": "10.0.20.1/24",
    "dhcpd_dns_1": "10.0.60.111",
    "dhcpd_dns_2": "1.1.1.1",
    "dhcpd_dns_3": "",
    "dhcpd_dns_4": ""
  }'
```

⚠️ **Pitfalls:**
- PUT **requires** `_id`, `name`, `purpose`, `vlan`, `dhcpd_enabled`, `enabled`, `ip_subnet` in the body — even if you're only changing DNS. Missing fields may silently reset to defaults!
- CSRF token per session — cookie expiry (~2h) invalidates it. Re-login for a new token if you get 403.
- The UDM doesn't validate the body beyond schema — you can PUT minimal fields as long as required ones are present.

### Verify Changes

```bash
curl -sk "https://10.0.10.1/proxy/network/api/s/default/rest/networkconf" \
  -b /tmp/unifi_cookies.txt \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for n in data.get('data', []):
    if n.get('purpose') == 'corporate':
        d1 = n.get('dhcpd_dns_1', '-')
        d2 = n.get('dhcpd_dns_2', '-')
        v = n.get('vlan', '-')
        print(f\"{n['name']:25s} V{v!s:3s} | DNS1={d1:15s} DNS2={d2:15s}\")
"

### Rollback from Backup

```bash
CSRF="fdccaf76-4725-47d9-8b78-4e70d129e0b4"
ID="<_id_to_rollback>"
# Extract old config for that network and PUT to restore
python3 -c "
import json
with open('/tmp/unifi_network_backup.json') as f:
    d = json.load(f)
for n in d['data']:
    if n['_id'] == '$ID':
        print(json.dumps(n))
    " | tee /tmp/_rollback.json
# Then PUT: curl -sk -X PUT ... -d @/tmp/_rollback.json
```

## mDNS Gateway Configuration

The mDNS Gateway reflects mDNS services (port 5353) between VLANs. Without it, devices in different VLANs can't discover each other via mDNS (Bonjour/ZeroConf).

```bash
# Read current mDNS config
curl -sk "https://10.0.10.1/proxy/network/api/s/default/rest/setting/mdns" \
  -b /tmp/unifi_cookies.txt | python3 -m json.tool

# Settings:
#   enabled_for: "all"          — reflect ALL mDNS services
#   mode: "all"                 — broadcast mode (not per-service)
#   enabled_for_network_ids: [] — which VLANs participate
```

⚠️ **Known quirk:** PUT on the mDNS setting returns HTTP 200 but `enabled_for_network_ids` stays empty. On UDM Pro with Network 8.x+, `"enabled_for": "all"` seems to imply all corporate networks. The per-network-list endpoint may not apply. If cross-VLAN mDNS doesn't work despite this, the device likely uses **SSDP/UPnP** (port 1900) instead of mDNS — see Cross-VLAN Discovery section below.

## IGMP Snooping

```bash
curl -sk "https://10.0.10.1/proxy/network/api/s/default/rest/setting/igmp_snooping" \
  -b /tmp/unifi_cookies.txt | python3 -m json.tool
```

Key fields:
- `enabled: true` — IGMP snooping active
- `subscription_mode: "ALL"` — forward all multicast subscriptions
- `forward_unknown_mcast_router_ports: false` — **unknown multicast NOT forwarded** (blocks SSDP cross-VLAN)
- `flood_unknown_multicast_for_network_ids: []` — no networks get unknown multicast flood
- `flood_known_protocols: true` — known protocols (like mDNS) forwarded

## Cross-VLAN Device Discovery Troubleshooting

**The Problem:** A device in VLAN A can't discover a device in VLAN B via mDNS/SSDP/UPnP, while direct IP connections work fine.

**Why:** Multicast traffic (mDNS:224.0.0.251:5353, SSDP:239.255.255.250:1900) stays in its origin VLAN. A router doesn't forward multicast by default. The UDM's mDNS Gateway solves this for **mDNS only** — SSDP/UPnP is not reflected by default.

### Diagnosis Checklist

1. **Check which VLANs each device is in** — use `rest/user` to find IPs, then correlate with `rest/networkconf` for subnet-to-VLAN mapping
2. **Check mDNS Gateway** — already set to `"enabled_for": "all"` on Goetschi Labs UDM
3. **Check IGMP snooping** — `forward_unknown_mcast_router_ports: false` prevents SSDP from crossing VLANs
4. **Check firewall rules** — `rest/firewallrule` — if empty, default "allow all between corporate" applies
5. **Check network isolation** — `network_isolation_enabled: false` on all networks
6. **Check each network's per-network mDNS/UPnP** — each corporate network has `mdns_enabled` and `upnp_lan_enabled` fields

### Why Some Devices Work Cross-VLAN

| Device | Discovery Mechanism | Why It Works |
|---|---|---|
| **Home Assistant** | Direct IP (API URL) | HA connects to Hue Bridge via configured IP — no discovery needed |
| **Alexa** | Cloud account | Alexa links Hue via cloud (Philips account), not local SSDP |
| **Philips TV** | SSDP/UPnP (local) | ❌ **Doesn't work** — SSDP multicast is VLAN-bound |

### Fix Options (in order of preference)

1. **Move device to the same VLAN** — simplest, most reliable. If the device's IP doesn't matter, just change its DHCP assignment or static IP to match the service's VLAN.
2. **Configure by static IP** — if the client supports manual configuration (some TVs let you enter Hue Bridge IP directly), bypass discovery entirely.
3. **Run a multicast relay** — `avahi-daemon` (reflector mode) or `udpbroadcastrelay` on a dual-homed host. Not possible on single-NIC hosts.
4. **Enable IGMP proxy on the UDM** — requires SSH into UDM (advanced, risk of breaking). Modify `/etc/igmpproxy.conf`.
```

## Standard Login Pattern

```bash
source ~/.hermes/.env
curl -sk -X POST "https://10.0.10.1/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$UNIFI_USER\", \"password\": \"$UNIFI_PASS\"}" \
  -c /tmp/unifi_cookies.txt -o /dev/null
```

Then query:
```bash
curl -sk "https://10.0.10.1/proxy/network/api/s/default/stat/device" \
  -b /tmp/unifi_cookies.txt | python3 -m json.tool
```

## Infrastructure (Goetschi Labs, Kriegstetten)

### Devices (8 total)
| Status | Device | IP | Model | Version |
|---|---|---|---|---|
| ✅ | UDM Pro (Gateway) | 172.16.0.2 | UDMPRO | 5.0.16.30692 |
| ✅ | US 24 (Switch) | 10.0.0.100 | US24 | 7.4.1.16850 |
| ✅ | U6 Pro Wohnzimmer | 10.0.0.9 | UAP6MP | 6.8.2.15592 |
| ✅ | U6 Pro Keller | 10.0.0.154 | UAP6MP | 6.8.2.15592 |
| ✅ | AC Pro Büro | 10.0.0.8 | U7PG2 | 6.8.2.15592 |
| ✅ | AC Pro Eingang | 10.0.0.173 | U7PG2 | 6.8.2.15592 |
| ✅ | AC Pro Wintergarten | 10.0.0.189 | U7PG2 | 6.8.2.15592 |
| ❌ | AC Pro (unnamed) | 10.0.0.109 | U7PG2 | 6.8.2.15592 — **Offline** |

### WAN — Salt Mobile SA Fiber
- Speed: **949 Mbps Up / 844 Mbps Down**
- Uptime: 100% (last 24h)
- Latency: 4-7ms to ping.ui.com, 1.1.1.1, 8.8.8.8
- UDM Pro: CPU 9.6%, RAM 85%, uptime ~5 days

### Client Distribution
- **39 clients total**: 26 WLAN + 13 Kabel
- **VLANs**: 20 (IoT, 24 clients), 60 (Server, 10 clients), 10 (LAN, 3 clients), 0 (native, 2 clients)

### Key Servers on VLAN 60 (10.0.60.0/24)
| Host | IP | Role |
|---|---|---|
| pve01.net.lan | 10.0.60.10 | Proxmox hypervisor |
| HAOS | 10.0.60.111 | Home Assistant OS |
| Dokploy | 10.0.60.121 | Docker deployment |
| InfluxDB | 10.0.60.140 | Time-series DB |
| Postgres-PGVector | 10.0.60.141 | PostgreSQL |
| Sipcall (Asterisk) | 10.0.60.167 | VoIP/SIP |
| **mt5-bot04** | **10.0.60.104** | **Trading Bot** |
| OpenClaw | 10.0.60.177 | ? |
| QDevice | 10.0.60.182 | QNAP device |
| ubuntu | 10.0.60.178 | Generic Ubuntu VM |

### Issues Found
- **AC Pro offline** (10.0.0.109) — unnamed AP, needs investigation
- WLAN health shows warning due to 1 disconnected AP
- Alice-im-Wland (Alexa, 10.0.20.112) has weak signal (-81dBm)

## Quick Analysis Script

```python
import json, subprocess

def unifi_query(endpoint):
    source = "source ~/.hermes/.env"
    login = """curl -sk -X POST "https://10.0.10.1/api/auth/login" -H "Content-Type: application/json" -d '{"username":"$UNIFI_USER","password":"$UNIFI_PASS"}' -c /tmp/unifi_cookies.txt -o /dev/null"""
    fetch = f"""curl -sk "https://10.0.10.1/proxy/network/api/s/default/{endpoint}" -b /tmp/unifi_cookies.txt"""
    cmd = f"{source} && {login} && {fetch}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

# Usage:
# devices = unifi_query("stat/device")
# clients = unifi_query("stat/sta")
# health = unifi_query("stat/health")
```

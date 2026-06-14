# Goetschi Labs Netzwerk-Infrastruktur (Stand 14.06.2026)

## Subnetz
- **Range:** 10.0.60.0/24 (254 Hosts)
- **Gateway:** 10.0.60.1 (vermutlich)
- **DNS:** 10.0.60.10 (vermutlich)

## Bekannti Hosts

| IP | Hostname | Beschrieb |
|----|----------|-----------|
| 10.0.60.1 | Gateway | Vermutlich Router/Firewall |
| 10.0.60.10 | DNS | Vermutlich DNS/DHCP |
| 10.0.60.60 | - | Unbekannt |
| 10.0.60.104 | Bot04 | MT5 Trading Bot (Port 8080) |
| 10.0.60.106 | - | Unbekannt |
| 10.0.60.110 | - | Unbekannt |
| 10.0.60.111 | - | Unbekannt |
| 10.0.60.121 | Dokploy-Host | NextCloud:8080, n8n, Paperless (Docker) |
| 10.0.60.135 | - | Unbekannt |
| 10.0.60.139 | CT118 | Coolify + MT5 API (Port 3007) |
| 10.0.60.140 | LXC109 | InfluxDB Tradingbot (Port 8086) |
| 10.0.60.141 | - | Unbekannt |
| 10.0.60.152 | - | Interner Node |
| 10.0.60.156 | Apollo | **DIESER HOST** — Hermes, LiteLLM, Kali Docker |
| 10.0.60.167 | Nova | Zweite Hermes-Instanz |
| 10.0.60.170 | CT107 | MCPHub Gateway (Port 3000) |
| 10.0.60.179 | - | Unbekannt |
| 10.0.60.186 | - | Unbekannt |
| 10.0.60.201 | - | Unbekannt |

## Security-Notes

- Diverse LXC-Container (Proxmox) — standardmässig abgsichert
- Docker uf Apollo isch **nicht aktiv** — Docker-Socket nöd available
- SSH Passwort-auth isch aktiv (Louis_one_13, Riotstar_*)
- Confluence + Jira sin **Cloud** (nöd im 10.0.60.0/24)
- NextCloud + n8n laufe uf 10.0.60.121 via Docker (Dokploy)
- InfluxDB uf 10.0.60.140:8086 (ke Auth vermuetlich)

## Scan-Befehle (sicher / read-only)

```bash
# Ping-Sweep (alle Hosts finde)
nmap -sn -T4 10.0.60.0/24 --reason

# Service-Scan (Top 1000 Ports)
nmap -sV -T4 --top-ports 1000 --reason 10.0.60.0/24

# Masscan (schneller, alli 65535 Ports)
masscan 10.0.60.0/24 -p1-65535 --rate=1000

# Schwachstelle-Check (nur bekannte Dienste)
nmap -sV --script vuln -T4 10.0.60.0/24
```

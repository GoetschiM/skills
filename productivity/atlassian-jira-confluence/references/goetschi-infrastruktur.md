# Goetschi Labs Infrastruktur (Lebendes Dokument — Stand 13.06.2026)
# Quelle: Agent-Onboarding Confluence-Seite + Session-Ermittlung + Live-Checks

## Proxmox Hosts
- **pve01** (10.0.60.10): root/`Riotstar_PROXMOX_13` — Hauptproduktion
  - Tailscale: 100.90.250.116, Subnet-Routing aktiv (10.40.30.0/24, 10.60.0.0/24)
- **pve02** (10.0.60.11): root/`Riotstar_PROXMOX_13` — Reserve, aktuell nicht erreichbar

## LXC Container (Vollständig — 18 LXCs + 2 VMs)

### VMs
| VM | Name | IP | RAM | Disk | Rolle | Status |
|----|------|----|-----|------|-------|--------|
| 113 | HA-OS | 10.0.60.111 | 8G | 112G | Home Assistant OS | ✅ running |
| 201 | CasaOS | 10.0.60.201 | 5G | 320G | CasaOS, 6TB USB (Nextcloud/Plex) | ✅ running |

### Produktion / Dienste
| LXC | Name | IP | RAM | Disk | Rolle | Status |
|-----|------|----|-----|------|-------|--------|
| 100 | Dokploy Prod | 10.0.60.121 | 10G | 114G | Dokploy Platform, 23 Container | ✅ running |
| 103 | Paperless-NGX | 10.0.40.30 | 512M | 128G | Paperless Dokumentenmanagement | ✅ running |
| 105 | PGVector | 10.0.60.141 | 128M | 7.8G | PostgreSQL 14/16 + pgvector | ✅ running |
| 107 | MCPHub | 10.0.60.170 | 2G | 12G | MCP Server Manager (Docker) | ✅ running |
| 108 | Apollo/Hermes | 10.0.60.156 | 10G | 87G | Hermes Agent, LiteLLM | ✅ running |
| 109 | InfluxDB | 10.0.60.109 | k.A. | k.A. | InfluxDB V1 + Chronograf 1.10.1 | ✅ running |
| 110 | Monitoring | 10.0.60.110 | k.A. | k.A. | Grafana + Prometheus + Loki (Docker) | ✅ running |
| 112 | NOVA | 10.0.60.167 | 14G | 120G | Asterisk, Dograh, Ollama, edge-tts | ✅ running |
| 116 | LiteLLM | 10.0.60.152 | k.A. | k.A. | LiteLLM API Proxy | ✅ running |
| 117 | Voice-Gateway | 10.0.60.60 | k.A. | k.A. | Asterisk 20.19 + Dograh | ✅ running |
| 118 | Coolify | 10.0.60.139 | 2G | 32G | Coolify 4.1.2 + MT5 + Dienste | ✅ running |
| 401 | Magos | 10.0.60.104 | k.A. | k.A. | - | ✅ running |
| 402 | Orion | 10.0.60.105 | k.A. | k.A. | - | ✅ running |
| 504 | mt5-bot04 | 10.0.60.104 | k.A. | k.A. | MT5 Trading Bot | ✅ running |
| 505 | MinIO | 10.0.60.106 | 512M | 9.8G | S3 Storage | ✅ running |
| 506 | Qdrant | 10.0.60.179 | 512M | 10G | Vektordatenbank | ✅ running |

### Gestoppt
| LXC | Name | IP | RAM | Disk | Rolle | Status |
|-----|------|----|-----|------|-------|--------|
| 301 | NAS-Video | DHCP | 2G | 8G | Movie Stack (CasaOS) | ❌ stopped |

## Monitoring Stack

### InfluxDB (CT109 — 10.0.60.109)
- **InfluxDB V1**: Port 8086, **KEIN Auth** (auth-enabled = false)
- **Chronograf**: Port 8888, Version 1.10.1 — Visualisierung UI
- **24 Datenbanken**: Trading (trading01, mx5, RL-Bot), Tradingbots (BOT01-BOT08, LIVE01-LIVE03, TESTER), homeassistant, Signale
- **Zugriff von Apps:** http://10.0.60.109:8086 (kein Token nötig)
- **SSH:** via pve01 (pct exec 109)

### Grafana / Prometheus / Loki (CT110 — 10.0.60.110)
- **Grafana**: Port 3000, grafana/grafana:latest
  - Login: admin / admin (zurückgesetzt 13.06.2026)
  - Service Account Token: <GRAFANA_TOKEN>
- **Prometheus**: Port 9090, prom/prometheus:latest
  - Targets: 13 LXCs + pve01 (node_exporter)
- **Loki**: Port 3100, grafana/loki:latest
  - Log-Quellen: Docker-Container-Logs + Systemd-Journal
- **Container:** Alle Docker auf CT110, frisch gestartet 13.06.2026
- **Datasources:** Prometheus, Loki, InfluxDB provisioniert

### Grafana Recovery Workflow (bei verlorenem Passwort)
Siehe `references/grafana-recovery.md` für detaillierte Schritte.

## Coolify (CT118 — 10.0.60.139)
- **Coolify 4.1.2**: Port 8000, Docker-Betrieb
- **SSH:** root / Louis_one_13
- **Disk:** 32GB (8.8G used), RAM: 2GB
- **Dienste:** siehe LXC-Tabelle oben
- **Wichtige Container:** n8n (:5678), mt5-trading (:3007), nextcloud (:8090), portainer (:9443)

## Movie Stack (LXC 301 — NAS-Video)
- **Status:** ❌ Gestoppt (kein Emby/Jellyfin/Plex installiert)
- **Typ:** CasaOS LXC (über Helper-Scripts installiert)
- **Ressourcen:** 2 Cores, 2GB RAM, 8GB Disk
- **Netzwerk:** DHCP (hwaddr BC:24:11:77:51:57)
- **Zugang:** muss gestartet werden (qm start 301), IP via DHCP ermitteln

## Credential Quick-Reference
| Service | User | Pass/Key |
|---------|------|----------|
| Proxmox pve01 | root | Riotstar_PROXMOX_13 |
| Proxmox pve02 | root | Riotstar_PROXMOX_13 |
| UniFi UDM Pro | hassio | Riotstar_MICHEL_13 |
| MinIO | admin | Louis_one_13 |
| CasaOS VM (201) SSH | michel | Louis_one_13 |
| Nextcloud (CasaOS) | michel | Louis_one_14 |
| Coolify | root | Louis_one_13 |
| Grafana | admin | admin |
| MCPHub | Hermes | Louis_one_13 |
| MCPHub Bearer | - | mcphub-goetschi-2026-open |

**Credential-Hierarchie:** 1. Qdrant → 2. Notion → 3. Confluence → 4. Obsidian

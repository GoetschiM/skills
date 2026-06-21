# Goetschi Labs — Infrastruktur-Dokumentation (pve01)
> Stand: 07.06.2026 | Proxmox 8.4.19 | Kernel 6.8.12-18-pve

---

## 🖥️ Proxmox Host — pve01

| Feld | Wert |
|------|------|
| **Hostname** | pve01 |
| **IP** | 10.0.60.10 |
| **URL** | https://10.0.60.10:8006 |
| **Root User** | root |
| **Root Passwort** | Riotstar_PROXMOX_13 |
| **Version** | pve-manager 8.4.19 |
| **Storage** | Disk (LVM): 83% (161GB frei), HDD (ZFS): 55% (418GB frei), local: 39% (54GB frei) |

---

## 📊 Container-Übersicht (18 Container / 2 VMs)

---

## 🏗️ 1. DEPLOYMENT & HOSTING

### CT100 — Dokploy (Production) ✅
| IP | 10.0.60.121 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 3000 (Dokploy UI), 8000/9443 (Portainer), 5678 (n8n), 8002 (Google MCP), 3033 (Moto-Poschung), 3007 (MT5-Trading), 1713 (Goetschi-Labs), 8420 (Signal-News) |
| Docker | 12 Container: Dokploy v0.29.2, Portainer, n8n, LiteLLM (intern), Postgres:16, Redis:7, Google-MCP-Server, MT5-TradingBot, Moto-Poschung, Signal-News, Goetschi-Labs-Web |
| URLs | http://moto-poschung.rebelone.ch, http://goetschi-labs.rebelone.ch, http://10.0.60.121:1713 |
| Beschreibung | 🔧 Haupt-Deployment-Plattform — Dokploy orchestriert 12 Docker-Container. Enthält: n8n (Workflow-Automation), Portainer (Docker-Management), Moto-Poschung (Kawasaki-Vertretung), Goetschi-Labs-Web, MT5-TradingBot, Signal-News-Bot. |
| Datenbanken | Postgres:16 (Dokploy + LiteLLM), Redis:7 |

### CT118 — Coolify ✅
| IP | 10.0.60.139 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 8000 (Coolify UI), 80/443 (Traefik), 8080 (Traefik Dashboard), 9443 (Portainer), 5006 (Actual Budget), 3007 (MT5 Trading), 5984 (CouchDB), 3034 (Besorgsdir WP) |
| Docker | 15 Container: Coolify 4.1.2, Traefik v3.6, Postgres:15, Redis:7, Vaultwarden, Portainer, Actual Budget, MT5 Trading, Obsidian CouchDB, Wordpress + MariaDB, Dograh-Stack (Redis, PG, Minio) |
| Beschreibung | 🚀 Selfhosting-Plattform — Coolify mit Traefik SSL. Hostet: Vaultwarden (Passwortmanager), Actual Budget (Finanzen), Besorgsdir (Wordpress), Obsidian Sync (CouchDB). |
| Datenbanken | PG:15 (Coolify), Redis:7, CouchDB 3.4.1, MariaDB 11, PG:17+pgvector (Dograh), Minio S3 |

### CT301 — NAS-Video ⛔
| IP | Keine (DHCP-Problem) |
| Typ | LXC (unprivilegiert) |
| Status | ⛔ stopped (onboot=0) |
| Problem | DHCP: eth0 bekommt keine Lease → kein Netzwerk. |
| Beschreibung | Sollte NAS/Video-Dienste hosten. Läuft nicht, kein Bedarf. |

---

## 🤖 2. AI-AGENTS & GATEWAYS

### CT108 — Hermes (Gen 1) ✅
| IP | 10.0.60.156 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running |
| Ports | 5002 (Hermes Call API) |
| Dienste | hermes-call-api.service, hermes-gateway.service, Postfix |
| Beschreibung | 🤖 Erste Hermes-Agent-Instanz — mit Call-API (ausgehende Anrufe, Port 5002). Wird abgelöst durch Magos/Orion. |

### CT112 — Nova ✅
| IP | 10.0.60.167 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 4010 (Nova AI Router), 5001 (Hermes API Layer), 5003 (Hermes Voice v2), 5004 (Nova Call VM API), 8890 (RTP Bridge), 3033 (Moto-Test) |
| Docker | 1 Container: moto-test |
| Dienste | ai-router-nova.service, hermes-api-layer.service, hermes-voice.service, hermes167.service, litellm-nova.service, nova-call-vm-api.service, rtp-bridge.service |
| Beschreibung | 🧠 NOVA — KI-Router & Sprachplattform. Bietet: OpenAI-kompatiblen Chat (5001), Voice-Service (5003), Call-Recording API (5004), LiteLLM (4000 intern), RTP-Bridge zu Asterisk (8890). |

### CT117 — Voice-Gateway ✅
| IP | 10.0.60.60 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 3010 (Dograh UI), 8000 (Dograh API), 6379 (Redis), 5432 (PG+pgvector), 2000 (Cloudflare Tunnel), 9001 (Minio Console), 5050 (Nova Call API), 5038 (Asterisk AMI), 8088 (Asterisk HTTP) |
| Docker | 6 Container: Dograh (UI, API, Redis, PG+pgvector), Cloudflared-Tunnel, Minio |
| Dienste | asterisk.service (Asterisk 20.19), nova-call-api.service, Docker |
| Datenbanken | PG:17+pgvector (Dograh), Redis:7, Minio S3 |
| Beschreibung | 📞 Telefonie-Gateway — Asterisk PBX + Dograh Voice. Cloudflare Tunnel für externen Zugriff. Nova-Call-API für TTS-Anrufe (Port 5050). |

### CT401 — Magos ✅
| IP | 10.0.60.185 |
| Typ | LXC (Ubuntu, 1 Core, 1024MB) |
| Status | ✅ running (onboot=1) |
| Dienst | Hermes Agent (Python 3.12, 17.7% MEM) |
| Beschreibung | 🧙 MAGOS G. — Knowledge Architect. Hermes-Gateway (AI-Agent). Reiner Client via DeepSeek V4 Flash. Kein Docker. |

### CT402 — Orion ✅
| IP | 10.0.60.135 |
| Typ | LXC (Ubuntu, 1 Core, 1024MB) |
| Status | ✅ running (onboot=1) |
| Dienst | Hermes Agent (Python 3.12, 41.8% MEM) |
| Beschreibung | ⚔️ ORION — Tactical Operations. Zweiter Hermes-Gateway. Höherer RAM-Verbrauch (438MB). Läuft mit --replace Flag. |

---

## 📄 3. DOKUMENTE & DATEN

### CT103 — Paperless-NGX ✅
| IP | 10.0.40.30 (VLAN 40) |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 8000 (Paperless Web), 80 (Apache Reverse Proxy), 139/445 (Samba), 8384 (Syncthing) |
| Dienste | Apache2, Paperless-Consumer, Paperless-Webserver (Gunicorn), PostgreSQL 15, Redis, Samba, Syncthing, Wazuh-Agent, Postfix |
| Datenbanken | PostgreSQL 15 (lokal, 5432), Redis (6379) |
| Beschreibung | 📄 Dokumentenmanagement — 1.491 Docs (2.2GB). Automatischer Consume, OCR, Tagging. Samba-Freigabe Paperless-Media. Live-Sync nach Nextcloud via lsyncd. |
| URLs | http://paper.rebelone.ch (Cloudflare), http://10.0.40.30:8000 (intern) |

### CT140 — InfluxDB V1 ✅
| IP | 10.0.60.140 |
| Typ | LXC (Debian 12) |
| Status | ✅ running |
| Port | 8086 (InfluxDB API, KEIN Auth) |
| Dienste | InfluxDB V1 (InfluxQL), 24 Datenbanken |
| Datenbanken | homeassistant (~1947 Measurements), trading01, trading, Signale, RL-Bot, Tradingbot_LIVE01-03, Tradingbot_BOT01-08, mx5 |
| Beschreibung | 📊 Zeitreihen-Datenbank — 2 Jahre HomeAssistant + Trading-Daten. Wichtigste Datenquelle für Grafana. |

### CT110 — Grafana + Prometheus + Loki ✅
| IP | 10.0.60.110 |
| Typ | LXC (Ubuntu 24.04) |
| Status | ✅ running |
| Ports | 3000 (Grafana UI), 9090 (Prometheus), 3100 (Loki) |
| Dienste | Grafana (Docker), Prometheus 3.12.0 (Docker), Loki 3.7.2 (Docker) |
| Prometheus | 12/13 Targets up — node_exporter auf allen LXCs |
| Grafana Login | admin / Louis_one_13 |
| Dashboards | 🏠 System Overview, 🌞 PV & Strom, 🚗 Tesla, 📈 Trading |
| Beschreibung | 📈 Monitoring-Stack — Visualisierung, Metrik-Sammlung, Log-Aggregation. Alle Dienste als Docker-Container auf CT110. |

### CT105 — PostgreSQL / PGVector ✅
| IP | 10.0.60.141 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 5432 (PostgreSQL, offen für alle) |
| Datenbanken | PG 14.19 + PG 16.12 mit pgvector 0.8.1 |
| Datenbanken | nei (45MB, n8n2), ownmcp_memory (21MB), nei_v2 (12MB), toni_app (12MB) |
| Beschreibung | 🗄️ Vektor-Datenbank — PostgreSQL mit pgvector für AI-Vektorsuche. |

### CT506 — Qdrant ✅
| IP | 10.0.60.179 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running |
| Ports | 6333 (API), 6334 (gRPC intern) |
| Collections | 6 Collections, 1.287 Vektorpunkte |
| Beschreibung | 🧩 Vektordatenbank — AI-Memory und Knowledge-Base. goetschi_labs_memory (793pts), tgs_knowledge (267pts). |

### CT505 — MinIO ✅
| IP | 10.0.60.106 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running |
| Ports | 9000 (S3 API), 9001 (Console) |
| Buckets | 15: asterisk-backups, backup, documents, google-mcp-server, hermes-*-backups, nova-*, qdrant-snapshots, sd-api, swarm-skills |
| Beschreibung | ☁️ S3-Objektspeicher — Zentraler Storage für Backups aller Dienste. |

---

## 🏠 4. SMART HOME & MEDIA

### VM113 — HA-OS ✅
| IP | 10.0.60.111 |
| Typ | Qemu VM (8GB RAM, 2 Cores, 112GB + 120GB Disk) |
| Status | ✅ running |
| Port | 8123 (Home Assistant UI) |
| Version | HA OS 2026.6.1 (aktuell, supervisor healthy) |
| Add-ons (aktiv) | Matter Server, Mosquitto Broker, OpenThread BR, Z-Wave JS UI, Cloudflared, evcc |
| Add-ons (gestoppt) | HACS, Studio Code Server, Music Assistant, ESPHome, Samba, AdGuard, Terminal |
| Beschreibung | 🏠 Smart Home Zentrale. Steuert: Z-Wave, Zigbee, Matter, Thread. EVCC für E-Auto-Ladesteuerung. |

### VM201 — CasaOS ✅
| IP | 10.0.60.201 |
| Typ | Qemu VM (5GB RAM, 2 Cores, 320GB + 6TB USB Western Digital) |
| Status | ✅ running |
| Ports | 80 (CasaOS UI), 139/445 (Samba), 8082 (qBittorrent), 32400 (Plex), 7878 (Radarr), 8989 (Sonarr), 9696 (Prowlarr) |
| SSH | michel / Louis_one_13 |
| Apps | Plex, qBittorrent, Radarr, Sonarr, Prowlarr, Immich, WireGuard-Easy |
| Nextcloud | Docker auf Port 10081. Admin: michel / Louis_one_14 |
| Beschreibung | 🌐 NAS & Media Server. 6TB USB (exfat, 7.3TB, 5.5TB frei). Plex/Radarr/Sonarr/qBittorrent für Media. |

---

## 🧩 5. MCP-INFRASTRUKTUR

### CT107 — MCPHub ✅⚠️
| IP | 10.0.60.170 |
| Typ | LXC (Ubuntu) |
| Status | ⚠️ running — degraded |
| Port | 3000 (MCPHub UI + API) |
| Docker | 2 Container: mcphub (samanhappy/mcphub:latest), google-mcp-server |
| MCPs | 11 Server, 9 connected ✅, 2 disconnected ❌ |
| Connected | Notion (22 Tools), Jira/Confluence (9), Qdrant (6), Proxmox (7), HA (8), MinIO (6), PG (7), Google (5), Paperless (7) |
| Disconnected | Asterisk ARI (❌ tools/list), UniFi (❌ connection closed) |
| Beschreibung | 🧩 MCP-Gateway. Verbindet Hermes-Agents mit 11 externen Diensten. |

---

## 🖥️ 6. SPEZIAL-ANWENDUNGEN

### CT504 — MT5-Bot04 ✅
| IP | 10.0.60.104 |
| Typ | LXC (Ubuntu, 1 Core, 1024MB) |
| Status | ✅ running (seit 27h+) |
| Ports | 8080 (Python API), 5900/5901 (VNC), 3389 (RDP), 6080 (noVNC) |
| Prozesse | MetaTrader 5 (Wine, 33.5% MEM), Uvicorn API, Xvfb + fluxbox + x11vnc |
| Beschreibung | 📈 Trading-Bot — MT5 unter Wine mit Desktop (Xvfb). Python API + VNC/RDP/noVNC. |

### CT116 — LiteLLM ✅
| IP | 10.0.60.152 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running |
| Port | 4000 (LiteLLM Proxy API) |
| Dienste | litellm.service, PostgreSQL 16 (lokal) |
| Beschreibung | 🔌 LLM-Proxy-Gateway — Einheitliche OpenAI-kompatible API. PostgreSQL 16 für Usage-Tracking. |

---

## 🌐 7. EXTERNE DOMAINS

| Domain | Zweck | Status |
| http://goetschi-labs.rebelone.ch | Goetschi Labs Website | ✅ CT100:1713 |
| http://moto-poschung.rebelone.ch | Moto Poschung (Kawasaki) | ✅ CT100:3033 |
| http://paper.rebelone.ch | Paperless-NGX (Cloudflare) | ✅ CT103:8000 |
| https://nextcloud.rebelone.ch | Nextcloud | ✅ CT201:10081 |
| http://10.0.60.201:80 | CasaOS UI | ✅ |
| http://10.0.60.201:32400 | Plex | ✅ |
| http://10.0.60.121:3000 | Dokploy UI | ✅ |
| http://10.0.60.139:8000 | Coolify UI | ✅ |
| http://10.0.60.170:3000 | MCPHub | ⚠️ Degraded |
| http://10.0.60.111:8123 | Home Assistant | ✅ |
| http://10.0.60.167:5001 | Nova API (OpenAI) | ✅ |

---

## ⚠️ OFFENE PUNKTE

| Prio | Problem | Betroffen |
| 🔴 | MCPHub degraded — 2/11 disconnected (Asterisk, UniFi) | CT107 |
| 🔴 | Notion-Token abgelaufen (401) | CT107 / Hermes |
| 🟡 | Asterisk Sound-Index — core reload nötig | CT117 |
| 🟡 | CT301 (NAS-Video) — DHCP-Problem, gestoppt | CT301 |
| 🟡 | Paperless MinIO-Backup fehlt | CT103/CT505 |
| 🟢 | SSH auf CT201 geht (michel), aber kein Root | VM201 |

## 🔐 PASSWORT-ZUSAMMENFASSUNG

| Dienst | User | Passwort |
| Proxmox pve01 | root | Riotstar_PROXMOX_13 |
| CasaOS VM201 SSH | michel | Louis_one_13 |
| Nextcloud | michel | Louis_one_14 |
| Nextcloud DB | nextcloud | NextCl...lDB! |
| MCPHub Admin | admin | goetschi2026 (Hash) |
| UniFi | hassio | Riotstar_MICHEL_13 |
| Confluence API | michelgoetschi@gmail.com | ATATT3xFf...93BE5 |
| Notion | michel | Token abgelaufen |

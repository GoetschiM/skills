# Goetschi Labs — Projektinventar (Stand Juni 2026)

Quelle: Notion Teamspace + Confluence, Stand 13.06.2026

## 🌐 Aktive Web-Projekte & Portale

| Projekt | URL | Tech | Status |
|---------|-----|------|--------|
| goetschi-labs.ch | https://goetschi-labs.rebelone.ch | React/Vite SPA + nginx | 🟢 Live (10.0.60.121:1713) |
| grow-pro.ch | https://grow-pro.ch | WordPress | 🟢 Live |
| MotoPoschung | https://moto.rebelone.ch | Next.js 16 + Dokploy | 🟡 Build-Error |
| SIGNAL App | http://10.0.60.121:8420 | Node.js, Dokploy | 🟢 Live (07.06.2026) |

## 🤖 KI-Agenten

| Agent | Rolle | Host |
|-------|-------|------|
| NOVA | Zentrale UI/Schnittstelle | LXC / Dokploy |
| HERMES | Orchestrator, Code | LXC 156 |
| APOLLO | Premium LLM-Zugang | LXC |
| ORION | Gedächtnis / Qdrant | LXC |
| Dograh | Telefonie / Asterisk | CT117 |

## 📈 Trading

| System | Status | Details |
|--------|--------|---------|
| GridBot (Bot04) | 🟢 Live | $16.000+ Echtgeld, MT5, FastAPI |
| NEI v2 | 🟡 Aktiv | Neuronale Erfahrungsintelligenz, Qdrant + PGVector |

## 🏠 Smart Home

| Komponente | Technologie |
|------------|-------------|
| Lichtsteuerung | Philips Hue (OpenHue CLI) |
| Präsenzsensoren | Aqara FP2 (mmWave) |
| PV-Management | EcoFlow PowerStream + DeltaMax 2kWh |
| Sicherheit | Alarmo (Home Assistant) |
| Sprachsteuerung | Amazon Echo + Google Nest |

## 🔧 Infrastruktur

| System | Details |
|--------|---------|
| Proxmox | 2x Intel Xeon, 15 LXC |
| Docker | ~23 Container auf Dokploy |
| Netzwerk | UniFi UDM Pro, VLANs, 5 Segmente |
| Cloudflare Tunnel | goetschi-labs.rebelone.ch |
| MinIO | S3-kompatibler Storage |
| Qdrant | Vektordatenbank (745+ Points) |

## 📦 Kundenprojekte & Individuallösungen

| Projekt/Kunde | Beschreibung | Stack |
|---------------|-------------|-------|
| MotoPoschung | Motorrad-Plattform (Berner Oberland) | Next.js 16, GSAP, Tailwind |
| grow-pro.ch | Pflanzenbau/Indoor-Growing | WordPress |
| Windows-Tools | Bildschirm-Wächter, Input-Recorder | Windows native |
| Paperless-NGX | Doku-Automation + n8n Pipeline | Docker, n8n |

## 🔄 Company Workflows (Automation)

| Workflow | Beschreibung | Auslöser |
|----------|-------------|----------|
| E-Mail Dispatch | Automatische Inbox-Verarbeitung | Cron (alle 15 min) |
| GitHub-Awesome-Reporter | YouTube-Summaries via Phone Call | !ga Command |
| GL-Ticket Polling | Jira → Telegram Benachrichtigungen | Cron |
| System Health Check | 15 Services alle 4h prüfen | Cron |
| Teams Meeting Summary | Pipeline | Event-driven |

## 💡 Wichtige Content-Regeln für die Website

1. **Diversität zeigen** — Nicht nur 1-2 Projekte hervorheben, sondern die ganze Breite
2. **Kundenorientiert sprechen** — "Wir bauen für dich", nicht "Wir experimentieren"
3. **Kein Moto-Poschung-Fokus** — MotoPoschung ist EIN Projekt von vielen
4. **Live-Daten nutzen** — GridBot $16k+, 745+ Qdrant Points, 23 Docker Container
5. **Schweiz-Bonus betonen** — Schweizer Server-Standort, Solarstrom-Betrieb

# CT100 — Trading Bot (GELÖSCHT + NEUPLANUNG)

**Last updated:** 12.06.2026 (19:00)

## ❌ Altes Konzept (Verworfen)

Der `goetschi-labs-mt5-tradingbot-ahilnv` Container wurde **gelöscht** (`docker service rm goetschi-labs-mt5-tradingbot-ahilnv`, Image `rmi`).  
Grund: **Falsche Architektur** — der Container enthielt **NUR** das FastAPI-Backend, kein MT5/Wine. MT5 lief separat auf LXC 504.  
Der User will explizit: **Alles in EINEM Container** (keine Netzwerk-Verteilung).

### Was vor der Löschung passiert ist:
- MQTT gelöscht (nicht verwendet)
- Telegram auf 44 Zeilen Minimal-SendOnly reduziert
- Screenshot-Loop + GUI/Xvfb/pkill Startup entfernt
- main.py neu geschrieben (2s Push, MT5 Auto-Reconnect, EA-File-Monitor)
- Code in api.py von Legacy-Zeugs befreit

## ✅ Neues Konzept: Single Container

**Ziel:** Ein Docker-Container auf CT100/Dokploy mit ALLEM drin.

### Architektur (Single Container)
```
Docker Container (Port 3007→8080)
├── Wine + xvfb (GUI-Emulator für MT5)
├── MT5 Terminal (Terminal64.exe via Wine)
├── EA (Connector_v3.mq5 / GridPro / Confluence)
├── Python App:
│   ├── main.py (Data-Push alle 2s via MT5 Python API)
│   └── api.py (FastAPI Backend, reduziert/minimal)
├── Hermes Agent (später!)
└── Frontend (minimal/optional, kein Full Dashboard)
```

### Key Design Principles
- **Single Container**, kein Multi-Container/Service
- **Alles in Dockerfile**: Wine-Installation, Python, MT5-Konfiguration
- **start.sh**: xvfb starten → wine mt5 terminal → python api.py → python main.py
- **Git-integriert**: Code via GitHub → Dokploy Build/Deploy
- **Hermes später**: Hermes als separater Prozess im selben Container (nicht separater Container!)

### Nächste Schritte
1. Dockerfile schreiben (debian:bookworm-slim, Wine, Python 3.11, Git)
2. start.sh (xvfb-run + wine mt5 + python api/main)
3. MT5 initial install + Demo-Account Bot01 (LibertexCom, Login 510037477) via start.sh
4. Connector EA auf Chart setzen (WebRequest an localhost:8080/api/update)
5. Test: MT5 connected, API liefert Daten
6. Hermes installieren

### Wichtige Credentials
- **Proxmox pve01 SSH**: root / Riotstar_PROXMOX_13 (10.0.60.10)
- **CT100 / LXC 100 SSH**: root / Louis_one_13 (10.0.60.121)
- **MT5 Demo Bot01**: LibertexCom, Login 510037477 (wie bisher, nötig für Start)
- **InfluxDB**: 10.0.60.140:8086 (LXC 109) — Read-Only ohne Auth

### pve01 Access Pattern
```bash
PASS="Riotstar_PROXMOX_13"
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@10.0.60.10 "pct exec 100 -- <command>"
# Oder direkt CT100 (Louis_one_13):
sshpass -p 'Louis_one_13' ssh -o StrictHostKeyChecking=no root@10.0.60.121 "<command>"
```

### Related Tickets
- **TRAD-9:** Trading Bot V2: Sandbox-Kopie + Optimierung
- **TRAD-5:** Trading Bot Vision (AI / Hybrid-System)

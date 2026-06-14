---
title: "MT5 Trading Docker Container Bauen"
name: "mt5-trading-docker"
description: "All-in-One Docker-Container mit Wine + MT5 Terminal + FastAPI Backend für Trading-Bots. Single-Container-Ansatz — MT5, API, Frontend/minimal, spöter Hermes. Nöd übers Netz verteilt."
category: mlops
tags: [mt5, wine, docker, trading, fastapi, deployment, dokploy]
---

# MT5 Trading Docker Container Bauen

E **Single Docker Container** wo alles din isch: Wine + MT5 Terminal + FastAPI Backend (+ optional Hermes). Kei Netzwerk-Verteilig.

## Grund-Prinzipie (Michel, Goetschi Labs)

- **Alles i eim Container:** Wine + MT5 (mind 64-bit, wine32 git's nüm), Python FastAPI Backend, minimales Frontend (optional), spöter Hermes
- **Nüt verteile:** MT5-Connector + API im gliiche Container. MT5 Python Library brucht direkt uf Wine/MT5 zue.
- **Demo-Account zum Teste** (LibertexCom). Niemols Live-Credentials.
- **AI-Hybrid-System:** GridBot + LLM-gsteuerti Optimierig (spöter)

## Dockerfile

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Bern
ENV DISPLAY=:99
ENV WINEARCH=win64
ENV WINEPREFIX=/opt/wineprefix

RUN apt-get update && apt-get install -y --no-install-recommends wine64 xvfb x11vnc fluxbox wget curl ca-certificates python3 python3-pip python3-venv git && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --break-system-packages fastapi uvicorn pydantic python-dotenv requests psutil pyjwt passlib aiosqlite

WORKDIR /app
COPY app/ ./app/
COPY static/ ./static/
COPY bot.env .env
COPY scripts/ /scripts/
RUN chmod +x /scripts/*.sh
EXPOSE 8080
CMD ["/scripts/start.sh"]

## start.sh

```
#!/bin/bash
set -e
Xvfb :99 -screen 0 1280x1024x16 &
sleep 1
fluxbox &
sleep 1
export $(cat /app/.env | xargs)
python3 -m uvicorn app.api:app --host 0.0.0.0 --port 8080 &
python3 /app/app/main.py &
wait
```

## Bekannti Fallstrick

1. **Wine32 git's nüm** — Ubuntu 22.04+ / Debian Bookworm het wine32 nöd. Nur wine64. Kei dpkg --add-architecture i386 mache — das verlengeret de Build um Ewigkeite (i386 Packages).
2. **Build-Zit 5-15 Min** — Immer nohup + build.log. `docker builder prune -af` vor Neustart.
3. **MetaTrader5 pip package** — C-Extension, lang zum kompiliere. `--no-cache-dir` verwende.
4. ***** Syntax Bug** — `***` i os.getenv() corrupted Code. Hardcoded Strings.

## Deployment uf Dokploy CT100 (10.0.60.121)

```bash
# 1. Files kopiere
sshpass -p 'Louis_one_13' scp -r /tmp/mt5-v2-build root@10.0.60.121:/tmp/

# 2. Build (Hintergrund)
sshpass -p 'Louis_one_13' ssh 10.0.60.121 'cd /tmp/mt5-v2-build && nohup docker build -t mt5-trading-v2 -f Dockerfile . > /tmp/mt5-build.log 2>&1 &'

# 3. Monitor
sshpass -p 'Louis_one_13' ssh 10.0.60.121 'tail -f /tmp/mt5-build.log'

# 4. Image prüefe
sshpass -p 'Louis_one_13' ssh 10.0.60.121 'docker images mt5-trading-v2'

# 5. Swarm Service deploye
docker service create --name goetschi-labs-mt5-trading-v2 --publish 3007:8080 mt5-trading-v2:latest
```

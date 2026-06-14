# Single-Container MT5 Bot Bauplan

**Ziel:** Ein Docker-Container auf CT100/Dokploy mit Wine+MT5+API+Hermes alles in einem.

## Basis-Image
- **`debian:bookworm-slim`** (Wine stable verfügbar, kleiner als Ubuntu)
- Oder `ubuntu:22.04` falls Wine issues

## Docker Build Pitfalls (discovered 12.06.2026)

### 1. KEIN `dpkg --add-architecture i386`!
```
❌ RUN dpkg --add-architecture i386 && apt-get update
```
Das aktiviert **alle i386-Pakete** in allen Repos (jammy, updates, backports, security) — apt-get wird tonnenweise Packages laden und ewig dauern. MT5 läuft als **64-bit** App, Wine64 reicht völlig!

**Lösung:** NUR `wine64` installieren, kein `wine32`, kein `wine32:i386`, kein `dpkg --add-architecture i386`.

```
✅ RUN apt-get install -y --no-install-recommends wine64 xvfb ...
```

### 2. Ubuntu 22.04 vs Debian Bookworm
- **Ubuntu 22.04** (Jammy): Wine aus den offiziellen Repos = Version 6.0.3 (alt, aber MT5 funktioniert). Build dauert **15–20 Min.** weil apt-get 187 Pakete (~179 MB) installiert (Wine braucht viele Dependencies: PulseAudio, GStreamer, SDL2, OpenAL, etc.).
- **Debian bookworm-slim**: Schneller, da schlanker Basis. Wine Version = 7.0 (aktueller). Noch nicht getestet.

### 3. `MetaTrader5` pip Package — Lange Kompilierung
Das Python-Paket `MetaTrader5` ist eine C-Extension, die bei `pip install` kompiliert wird. Das kann **5–10 Minuten** dauern, da es Cython-basiert ist und mit Python C-API arbeitet.

**Beobachtung:** Der Build hängt scheinbar beim pip-Install-Schritt — der Docker-Build-Kontext zeigt keine Fortschritte während der Kompilierung. Gib dem Build >600s Timeout!

**Lösung:** Build in Hintergrund starten (`nohup docker build ... >/tmp/out.log &`) und mit `tail -f` überwachen. Der Build scheitert nicht — er dauert nur sehr lange.

### 4. apt-get Lock in Build-Container
Wenn ein früherer Build abbricht (Timeout), bleiben apt-Locks bestehen. Vor Neustart:
```bash
docker builder prune -f
# Alte Build-Prozesse killen:
ps aux | grep "docker build" | grep -v grep
```

### 5. pip Install mit `--break-system-packages`
Auf Debian Bookworm muss `--break-system-packages` bei `pip install` verwendet werden, sonst blockiert PEP 668:
```
✅ RUN python3 -m pip install --break-system-packages fastapi uvicorn MetaTrader5 ...
```

### 6. `fastapi[all]` vermeiden (zu groß)
`pip install fastapi[all]` installiert ~50 zusätzliche Pakete (Jinja2, python-multipart, httpx, aiofiles, etc.). Explizit nur benötigte Pakete installieren:
```
fastapi uvicorn pydantic python-dotenv
requests psutil pyjwt passlib aiosqlite
```

Kein `MetaTrader5` im pip-Schritt testen — MetaTrader5 braucht die C-Kompilierung und verzögert den Build massiv.

## start.sh
```bash
#!/bin/bash
# Start Xvfb (virtual display für Wine/MT5)
Xvfb :1 -screen 0 1280x1024x16 &
export DISPLAY=:1

# Start fluxbox (window manager, braucht MT5 manchmal)
fluxbox &

# Start MT5 Terminal via Wine
wine ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/terminal64.exe &

# Start Python API
cd /app/app
python3 api.py &

# Start main.py (MT5 Data-Push)
python3 main.py &

# Wait for all background processes
wait
```

## requirements.txt
```
fastapi
uvicorn
MetaTrader5
requests
python-dotenv
psutil
httpx
passlib
python-jose[cryptography]
apscheduler
```

## MT5 Initial Setup (einmalig)
Nach Container-Start:
1. **Wine-Prefix initialisieren:** `wine wineboot --init` (erzeugt ~/.wine)
2. **MT5 Installer ausführen:** `wine /tmp/MetaTrader5.exe /auto` (silent install)
3. **MT5 starten:** `wine "$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"`
4. Login mit Demo-Account (LibertexCom, 510037477)
5. Connector EA (Connector_v3.mq5) auf Chart ziehen
6. EA-Parameter: API_URL=http://localhost:8080/api/update, API_SECRET=...

**Hinweis:** Der MT5-Installer (MetaQuotes-Download) kann sich ändern — immer aktuelle URL von `https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/MetaTrader5.exe` holen und prüfen ob das Terminal im Wine läuft. MT5 braucht **kein** `wine32` — die 64-bit Version (`wine64`) funktioniert für MT5 64-bit.

## Hermes Integration (Phase 2)
Nachdem MT5+API laufen:
1. Hermes im selben Container installieren (nicht separater!)
2. `uv pip install hermes-agent` oder Direkt-Download
3. Hermes kommuniziert mit api.py via localhost:8080
4. Hermes kann EA-Set-Files editieren (liegen auf /app/mt5/presets/)
5. Hermes kann Orders triggern via MT5 Python API

## Ports
- **8080**: FastAPI Backend intern
- **3007**: Host-Port → 8080 (via Dokploy)
- **5900**: VNC later (nur für Debug, optional)

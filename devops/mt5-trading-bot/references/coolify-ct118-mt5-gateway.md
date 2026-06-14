# MT5 Gateway Phase 1 — Bauplan (Coolify CT118)

**Stand:** 13.06.2026
**Ziel:** FastAPI Gateway für MT5 (Health, Account, Positions, Orders, Market Data) im Single-Container-Architektur auf Coolify CT118.

## Prinzip

Alles in EINEM Docker-Container auf Coolify CT118 (10.0.60.139):
- Wine + MT5 Terminal (Headless via xvfb)
- FastAPI Gateway (Python)
- Hermes Agent (später Phase 2)

Keine Netzwerkverteilung. Direkter Zugriff auf lokales MT5 via Python MetaTrader5-Bibliothek.

## Aktueller Stand

- MT5 Container läuft auf Port 3007 (`goetschi-labs-mt5-tradingbot:latest`)
- Aktuelle api.py ist **NUR ein Dummy** (`{"status":"migrated"}`)
- Kein SSH/Coolify-API-Zugriff von Hermes aus (siehe `references/coolify-ct118.md`)

## Projektstruktur (geplant)

```
/opt/hermes-trading/            ← NEU: Gateway + Engine
├── gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             ← FastAPI App
│   │   ├── models.py           ← Pydantic Models
│   │   ├── mt5_client.py       ← MT5 Kommunikation (MetaTrader5 Bibliothek)
│   │   └── routes/
│   │       ├── account.py      ← GET /api/v1/account
│   │       ├── positions.py    ← GET /api/v1/positions
│   │       ├── orders.py       ← GET/POST /api/v1/orders
│   │       └── market.py       ← GET /api/v1/market/{symbol}
│   └── docker-compose.yml
├── docs/
│   └── api.md                  ← API-Dokumentation
└── tests/
```

## API Endpoints (Phase 1)

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/api/v1/health` | GET | Gesundheitscheck (Container + MT5-Connection) |
| `/api/v1/account` | GET | Kontostand, Equity, Margin, Margin Level |
| `/api/v1/positions` | GET | Offene Positionen (Symbol, Volume, Profit, SL/TP) |
| `/api/v1/orders` | GET | Aktuelles Orderbuch |
| `/api/v1/orders` | POST | Neue Order (Symbol, Type, Volume, SL, TP) |
| `/api/v1/orders/{id}` | DELETE | Order stornieren |
| `/api/v1/market/{symbol}` | GET | Marktdaten (Bid, Ask, Spread, High, Low) |
| `/api/v1/history` | GET | Historische Trades |
| `/api/v1/risk` | GET | Risikokennzahlen |

## Dockerfile (Basis)

```dockerfile
FROM python:3.11-slim

# Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xvfb \
    fluxbox \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projekt kopieren
COPY app/ /app/
WORKDIR /app

# Startscript
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080

CMD ["/start.sh"]
```

```txt
# requirements.txt
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.9.0
MetaTrader5==5.0.45
```

## Datenbond-Integration (geplant Phase 1b)

Der Datenbond (externer Datenservice) läuft auch auf Coolify → bekommt eigene Endpoints für Marktdaten-Feeds. Details folgen in Phase 1b.

## Umgebungsvariablen (.env)

```
MT5_ACCOUNT=12345678
MT5_PASSWORD=secret
MT5_SERVER=LibertexCom-Server
MT5_PATH=/root/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe
API_PORT=8080
```

## Monitoring & Datenbanken

- **InfluxDB** (separat): CT109 (10.0.60.140:8086) — Zeitreihen-DB für MT5-Metriken
- **Grafana** (separat): CT110 (10.0.60.141) — Visualisierung
- Bot04 sendet Daten bereits via `POST /api/update` → neuer Gateway soll das ebenfalls können

## Nächste Schritte

1. Coolify-Zugriff herstellen (SSH-Key oder API-Token)
2. Projektstruktur auf Coolify anlegen
3. FastAPI Gateway mit ersten 3 Endpoints (health, account, positions)
4. Docker-Image bauen + deployen (im selben Container wie ewiger MT5)
5. Verify: curl http://10.0.60.139:3007/api/v1/health
6. Datenbond-Integration (Marktdaten-Feeds)

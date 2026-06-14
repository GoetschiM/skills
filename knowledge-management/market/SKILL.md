---
name: market
description: Finanz-Marktdaten abrufen via Finhub.io (Quotes, Profile, News, Search, Candles)
category: knowledge-management
tags:
  - finhub
  - market
  - stocks
  - finance
  - api
---

# 📊 Market — Finanzdaten via Finhub.io

## Beschreibung
Ruft Echtzeit- und Fundamental-Marktdaten via [Finhub.io](https://finnhub.io) API ab. Unterstützt Aktien, ETFs, Krypto und Indizes.

## API-Key
Gespeichert im Script (`/root/.hermes/scripts/market.py`):
```
FINHUB_API_KEY = d1f5rthr01qsg7dakmf0d1f5rthr01qsg7dakmfg
```
Zusätzlich 12data-Key vorhanden (noch nöd integriert):
```
12DATA_KEY = e8f390957e6246a78548bce9cb83fd25
```

## Usage
```bash
# Aktuelle Kursdaten
market.py quote TSLA

# Unternehmensprofil
market.py profile AAPL

# Historische Candles (benötigt Premium-Account)
market.py candles MSFT D 2026-04-01 2026-05-17

# News
market.py news NVDA

# Symbol-Suche
market.py search "Bitcoin"
```

## Commands
| Command | Beschreibung | Free Tier |
|---------|-------------|-----------|
| `quote <SYMBOL>` | Real-Time Quote: Current, Change, High, Low, Open, Prev Close | ✅ |
| `profile <SYMBOL>` | Company Profile 2: Name, Exchange, Sector, mktCap, IPO | ✅ |
| `candles <SYMBOL> <RES> <FROM> <TO>` | OHLCV Candles (resolution: 1/5/15/30/60/D/W/M) | ✅ 12data (Limit 8/min) |
| `news <SYMBOL>` | Neuste 5 News-Artikel | ✅ |
| `search <QUERY>` | Symbol-Suche (Firmenname, Ticker) | ✅ |
| `cross <A> <B> [C...]` | Cross-Asset Vergleich + EUR/USD Kurs | ✅ 12data |

## Quellen
- **Finhub.io**: Quotes, Profile, News, Search (60 Req/min Free)
- **12data**: Cross-Asset, Candles (8 Req/min Free, braucht Warteziite bi viele Abfrage)

## Limits (Free Tier)
- **Finhub**: 60 Requests/Minute, kein historische Candles
- **12data**: 8 Requests/Minute (teilt sich uf alli Endpoints)
- News nur letzti 3 Monat

## Integration
- Skill: `knowledge-management/market` (uf MinIO)
- Script: `/root/.hermes/scripts/market.py`
- Confluence: "📊 Market: Finanzdaten via Finhub.io"
- Notion Knowlage Base: Market-Sektion

## Pitfalls
- Candles-Endpoint (Premium) → 403 ohni Paid-Tier
- News-Datum nur ISO-Timestamp (epoch seconds)
- Symbol-Suche: Case-insensitive, aber volle Name für besseri Resultat

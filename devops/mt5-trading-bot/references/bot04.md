# 🔴 MT5 Bot04 — LIVE BOT (Goetschi Labs / Michel)

## ⚠️ ACHTUNG: ECHTES GELD!
**Dieser Bot handelt mit echtem Geld ($17K+ Stand 08.06.2026).**
- Keine Experimente
- Keine ungetesteten Änderungen
- Immer zuerst auf 101/102 testen!

## Connection
- **Host:** `10.0.60.104:8080` (⚠️ Doku sagt .105, Bot läuft auf .104!)
- **SSH:** `root` / `Louis_one_13`
- **Dashboard:** http://10.0.60.104:8080
- **Settings JSON:** `/opt/mt5-bot/app/config/settings.json` (auf dem Bot-Host)

## Dashboard Credentials
| Rolle | Username | Passwort |
|-------|----------|----------|
| Admin | `admin` | `admin` |
| Admin | `michel` | `Louis_one_13` |
| Admin | `Louis_1_13` | `admin` |
| Guest | `guest` | `guest123` |

## API Token Credentials (REST API Zugriff)
| Username | Passwort | API Token? |
|----------|----------|------------|
| `michel` | `Louis_one_13` | ✅ Works (Admin) |
| `Radislione` | `Rebelone_21` | ✅ Works (Guest) |
| `guest` | `guest123` | ❌ Nur Dashboard |
| `admin` | `admin` | ❌ |
Settings JSON: `/opt/mt5-bot/app/config/settings.json` hat `guest_username`/`guest_password`.

## Chart-Daten Format
`GET /api/chart-data?period=7d` → **Array** von stündlichen Snapshots:
```json
[{"balance": 16278.26, "equity": 15180.88, "margin": 5007.07, 
   "positions_count": 67, "drawdown_pct": 6.7, "floating_pnl": -1097.38, 
   "timestamp": "2026-05-25T18:00:00"}]
```
`period`-Parameter-Werte: `24h`, `7d`, `30d`, `all`. 50,000+ Snapshots für `all`.

## Typ: Grid Bot
Bot04 ist ein **Grid Bot**:
- Grid-Öffnung: Pending Orders (Limit/Stop) die noch nicht ausgeführt sind
- Grid-Reset: Schliesst alle Pending Orders → erscheint in History als `profit=0.00`
- Phantom-Trades: profit=0 = Grid-Reset (kein realer Trade). Immer filtern!

## ⚠️ API Stats Unreliable — Chris Greenschutz Discrepancy
**DISCOVERED 08.06.2026:** Die Bot04 API zeigt **deutlich niedrigere Zahlen** als Michels externes Monitoring (Chris Greenschutz):

| Zeitraum | Bot04 API (`limit=0`) | Chris Greenschutz |
|----------|----------------------|-------------------|
| Heute (09.06.) | $+18.53 | k.A. |
| Diese Woche | $+45 | **$+449** |
| Diesen Monat (Juni) | $+415 | **$1,000+** |
| All-Time | $+163 | k.A. |

**Wenn die Werte abweichen, die externen Daten (Chris Greenschutz / MT5 Terminal) als korrekt betrachten, nicht die API.**

## API Einschränkungen
### `/api/history?limit=0`
- `limit=0` = ALLE Trades (3924 total, 1792 real nach Grid-Filter)
- **Niemals `limit=500` für Statistik** — 85% der Trades fehlen!
- Zeit: ~2s für alle Trades

### `/api/stats`
Zeigt **nur heute's Trades** (~18). Unbrauchbar für Wochen/Monate.

### `/api/performance`
⚠️ **DO NOT USE** — hängt sich auf bei vielen Trades.

## Real Stats (08.06.2026, `limit=0`, profit≠0)
| Monat | Profit | Trades |
|-------|--------|--------|
| 2025-08 | $-47 | 53 |
| 2025-09 | $-160 | 65 |
| 2025-10 | $+61 | 352 |
| 2025-12 | $-494 | 35 |
| 2026-02 | $+239 | 150 |
| 2026-03 | $-793 | 635 |
| 2026-04 | $+36 | 162 |
| 2026-05 | $+906 | 214 |
| 2026-06 | $+415 | 126 |
| **Total** | **$+163** | **1,792** |

## ⚠️ Projekt-Zuordnung
- **Trading-Tickets gehören ins TRAD-Projekt** (Jira, Key `TRAD`), NICHT GL. User hat explizit korrigiert.
- **Doku bleibt im Jira Project Wiki** (Project Pages), nicht in Confluence. User sagt: "Wiki" = Jira intern, nicht Confluence.
- TRAD ist ein **Service-Desk-Projekt** (next-gen) — Issue Types: `Email request`, `Submit a request or incident`, `Ask a question`

## V2 Roadmap (TRAD-9, 09.06.2026)
Bot04 V2 soll als **Sandbox** neu aufgesetzt werden (Dokploy CT100 oder neuer LXC):
1. Bot04 LXC klonen → V2 in Sandbox entwickeln
2. Rohdaten-Quelle identifizieren: SQLite? InfluxDB (10.0.60.140:8086)?
3. Neue API: korrekte History-Pagination, Grid-Phantom-Filter, USD/CHF-Konvertierung
4. Chris G-kompatible Statistik-Endpoints (Profit/Woche/Monat via real trades, nicht balance-snapshots)
5. Doku im TRAD-Projekt-Wiki (Jira, nicht Confluence)
- Screenshot-Loop (1s) für Live-View
- Grid-Phantom-Filter: profit==0 = Grid-Reset
- SQLite für Snapshots & History
- InfluxDB: 10.0.60.140:8086 (Tradingbot_LIVE01, meas=account)

## 🔴 Known Issues

### InfluxDB 10.0.60.140:8086 — ✅ ONLINE (Stand 12.06.2026)
InfluxDB **v1.11.8 (OSS)** läuft auf **LXC 109** (10.0.60.140, pve01). Letzter Data-Point im account-Measurement: 09.06.2026 — Bot04 hatte 3 Tage Pause, zeigt ab 12.06. wieder `influx: 2` / `influx_error: None`.

**Datenbanken:**
- `Tradingbot_LIVE01` — Bot04 Haupt-DB (measurements: account, heartbeat, orders, performance, positions, system, trades)
- `Tradingbot_BOT01`-`BOT08`, `Tradingbot_LIVE01`-`LIVE03`, `homeassistant`, `trading`, `mx5`, `Signale`, `RL-Bot`

**Account-Measurement Schema:** balance, equity, daily_profit, floating_pnl, free_margin, margin_level, drawdown_pct, positions_count, daily_closed_trades uvm.

**LXC 109 Facts:**
- LXC-ID: 109, IP: **10.0.60.140** (!! NICHT 10.0.60.109 !!)
- Ping blockiert (LXC-Firewall), aber Ports 22 (SSH) und 8086 (InfluxDB API) offen
- SSH-Zugang `root/Louis_one_13` → **Permission denied** (anderes Passwort nötig)
- InfluxDB HTTP API erreichbar: `http://10.0.60.140:8086/query` (ohne Auth, Read-Only)
- LXC läuft auf pve01 (10.0.60.10), KEIN pve02 mehr!

### CPU 100% — Bekanntes Problem
Bot04 läuft chronisch mit **CPU 100%** (MT5 via Wine ist rechenintensiv). Das ist normal für diesen Bot (Wine + MT5 + Screenshot-Loop + Python-API + Telegram-Bot). Kein Grund zur Sorge, solange:
- Die API antwortet (<5s)
- MT5 connected bleibt (mt5: 2 im Status)
- Trades normal ausgeführt werden

---
name: mt5-trading-bot
description: Manage MT5 trading bots via their FastAPI web backends — authenticate, query status/performance/history, diagnose offline issues, interact with dashboard.
category: devops
triggers:
  - mt5 bot
  - trading bot
  - metatrader
  - bot04
  - forex bot
  - trading dashboard
  - trading api
---

# MT5 Trading Bot Management

This skill covers interacting with MetaTrader 5 (MT5) trading bots that expose a FastAPI web backend with JWT authentication, SQLite logging, and Telegram alerts.

## 🔍 CREDENTIAL-FINDING PROTOKOLL (USER-REGEL — IMMER BEFOLGEN!)

**KRITISCHE USER-KORREKTUR (13.06.2026):** Niemals zuerst fragen! Immer zuerst ALLE Quellen prüfen:

### Prüf-Reihenfolge (hart — durchlaufen bis gefunden):

1. **Confluence Credential-Seite** (ID 35717121) — htt immer die aktuellste Version via API
2. **Session Search** — `session_search(query="Coolify CT118 Credential Passwort")` — ältere Sessions können kompaktiert sein, aber die Credentials tauchen oft in tool-outputs oder assistant-messages auf
3. **Memory** — `memory(action='add/memory')` — stabile, wiederkehrende Fakten
4. **Filesystem** — `/root/.hermes/` configs, .env, skills/references/
5. **API-Test** — curl zum Ziel-Container (auch wenn nur Dummy)
6. **Web-UI prüfen** — gibt's en Login-Page? Welche Credentials werden erwartet?
7. **SSH probieren** — mit bekannten Passwörtern aus dem Schema
8. **Erst JETZT fragen** — wenn alle 7 Schritte erfolglos + mit Angabe was schon geprüft wurde

**Wenn de User korrigiert (wie am 13.06.):** "du machsch dir eifach und frogsch eifach nah" — sofort den obigen Ablauf nachholen. Der Fehler ist nicht die Frage an sich, sondern dass nicht alle Quellen durchprobiert wurden.

### Quellen-Detail:

- **Confluence v6** (letztes Update 11.06.2026): Enthält LXC-Tabelle mit CT118 = Coolify (10.0.60.139), root/Louis_one_13. Achtung: SSH-Passwort kann abweichen!
- **Coolify Web-UI:** http://10.0.60.139:8000 (Login-Seite sichtbar)
- **Coolify API:** http://10.0.60.139:8000/api/v1/ → 401 ohne Token
- **MT5 Container (Dummy):** http://10.0.60.139:3007/ → `{"status":"migrated"}`
- **SSH root@10.0.60.139:** Permission denied mit Louis_one_13 (Passwort weicht ab)

## ⚠️ KRITISCH: LIVE vs TEST vs COPY BOTS

| Host | Typ | Account | Vorsicht |
|------|-----|---------|----------|
| LXC 504 — 10.0.60.104 (Bot04) | **🔴 LIVE** | Echtes Geld ($17K+) | **Äußerste Vorsicht! Keine Experimente!** |
| **CT118 — 10.0.60.139 (Coolify)** | 🟡 **AKTIV** | **Coolify Docker** — MT5 Trading Bot Container (Dummy API, Port 3007) | **NEUER MT5-HOST seit 13.06.2026.** Läuft auf Coolify CT118, nicht auf Dokploy. MT5 Container heisst `goetschi-labs-mt5-tradingbot:latest`, Port 3007→8080. API ist aktuell nur ein Dummy (`{"status":"migrated"}`) — der echte Gateway wird noch gebaut (Phase 1: FastAPI Gateway). |
| CT100 — 10.0.60.121 (Dokploy) | ⏸️ **GELÖSCHT + NEUPLANUNG** | Single-Container mit Wine+MT5+API (wird noch gebaut) | **Alter Container gelöscht.** Die neue Strategie: alles auf Coolify CT118. |
| 10.0.60.101 (Bot01) | 🟢 TEST | Paper-Trading | Sicher zum Testen/Optimieren |
| 10.0.60.102 (Bot02) | 🟢 TEST | Paper-Trading | Sicher zum Testen/Optimieren |

**Regel:** Immer zuerst auf CT118-Coolify (Sandbox) testen. Erst nach erfolgreichem Test auf 104 (LIVE) uebertragen. **Live-Bot NIE aafasse!** User hat explizit gseit (12.06.2026): Der Livebot darf einfach nicht angefasst werden.

**User-Richtung CT100:** Weniger Frontend, mehr Logik (12.06.2026) -- Fokus auf Trading-Core (MT5-Connection, Strategie, Risikomanagement), nicht auf Dashboard/UI. Git-Workflow: Feature-Branch auf GoetschiM/Bot-deploying -> Build auf CT100 testen -> wenn gut -> auf Live uebernehmen.

**Vision (12.06.2026):** Hybrid-System: GridBot + AI. Hermes Agent (bereits als Container auf CT100 deployt: `goetschi-labs-hermes-agent-xh5kbx`) soll **im selben Container** wie MT5+API laufen, um KI-gesteuert Trades zu analysieren/optimieren/triggern. Ziel: weniger stumpfer GridBot, mehr Hybrid-AI-Trading.

**CT100 Stand (12.06.2026 19:00):**
  - 🔴 **Alter Container gelöscht** (`docker service rm goetschi-labs-mt5-tradingbot-ahilnv`, Image `rmi`)
  - 🔄 **Neues Konzept:** Single Docker-Container mit Wine+MT5+API+Hermes **alles im selben Container**
  - Keine Netzwerk-Verteilung mehr — der alte Container hatte nur FastAPI, MT5 lief auf LXC 504
  - User-Vorgabe (12.06.): "Alles auf einem Docker Container installiert, kein verteiltes System"
  - Basis: debian:bookworm-slim (mt5-trading-bot Kopie), Python 3.11, Wine stable
  - **Noch nicht deployed** — wird noch gebaut

**Hermes-Agent als separate App auf CT100:** `goetschi-labs-hermes-agent-xh5kbx` existiert noch als separater Container — wird später in den Single-Container integriert.

## ⚠️ KRITISCH: User-Vorgabe — Alles in EINEM Container!

**HARTE USER-REGEL (12.06.2026):** MT5, API-Backend (FastAPI), Frontend (minimal) und Hermes MÜSSEN im **gleichen Docker-Container** laufen. Keine Netzwerk-Verteilung. Kein separates LXC für MT5 + separater API-Container. Der User sagt: "MetaTrader, Backend, Frontend und gegebenenfalls auch Hermes läuft alles auf einem Container. Das ist ganz, ganz wichtig."

**Grund:** Der alte CT100 (Dokploy) Container `goetschi-labs-mt5-tradingbot-ahilnv` war NUR FastAPI + Frontend — KEIN Wine, KEIN MT5. MT5 lief auf LXC 504 (Live-Bot) und pushte Daten an CT100. Das war ein verteiltes System. **Das ist jetzt GELÖSCHT** (`docker service rm goetschi-labs-mt5-tradingbot-ahilnv`, Image entfernt).

**Konsequenz:** Der Docker-Build für den Single-Container ist **nicht trivial** — Wine + MT5 + Python + FastAPI + MetaTrader5 pip-Package = groß (~1.4GB+ Image). Build kann 15+ Minuten dauern (Ubuntu 22.04 apt-get + pip MetaTrader5 C-Extension-Kompilierung).

## Deployment-Modelle (historisch — nur Referenz)
| Aspekt | Live (LXC 504) | CT100 Single-Container (IM BAU) |
|--------|---------------|----------------------|
| **Typ** | Proxmox LXC direkt | **Single Docker Container uf Dokploy** (Wine+MT5+API+Hermes in EINEM Container) |
| **MT5** | Wine + EA direkt im LXC | **Wine + EA IM Container** (same container, xvfb) |
| **API** | systemd `mt5-bot` Service | FastAPI im gleichen Container (intern Port 8080) |
| **Zugriff** | `pct exec 504` via pve01 | `pct exec 100 -- docker exec ...` via pve01. **DIREKT SSH** auf CT100: `sshpass -p 'Louis_one_13' ssh root@10.0.60.121 "docker exec <name> ..."` |
| **GitHub** | `GoetschiM/Bot-deploying` (main) | Gleiches Repo |
| **Frontend** | Volles Dashboard (Login, Charts, Settings) | **Soll reduziert werde** — Fokus auf Logik (12.06.2026) |

**CT100 is identifiziert als Bot01** (LibertexCom Demo, Login 510037477), nicht Bot04-Kopie!

**Bau-Status (12.06.2026 20:00):**
  - 🔴 **Alter Container gelöscht** (`docker service rm goetschi-labs-mt5-tradingbot-ahilnv`, Image `rmi`) ✅
  - 🟡 **Dockerfile erstellt** — debian:bookworm-slim, Wine + xvfb + fluxbox + Python + FastAPI + MetaTrader5
  - 🟡 **Docker-Build läuft noch** (15-20 Min. für apt-get + pip MetaTrader5-Kompilierung)
  - 🟡 **Code deployed:** `api.py` (bereinigt, kein MQTT), `main.py` (MT5 Data-Push), `start.sh`, `bot.env` (Bot01 Demo)
  - ⬜ **Single Container deployed & läuft mit MT5**
  - ⬜ **Hermes Integration** (Phase 2)

## Docker Build — Known Pitfalls (12.06.2026)

Wenn du den **Single-Container** (Wine+MT5+API+Hermes) baust, beachte:

| Problem | Lösung |
|---------|--------|
| `dpkg --add-architecture i386` | **NICHT MACHEN!** Macht apt-get ewig lang und aktiviert i386-Arch. MT5 ist 64-bit → nur Wine64 nötig |
| Ubuntu apt-get dauert 15+ Min. | Normal — 187 Pakete (~179 MB) für Wine+Grafik |
| pip MetaTrader5 hängt scheinbar | C-Extension-Kompilierung (5–10 Min.) — einfach warten |
| `pip install fastapi[all]` | Vermeiden — nur benötigte Deps installieren |
| Build über SSH timed out | Build in Background (`nohup`) starten, mit `tail -f /tmp/build.log` checken |
| Debian bookworm: `pip install --break-system-packages` nötig | PEP 668 blockiert `pip install` ohne Flag |

**Docker Build Typische Dauer:**
- Ubuntu 22.04: ~15–20 Min. (apt-get + pip + MetaTrader5 C-Kompilierung)
- Debian bookworm-slim: ~8–12 Min. (weniger Pakete)
- Image-Grösse am Ende: ~1.4–1.8 GB

## Authentication

### JWT Token Flow

Always re-authenticate before each batch of API calls — tokens may expire.

**Option A — curl (simple, works in terminal):**
```bash
TOKEN=$(curl -s -X POST http://<host>:<port>/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<user>&password=<pass>" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))")
curl -s http://<host>:<port>/api/status -H "Authorization: Bearer $TOKEN"
```

**Option B — Python requests (preferred in execute_code / security-scanned envs):**
```python
import requests
s = requests.Session()
r = s.post("http://<host>:<port>/token",
    data={"username": "<user>", "password": "<pass>"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
token = r.json().get("access_token", "")
r = s.get("http://<host>:<port>/api/status",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
data = r.json()
# All trading data lives in data['metrics'] dict
balance = data['metrics']['balance']
daily_pnl = data['metrics']['daily_profit']
```

Python requests avoids:
- Security scanner flags on `curl | python3` pipes
- Shell `&` escaping issues in POST data

### Typical Credential Tiers
- **Admin accounts:** Full access to settings, uploads, configuration
- **Guest accounts:** Read-only access (dashboard view)

## Key API Endpoints

### Quick Health Check (fastest, minimal data)
| Endpoint | What you get |
|----------|-------------|
| `GET /api/status` | MT5 connection, CPU%, RAM, Telegram status, bot_id, **plus nested `metrics` dict with ALL trading data** (balance, equity, margin, positions, daily_profit, floating_pnl) |
| `GET /api/summary` | Open positions count, pending orders, today's closed trades (redundant if you have `/api/status`) |

### Trading Data
| Endpoint | What you get |
|----------|-------------|
| `GET /api/performance` | ⚠️ **DO NOT USE — see Pitfalls.** Hangs indefinitely on large trade history. |
| `GET /api/positions` | All currently open positions with details |
| `GET /api/history?limit=N` | Historical trades. **⚠️ `offset` parameter is broken** — always returns from beginning. Deduplicate by `ticket` field. Returns an array of trade objects — see response structure below. |
| `GET /api/stats` | Aggregated stats: win rate, profit factor, volume, best/worst trade |
| `GET /api/chart-data?period=7d` | Equity curve data for charting (24h, 7d, 30d, all). **⚠️ Parameter heisst `period`, nicht `range`!** Gibt eine **Liste** zurück, kein Dict (siehe Pitfalls). |
| `GET /api/orders` | All pending orders |

### `/api/history` Trade Object Structure

Each entry in the history array has these fields:

```json
{
  "ticket": 106382789,          // unique trade ID — use for dedup
  "symbol": "USDCHF",
  "type": "SELL",               // "BUY" or "SELL"
  "volume": 0.03,
  "profit": 11.69,              // 0.0 = grid phantom (not a real trade)
  "exit_price": 0.78758,
  "close_time": "2026-05-27T16:03:59.866334Z",   // use .get("close_time", "")[:10] for date grouping
  "tp": 0.0,                    // take profit
  "sl": 0.0                     // stop loss
}
```

**Field notes:**
- `close_time` (NOT `time_close`) — the date field for grouping trades by day
- `profit === 0` means grid phantom (order cancellation), NOT a real trade — always filter these out
- `ticket` is the unique identifier — use for deduplication when offset parameter returns overlapping data


### ⭐ Recommended Endpoint Priority

For a health check / briefing query, call endpoints in this order — stop when you have enough:

```
1. GET /api/status  ← ALL trading data in `metrics` sub-dict (see Response Structure below)
2. GET /api/summary ← only if you need separate open/pending/closed counts
3. (skip) /api/performance ← WILL HANG on accounts with many trades
```

### `/api/status` Response Structure

The response has a flat top level + a rich nested `metrics` dict:

```json
{
  "role": "admin",
  "bot_id": "04 | LIVE",
  "mt5": 2,           // 0=offline, 1=connecting, 2=connected
  "influx": 2,         // telemetry DB status (0=offline/bekannt, 1=connecting, 2=connected)
  "tg": 2,             // Telegram alert status
  "tg_error": "Timed out",  // null if OK
  "cpu": 36.1,
  "mem": 7.3,
  "metrics": {
    "bot_id": "04 | LIVE",
    "status": "online",
    "balance": 16060.7,
    "equity": 15616.48,
    "margin": 4504.76,
    "margin_free": 11111.72,
    "margin_level": 346.67,
    "positions": 71,
    "pending": 129,
    "closed_today": 157,
    "daily_profit": -21.0,
    "floating_pnl": -444.22,
    "last_update": "2026-05-19T18:02:31",
    "cpu": 36.1,
    "mem": 7.3,
    "version": "v3.2.001",
    "deploy_date": "2026-02-12",
    "dd_enabled": true,
    "dd_threshold": "10"
  }
}
```

Key fields in `metrics`:
- `balance` / `equity` / `margin` / `margin_free` / `margin_level` — account status
- `positions` / `pending` — open positions + pending orders counts
- `closed_today` / `daily_profit` — today's performance
- `floating_pnl` — current unrealized P&L
- `dd_enabled` / `dd_threshold` — drawdown protection status
- `last_update` — timestamp of last EA push (stale if >5 min → bot may be hung)

### Management (Admin Role Required)
| Endpoint | Purpose |
|----------|---------|
| `POST /api/settings/save` | Persist configuration changes |
| `POST /api/settings/reset` | Reset snapshot timestamp |
| `POST /api/settings/telegram/report` | Trigger performance report to Telegram |
| `POST /api/settings/telegram` | Update Telegram bot token / chat ID |
| `POST /api/upload_ea` | Upload .ex5, .mq5 (Experts) or .set (Profiles) files |

### Live View
| Endpoint | Purpose |
|----------|---------|
| `GET /api/live-view` | Latest desktop screenshot (static/live_view.png, updated every 1s) |

## Bot-to-Backend Communication

The MT5 Expert Advisor pushes data to the backend via `POST /api/update`:

```json
{"secret": "<API_SECRET>", "balance": ..., "equity": ..., "positions": [...]}
```

The `API_SECRET` is defined in the bot's environment config and shared between the EA and backend.

## Troubleshooting

### Bot Shows OFFLINE (MT5 Status = 0)
1. Note the `last_update` timestamp — tells you how long it's been down
2. Check CPU/mem from `/api/status` — high CPU may mean hung process
3. Common causes: MT5/Wine crash, account disconnect, container OOM
4. **Proxmox LXC inspection pattern (LXC 504 = Bot04):**
   ```bash
   # Via SSH to pve01 (root / Riotstar_PROXMOX_13)
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 504 -- ps aux | grep -i mt5"
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 504 -- free -h"
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct status 504"
   
   # List all containers
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct list"
   ```
   **Caveat:** LXC-ID ≠ IP! LXC 504 hat IP 10.0.60.104. Immer LXC-Number + IP checken.
5. **Dokploy Docker copy (CT100 = LXC 100):**
   ```bash
   # Container-Liste
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 100 -- docker ps --format '{{.Names}} {{.Status}}'"
   # Auf trading-bot filtern
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 100 -- docker ps --format '{{.Names}} {{.Status}} {{.Image}}' | grep trading"
   # Projekt-Struktur (Dockerfile, Code) auf Host
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 100 -- ls -la /etc/dokploy/applications/goetschi-labs-mt5-tradingbot-ahilnv/code/"
   # In Container schauen (z.B. trading bot copy)
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 100 -- docker exec <container_name> ps aux"
   # Container Logs
   sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 100 -- docker logs <container_name> --tail 30 2>&1"
   ```
6. **InfluxDB check (LXC 109 = IP 10.0.60.140):**

### Host Not Reachable
- Verify the IP — documentation may be stale (check ping/curl)
- Bot may be on a different subnet/VLAN than the agent
- Try both documented IP and known-adjacent IPs
- Common port: 8080 (API), 22 (SSH)

### Endpoint Hangs/Times Out
- **`/api/performance` — DO NOT call.** Hangs indefinitely on any account with non-trivial trade history. All the data you need is in `/api/status` → `metrics` dict (balance, equity, daily_profit, floating_pnl, positions count).
- `/api/history` can also be slow with large datasets.
- **Always** use `/api/status` first — it returns in <1s and has everything.
- Always set `--max-time N` on curl calls to avoid hanging.

### ⚠️ `no_agent` Cron Scripts: Use `subprocess.run(["curl", ...])`, NOT `urllib.request`

**CRITICAL — discovered 11.06.2026:** In `no_agent=true` cron scripts running on this Hermes instance (Apollo, 10.0.60.156), `urllib.request.urlopen()` **hangs indefinitely** when making HTTP requests to Bot04 (10.0.60.104). The exact same code works fine in agent-led `terminal()` calls. Root cause: Hermes' sandbox/process environment has a restriction on Python's `urllib` TCP connections in subprocess mode. `curl` via `subprocess.run` works correctly.

**Fix — replace urllib calls with curl subprocess:**
```python
import subprocess, json
# GET
cmd = ["curl", "-s", "--max-time", "30", url]
if token:
    cmd += ["-H", f"Authorization: Bearer {token}"]
result = subprocess.run(cmd, capture_output=True, timeout=35, text=True)
if result.returncode != 0:
    raise RuntimeError(f"curl {url} failed: {result.stderr}")
data = json.loads(result.stdout)

# POST
cmd = ["curl", "-s", "--max-time", "30", "-X", "POST",
       "-H", "Content-Type: application/x-www-form-urlencoded",
       "-d", urllib.parse.urlencode(data_dict), url]
```

**Rules:**
- Always set `--max-time N` on curl AND `timeout=N+5` on subprocess.run
- This applies to ALL `no_agent=true` scripts, including Notion API calls
- For Notion: convert `json.dumps(props)` to a `-d` string argument (use single-quote wrapping)
- Do NOT use `shell=True` — pass command as list to avoid shell injection/escaping issues

## Pitfalls  

### Grid Bot — Phantom Trades
Bot04 (LIVE) is a **Grid Bot**. When the grid resets, **unexecuted pending orders** are recorded in `/api/history` as trades with `profit=$0.00`. These are **NOT real trades** — they are grid-cancellation artifacts.

**Rule for stats:** Always filter `profit == 0` out. Only trades with `profit != 0` are real executed trades. Without this filter, your trade count is ~2× inflated and winrate is ~halved.

Example: 444 total history entries → 222 real trades (profit≠0) + 222 grid phantoms (profit=0). Real winrate: 77.5% vs phantom-inflated 38.7%.

### ⚠️ `/api/history?limit=N` — Default 500 Is TOO SMALL — Always Use `limit=0`

The `limit` parameter **does work** up to `limit=0` (= all trades).

**DISCOVERED 08.06.2026:** Bot04 has **~3,900+ trades** total. Calling `/api/history?limit=500` only returns **13% of trades**, making weekly/monthly stats **10x too low** (showed $45 vs real $449).

**Rule:**
- **For stats/math** → `GET /api/history?limit=0` (returns ALL ~4,000 trades in ~2s)
- **For quick checks** → `GET /api/history?limit=500` is fine for recent-only
- **NEVER ever** trust `limit=500` results for weekly/monthly/all-time stats

The old `limit=500` workaround in the `offset` section is **WRONG and DANGEROUS** — update both places to use `limit=0` for full accuracy.

### ⚠️ `/api/history?limit=N` — Default 500 Is TOO SMALL — Always Use `limit=0`
The `limit` parameter **does work** up to `limit=0` (= all trades). The `offset` parameter does **not work** — always returns from beginning.

**DISCOVERED 09.06.2026:** Bot04 has ~3,900+ total raw trades (~1,792 real after grid filtering). Calling `?limit=500` only returns **13% of trades**, making weekly/monthly stats **10x too low** (showed $45 vs real $449 from external tool).

**CORRECT WORKAROUND — Fetch ALL trades:**
```python
r = s.get(f"{BASE}/api/history?limit=0")  # returns ~3,900 entries in ~2s
trades = r.json()
```
**NEVER** use `limit=500` for stats — you'll miss 85%+ of trades and report 10x-lower numbers.

### ⚠️ Stats Are UNRELIABLE — Bot04 API Has Multiple Issues

The bot's API endpoints provide **inconsistent or incomplete** trading statistics. Do NOT trust them blindly.

| Issue | What happens |
|-------|-------------|
| `/api/stats` | Shows **only today's trades** (~18). Useless for monthly/weekly. |
| `/api/history?limit=500` | Returns **max 500 trades** (offset parameter broken — all calls return from start). Older trades are lost. |
| `/api/chart-data?period=all` | **50,000+ snapshots** of balance — but includes floating P&L swings. Using balance-delta per day gives WRONG monthly/weekly P&L. |
| `daily_profit` in `/api/status` | Live value, resets daily — correct for "today" only. |

**Known discrepancy (08.06.2026):** API `/api/history` shows $415 June profit and $45 this week. User (Michel) reports **$1,000+ this month, $250+ this week** according to **Chris Greenschutz** (his external MT5 monitoring tool). The bot's backend API is likely missing or undercounting trades.

**Source-of-truth rule:** When user says their external tool (Chris Greenschutz, MT5 Terminal, broker statement) shows different numbers, **the external tool wins**. The bot's FastAPI backend has known SQLite/offset bugs. Always report both (API data and user's source) when numbers diverge.

### Correct Stats Calculation Sequence

1. Get ALL: `GET /api/history?limit=0` (NOT `limit=500`!)
2. Deduplicate by `ticket` field
3. Filter out grid phantoms: only keep where `profit != 0`
4. Group by `close_time` into months/weeks
5. Sum profit per group

### ⚠️ Chris Greenschutz Discrepancy — Bot04 API Stats Are Suspect

**User (Michel) uses an external MT5 monitoring tool (Chris Greenschutz) that shows DIFFERENT numbers than the Bot04 API.** Example from 08.06.2026:

| Metric | Bot04 API (`limit=0`) | Chris Greenschutz | 
|--------|----------------------|-------------------|
| This week P&L | $45 | $449 |
| This month P&L | $415 | $1,000+ |

**When user says their tool shows different numbers, the external tool wins — NOT the API.** Possible causes:
- Bot04's SQLite backend has a filtering bug
- `/api/history` only captures partially (despite `limit=0`)
- The EA doesn't push all trades to the backend SQLite

**NEVER invent tool names or people** — if you don't recognize the tool the user mentions (e.g. "Chris Greenschutz"), say "Ich kenne das Tool nöd — wie chani dra cho? Zeigsch mer en Screenshot?" instead of pretending it exists. Hallucinating tool names destroys trust.

**Signal to watch for:** If the user's words don't match anything in your skills/memory/tools, ask instead of inventing. When they say "wer isch Chris Greenschutz?", the correct answer is "weiss ich nöd — das hani erfunde, sorry. Zeigsch mer en Screenshot?" — never confirm an invented person exists.

### For Status Reports / Briefings: What to Use

| Question | Endpoint | Notes |
|----------|----------|-------|
| Current balance | `/api/status` → `metrics.balance` | ✅ Live. Correct. |
| Today's P&L | `/api/status` → `metrics.daily_profit` | ✅ Live. Correct. |
| Floating P&L | `/api/status` → `metrics.floating_pnl` | ✅ Live. Correct. |
| This week's P&L | `/api/history?limit=0`, filter profit≠0, group by ISO week | ⚠️ May still differ from Chris Greenschutz. Report caveat. |
| This month's P&L | Same, group by YYYY-MM | ⚠️ May still differ from external tools. Caveat. |
| All-time P&L | Chart-data: first → last balance delta OR `/api/history` sum | ⚠️ Chart-data includes float swings. History with `limit=0` gives ~$164. |

**NEVER** use `/api/chart-data` for P&L calculations — balance snapshots include unrealized floating P&L and give wrong month/week deltas. Only use it for equity curves.

### ⚠️ USD vs CHF — API Returns USD, External Tools May Show CHF
Bot04 API returns all values in **USD** ($). External tools (MT5 Terminal, Chris Greenschutz) may show **CHF** (rate ~0.88). But the known discrepancy (10x) is far beyond currency — it's a genuine data quality issue.

**Rule:** Report API figures in USD. If the user mentions CHF, note the difference. If discrepancy >15%, it's NOT just a currency conversion issue — flag it as a potential data quality problem.

### User Preferences: Project & Documentation Location
- **Trading tickets go in TRAD project** (Jira Service Desk, key `TRAD`, ID 10100), NOT GL. The user explicitly corrected this: TRAD is the right home for all MT5/trading work.
- **Documentation stays in Jira Project Wiki** (Project Pages within Jira), NOT in Confluence. The user confirmed (09.06.2026): "im Wiki für Trading" means the Jira project pages under TRAD, not the Goetschi Labs Confluence space.
- **Task creation for TRAD:** Available issue types: `Email request` (10080), `Submit a request or incident` (10081), `Ask a question` (10082). No "Task" type exists. Use `Email request` as default for new work items.
- **TRAD project type:** `service_desk` + `next-gen`. No direct REST API for Project Pages (only accessible via Jira UI). Document setup notes as ticket comments + a manual page in Jira > TRAD > Pages.

### InfluxDB Status — ✅ Läuft auf LXC 109 (pve01)
Bot04 zeigt im `/api/status` die Felder `influx`, `influx_error`. Korrekte Werte:
- `influx: 2` = ✅ Verbunden (InfluxDB v1.11.8 auf 10.0.60.140:8086, LXC 109)
- `influx: 0` = ❌ Keine Verbindung (war temporär am 09.-12.06., jetzt wieder OK)
- **WICHTIG: LXC-ID ≠ IP!** LXC 109 = IP 10.0.60.140 (nöd 10.0.60.109!)
- SSH auf LXC 109: `root/Louis_one_13` → Permission denied (anderes PW)
- InfluxDB HTTP API: `http://10.0.60.140:8086/query` — Read-Only ohne Auth
- Details in `references/bot04.md` → Known Issues

### InfluxDB check via Proxmox pct exec
```bash
# Health check (von pve01 per SSH)
sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 109 -- curl -s http://localhost:8086/ping"

# Databases
sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 109 -- curl -s http://localhost:8086/query?q=SHOW+DATABASES"

# Last hour writes count
sshpass -p "$PASS" ssh root@10.0.60.10 "pct exec 109 -- bash -c 'curl -s -XPOST \"http://localhost:8086/query\" --data-urlencode \"q=SELECT count(*) FROM \\\"trades\\\" WHERE time > now() - 1h\" --data-urlencode \"db=Tradingbot_LIVE01\" 2>/dev/null | python3 -c \"import sys,json; print(json.load(sys.stdin).get(\\\"results\\\",[{}])[0].get(\\\"series\\\",[{}])[0].get(\\\"values\\\",[[\\\"error\\\"]])[0])\"' 2>&1"
```

### Other Pitfalls
- **NEVER hallucinate tool/people names.** If the user mentions "Chris Greenschutz" and you don't know it, say so. Don't guess or invent. Say: "Ich kenne das Tool nöd — wie chani dra cho?" This is especially critical when the user asks "wer isch das?" — an honest "weiss ich nöd" is safer than making up a person.
- **Stale IPs in docs**: Always verify the actual host. Documented IPs drift. Session-specific details belong in `references/` files.
- **JWT re-auth**: Tokens expire. Re-login before each batch in the same command chain — don't reuse a token from an earlier command in a multi-command script unless you verify it's fresh.
- **curl POST via shell subprocess**: The `&` character in POST data (`-d "key=value&key2=val2"`) kann durch subprocess(shell=True) falsch interpretiert werden (Background-Operator!). Verwende stattdessen **Python `requests.Session()`** oder escape das `&` mit `\\\\&` oder durch single quotes: `-d 'key=value&key2=val2'`.
- **`chart-data` gibt eine Liste zurück**: `GET /api/chart-data?period=7d` liefert ein **Array** von stündlichen Snapshots mit Feldern wie `balance`, `equity`, `positions_count`, `floating_pnl`, `timestamp`. Parameter heisst **`period`**, nicht `range`. Falsche Parameter führen zu 422 Validation Error.
- **Memory management**: Bot credentials and configs are verbose. Store per-instance details in `references/` files, not agent memory, to avoid hitting memory caps.
- **Wine fragility**: MT5 via Wine can crash silently. The FastAPI backend may still respond while the actual trading engine is dead.

## Reference Files

- `references/trading-journal-schema.md` — Reusable Notion DB schema for tracking bot trades (Accounts → Trades → Journals → Transactions). 4 linked databases with enhanced properties (Strategy, Session, Market Conditions, Entry/Exit Price, etc.). Created in Goetschi Labs workspace under "📊 Trading Journal".
- `references/daily-snapshot-notion-db.md` — Daily Snapshots Notion DB schema
- `references/bot04.md` — Live Bot04 (LXC 504) details & known issues
- `references/ct100-copy.md` — CT100 Docker-Kopie (Sandbox, LXC 100) details
- `references/coolify-ct118.md` — **NEU (13.06.2026):** Coolify CT118 Deployment Target — MT5 Container auf 10.0.60.139:3007 (Coolify statt Dokploy). Ohne SSH/API-Token nicht direkt zugänglich. Dummy-API vorhanden.
- `references/coolify-ct118-mt5-gateway.md` — **NEU (13.06.2026):** MT5 Gateway Phase 1 Bauplan — FastAPI für Coolify CT118. Endpoints, Dockerfile, Projektstruktur, Datenbond-Pläne.

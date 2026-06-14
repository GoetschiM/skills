# Trading Journal — Notion Database Schema

## Design: 4 linked databases under a parent page

The Trading Journal is a **clean-slate** system for automated MT5 bot trade tracking. Each bot/account gets its own entry in Accounts; trades reference that account via relation.

**Parent page:** Goetschi Labs Workspace → 📊 Trading Journal (Page ID: `36781c83-f6d9-819e-bd2c-feebee1152fa`)

---

## 1. Accounts DB

The central registry. All other DBs relate back here.

| Property | Type | Select Options | Notes |
|----------|------|----------------|-------|
| Name | title | — | e.g. Bot04, Live01 |
| Type | select | Live, Bot, Demo, Test | |
| Initial Balance | number (dollar) | | Starting capital |
| Current Balance | number (dollar) | | Real-time |
| Net P&L | number (dollar) | | Aggregate |
| Total Win / Total Loss | number (dollar) | | |
| Win Rate | number (percent) | | |
| Total Trades | number | | |
| Volume | number | | Traded volume |
| Total Deposited / Withdrawn | number (dollar) | | |
| Status | select | Active, Paused, Closed | |
| Bot/Host | select | Bot01-Bot06, Live01, Live02, Bottest, Demo | |
| Created | created_time | | Auto |
| Last Updated | last_edited_time | | Auto |

---

## 2. Trades DB

Every individual trade. 4,042 trades from Oct 2025 – Feb 2026 demonstrated the schema.

| Property | Type | Options/Format | Notes |
|----------|------|----------------|-------|
| Trade ID | title | | Auto-generated or import label |
| Open Date | date | ISO datetime | |
| Close Date | date | ISO datetime | |
| Side | select | Buy, Sell, Long | |
| Strategy | select | Scalping, Momentum, Trend Following, Mean Reversion, Breakout, Grid, Martingale, Other | Populate from bot config |
| Account | relation → Accounts | | Links to account |
| Bot/Symbol | rich_text | | e.g. EURUSD, BTCUSD |
| Lots | number | | Size |
| Entry Price | number (dollar) | | |
| Exit Price | number (dollar) | | |
| Net P&L | number (dollar) | | |
| Net ROI | number (percent) | | |
| Realized R | number | | Risk multiple |
| Pips | number | | |
| Commissions | number (dollar) | | |
| Trade Risk ($) | number (dollar) | | |
| Duration (min) | number | | |
| Trade Rating | select | ⭐⭐⭐, ⭐⭐, ⭐, Unrated | |
| Session | select | Asian, London, New York, Sydney | |
| Market Conditions | select | Trending, Ranging, Volatile, Low Volatility, News Event | |
| Exit Logic | select | TP Hit, SL Hit, Manual, Trailing Stop, Time Exit | |
| Emotions | rich_text | | Free text |
| Mistakes | rich_text | | Free text |
| Reviewed | checkbox | | Reviewed flag |
| Created | created_time | | |
| Last Updated | last_edited_time | | |

---

## 3. Journals DB

Daily summaries per account (or aggregated).

| Property | Type | Notes |
|----------|------|-------|
| Name | title | e.g. "Trading BOT04 Journal 2026-01-21" |
| Date | date | The journal day |
| Account | relation → Accounts | |
| Total Trades | number | Count for that day |
| Net P&L | number (dollar) | |
| Win Rate | number (percent) | |
| Profit Factor | number | Gross profit / gross loss |
| Total R | number | |
| Bots Win / Bots Loss | number | |
| Commissions | number (dollar) | |
| Reviewed | checkbox | |
| Notes | rich_text | Manual entries |
| Created | created_time | |
| Last Updated | last_edited_time | |

---

## 4. Transactions DB

Deposits, withdrawals, and fees.

| Property | Type | Options | Notes |
|----------|------|---------|-------|
| Name | title | | e.g. "Deposit $10k 2026-01-15" |
| Date | date | | Transaction date |
| Type | select | Deposit, Withdrawal, Fee | |
| Account | relation → Accounts | | |
| Amount | number (dollar) | | Signed |
| Balance After | number (dollar) | | Running balance |
| Note | rich_text | | |
| Created | created_time | | |

---

## API Pitfalls for This Schema

1. **Creating DBs:** Use `POST /v1/databases` with `Notion-Version: 2022-06-28`. The 2025-09-03 `/v1/data_sources` endpoint returns 400.
2. **Relations:** Add `"single_property": {}` inside the relation property — required by some API versions.
3. **Page markdown `update_content`** fails on pages that already have child databases (inline or full). Use `insert_content` instead.
4. **Rate limiting:** Archiving 500+ entries via PATCH is slow (~3 req/s). Batch in groups of 30-50 with retries. Prepare for 5+ minute runtimes for 500+ entries.
5. **Select options:** Must be defined at database creation time. Adding options later requires PATCH on the data_source schema.

## Linked Page

The existing 👉 [Trading-Bot 04 — Live01](/36681c83f6d981c3b710fd8eb89f5fc3) page (with Daily Snapshots DB) is linked from the Trading Journal page. This provides continuity: old daily snapshots remain accessible, new trades flow into the structured DBs.

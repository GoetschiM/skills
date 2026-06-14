# Trading Journal — Database Schema

Reusable Notion database schema for tracking MT5 trading bot performance. Created for Bot04 — Live01 with 4 linked databases.

## Data Model

```
Accounts 1──* Trades        — Each trade belongs to one account
Accounts 1──* Journals      — Daily summary per account
Accounts 1──* Transactions  — Deposits/withdrawals per account
```

## Databases

### Accounts DB

| Property | Type | Options/Format |
|----------|------|----------------|
| Name | title | Account name (e.g. "Bot04") |
| Type | select | Live / Bot / Demo / Test |
| Bot/Host | select | Bot01–Bot06, Live01, Live02, Bottest, Demo |
| Initial Balance | number ($) | Starting capital |
| Current Balance | number ($) | Current (auto-updated) |
| Net P&L | number ($) | Total profit/loss |
| Total Win / Total Loss | number ($) | Sum of winning/losing trades |
| Win Rate | number (%) | Win rate percentage |
| Total Trades | number | Trade count |
| Volume | number | Total lots |
| Total Deposited / Withdrawn | number ($) | Cash flow |
| Status | select | Active / Paused / Closed |

### Trades DB

| Property | Type | Notes |
|----------|------|-------|
| Trade ID | title | From MT5 or auto-generated |
| Open Date / Close Date | date | Trade timeframe |
| Side | select | Buy / Sell / Long |
| Strategy | select | Scalping / Momentum / Trend Following / Mean Reversion / Breakout / Grid / Martingale / Other |
| Account | relation → Accounts | Parent account |
| Bot/Symbol | rich_text | e.g. "EURUSD" |
| Lots | number | Trade size |
| Entry Price / Exit Price | number ($) | Price levels |
| Net P&L | number ($) | Profit/loss |
| Net ROI | number (%) | Return on investment |
| Realized R | number | Risk units (R-multiple) |
| Pips | number | Pip gain/loss |
| Commissions | number ($) | Fees |
| Trade Risk ($) | number ($) | Risk amount |
| Duration (min) | number | Trade length |
| Trade Rating | select | ⭐⭐⭐ / ⭐⭐ / ⭐ / Unrated |
| Session | select | Asian / London / New York / Sydney |
| Market Conditions | select | Trending / Ranging / Volatile / Low Volatility / News Event |
| Exit Logic | select | TP Hit / SL Hit / Manual / Trailing Stop / Time Exit |
| Emotions / Mistakes | rich_text | User notes |
| Reviewed | checkbox | Review flag |

### Journals DB

Daily summaries: Date, Account (relation), Total Trades, Net P&L, Win Rate, Profit Factor, Total R, Commissions, Notes.

### Transactions DB

Deposits/Withdrawals: Date, Type (Deposit/Withdrawal/Fee), Account (relation), Amount, Balance After, Note.

## Strategy

- **Clean slate preferred** — create empty databases, populate via MT5 API.
- Old data (~4K trades Oct 2025–Feb 2026, $166K P&L, 9 accounts) archived — not migrated.
- Integrate live: pull `/api/status` → `metrics` for daily snapshots, `/api/history` for individual trades.
- See Goetschi Labs workspace: "📊 Trading Journal" page.

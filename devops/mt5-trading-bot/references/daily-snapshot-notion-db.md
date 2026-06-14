# Daily Snapshots Notion Database

**Database:** "Daily Snapshots" — embedded in the "Trading Bot" Notion page
**DB ID:** `36681c83f6d9815b8323d436334b2ce3`
**Parent Page ID:** `36681c83f6d981c3b710fd8eb89f5fc3`
**Created:** 2026-05-20
**Script:** `~/.hermes/scripts/daily_trading_snapshot.py`
**Cron:** `14df9587e8fd` — `no_agent=true`, schedule `0 21 * * *`

## Properties

| Name | Type | Notes |
|------|------|-------|
| Name | title | Convention: `Bot04 - YYYY-MM-DD` |
| Datum | date | Single date, no range |
| Balance | number | Account balance at snapshot time |
| Equity | number | Current equity |
| Daily PnL | number | Today's profit/loss |
| Daily Closed Trades | number | Count of closed trades today |
| Open Positions | number | Current open positions count |
| Pending Orders | number | Current pending orders count |
| Free Margin | number | Available margin |
| Margin Level (%) | number (percent) | Margin level percentage |
| Floating PnL | number | Unrealized P&L |
| Max Drawdown (%) | number (percent) | Drawdown threshold (from Bot04 `dd_threshold`) |
| Win Rate (%) | number (percent) | Today's win rate |
| Profit Factor | number | Gross profit / gross loss ratio |
| Equity Curve | rich_text | Text breakdown by symbol |
| Notes | rich_text | Freeform notes: CPU, MEM, version info |
| Bot | select | Options: `Bot04 LIVE` (red), `Bot01 TEST` (green), `Bot02 TEST` (green) |

## ⚠️ Critical: `no_agent` Scripts MUST use curl, NOT urllib.request

In `no_agent=true` cron scripts on this Hermes instance, `urllib.request.urlopen()` **hangs indefinitely** when making any network call. Always use `subprocess.run(["curl", ...])` instead.

### Working Python Code (curl-based)

```python
import subprocess, json, urllib.parse

def curl_get(url, bearer_token=None):
    cmd = ["curl", "-s", "--max-time", "30"]
    if bearer_token:
        cmd += ["-H", f"Authorization: Bearer {bearer_token...append(url)
    result = subprocess.run(cmd, capture_output=True, timeout=35, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl {url} failed: {result.stderr}")
    return json.loads(result.stdout)

def curl_post(url, data, token=None):
    cmd = ["curl", "-s", "--max-time", "30", "-X", "POST",
           "-H", "Content-Type: application/x-www-form-urlencoded",
           "-d", urllib.parse.urlencode(data)]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token...append(url)
    result = subprocess.run(cmd, capture_output=True, timeout=35, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl POST {url} failed: {result.stderr}")
    return json.loads(result.stdout)

def notion_create(props):
    cmd = ["curl", "-s", "--max-time", "30", "-X", "POST",
           "https://api.notion.com/v1/pages",
           "-H", f"Authorization: Bearer {NT}",
           "-H", "Notion-Version: 2025-09-03",
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"parent": {"database_id": DB_ID}, "properties": props})]
    result = subprocess.run(cmd, capture_output=True, timeout=35, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Notion API failed: {result.stderr}")
    return json.loads(result.stdout)
```

### Property Structure

```python
props = {
    "Name": {"title": [{"text": {"content": f"Bot04 - {date}"}}]},
    "Datum": {"date": {"start": date}},
    "Balance": {"number": round(balance, 2)},
    "Equity": {"number": round(equity, 2)},
    "Daily PnL": {"number": round(daily_pnl, 2)},
    "Daily Closed Trades": {"number": closed_count},
    "Open Positions": {"number": position_count},
    "Pending Orders": {"number": pending_count},
    "Free Margin": {"number": round(free_margin, 2)},
    "Margin Level (%)": {"number": round(margin_level, 2)},
    "Floating PnL": {"number": round(floating_pnl, 2)},
    "Max Drawdown (%)": {"number": float(dd_threshold)},
    "Win Rate (%)": {"number": win_rate},
    "Profit Factor": {"number": profit_factor},
    "Equity Curve": {"rich_text": [{"text": {"content": equity_text[:2000]}}]},
    "Notes": {"rich_text": [{"text": {"content": notes[:2000]}}]},
    "Bot": {"select": {"name": "Bot04 LIVE"}}
}
```

## Backfill Strategy

To backfill historical entries from trade history:

1. Fetch `/api/history?limit=0` from Bot04 (use `limit=0` for ALL trades!)
2. Filter out grid phantom trades (`profit == 0`)
3. Group by `close_time[:10]` (date)
4. For each date: calculate PnL sum, win rate, profit factor, symbol breakdown for equity curve
5. For point-in-time fields (balance, equity, margin): use 0 for historical days (mark as "Historical Rebuild" in Notes)
6. Use current Bot04 status metrics for today's entry

The `Max Drawdown (%)` field comes from `dd_threshold` which is a string from the API — cast to `float()` before passing as number.

**Notion API rate limit:** Add `time.sleep(0.35)` between consecutive writes to avoid 429 rate limiting.

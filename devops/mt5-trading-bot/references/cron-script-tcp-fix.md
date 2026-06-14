# Cron Script: urllib → curl TCP-Fix

## Problem
In `no_agent=true` cron scripts on Apollo (Hermes, 10.0.60.156), `urllib.request.urlopen()` **hangs indefinitely** when making HTTP requests to Bot04 (10.0.60.104) or other internal services. The exact same code works fine in agent-led `terminal()` calls.

Root cause: Hermes' sandbox/process environment restricts Python's `urllib` TCP connections in subprocess mode. `curl` via `subprocess.run` works correctly.

## Fix Template

Replace urllib calls with `subprocess.run(["curl", ...])`:

```python
import subprocess, json, urllib.parse

def curl_get(url, token=None, timeout=30):
    """Replacement for urllib.request.urlopen() in no_agent cron scripts."""
    cmd = ["curl", "-s", "--max-time", str(timeout), url]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"curl {url} failed (rc={result.returncode}): {result.stderr[:200]}")
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"curl {url} timed out after {timeout}s")
    except json.JSONDecodeError as e:
        raise ValueError(f"curl {url}: invalid JSON response: {result.stdout[:200]}")

def curl_post(url, data, timeout=30):
    """POST with form-encoded data via curl subprocess."""
    cmd = ["curl", "-s", "--max-time", str(timeout), "-X", "POST",
           "-H", "Content-Type: application/x-www-form-urlencoded",
           "-d", urllib.parse.urlencode(data), url]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"curl POST {url} failed (rc={result.returncode}): {result.stderr[:200]}")
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"curl POST {url} timed out after {timeout}s")
```

## Rules
- Always set `--max-time N` on curl AND `timeout=N+5` on subprocess.run
- This applies to ALL `no_agent=true` scripts, including Notion API calls
- For Notion: convert `json.dumps(props)` to a `-d` string argument (use single-quote wrapping)
- Do NOT use `shell=True` — pass command as list to avoid shell injection/escaping issues
- `urllib.parse.urlencode()` for POST data is safe and avoids shell `&` issues
- TCP timeout: use `-m 30` or `-m 60` depending on how slow the endpoint is (Bot04 `/api/history?limit=0` braucht ~2-5s auf CT100)

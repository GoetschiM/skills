# Fixing the teichpumpe cron prompt

## Context

The teichpumpe cron job may have been created with an inline prompt containing sync logic steps instead of a simple script invocation. This creates a second source of truth that drifts.

## Detection

Check the cron job's current prompt:

```bash
hermes cron list | grep -i teichpumpe
```

If the prompt contains inline steps (HA reads, Shelly POSTs, etc.) instead of just `python3 /root/.hermes/skills/smart-home/teichpumpe-bridge/scripts/teichpumpe-bridge.py`, it needs updating.

## Fix Steps

1. **Find the job ID:**

```bash
hermes cron list
```

2. **Update the cron job:**

```bash
hermes cron update <JOB_ID> \
  --prompt "python3 /root/.hermes/skills/smart-home/teichpumpe-bridge/scripts/teichpumpe-bridge.py" \
  --skills teichpumpe-bridge
```

3. **Verify:**

```bash
hermes cron list | grep -i teichpumpe
```

The prompt should now show the short invocation form above, and `skills` should include `teichpumpe-bridge`.

## What was fixed (2026-05-24 11:20)

- The canonical script was rewritten from `subprocess.run` + `curl` to pure `urllib.request`
- Token discovery expanded to include env vars (most authoritative)
- The old broken token interpolation (`***` embedded in curl f-strings) is gone
- No shell, no subprocess, no tirith interference

## Prior cost (historical)

Before May 24 11:20, ~20 cron sessions each wasted 2-8 tool calls bypassing the broken inline prompt and broken subprocess+curl script. The fix: rewrite the script to use `urllib.request` (no shell, no token interpolation in f-strings) and update the cron to use `--skills teichpumpe-bridge`.

## Current status (2026-05-24 18:33 — still not fixed after 52 runs)

The cron prompt has **NOT** been updated yet after 52 consecutive runs. It still:
- References `/root/hermes-runtime-167/home/.hermes/.env` — a path that does not exist
- Contains 15+ lines of inline sync logic steps (HA reads, Shelly POSTs, etc.)
- References `input_boolean.teichpumpe_soll` instead of `switch.teichpumpe` (the canonical script switched to `switch.teichpumpe` on 2026-05-24)
- Has no `--skills teichpumpe-bridge` configured

Only 8/52 runs (15.4%) eventually executed the canonical script (runs #8, #16, #20, #25, #27, #32, #50, #52). Run #52 was a mid-session correction (agent started stale, discovered the skill mid-way). The remaining ~44 followed the stale inline prompt fully. 4 confirmed wrong actions (7.7%) — runs #15, #19, #21, #26.

**Per-run details:** See `references/run-log.md` for the complete chronological narrative of all 52 runs.

**Root cause:** Cron sessions cannot modify cron jobs (the cronjob tool is not available to cron-run agents). The fix must be applied by a non-cron session or manually.

**Root cause:** Cron sessions cannot modify cron jobs (the cronjob tool is not available to cron-run agents). The fix must be applied by a non-cron session or manually.

**Key insight:** The agent's "scan skills" persona instruction works, but triggers *after* inline-prompt exploration, not before. Runs that matched the skill immediately (runs #8, #20) did so because the task description shared keywords with the skill's description in the available_skills list. The canonical cron prompt should include entity names (`switch.teichpumpe`, `Shelly 10.0.20.144`) to help the skill matcher fire even without `--skills` configured.

**Lesson for agents creating cron jobs:** When creating a cron job that loads a skill, the prompt should contain only a single script‑invocation line — never inline sync logic. Inline logic in the prompt becomes a parallel source of truth that agents follow instead of the skill, and that drifts when the skill updates.

```text
python3 /root/.hermes/skills/smart-home/teichpumpe-bridge/scripts/teichpumpe-bridge.py
```

With `--skills teichpumpe-bridge` set, the agent loads the skill banner first and sees the one‑line instruction before executing the stale inline prompt.

**Cost so far (52 runs):**
- ~100-175 tool calls wasted on stale-prompt detours (2–4 per run × ~44 non-canonical-or-mid-session runs)
- 4 incorrect physical actions (pump-off events in runs #15, #19, #21, #26) + 3 unknown-correctness actions (runs #33, #38, #42)
- 8 successful canonical-script runs (#8, #16, #20, #25, #27, #32, #50, #52 — Run #52 was a mid-session correction)
- The fix above has been ready to apply since run #1 — 52 runs and counting

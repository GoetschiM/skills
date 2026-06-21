---
name: debugging-workflows
description: "Debugging techniques for Python (pdb, debugpy) and Node.js (--inspect, CDP). Systematic approaches for root cause analysis and breakpoint-driven investigation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, cdP, breakpoints, root-cause]
    related_skills: [systematic-debugging, test-driven-development]
---

# Debugging Workflows

Debugging techniques across Python and Node.js ecosystems. This umbrella skill covers both Python (pdb, debugpy) and Node.js (--inspect, CDP, node inspect) debugging tools, plus the 4-phase systematic root cause methodology.

## Table of Contents

1. [Systematic Root Cause Investigation](/skills/software-development/systematic-debugging/SKILL.md)
2. [Python Debugging (pdb, debugpy, remote-pdb)](/skills/software-development/python-debugpy/SKILL.md)
3. [Node.js Debugging (--inspect, CDP, node inspect)](/skills/software-development/node-inspect-debugger/SKILL.md)

---

## Quick Decision Tree

| Situation | Tool | Skill |
|-----------|------|-------|
| Python test failing | `breakpoint()` + `pdb` | python-debugpy |
| Remote/long-lived Python process | `debugpy` or `remote-pdb` | python-debugpy |
| Node.js test or script | `node inspect` | node-inspect-debugger |
| Running Node.js TUI/gateway | `kill -SIGUSR1` + `node inspect -p` | node-inspect-debugger |
| Complex multi-component bug | Systematic 4-phase investigation | systematic-debugging |
| Post-mortem after exception | `pdb.post_mortem()` | python-debuggy |

## § 1 — Python Debugging (pdb, debugpy, remote-pdb)

Three tools, picked by situation:

| Tool | When |
|------|------|
| `breakpoint()` + pdb | Local, interactive, simplest |
| `python -m pdb` | Launch script under pdb with no source edits |
| `debugpy` | Remote / headless / attach to running process |
| `remote-pdb` | Cleanest agent-friendly remote debug — `nc` to get a pdb prompt |

### Local breakpoint

```python
def compute(x, y):
    breakpoint()  # drops into pdb here
```

### Launch under pdb

```bash
python -m pdb path/to/script.py arg1
```

### pytest under debugger

```bash
scripts/run_tests.sh tests/test_file.py::test_name --pdb
# IMPORTANT: add -p no:xdist or use --pdb with -n 0
```

### Remote debug with remote-pdb

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```
Then: `nc 127.0.0.1 4444` — you get a (Pdb) prompt.

### Quick pdb commands

| Command | Action |
|---------|--------|
| `n` | Next line |
| `s` | Step into |
| `c` | Continue |
| `w` | Where (stack trace) |
| `l` / `ll` | List source |
| `p expr` / `pp expr` | Print expression |
| `interact` | Full Python REPL in scope |
| `b file:line` | Set breakpoint |
| `cl N` | Clear breakpoint N |
| `!stmt` | Execute arbitrary Python |

**Always remove `breakpoint()` before committing.** Use `rg -n 'breakpoint\\(\\)' --type py`.

Full guide: see `/skills/software-development/python-debugpy/SKILL.md`.

---

## § 2 — Node.js Debugging (--inspect, CDP)

Two tools:

| Tool | When |
|------|------|
| `node inspect` | Built-in, zero install, CLI REPL |
| CDP via `chrome-remote-interface` | Scriptable, automate many breakpoints |

### node inspect REPL

```bash
node inspect path/to/script.js
# or with TypeScript
node --inspect-brk $(which tsx) path/to/script.ts
```

Key commands:
- `c` (continue), `n` (next), `s` (step), `o` (out)
- `sb('file.js', 42)` — set breakpoint
- `bt` — backtrace
- `repl` — drop into REPL in current scope
- `watch('expr')` — evaluate on every pause

### Attach to running process

```bash
kill -SIGUSR1 <pid>
node inspect -p <pid>
```

### Programmatic CDP

```bash
npm i -g chrome-remote-interface
```

Then write a driver script that autmates breakpoints, scope inspection, and state capture.

Full guide: see `/skills/software-development/node-inspect-debugger/SKILL.md`.

---

## § 3 — Systematic Root Cause Analysis

**Core principle**: ALWAYS find root cause before attempting fixes.

### The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

### 4-Phase Process

1. **Root Cause Investigation** — Read errors, reproduce, check changes, trace data flow
2. **Pattern Analysis** — Find working examples, compare against references
3. **Hypothesis & Testing** — Form theory, test minimally, one variable at a time
4. **Implementation** — Create regression test, fix root cause, verify

### Red Flags (STOP and return to Phase 1)

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Skip the test, I'll manually verify"
- Proposing solutions before tracing data flow

### 3+ Failed Fixes → Question Architecture

If you've tried 3 fixes and none worked, the problem is architectural. Stop and discuss with the user before attempting more.

Full guide: see `/skills/software-development/systematic-debugging/SKILL.md`.

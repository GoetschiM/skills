# Nova Deployment Host — Hardware Profile

**Hostname:** Nova-Sipcall  
**IP:** 10.0.60.167  
**Role:** Asterisk/Audio processing + local LLM inference (simple tasks)

## Specs

| Component | Detail |
|---|---|
| **CPU** | Intel Core i5-6500T @ 2.50GHz |
| **Cores** | 4 cores, 4 threads (no hyperthreading) |
| **RAM** | 14 GiB total, ~6 GiB available after OS/processes |
| **GPU** | None (Intel iGPU present at vendor 0x8086, but no /dev/dri — not usable by Ollama) |
| **Storage** | /opt/hermes167 on main partition (check with `df -h`) |
| **OS** | Debian/Ubuntu (check with `cat /etc/os-release`) |
| **Asterisk** | Installed on host directly (not containerized) |
| **Python** | 3.11 (hermes venv) + 3.12 (system) |

## Running Services

| Service | Port | Bound To |
|---|---|---|
| Ollama serve | 11434 | 127.0.0.1 only |
| Hermes Gateway (hermes167) | 8642 | 127.0.0.1 only |
| Nova Call VM API | 5001 | 0.0.0.0 |
| Asterisk ARI | 8088 | 0.0.0.0 |
| Asterisk AMI | 5038 | 0.0.0.0 |

## Local Model Inference Constraints

**⬆️ Verified working (fast enough for interactive use):**
- `gemma2:2b` (1.6 GB) — loads fast, responds in 1-3 seconds on CPU

**⬇️ Too slow for interactive use:**
- `gemma4:e2b-it-q4_K_M` (7.2 GB) — 60+ seconds per inference, CPU pegged at 97%, heavy swap. Model passes `ollama list` and runner starts, but timeouts on any API call.

**⚠️ Model selection rule:** For CPU-only inference on i5-6500T, stay at ≤2B parameters and ≤2 GB file size. Anything above that overwhelms the 4 cores + limited RAM.

**Default model (set in `/opt/hermes167/data/config.yaml`):**
- Provider: `ollama-local` (ollama on localhost:11434)
- Model: `gemma4:e2b-it-q4_K_M` (slow — user may want to switch back to gemma2:2b)

## Pipeline Scripts Location

- Pipeline scripts: `/usr/local/bin/hermes_*` or `/tmp/`
- Logs: `/var/log/hermes_*.log`
- Asterisk sounds: check `asterisk -rx "core show settings" | grep sounds` — typically `/var/spool/asterisk/sounds/`
- Config: `/opt/hermes167/data/config.yaml`

## SSH Access

- From Hermes (10.0.60.156): `sshpass -p 'PASSWORD' ssh root@10.0.60.167`
- SCP: `sshpass -p 'PASSWORD' scp SOURCE root@10.0.60.167:DEST`
- Password in Jira / memory.

**⚠️ Hermes → Nova SSH:**
- Complex heredocs often fail with exit 255 (quotation issues in nested SSH). 
- Use one-liners with `&&` chaining, or write fix scripts locally and SCP them over, or pipe via base64.
- Long-running commands can timeout on Hermes side (60s default) — use SSH directly with `-o ConnectTimeout=10`.

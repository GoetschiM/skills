# Model Context Length — Local Ollama Models

## Problem
Config.yaml sets `context_length` for a local model (e.g. `gemma4:e4b` or `gemma2:2b`), but Hermes Agent either:
- Refuses to start because the detected context falls below the **mandatory 64K minimum** (`MINIMUM_CONTEXT_LENGTH = 64_000`)
- Runs with severely limited context

Two distinct scenarios:
1. **Model actually supports >64K** but config has a wrong low value (e.g. config says 8192, model supports 131072)
2. **Model genuinely has <64K context** (e.g. gemma2:2b has only 8192) — you must override both the model AND auxiliary compression context_length to bypass the minimum check

## Root Cause

Hermes Agent in `run_agent.py` raises a hard `ValueError` when `self.context_compressor.context_length < MINIMUM_CONTEXT_LENGTH` (64,000). This check fires regardless of whether the context was user-overridden in config.

The context_length is resolved from multiple sources (in priority order):
1. `model.context_length` in config.yaml (direct override)
2. `custom_providers` per-model entry
3. Auto-detection via ollama API (`/api/show`), model catalog, probes etc.
4. Default fallback (256K)

**Crucially:** the minimum check also applies to the **auxiliary compression model**, which by default uses the same model. If the main model is small (<64K), the auxiliary compression model needs its own override too — otherwise you get a secondary error after fixing the primary one.

## Fix

### Scenario A: Model supports >64K but config is wrong

```bash
# Check the model's real context length
ollama show <model> | grep "context length"
```

Then set the correct value:

```yaml
# config.yaml — under the provider's model entry
providers:
  litellm-local:
    models:
      gemma4:e4b:
        context_length: 131072  # from ollama show output
```

### Scenario B: Model genuinely has <64K context (e.g. gemma2:2b)

You MUST set **both** overrides to bypass the 64K minimum check:

```yaml
# config.yaml — top-level model section AND auxiliary compression
model:
  context_length: 64000          # bypass main check (ollama truncates at real limit)
  default: gemma2:2b
  provider: custom               # NOT "ollama-local" — see Provider Name Pitfall below

auxiliary:
  compression:
    context_length: 64000        # bypass auxiliary check (same reason)
```

Without `auxiliary.compression.context_length`, you get:
```
Auxiliary compression model gemma2:2b has a context window of 8,192 tokens,
which is below the minimum 64,000 required by Hermes Agent.
```

### 3. Restart gateway
```bash
systemctl restart hermes-gateway
```

## Provider Configuration Pitfall: Use `custom`, NOT `ollama-local`

**`ollama-local` is NOT a recognised provider in Hermes v0.13.0.** Valid built-in providers include: `custom`, `openrouter`, `anthropic`, `openai-codex`, `ollama-cloud`, `litellm-local`, `lmstudio`, and others — but NOT `ollama-local`.

When you set `model.provider: ollama-local`, `_resolve_runtime_agent_kwargs()` fails with:
```
Primary provider auth failed: Unknown provider 'ollama-local'
```
and falls back to `fallback_providers` in config.yaml. The fallback resolution returns a dict that INCLUDES `model` (from the fallback model). When the gateway then calls `AIAgent(model=model, **runtime_kwargs, ...)`, the `model` key appears twice — causing:
```
TypeError: run_agent.AIAgent() got multiple values for keyword argument 'model'
```

**Fix:** Use `provider: custom` instead.

```yaml
model:
  default: gemma2:2b
  provider: custom               # ← correct
  base_url: http://127.0.0.1:11434/v1
  api_mode: chat_completions
```

The `custom` provider is always recognised and resolves to the configured `base_url` directly without triggering fallback logic.

### api_key in config (for cloud endpoints)

When pointing the `custom` provider at a cloud endpoint (e.g. another LiteLLM proxy), you may also need `api_key` in the model section:

```yaml
model:
  default: smart-free
  provider: custom
  base_url: http://10.0.60.157:4000/v1
  api_key: sk-your-key-here    # ← inline key for cloud endpoints
  context_length: 64000
```

**Important:** The `custom` provider does NOT read `HERMES_API_KEY` from the .env. The API key must be either:
1. Inline in config.yaml as `model.api_key` (shown above), OR
2. In the system environment as `CUSTOM_API_KEY`, OR
3. From a `providers` dict entry in config.yaml with a `key_env` field

For ollama (local), no API key is needed — the `custom` provider with `base_url: http://127.0.0.1:11434/v1` works without authentication.

### Verification that fallback is NOT being triggered

Run this to confirm the primary provider resolves cleanly:
```bash
cd /opt/hermes167/app
HOME=$HERMES_HOME/data/home HERMES_HOME=$HERMES_HOME/data hermes python3.11 -c "
from gateway.run import _resolve_runtime_agent_kwargs
r = _resolve_runtime_agent_kwargs()
print('Has model in kwargs:', 'model' in r)
print('Provider:', r.get('provider'))
"
```
Expected: `Has model in kwargs: False` — the `model` key should NOT be present in runtime kwargs.

## Complete Config Example (gemma2:2b on Nova)

```yaml
model:
  api_mode: chat_completions
  base_url: http://127.0.0.1:11434/v1
  context_length: 64000
  default: gemma2:2b
  provider: custom

auxiliary:
  compression:
    context_length: 64000
```

## Editing Config on Remote Hosts — CRITICAL Pitfall

**Never use `sed -i` to edit a YAML value on a remote host via SSH!** The `-i` flag edits in-place and replaces ALL occurrences of the pattern, not just the one you intend. Example:

```bash
# DANGEROUS — destroys config!
ssh host "sed -i 's/context_length: 8192/context_length: 64000/' config.yaml"
```

This replaces EVERY occurrence of `context_length: 8192` — including model entries under `providers.litellm-local.models.llama3.2` — collapsing the config to a single line.

**Safe alternatives:**
1. Use `patch` tool (Hermes' structured editing tool) — it only replaces exactly one match
2. Use `sed` with line-number targeting: `sed -i '30s/.../.../' config.yaml` (after confirming the exact line with `grep -n`)
3. Use `cat` with heredoc to rewrite the whole section
4. Always create a backup first: `cp config.yaml config.yaml.bak`

## Verification
After restart, test the API directly:
```bash
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Sag Hallo!"}],"max_tokens":20}'
```
Expected: a JSON response with `choices[0].message.content`, not an error.

Also check gateway logs:
```bash
journalctl -u hermes-gateway --no-pager -n 30 | grep -i "model\\|context"
```

## Critical: Tool/Function Calling Support

**Hermes Agent requires tool calling.** Every action (terminal, file, memory, search, etc.) goes through the LLM's function-calling API. A model that doesn't support tool calling is **unusable** with Hermes — every request fails with HTTP 400 from the provider.

### How to verify tool support

```bash
# Test with ollama's OpenAI-compatible endpoint
curl -s http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"<model-name>",
    "messages":[{"role":"user","content":"test"}],
    "max_tokens":10,
    "tools":[{"type":"function","function":{"name":"test_fn","description":"test","parameters":{"type":"object","properties":{}}}}]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Supports tools' if 'choices' in d else '❌ No tools:', d.get('error',{}).get('message',''))"
```

If the model returns `"does not support tools"`, it cannot be used as a primary model for Hermes.

### Models known to support tools in ollama
- `qwen2.5:7b` ✅ (~4.7GB, needs 6GB+ RAM)
- `qwen2.5:3b` ✅ (~2GB, runs on CPU)
- `qwen2.5:1.5b` ✅ (~0.9GB, **smallest tool-capable model**, runs on CPU)
- `llama3.1:8b` ✅ (~4.9GB)
- `llama3.2:3b` ✅ (~2GB)
- `phi3:mini` ✅ (~2.5GB)

### Models known NOT to support tools in ollama
- `gemma2:2b` ❌
- `gemma4:*` ❌ (no Gemma models support tools)

### Handling models without tools

**Option 1: Use a tool-capable model as primary + set fallback_providers for reliability**
```yaml
model:
  default: qwen2.5:3b
  provider: custom
  base_url: http://127.0.0.1:11434/v1

fallback_providers:
  - model: deepseek-v4-flash
    provider: custom:litellm-local
```

**Option 2: Accept the fallback** — let the non-tool model fail and the gateway automatically switches to the fallback. The user will see:
```
⚠️ Non-retryable error (HTTP 400) — trying fallback...
🔄 Primary model failed — switching to fallback: deepseek-v4-flash
```

This works but wastes time (the failed API call + fallback resolution adds 30-90s latency per request).

**Option 3: Cloud endpoint directly** — skip local models entirely and use litellm-local or OpenRouter.

## Model-Specific Notes

### CPU Inference Performance
Running models on CPU (Intel i5-6500T, 4 cores, 2.5GHz, no GPU) is slow:
- **gemma2:2b (1.6GB):** 25-90s per response
- **gemma4:e2b-it-q4_K_M (5.1B, 7.2GB):** times out after 60s (too large for CPU+RAM)
- Expect context building to take extra time (15K+ prompt tokens for memory + instructions)

For any real-time use (dialog, interactive), prefer a cloud endpoint or a model <3B with good CPU performance.

### gemma2:2b (2B)
- Ollama: `ollama pull gemma2:2b`
- Size: 1.6GB
- Context: 8192 native (must override both `model.context_length` and `auxiliary.compression.context_length`)
- **🚫 Does NOT support tool/function calling!** Ollama returns HTTP 400 with `"registry.ollama.ai/library/gemma2:2b does not support tools"`. This means Hermes Agent cannot use any tools (terminal, files, memory, etc.) — every API call fails with HTTP 400 and the gateway falls back to fallback_providers.
- **Only suitable for:** pure text-generation tasks (cron summaries, status reports). Not usable for agentic workflows.
- CPU inference: ~25s first response (small prompts), manageable for background tasks

### qwen2.5:3b (3B)
- Ollama: `ollama pull qwen2.5:3b`
- Size: 1.9GB
- Context: 32768 native (set `model.context_length: 64000` and `auxiliary.compression.context_length: 64000` to bypass Hermes' 64K minimum)
- **✅ Supports tool/function calling!** Tested with `get_weather` function — responds correctly with tool_calls format.
- **Prompt-size sensitivity (CRITICAL):** Response time scales with input size:
  - ~30 tokens input: ~3s ✅
  - ~162 tokens input (with tools): ~6s ✅
  - **~15K tokens input (Hermes full prompt + memory + tools): 5-10 MINUTES** ❌
  - The prompt processing (context ingestion) on CPU is the bottleneck, not generation
- **Use as primary model with fallback_providers** for interactive use. Fast cloud responses when fallback is available; slow local fallback when cloud is down.
- **Runner hang recovery:** If the ollama runner gets stuck at >200% CPU for >5 minutes with no response, kill it: `kill -9 <runner-pid>`. The ollama serve process automatically restarts a new runner on the next request.
- CPU inference (i5-6500T, 4 cores): manageably fast for background cron jobs, too slow for real-time dialog.

### qwen2.5:1.5b (1.5B) — RECOMMENDED FOR CPU
- Ollama: `ollama pull qwen2.5:1.5b`
- Size: **0.9GB** (half of 3b variant)
- Context: 32768 native (same 64K override needed)
- **✅ Supports tool/function calling!** Tested with `get_weather` function and tool_choice="auto" — correctly returns `"finish_reason":"tool_calls"` with function arguments.
- **Best CPU-performance-to-tool-support ratio for Nova (i5-6500T, 4 cores):**
  - ~30 tokens input: ~3s ✅
  - ~162 tokens input (with tools): ~5s ✅
  - ~15K tokens (Hermes full prompt): still **5-10 min** (context ingestion dominates)
- **Primary use case:** Cron jobs, status checks, pump control, simple Telegram responses — tasks where 2-5 minute latency is acceptable.
- **For interactive dialog:** Still too slow with full Hermes context. Pair with fallback_providers for fast cloud responses.
- **RAM usage:** ~1.2GB resident, 3.2GB virtual. Leaves 12+GB free for other processes.
- **Runner state:** ollama keeps the model loaded for ~4 minutes after last request (`ollama ps` shows "4 minutes from now"). Multiple sequential requests don't incur reload overhead.
- **CPU load:** ~240% CPU (uses 2.4 cores out of 4) during inference. System stays usable with load average ~9-12.
- **Runner hang recovery:** Runner occasionally gets stuck (100% CPU, no output for 5+ min). Kill runner PID, ollama serve auto-restarts a fresh one on next request.

### gemma4:e2b (2B class models)

**Not all Gemma 4 variants are available on Linux!**

| Tag | Platform | Params | Size | Context | Notes |
|-----|----------|--------|------|---------|-------|
| `gemma4:e2b-mlx` | macOS only | 2B | ~2GB | 131K | Requires Apple MLX framework |
| `gemma4:e2b-it-q4_K_M` | Linux ✅ | 5.1B | 7.2GB | 131K | Instruction-tuned, Q4_K_M quant |
| `gemma4:e2b-it-bf16` | Linux ✅ | 2B | ~4GB | 131K | Larger, higher precision |

The `mlx` suffix ALWAYS means macOS-only (Apple MLX). Use `q4_K_M` or `bf16` variants on Linux.

**Memory consideration:** On systems with only 3.6GB free RAM (like Nova's 14GB LXC), a 5.1B Q4_K_M model is borderline. Prefer `gemma2:2b` (1.6GB) if RAM is tight.

## Historical Examples

### Example 1: Gemma4:e4b on Nova (22.05.2026)
- Config had `context_length: 8192` → Hermes rejected with `ValueError: ... below minimum 64,000`
- `ollama show gemma4:e4b` → `context length 131072`
- Updated to `131072` → Gateway started fine with full context
- Later swapped to `gemma4:e2b-it-q4_K_M` (5.1B) because 8B was too memory-heavy

### Example 2: gemma2:2b on Nova (23.05.2026)
- Switched from oversize gemma4:e2b-it-q4_K_M (7.2GB) to gemma2:2b (1.6GB) for CPU inference
- First discovered `ollama-local` is not a valid provider → used `custom` instead
- Model has real 8192 context → set BOTH `model.context_length: 64000` AND `auxiliary.compression.context_length: 64000`
- Gateway responded successfully after these fixes, running on CPU with 25-90s response time

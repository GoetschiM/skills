# CPU SD Model Benchmark — 19 May 2026

Tested on NOVA (10.0.60.167, 4 CPU cores, 10GB RAM).
All models via diffusers + FastAPI on CPU (no GPU available).

## Models Tested

### 1. segmind/tiny-sd (LCM) — Port 3020 ✅ RECOMMENDED
- **app.py** at `/opt/hermes167/data/sd-api/app.py`
- **Speed:** ~30s for 384×384, 4 steps
- **Quality:** Low/blurry but acceptable for quick previews
- **RAM:** ~2.9GB
- **Max steps in API:** 50 (hardcoded in Pydantic validator `le=50`)
- **LCM note:** Increasing steps beyond 4 does NOT improve quality (LCM converges in 4 iterations)
- **Scheduler:** LCMScheduler
- **Guidance scale default:** 2.0
- **Test prompt used:** `"white Tesla on the Moon, Earth rising in the dark starry sky, rocky surface, cinematic"`

### 2. nota-ai/bk-sdm-tiny (SD 1.5) — Port 3022 ⚠️ SLOW
- **Script:** `/opt/hermes167/data/sd-api/hermes_sd_v3.py`
- **Speed:** 25 steps → ~3min, 50 steps → >5min (timeout)
- **Quality:** Better than tiny-sd, more detail
- **RAM:** ~0.6GB (tiny model at 47MB)
- **Scheduler:** DPMSolverMultistepScheduler with karras_sigmas
- **Guidance scale:** 7.5 (default)
- **Resolution:** 512×512 supported
- **First load:** ~27.5s (download + cache from HuggingFace)
- **Config File:** 14 files fetched from HF Hub
- **Note:** Acceptable speed only at 20-25 steps. 50 steps = >5min.

### 3. dreamlike-art/dreamlike-photoreal-2.0 (SD 1.5) — Port 3021 ❌ FAILED
- **Script:** `/opt/hermes167/data/sd-api/hermes_sd_api_v2.py`
- **Runtime RAM:** 5.2GB (50.2% of 10GB total)
- **Speed:** >10min for 512×512, 30 steps (curl timed out after 180s)
- **Issue:** UNet has 1.2B+ params, designed for GPU inference
- **Combined with tiny-sd:** 8.1GB total → RAM exhaustion, CPU load >10 on 4 cores, system near-freeze
- **Killed with:** `kill -9 <PID>` (pkill through SSH caused connection errors)
- **After kill:** RAM dropped from 9GB used to 4GB used

### 4. Pydantic max steps limit
- tiny-sd (app.py): `num_inference_steps: int = Field(default=4, ge=1, le=50)`
- bk-sdm-tiny (hermes_sd_v3.py): `num_inference_steps: int = Field(default=25, ge=1, le=100)`
- Trying 100 on tiny-sd returned: `{"detail":[{"type":"less_than_equal","loc":["body","num_inference_steps"],"msg":"Input should be less than or equal to 50","ctx":{"le":50}}]}`

## Key Commands Reference

```bash
# Health check both services
curl -s http://10.0.60.167:3020/health
curl -s http://10.0.60.167:3022/health

# Generate with tiny-sd (fast, low quality)
curl -s -X POST http://10.0.60.167:3020/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"white Tesla on the Moon, cinematic"}' \
  -o /tmp/test.png

# Generate with bk-sdm-tiny (slow, better quality)
curl -s -X POST http://10.0.60.167:3022/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"white Tesla on the Moon, cinematic", "num_inference_steps": 25, "guidance_scale": 7.5}' \
  -o /tmp/test.png

# Kill & restart tiny-sd
ssh root@10.0.60.167 "kill -9 \$(pgrep -f 'app.py' | head -1); sleep 1; nohup python3 /opt/hermes167/data/sd-api/app.py > /tmp/sd_tiny.log 2>&1 &"

# Deploy new script to NOVA
scp /tmp/hermes_sd_v3.py root@10.0.60.167:/opt/hermes167/data/sd-api/
```

## Herman Resource Limits
| Resource | Hermes (10.0.60.156) | NOVA (10.0.60.167) |
|----------|----------------------|---------------------|
| RAM | 5 GB (3.7 free) | 10 GB |
| CPUs | 2 | 4+ |
| tiny-sd viable | ✅ (30s) | ✅ (30s) |
| SD 1.5 (25 steps) | ❌ (5-10min) | ⚠️ (3min) |
| SD 1.5 (50 steps) | ❌ | ❌ (>5min, timeout) |

## Dokploy SD 1.5 — Real Benchmark (19.05.2026)

| Property | Value |
|----------|-------|
| Host | 10.0.60.121 (Dokploy) |
| CPUs | 3 (shared) |
| RAM | 10 GB (5.7 GB available after load) |
| Model | `runwayml/stable-diffusion-v1-5` |
| Pipeline | `AutoPipelineForText2Image` |
| Scheduler | DPMSolverMultistepScheduler (karras_sigmas) |
| Precision | float32 (CPU) |
| **Model download** (first start) | **79s** (13 files from HF Hub) |
| **Pipeline load** | **17s** (6 components) |
| **Total first-start** | **96.7s** |
| **25 steps, 512×512** | **449s** (7.5 minutes) |
| Output | 435 KB PNG, 512×512 |
| CPU saturation | 86.8% us, load avg 6.33 |
| curl timeout | **300s too short** — use `--max-time 600` |

**Verdict:** SD 1.5 on Dokploy CPU is usable only for batch/pre-planned generation. Not interactive. Use tiny-sd on NOVA (~30s) for quick demos.

# NOVA SD-API: app.py Analysis & Model Upgrade Guide

Source: `/opt/hermes167/data/sd-api/app.py` on NOVA (10.0.60.167)
API: `http://10.0.60.167:3020`
Discovered: 19.05.2026 during voice conversation with Michel

## Code Structure

```python
# Framework: FastAPI + diffusers
MODEL_ID = "segmind/tiny-sd"           # hardcoded
pipeline = AutoPipelineForText2Image.from_pretrained(
    MODEL_ID, cache_dir=...,
    torch_dtype=torch.float32,
    safety_checker=None,
    requires_safety_checker=False,
)
pipeline.scheduler = LCMScheduler.from_config(pipeline.scheduler.config)
pipeline.set_progress_bar_config(disable=True)

# API endpoints:
# GET /health  → {"status":"ok","model":"segmind/tiny-sd","device":"cpu","loaded":true}
# POST /generate → image/png response
```

## Parameters available (from pydantic model)

| Field | Type | Default | Range |
|-------|------|---------|-------|
| prompt | str | required | 1-500 chars |
| negative_prompt | Optional[str] | "ugly, blurry, low quality, distorted" | any |
| width | int | 384 | 64-1024 |
| height | int | 384 | 64-1024 |
| num_inference_steps | int | 4 | 1-50 |
| guidance_scale | float | 2.0 | 0.0-20.0 |
| seed | Optional[int] | None | any int |

## Model Comparison Table

### LCM Models (fast, current architecture: 4 steps)

| Model ID | Size | Quality | Steps | Est. Time (CPU) |
|----------|------|---------|-------|-----------------|
| segmind/tiny-sd | 200MB | Low (blurry) | 4 | ~30s |
| segmind/SSD-1B | 1.3GB | Medium | 4 | ~40s |
| latent-consistency/lcm-lora-sdv1-5 | 50MB LoRA | Medium | 4-8 | ~30-45s |
| warp-diffusion/warp-lcm-sd15 | 2GB | Medium-High | 4-8 | ~40-60s |

### Standard SD 1.5 (higher quality, 25-50 steps, remove LCM scheduler)

| Model ID | Size | Style | Steps | Est. Time (NOVA CPU) |
|----------|------|-------|-------|---------------------|
| dreamlike-art/dreamlike-photoreal-2.0 | 2GB | Photorealistic, cinematic | 25-50 | 2-5min |
| wavymulder/Analog-Diffusion | 2GB | Analog film look | 25-50 | 2-5min |
| prompthero/openjourney-v4 | 2GB | Midjourney-style | 25-50 | 2-5min |
| stabilityai/stable-diffusion-2-1 | 2.5GB | Generic realistic | 25-50 | 2-5min |
| dreamshaper/dreamshaper-8 | 2GB | Best all-around quality | 25-50 | 2-5min |
| runwayml/stable-diffusion-v1-5 | 2GB | Original SD 1.5 | 25-50 | 2-5min |

### SDXL (too large for CPU, needs GPU + 7GB VRAM)

| Model ID | Size | Notes |
|----------|------|-------|
| stabilityai/stable-diffusion-xl-base-1.0 | 7GB | Needs GPU |
| SDXL-Lightning | 7GB | 2-4 steps but GPU required |

## Deployment Targets

- **NOVA (10.0.60.167):** 10GB RAM, capable of all SD 1.5 models
- **Hermes (10.0.60.156):** 5GB RAM, 2 CPUs. Only tiny-sd/RCM models practical. Would need resource upgrade for SD 1.5
- **If Hermes is upgraded** (more RAM/CPU): can run SD 1.5 models ~2-3min/image

## Swap Procedure

```bash
# 1. SSH to NOVA
sshpass -p 'Louis_one_13' ssh root@10.0.60.167

# 2. Edit app.py
sed -i 's|MODEL_ID = "segmind/tiny-sd"|MODEL_ID = "dreamshaper/dreamshaper-8"|' /opt/hermes167/data/sd-api/app.py
# For standard SD (not LCM): comment out the LCMScheduler line:
sed -i '/pipeline.scheduler = LCMScheduler/s/^/# /' /opt/hermes167/data/sd-api/app.py

# 3. Adjust defaults for better quality
sed -i 's|num_inference_steps: int = Field(default=4|num_inference_steps: int = Field(default=25|' /opt/hermes167/data/sd-api/app.py
sed -i 's|guidance_scale: float = Field(default=2.0|guidance_scale: float = Field(default=7.5|' /opt/hermes167/data/sd-api/app.py

# 4. Kill and restart
pkill -f "python3 /opt/hermes167/data/sd-api/app.py"
cd /opt/hermes167/data/sd-api
nohup python3 app.py > /tmp/sd-api.log 2>&1 &
# First start: model download takes 10-20s on CPU

# 5. Test
curl -X POST http://127.0.0.1:3020/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","num_inference_steps":25,"guidance_scale":7.5}' \
  -o /tmp/test.png
ls -la /tmp/test.png

# 6. Verify from Hermes
curl -X POST http://10.0.60.167:3020/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"cat in space"}' -o /tmp/cat.png
```

## Real-World Performance Data (19.05.2026)

### Crash incident: Running tiny-sd + dreamlike-photoreal simultaneously

On 19.05.2026, two SD models were started together:
- tiny-sd (PID 72239, port 3020): 2.9 GB RAM (28% of 10GB)
- dreamlike-photoreal-2.0 (PID 141159, port 3021): 5.2 GB RAM (50% of 10GB)
- **Combined: 8.1 GB / 10 GB → effectively full swap**
- CPU load average: **10.25** on 4 cores
- Result: total system freeze — ALL generate requests timed out (even tiny-sd)

**Lesson:** NEVER run two SD models concurrently on NOVA. Kill the old model before starting the new one.

### tiny-sd performance after restart

After killing dreamlike-photoreal and restarting tiny-sd:
- 384×384, 4 steps, LCM → ~30s per image ✅
- 512×512, 4 steps → ~45-60s
- 384×384, 8 steps → ~45-60s

### dreamlike-photoreal CPU inference result

- **Model load:** 34.9s (including download from HuggingFace)
- **512×512, 30 steps:** NOT COMPLETED (client timeout at 180s, process still running)
- **384×384, 15 steps:** NOT COMPLETED (timeout at 120s)
- **Conclusion:** Dreamlike-photoreal is UNUSABLE for CPU inference. Despite being SD 1.5 (~2GB), its UNet is too large for CPU. Stick with LCM models for CPU.
- **Fix:** The service was killed with `kill -9` after the test. This freed 5+ GB RAM instantly.

### New API endpoint design (for reference)

A second API was created as a prototype on port 3021 (`hermes_sd_api_v2.py`) with:
- `DPMSolverMultistepScheduler` with `use_karras_sigmas=True, algorithm_type="sde-dpmsolver++"`
- Recommended defaults: 30 steps, 512×512, guidance_scale=7.5
- Additional `/model-info` endpoint
- **Result:** Found to be too slow for CPU even at 15 steps/384px

## API Endpoint for better quality (dreamlike-photoreal v2 script)

The v2 script was deployed to `/opt/hermes167/data/sd-api/hermes_sd_api_v2.py` on NOVA (port 3021). It was removed after testing because dreamlike-photoreal is not suitable for CPU. The script file still exists as reference for future GPU-based deployment.

FastAPI auto-generates docs:
- `http://10.0.60.167:3020/docs` — interactive Swagger UI
- `http://10.0.60.167:3020/openapi.json` — raw OpenAPI schema

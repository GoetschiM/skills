---
name: nova-sd-image-gen
description: "Image generation via Stable Diffusion — tiny-sd (LCM) on NOVA CPU or SD 1.5 via Docker on Dokploy. User preference: min 20-25 steps for quality."
tags: [image-gen, sd-api, nova, stable-diffusion, docker, dokploy]
category: mlops
---

# Image Generation — SD Deployment Guide

Generate images via Stable Diffusion. Two deployment targets:

| Target | Model | Speed | Quality | Use Case |
|--------|-------|-------|---------|----------|
| **NOVA** (3020) | tiny-sd (LCM) | ~30s | Low-Medium | Fast interactive, small images |
| **Dokploy** (3024) | SD 1.5 (Docker) | ~7.5min | High | Best quality, photorealistic |

**User preference:** Minimum 20 steps, up to 25. More steps = better quality. NOVA's tiny-sd (LCM) is the exception at 4 steps (LCM converges at 4).

---

## A. NOVA: tiny-sd (LCM, CPU)

**Endpoint:** `POST http://10.0.60.167:3020/generate`
**Model:** `segmind/tiny-sd` with LCM scheduler
**Device:** CPU (NOVA, 4 cores, 10GB RAM)
**Speed:** ~30-33s per image
**Resolution:** 384×384 PNG
**Steps:** 4 (LCM-optimized)

```bash
curl -s -X POST http://10.0.60.167:3020/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a cute orange cat sitting on a bookshelf, digital art"}' \
  -o /tmp/image.png
```

**Full params example:**
```bash
curl -s -X POST http://10.0.60.167:3020/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"white Tesla Model 3 on Mars, photorealistic",
    "negative_prompt":"ugly, blurry, cartoon",
    "width":512,
    "height":512,
    "num_inference_steps":25,
    "guidance_scale":7.5,
    "seed":42
  }' \
  -o /tmp/output.png
```

> ⚠️ **WARNING:** >384px = very slow on CPU. Stick to 384×384 for interactive use on NOVA.

---

## B. Dokploy: SD 1.5 (Docker, better quality)

**Endpoint:** `POST http://10.0.60.121:3024/generate`
**Model:** `runwayml/stable-diffusion-v1-5` via `AutoPipelineForText2Image`
**Host:** 10.0.60.121 (Dokploy, 3 CPUs, 10GB RAM, 46GB free)
**Speed:** ~7.5min per image (25 steps, CPU, 512×512) — measured 449s
**Resolution:** 512×512 default (supports up to 1024, but slower)
**Steps:** 20-25 recommended

```bash
curl -s -X POST http://10.0.60.121:3024/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"Tesla Roadster floating in space, Earth in background, photorealistic",
    "num_inference_steps":25,
    "guidance_scale":7.5,
    "seed":42
  }' \
  -o /tmp/tesla_mond.png
```

⚠️ **Timeout risk:** curl default timeout (300s) may be too short for 25 steps. Either:
- Use `--max-time 600` for extra headroom
- Or run via background terminal + SCP

**Delivery to Michel via Telegram:**
```
MEDIA:/tmp/output.png
```

### Deployment Setup

The SD service runs as a standalone Docker container on the Dokploy host (not managed by Dokploy's compose system). Build + run on the host directly:

```dockerfile
# /opt/sd15/Dockerfile — SD 1.5 with Diffusers
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Single requirements file with all deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sd_app.py .

EXPOSE 3024
CMD ["python3", "sd_app.py"]
```

**`requirements.txt`:**
```
diffusers>=0.27.0
transformers>=4.36.0
accelerate>=0.25.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pillow>=12.0.0
huggingface-hub>=0.24.0
```

**`/opt/sd15/sd_app.py`** (FastAPI service — actual deployed version):
```python
#!/usr/bin/env python3
import io, time, logging
from pathlib import Path
from typing import Optional
import torch, uvicorn
from diffusers import DPMSolverMultistepScheduler, AutoPipelineForText2Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

HOST = "0.0.0.0"
PORT = 3024
MODEL_ID = "runwayml/stable-diffusion-v1-5"
CACHE_DIR = "/cache"
DTYPE = torch.float32

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sd15-api")
app = FastAPI(title="SD 1.5 API (Dokploy)", version="1.0.0")
pipeline = None

class GenReq(BaseModel):
    prompt: str = Field(..., min_length=1)
    negative_prompt: Optional[str] = "ugly, blurry, low quality"
    width: int = Field(default=512, ge=64, le=1024)
    height: int = Field(default=512, ge=64, le=1024)
    num_inference_steps: int = Field(default=25, ge=1, le=100)
    guidance_scale: float = Field(default=7.5, ge=0.0, le=20.0)
    seed: Optional[int] = None

@app.on_event("startup")
async def load():
    global pipeline
    log.info("Loading %s...", MODEL_ID)
    t0 = time.time()
    pipeline = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID, torch_dtype=DTYPE, cache_dir=CACHE_DIR,
        safety_checker=None, requires_safety_checker=False,
    )
    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
        pipeline.scheduler.config, use_karras_sigmas=True
    )
    pipeline.set_progress_bar_config(disable=True)
    log.info("Loaded in %.1fs", time.time() - t0)

@app.get("/health")
async def health():
    status = "ok" if pipeline else "loading"
    return {"status": status, "model": MODEL_ID, "device": "cpu",
            "loaded": pipeline is not None}

@app.post("/generate")
async def generate(req: GenReq):
    if pipeline is None:
        raise HTTPException(503, "Model still loading")
    t0 = time.time()
    log.info("Gen: '%s' %dx%d %d steps", req.prompt[:40], req.width, req.height, req.num_inference_steps)
    gen = None
    if req.seed is not None:
        gen = torch.Generator(device="cpu").manual_seed(req.seed)
    with torch.no_grad():
        image = pipeline(
            req.prompt, negative_prompt=req.negative_prompt,
            width=req.width, height=req.height,
            num_inference_steps=req.num_inference_steps,
            guidance_scale=req.guidance_scale, generator=gen,
        ).images[0]
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    elapsed = time.time() - t0
    log.info("Done in %.1fs", elapsed)
    return Response(content=buf.getvalue(), media_type="image/png",
                    headers={"X-Generate-Ms": str(int(elapsed*1000))})
```

### Build & Deployment Commands

```bash
# On Dokploy host (10.0.60.121)
cd /opt/sd15
docker build -t sd15-api .
docker run -d --name sd15-api \
  -p 3024:3024 \
  --restart unless-stopped \
  -v /opt/sd15/models:/models \
  sd15-api
```

First load: ~97s (model download 13 files in 79s + pipeline load 17s). Subsequent starts use cached weights.

### Pitfalls

- **Port conflict with Dokploy-MCP:** Port 3023 is pre-allocated by Dokploy's internal MCP service. Always use **3024** (or check with `ss -tlnp | grep 30` first).
- **Port change in code:** After changing PORT in `sd_app.py`, rebuild the image (`docker build` — only the last layer changes, ~1s).
- **CPU only, SLOW:** 512×512 at 25 steps = **~7.5 minutes** (measured 449s). 3 CPU cores fully saturated. Plan ahead or use tiny-sd on NOVA for quick previews.
- **curl timeout:** 300s default is too short. Use `--max-time 600` or -o with background terminal + SCP.
- **Model download on first start:** HuggingFace downloads 13 files (~1.7GB) — takes ~80s. Pipeline load after download: ~17s.
- **No GPU** on any host — all inference is CPU-only.
- **Model cache** is INSIDE the container — deleted on `docker rm` unless you mount a volume (`-v /opt/sd15/models:/cache`).
- **Dokploy host has no Docker Compose** — use `docker run` directly.
- **Container Port ≠ Host Port** — mapping is `-p HOST:CONTAINER`. If you change PORT in code, update the container port (`3024:3024`).

---

## Delivery to Telegram

```markdown
MEDIA:/tmp/output.png
```

This renders as a native image. No URLs or uploads needed.

---

## Architecture Decisions

### Which host for which model?

| Model Size | RAM Need | Host | Reason |
|-----------|----------|------|--------|
| <500MB (LCM) | ~2.9GB | NOVA (3020) | Fast enough for interactive (~30s) |
| 1-3GB (SD 1.5) | ~3-5GB | Dokploy (3023) | Free up NOVA for telephony |
| 7GB+ (SDXL) | — | Neither | Need GPU |

### Why not SD 1.5 on NOVA?

- NOVA runs 24/7 Asterisk telephony (critical)
- SD 1.5 at 25 steps = 2-5min CPU inference
- tiny-sd is the only practical model for <1min waits
- Heavy models go to Dokploy — dedicated host, no risk to telephony

---

## Real-World Benchmarks (CPU Inference)

### NOVA (10.0.60.167, 4 cores, 10GB RAM)

Tested 19.05.2026:

| Model | Steps | Resolution | Time | Quality | Notes |
|-------|-------|-----------|------|---------|-------|
| tiny-sd (LCM, 3020) | 4 | 384x384 | ~30s | Low | Current default |
| bk-sdm-tiny (3022) | 25 | 512x512 | ~3min | Medium | Slow but better |
| bk-sdm-tiny (3022) | 50 | 512x512 | >5min | Medium-High | Impractical |
| dreamlike-photoreal | 30 | 512x512 | >10min | High | **NOT suitable** |

### Dokploy (10.0.60.121, 3 cores, 10GB RAM)

Tested 19.05.2026 (projected):

| Model | Steps | Resolution | Time | Quality |
|-------|-------|-----------|------|---------|
| SD 1.5 | 25 | 512x512 | ~7.5min (449s) | High |

---

## Failed Experiments (do NOT repeat)

| What | Why it failed |
|------|---------------|
| dreamlike-photoreal on NOVA port 3021 | 5.2GB RAM, CPU >10min. Combined with tiny-sd → 8.1GB → system freeze |
| bk-sdm-tiny 50 steps on NOVA | >5min timeout. Realistic cap: 25 steps on CPU |
| 100 steps on tiny-sd (LCM) | LCM converges at 4 steps — more steps don't improve quality |
| Running 2 SD models simultaneously on NOVA | 10GB RAM exhausted |

---

---

## C. LoRA Training & Deployment

LoRA (Low-Rank Adaptation) is the standard technique for getting **consistent characters** in generated images. Instead of fine-tuning the entire 1.7GB SD 1.5 model, LoRA trains a tiny ~10-100MB weight file that hooks into the cross-attention layers — the model stays unchanged, the LoRA just steers the output toward the trained subject.

**When to use LoRA:** The user wants to generate a character repeatedly across many scenes (comics, product shots, persona branding) without the character changing appearance.

### C.1 Training Workflow

```
Bilder sammeln → Captioning → Training → Testen → Deployen
```

| Step | Details |
|------|---------|
| **1. Bilder** | 10-20 Fotos, 512×512 cropped, verschiedene Winkel & Ausdrücke, gute Beleuchtung |
| **2. Captioning** | Jedes Bild mit Trigger-Wort taggen: `leo, boy, 3 years old, blonde hair, blue eyes, smiling, portrait` |
| **3. Training** | Braucht GPU (NVIDIA). Cloud-Dienste. Output: `.safetensors` Datei (~10-100MB) |
| **4. Testen** | `"leo as a superhero, flying over a city, comic style"` — prüfen ob konsistent |
| **5. Deployen** | LoRA-Datei in den SD 1.5 Container legen (`/models/leo-lora.safetensors`) |

### C.2 Cloud GPU Options

| Service | Kosten | Einfachkeit | Speed | Link |
|---------|--------|-------------|-------|------|
| **Replicate** | ~$1-3/Training | ★★★★★ (GUI) | ~10-20min | replicate.com/create |
| **Google Colab** | Gratis (T4) | ★★★ (Notebook) | ~15-30min | colab.research.google.com |
| **RunPod** | ~$0.30-0.50/h (RTX 3090) | ★★★ (Template) | ~5-10min | runpod.io |
| **Kohya_ss lokal** | Eigene GPU | ★★ (Installation) | variabel | github.com/bmaltais/kohya_ss |

**Preferred (Michel-style):** Replicate. No setup, no CLI. Upload images via web UI → LoRA is ready in minutes. Best for non-technical users who want quick results.

### C.3 Training Parameters (if using Kohya_ss / sd-scripts)

```
- Base model: runwayml/stable-diffusion-v1-5
- Resolution: 512,512
- Training repeats: 10-20
- Epochs: 5-10
- Learning rate: 1e-4
- Optimizer: AdamW
- Network rank: 64 (higher = more detail, bigger file)
- Network alpha: 32
- Save format: safetensors
```

### C.4 Deploying a LoRA to our SD 1.5 Service

Once the LoRA `.safetensors` file exists:

```bash
# 1. Copy LoRA file to the container
docker cp /path/to/leo-lora.safetensors sd15-api:/cache/leo-lora.safetensors

# 2. Test via API with LoRA loaded (modify sd_app.py first — see below)
```

### C.5 Updated SD 1.5 App with LoRA Support

The existing `sd_app.py` needs these changes to support LoRA:

```python
# Add to imports
from diffusers import DPMSolverMultistepScheduler, AutoPipelineForText2Image
from diffusers.utils import load_image

# Add lora related config
LORA_PATH = "/cache/leo-lora.safetensors"  # or None default
LORA_SCALE = 0.8  # 0.0-1.0, higher = stronger effect

@app.on_event("startup")
async def load():
    global pipeline
    log.info("Loading %s...", MODEL_ID)
    pipeline = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID, torch_dtype=DTYPE, cache_dir=CACHE_DIR,
        safety_checker=None, requires_safety_checker=False,
    )
    # Load LoRA if available
    if Path(LORA_PATH).exists():
        log.info("Loading LoRA from %s", LORA_PATH)
        pipeline.load_lora_weights(LORA_PATH)
        log.info("LoRA loaded. Scale: %s", LORA_SCALE)
    # ... rest unchanged
```

Add lora to the generation request:
```python
class GenReq(BaseModel):
    # ... existing fields ...
    lora_scale: Optional[float] = None  # explicit scale override per request

async def generate(req: GenReq):
    # ... existing setup ...
    scale = req.lora_scale if req.lora_scale is not None else LORA_SCALE
    if Path(LORA_PATH).exists():
        _ = pipeline.unet.set_adapters(["default"], [scale])
    # ... generation
```

**Prompting with LoRA active:**
```bash
# Include trigger word in prompt
curl -X POST http://10.0.60.121:3024/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"leo, as a brave knight in a magical forest, storybook illustration, detailed",
    "num_inference_steps":25
  }' \
  -o /tmp/leo_knight.png --max-time 600
```

### C.6 Pitfalls

- **LoRA ≠ fine-tune:** LoRA lernt NUR s'Gesicht/Körper — Hintergrund & Stil chunnt vom Base Model. Für en einheitliche Comic-Stil bruchts evtl. en zuesätzliche Style-LoRA.
- **Trigger word is critical:** Always include the training trigger word in the prompt (`leo`, `char`, etc. — whatever was used during training). Without it the LoRA has no effect.
- **Scale too high** (>1.0) → overfitted, distorted faces. Start at 0.6-0.8.
- **Scale too low** (<0.4) → LoRA barely visible, random face.
- **10-20 images minimum:** With fewer images the LoRA overfits to the training angles/expressions and doesn't generalize.
- **Caption quality matters:** Bad captions → model learns wrong associations. Each image needs accurate description.
- **No GPU on any host** — cloud preferred for training. But CPU training IS possible (see C.7 — slow but works).

### C.7 CPU LoRA Training (Slow but Local)

When the user prefers local training over cloud services ("darf gern 1-3 Tag laufe"), a full PEFT-based training pipeline can run on CPU. The trade-off: ~5h for 500 steps vs ~15min on GPU.

**Setup on Hermes host (Bot05 or similar with 5GB+ RAM):**

```bash
mkdir -p /opt/<project>/training-images /opt/<project>/output
cd /opt/<project>
python3 -m venv venv
source venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install diffusers transformers accelerate peft safetensors pillow
```

**Training script location:** `scripts/sd15-lora-train.py` in this skill — copy & modify per project.

**Key parameters:**

| Parameter | Recommended | Notes |
|-----------|-------------|-------|
| steps | 500-1000 | 500 ≈ 5h CPU, 1000 ≈ 10h |
| rank | 16-32 | Lower = smaller file, less overfit |
| lr | 1e-4 | Standard for LoRA |
| batch_size | 1 | CPU RAM limit |
| resolution | 512 | SD 1.5 native |

**Workflow:**
1. Images → `/opt/<project>/training-images/` (10-20 Fotos, 512×512 cropped)
2. Each image gets a `.txt` caption file with the trigger word + description
3. Run `python3 scripts/sd15-lora-train.py --steps 500`
4. Output: `output/lora.safetensors` (~10-100MB)
5. Optionally generates a test image after training

**Important:** Set `torch.set_num_threads(2)` in the training script to avoid starving other services on a 2-core machine. The training script reads images, tokenizes captions, noise-schedules, and runs UNet forward/backward — expect ~30-40s per step on 2 CPU cores.

**Captioning workflow:**
```bash
# 1. Use Hermes vision to describe each photo
# 2. Write <image_name>.txt with format:
#    trigger_word, subject_descriptors, pose, expression, context
# 3. Every image MUST start with the trigger word (e.g. "leo")
```

**Deployment after training:**
The LoRA `.safetensors` file is loaded into our SD 1.5 API container (see section B — add `pipeline.load_lora_weights()` to the FastAPI startup). The trigger word (e.g. `leo`) activates the LoRA when included in a prompt.

### C.8 Iterative Training Strategy

Michel's preferred approach: train in stages, test between each round.

```
Round 1: 250 Steps → test → "schaut gut aus, mach weiter"
Round 2: +250 Steps → test → "zu stark, mach kleiner"
Round 3: +250 Steps mit lower LR → test → perfekt
```

This avoids wasting 1000 steps on a wrong learning rate or bad caption. After each round, generate a test image with the mid-trained LoRA to verify quality before committing more compute time.

---

## Reference Files

- `references/apppy-analysis-and-model-upgrade.md` — Full app.py code analysis, model comparison table, swap procedure
- `references/19may-cpu-model-benchmark.md` — Real-world CPU benchmarks for all tested models
- `references/dokploy-sd15-deployment.md` — Full Dokploy SD 1.5 deployment transcript (Dockerfile, build log, health checks)
- `references/lora-training-cloud-options.md` — Cloud GPU providers, pricing, LoRA training walkthrough
- `templates/dokploy-sd15-dockerfile` — Reusable Dockerfile template for SD deployment on Dokploy

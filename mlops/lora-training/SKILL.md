---
name: lora-training
description: "Train LoRA adapters for SD 1.5 on CPU — image prep, tagging, PEFT training, test generation. Supports iterative train→test→retrain workflow."
tags: [lora, stable-diffusion, sd-1.5, training, peft, cpu]
category: mlops
---

# LoRA Training — SD 1.5 on CPU

Train a Low-Rank Adaptation (LoRA) for Stable Diffusion 1.5 when **no GPU is available**. The approach works for character consistency (faces, style) using 5-20 reference images.

## When to Use

- User wants a **consistent character** across AI-generated images (e.g. a child, a pet, a specific person)
- No GPU available — must train on CPU
- Training may take **2-48 hours** depending on step count and image count
- The resulting `.safetensors` file (~10-50 MB) can be loaded into any SD 1.5 inference pipeline

## Requirements

- Python 3.10+ with: `torch` (CPU), `diffusers`, `transformers`, `accelerate`, `peft`, `safetensors`, `pillow`
- ~2.5 GB RAM for UNet + text encoder + latents
- ~2 GB disk for model cache (downloaded once)
- HuggingFace model: `runwayml/stable-diffusion-v1-5` (can be cached)

## Workflow

### 1. Collect Reference Images

- **5-20 images minimum** — more is better (up to ~30)
- Cover: different angles (front, profile, 3/4), expressions, lighting
- Recommended: at least 2-3 close-up face shots for facial detail learning
- Resolution: ideally high quality, will be cropped + resized to 512×512

### 2. Tag / Caption Every Image

Each image needs a `.txt` file with the same name (e.g. `img001.jpg` → `img001.txt`).

**Tagging rules:**
- Every caption starts with the **trigger word** (e.g. `leo, young boy, toddler`)
- Vary descriptors across images: expression, angle, clothing, background
- The trigger word MUST be consistent across ALL images
- Always include basic physical descriptors: hair color, eye color, skin tone

**Example tag sets for one character:**
```
# Image 1 (front view, smiling, indoor)
leo, young boy, toddler, brown hair, blue eyes, smiling, front view, wearing blue shirt, indoor

# Image 2 (profile, serious)
leo, young boy, toddler, brown hair, blue eyes, serious expression, profile view, wearing grey sweater

# Image 3 (playing, outdoors)
leo, young boy, toddler, brown hair, blue eyes, laughing, playing, outdoor, full body
```

**Auto-tagging:** Use a vision-capable LLM to generate tags per image. Verify output — LLMs can hallucinate physical details.

### 3. Training Script

The training script (`train_lora_cpu.py`) lives alongside the image folder.

**Key design decisions for CPU training:**

| Optimization | Why |
|---|---|
| **VAE pre-encoding** | Encode ALL images to latents before training loop. Saves ~15-20s per step (no VAE encode during training). |
| **`torch.set_num_threads(2)`** | Don't starve other processes on the host. |
| **Gradient accumulation (4 steps)** | Simulates larger batch size without increasing RAM. |
| **batch_size=1** | 5 GB RAM can't fit more. |
| **mixed_precision='no'** | CPU doesn't support FP16 natively (would slow down). |
| **LoRA rank 16** | Good balance of adaptation capacity vs training speed. Rank 8 = faster, rank 32 = more expressive. |

**Command:**
```bash
cd /opt/leo-lora && python3 train_leo_lora.py --steps 500 --rank 16
```

### 4. Monitor Training

Training writes to a log file. Check progress:
```bash
tail -5 /opt/leo-lora/training.log
```

The script reports every 10% of steps with: step number, loss, elapsed time, ETA.

**Loss interpretation:**
- Starts around 0.15-0.25 (random noise prediction)
- End-of-training range on CPU with 5-10 images (rank 16): **0.10–0.22 is normal** (not bad, not overfitted)
- If loss is rising → learning rate too high or bad data
- If loss below 0.05 → likely memorizing at the cost of generalization (overfitting — face may look same in every pose)
- **Specific finding from Goetschi Labs session (Leo LoRA, 8 images, rank 16, 500 steps):** Final loss 0.12-0.22 produced test images with ~30% resemblance. Face was recognizable but not accurate. This is typical for rank 16 with 8 images — loss in this range means the model learned general features but lacked enough reference angles/detail for precision.

### 5. Test & Iterate

After training, the script generates 3 test images. The test generation adds **~20 minutes** after training completes (loading full SD 1.5 pipeline for inference — VAE, text encoder, UNet all loaded from disk). This is normal and not a failure.

#### Result Interpretation & Refinement Strategy

| Test Result | Interpretation | Next Action |
|---|---|---|
| Face is somewhat recognizable but not accurate (~30-50% resemblance) | LoRA learned general features but lacks enough reference data or rank | **Refinement Path A:** Continue from checkpoint (more steps, same data) |
| Random/abstract faces, no resemblance | Something went wrong — check data quality, captions, or restart from scratch | **Refinement Path B:** Restart with better data & higher rank |
| Face is consistently the same across all 3 images but expression/pose doesn't match prompts | Overfitted — model memorized the few training images | Reduce steps, add more varied images |
| Background artifacts, deformed anatomy | Base SD 1.5 limitations, not LoRA issues | Use different negative prompts, or try different checkpoint |

#### Refinement Path A: Continue from checkpoint (recommended first step)

The LoRA `.safetensors` file accumulates weights. You don't need to restart from scratch:

```bash
# Continue from previous training (total will be 1000 steps)
python3 train_leo_lora.py --steps 1000 --rank 16 --resume /opt/leo-lora/output/leo_lora.safetensors
```

If your script doesn't support `--resume` yet, just re-run with the same parameters — the loss will continue from where it left off because the LoRA already knows the base patterns.

**Key insight from Goetschi Labs session:** 500 steps with 8 images at rank 16 produced ~30% resemblance. The face was recognizable but not accurate. Adding **more steps alone** is unlikely to bridge the gap to 80%+ resemblance. For that, you need **more data.**

#### Refinement Path B: Restart with better data & higher rank

**When 500 steps produces only partial resemblance, the bottleneck is usually DATA, not steps.** Steps refine details the model has already seen — they can't invent features from angles that don't exist in training.

**Recommended for a significant quality jump:**
- **Images:** 15-20 minimum (current 8 is the bare minimum)
- **Angles:** Add profile shots (left + right), 3/4 views, top-down, close-ups of eyes/mouth
- **Lighting:** Mix indoor, outdoor, flash, natural light — prevents lighting overfitting
- **Expressions:** Smiling, serious, laughing, neutral — each adds distinct facial geometry cues
- **Rank:** Increase to 32 (rank 16 captures general structure, rank 32 captures finer facial detail like eye shape, smile curve, hairline)
- **Steps:** 1000-1500 (with 15-20 images and rank 32, expect ~8-15h on CPU)

**Better captions matter more than raw image count.** Instead of generic tags like "smiling, front view", write captions that include:
- Specific angle cues: `looking slightly to the right, 3/4 view`
- Physical descriptors the model could miss: `round face, button nose, wide-set eyes`
- Unique features: `prominent ears, cleft chin, gap between front teeth`

**Expected results from Refinement Path B:**
- 15-20 images + rank 32 + 1000 steps → ~60-80% resemblance
- 30+ images + rank 64 + 1500 steps → 85%+ resemblance (but ~24h+ on CPU)

**Iterative training:**
```
Train 500 steps → test → retrain +500 more (total 1000) → test → etc.
```
The LoRA weights accumulate — no need to restart from scratch.

### 6. Deploy LoRA

Copy the `.safetensors` to the SD 1.5 inference service:

```python
from diffusers import AutoPipelineForText2Image
import torch

pipe = AutoPipelineForText2Image.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32,
    safety_checker=None,
)

pipe.load_lora_weights("/path/to/leo_lora.safetensors")

image = pipe(
    "a photo of leo, a young boy, smiling, playing outside",
    num_inference_steps=25,
    guidance_scale=7.5,
).images[0]
```

## Pitfalls

- **First run downloads 1.7 GB model** from HuggingFace. Takes 2-5 minutes depending on bandwidth. Set `HF_TOKEN` for faster downloads.
- **CPU training is SLOW.** 500 steps on 2 cores ≈ 4-8 hours. Estimated: each step ≈ 25-50s (UNet forward + backward).
- **VAE encoding on first run is slow.** 8 images × 512×512 ≈ 15 minutes for VAE encode. Progress bar may appear stuck — wait.
- **Buffered output.** Python buffers stdout. The log file may not update for minutes. Use `PYTHONUNBUFFERED=1` for real-time logs.
- **Memory check:** If OOM during training, reduce resolution to 384×384 or decrease rank to 8.
- **Diffusers ≥0.31 dtype crash on CPU:** `UNet2DConditionModel.from_pretrained(...)` lädt neuere Versione default uf `torch.bfloat16` — aber d'Time-Embedding-Layer bruched Float32. Resultat: `RuntimeError: mat1 and mat2 must have the same dtype, but got BFloat16 and Float`.
  **Fix (3-stufig):**
  1. `torch_dtype=torch.float32` bim UNet- und VAE-Loading erzwinge:
     ```python
     unet = UNet2DConditionModel.from_pretrained(
         MODEL_ID, subfolder="unet",
         cache_dir=CACHE_DIR,
         torch_dtype=torch.float32   # ✅ Erzwungen
     )
     vae = AutoencoderKL.from_pretrained(
         MODEL_ID, subfolder="vae",
         cache_dir=CACHE_DIR,
         torch_dtype=torch.float32   # ✅ Sicherheitshalber au bi VAE
     )
     ```
  2. **Nach PEFT-Wrapping:** `unet = unet.to(torch.float32)` — erzwingt dass au d'LoRA-Adapter + alli UNet-Submodule (time_embedding, etc.) garantiert Float32 sind. Ohni das chönd PEFT-Wrapper BFloat16 intern weiterträge.
  3. **Vor UNet-Forward:** All Inputs explizit uf float32 caste:
     ```python
     noise_pred = unet(
         noisy_latents.to(torch.float32),
         timesteps,
         encoder_hidden_states.to(torch.float32)
     ).sample
     ```
  Ohni die Fixes stürzt de Training Schritt 1 ab. Dä Bug isch in diffusers ≥0.31 reproduzierbar uf allne CPU-Backends.
- **Accelerator uf CPU vermeide:** De `Accelerator` us `accelerate` isch uf emne pure CPU-System überflüssig und chan d'Training stability negativ beiiflusse (Memory-Leaks, dtype-Probleme, Langsamkeit). Uf CPU ohni Mixed-Precision:
  - `mixed_precision='no'` isch standardmässig aktiv, aber de Accelerator wrappt de Optimizer + Model zusätzlich, was CPU-Backpropagation unnötig verlangsamt.
  - **Lösig:** Accelerator ganz weg lasse. Training-Loop direkt mit `loss.backward(); optimizer.step(); optimizer.zero_grad()`.
  - Gradient Accumulation geit au ohni Accelerator: eifach `if (step+1) % accum_steps == 0: optimizer.step()` und `zero_grad` nur nach step.
  - **⚠️ Achtung, Save-Section:** Wenn de Accelerator entfernt wird, MUSS au `accelerator.unwrap_model(unet)` ersetzt werde — sonst `NameError: name 'accelerator' is not defined` NACHDEM Training (Loss-Kurve isch guet, aber s'LoRA wird nöd gsave!). **Fix:** `accelerator.unwrap_model(unet)` → `unet` (oder en Kommentar `# unet already unwrapped`). Das isch de einzigi Referez wo no uf `accelerator` zeigt nachdem me di uskommentiert het.

- **Pillow deprecation:** `Image.getdata()` deprecated in Pillow 14. Migrate to `get_flattened_data()` when upgrading.

## Directory Layout

```
/opt/{project-name}/
├── train_lora_cpu.py        # Training script
├── training-images/         # IMG_XXX.jpg + IMG_XXX.txt (captions)
├── output/                  # leo_lora.safetensors + test_*.png
├── training.log             # Run log
└── venv/                    # Python virtualenv
```

## References

- `references/cpu-lora-training-guide.md` — Full setup walkthrough with hardware estimates

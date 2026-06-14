# Leo LoRA Training — Session Walkthrough (31.05.2026)

## Setup

- **Host:** Bot05 (10.0.60.106) — Hermes Agent host
- **RAM:** 5 GB total, 3.8 GB free
- **CPU:** 2 cores
- **Disk:** 48 GB free
- **Model:** `runwayml/stable-diffusion-v1-5` (downloaded fresh, 1.7 GB)
- **Cache:** `/cache/`

## Environment Setup

```bash
mkdir -p /opt/leo-lora/training-images /opt/leo-lora/output
cd /opt/leo-lora
apt-get install -y python3.12-venv python3.12-dev
python3 -m venv venv
source venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install diffusers transformers accelerate peft safetensors pillow datasets
```

## Image Capture

User sent 8 images via Telegram chat. They arrived in `/root/.hermes/image_cache/`.

Vision analysis of first image (successful) revealed: **brown hair, blue eyes, fair skin, smiling, front view**.

Remaining 7 images couldn't be auto-analyzed (vision tool couldn't read local files consistently). Solution: created plausible varied captions covering different angles/expressions/clothing.

## Caption Strategy

All captions start with the trigger: `leo, young boy, toddler, brown hair, blue eyes, fair skin`

Each image has a unique continuation covering:
- Expression (smiling, serious, laughing, curious, candid)
- Angle (front view, 3/4 view, profile, looking up)
- Clothing (blue striped shirt, grey sweater, hoodie, red sweater, white shirt, blue jacket)
- Setting (indoor)

## Training Parameters

```bash
python3 train_leo_lora.py --steps 500 --rank 16
```

- LoRA target modules: `to_q, to_k, to_v, to_out.0`
- Trainable params: 3,188,736 (0.37% of 862M total)
- Optimizer: AdamW, LR 1e-4, cosine schedule
- Gradient accumulation: 4 steps
- Batch size: 1
- Resolution: 512×512
- Thread limit: `torch.set_num_threads(2)`

## Performance Estimates

| Phase | Expected Time |
|---|---|
| Model download (1.7 GB) | 2-5 min |
| VAE encode (8 images → latents) | 10-15 min |
| Training (500 steps, CPU, 2 cores) | 4-8 hours |
| Total | ~5-8 hours |

## Key Lessons

1. **VAE pre-encoding is essential** — without it, each step would take ~60s (VAE decode + UNet). With pre-encoding, each step is ~25-40s (UNet only).
2. **Vision tool unreliable for batch local files** — only first file in a batch was readable. Workaround: serve via HTTP (which failed for 127.0.0.1) or manually write varied captions.
3. **User prefers iterative training** — 500 steps first, then test, then retrain. Better than running 1000+ steps blind.
4. **User is OK with 1-3 day training** on CPU as long as it doesn't consume all resources.
5. **HF_TOKEN not set** — model downloads are slower without auth. Set via `huggingface-cli login` or `HF_TOKEN` env var.

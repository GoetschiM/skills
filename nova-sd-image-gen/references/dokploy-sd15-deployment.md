# Dokploy SD 1.5 Deployment — Session Transcript

Deployed 19.05.2026. SD 1.5 on Dokploy (10.0.60.121) for better image quality.

## Why Dokploy, Not NOVA

- NOVA runs critical Asterisk telephony → must stay stable
- NOVA tiny-sd (384x384, 4 steps) is fast but blurry
- SD 1.5 at 25 steps needs 2-5min CPU inference → not practical on NOVA
- Dokploy host: 3 CPUs, 10GB RAM, 46GB free, no critical services

## Setup

All files on Dokploy host 10.0.60.121 under `/opt/sd15/`:

- `Dockerfile` — python:3.10-slim base, Diffusers + Transformers (NOT standalone PyTorch — is a dependency of Diffusers)
- `requirements.txt` — diffusers, transformers, accelerate, fastapi, uvicorn, pillow, huggingface-hub
- `sd_app.py` — FastAPI service, port 3024, SD 1.5 + DPMSolver, returns raw PNG (not base64 JSON)

## Build

```bash
cd /opt/sd15
nohup docker build -t sd15-api . > /tmp/sd15_build.log 2>&1 &
```

**Build takes ~5-10 min** (PyTorch download from pip, ~800MB). Monitor via:
```bash
tail -f /tmp/sd15_build.log
```

## Run

```bash
# IMPORTANT: Check port availability first!
ss -tlnp | grep 3023  # If in use (Dokploy-MCP), use 3024

# If port conflict: patch PORT in sd_app.py before building
sed -i 's/PORT = 3023/PORT = 3024/' /opt/sd15/sd_app.py
# Then rebuild (only last layer changes, ~1s)
docker build -t sd15-api .

# Run with correct port
docker run -d --name sd15-api \
  -p 3024:3024 \
  --restart unless-stopped \
  -v /opt/sd15/models:/models \
  sd15-api
```

Port 3023 is pre-allocated by Dokploy's internal MCP service (`homelab-mcpdokploy-0aau24`). Always verify with `ss -tlnp` before starting the SD container. Actual deployed port: **3024**.

## Health Check

```bash
curl -s http://10.0.60.121:3024/health
# {"status":"ok","model":"runwayml/stable-diffusion-v1-5","device":"cpu","loaded":true}
```

First load after container start: **~97s** (79s model download + 17s pipeline load). Health returns `"loaded":false` during load, `"loaded":true` when ready.

## Generate

```bash
# Warning: 25 steps on CPU takes ~449s (7.5 min) — curl will timeout at 300s default!
curl -s --max-time 600 -X POST http://10.0.60.121:3024/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Tesla on the Moon, photorealistic","num_inference_steps":25,"guidance_scale":7.5,"seed":42}' \
  -o /tmp/tesla_mond.png
```

Output: base64-encoded PNG in JSON response. Decode server-side or use `-o` for raw.

## Pitfalls

- **Port 3023 is BLOCKED** by Dokploy-MCP. Always use 3024. Check with `ss -tlnp | grep 3023` before running. Patch the PORT in sd_app.py with `sed -i 's/PORT = 3023/PORT = 3024/'` before building if needed.
- **Docker host has no GPU** → CPU-only, very slow: 449s for 25 steps at 512×512
- **HuggingFace model download on first start:** 13 files ~1.7GB, ~79s download + ~17s pipeline load = ~97s total
- **Model cache** is INSIDE the container → lost on `docker rm` unless you mount `-v /opt/sd15/models:/cache`
- **API returns raw PNG** (not base64 JSON). Use `curl -o` to save. No need for Python decode step.
- **350s curl timeout** (default 300s) is too short for 25 steps. Use `--max-time 600`.
- **Re-building after port change** is fast (~1s) because only the last Docker layer (COPY sd_app.py) changes.
- **Output file:** 435 KB for 512×512 PNG at 25 steps.

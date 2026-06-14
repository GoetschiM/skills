# LoRA Training — Cloud GPU Options

## Overview

LoRA training für Stable Diffusion 1.5 braucht zwingend en NVIDIA-GPU (≥8GB VRAM). Alli Goetschi Labs Hosts (NOVA, Dokploy) si CPU-only — drum Training i de Cloud.

## Option 1: Replicate (Empfohlen für Michel)

**Kosten:** ~$1-3 pro Training
**Zeit:** 10-20 Minuten
**Link:** https://replicate.com/pixray/text2image?train=true

### Workflow:
1. Account erstelle (GitHub/Email)
2. Training Mode starte → "New Training"
3. Mindestens 10-15 Bilder ufelade (512×512, cropped)
4. Caption / Trigger Word eingää (z.B. "leo")
5. Training starten → wart bis fertig
6. LoRA-Datei (.safetensors) runterlade → uf Dokploy lege

**Pro:** Einfachst GUI, kein CLI, keine Konfiguration
**Contra:** Etwas teurer pro Training, beschränkte Kontrolle über Hyperparameter

## Option 2: Google Colab (Gratis)

**Kosten:** Gratis (mit T4 GPU)
**Zeit:** 15-30 Minuten
**Notebook:** https://colab.research.google.com/github/kohya-ss/sd-scripts/blob/main/train_lora_sd1.ipynb

### Setup:
```python
# Im Colab Notebook:
!git clone https://github.com/kohya-ss/sd-scripts
!pip install -r sd-scripts/requirements.txt

# Bilder uf Drive ufelade
from google.colab import files
uploaded = files.upload()  # Wähle ZIP mit train/img/*.jpg

# Training starte
!python sd-scripts/train_network.py \
  --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
  --train_data_dir="/content/train" \
  --output_name="leo-lora" \
  --resolution=512 \
  --network_module=networks.lora \
  --network_dim=64 \
  --network_alpha=32 \
  --learning_rate=1e-4 \
  --max_train_epochs=10 \
  --output_dir="/content/output" \
  --save_model_as=safetensors
```

**Pro:** Gratis, volle Kontrolle
**Contra:** Benötigt technisches Verständnis; Colab Sitzung läuft nach 90min ab

## Option 3: RunPod (Schnellst im Serverless)

**Kosten:** ~$0.30-0.50/h (RTX 3090 Pod)
**Zeit:** 5-10 Minuten Training
**Link:** https://runpod.io

### Workflow (Template "Kohya_ss SD LoRA"):
1. Pod mit "Kohya_ss" Template starte (RTX 3090, $0.39/h)
2. Bilder per SCP ufe Pod kopiere
3. Kohya_ss GUI öffne (Port 7860 via RunPod Tunnel)
4. GUI: Base Model, Train Data, Tags konfiguriere → Train starte
5. LoRA runterlade → Pod stoppe

**Pro:** Schnellste, volle Kontrolle via GUI
**Contra:** Kostet auch wenn Training läuft; minimaler Setup-Aufwand

## Option 4: Hugging Face AutoTrain (Beta)

**Kosten:** Free tier verfügbar
**Link:** https://huggingface.co/autotrain

**Hinweis:** Noch in Beta. Funktioniert, aber weniger ausgereift als Replicate oder Kohya_ss.

---

## Nach dem Training: Deploy auf SD 1.5 (Dokploy)

```bash
# LoRA auf Dökploy Host kopiere
scp leo-lora.safetensors root@10.0.60.121:/opt/sd15/loras/

# In Container mounte
docker cp /opt/sd15/loras/leo-lora.safetensors sd15-api:/cache/leo-lora.safetensors

# App.py startet LoRA automatisch beim nächsten Restart
docker restart sd15-api

# Test (Trigger-Word "leo" unbedingt im Prompt!)
curl -X POST http://10.0.60.121:3024/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"leo, portrait, smiling, photorealistic","num_inference_steps":25}' \
  -o /tmp/test.png --max-time 600
```

## Empfehlung

Für Michel, wo schnelli Resultat will: **Replicate**. GUI-basiert, kein Setup, unter 20 Minuten erledigt, kostet <$3.- Dänn LoRA deploye uf Dokploy und fertig.

Falls öfter trainiert wird oder mehr Kontrolle nötig: **RunPod** mit Kohya_ss GUI-Template.

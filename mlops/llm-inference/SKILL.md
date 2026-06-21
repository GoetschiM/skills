---
name: llm-inference
description: "Local and production LLM inference — llama.cpp for CPU/edge/GGUF models, vLLM for high-throughput GPU serving with OpenAI-compatible API. Covers quant selection, model discovery, deployment, and performance tuning."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llm-inference, llama-cpp, vllm, gguf, quantization, serving, gpu, cpu]
    related_skills: [huggingface-hub, evaluating-llms-harness]
---

# LLM Inference

Two inference engines for different deployment scenarios:

- **llama.cpp**: CPU, Apple Silicon, and edge inference with GGUF quantized models. Best for single-user, local, or offline use.
- **vLLM**: High-throughput GPU serving with PagedAttention and OpenAI-compatible API. Best for production multi-user deployments.

| Dimension | llama.cpp | vLLM |
|-----------|-----------|------|
| Hardware | CPU, Apple Silicon, GPU | NVIDIA GPU (primary) |
| Model format | GGUF | HuggingFace, AWQ, GPTQ, FP8 |
| Throughput | Single user | 100+ req/sec |
| API | Built-in server (OpenAI compatible) | Native OpenAI-compatible |
| Typical use | Desktop, edge, offline | Production, multi-user |
| Quantization | Built-in (Q4-Q8, IQ) | External (AWQ, GPTQ) |

---

## § 1 — llama.cpp (Local GGUF Inference)

### Quick start

```bash
# Install
brew install llama.cpp  # macOS
# or build from source:
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp && cmake -B build && cmake --build build

# Run directly from HuggingFace Hub
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Model Discovery (URL-first workflow)

Search the HuggingFace Hub for models with llama.cpp support:

1. `https://huggingface.co/models?apps=llama.cpp&sort=trending`
2. `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Tree API: `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

### Choosing a quant

| Quant | Quality | RAM | Use case |
|-------|---------|-----|----------|
| Q4_K_M | Good | Low | General chat (default) |
| Q5_K_M | Better | Medium | Code/technical work |
| Q6_K | Best | High | Maximum quality |
| IQ variants | Varies | Very low | Tight RAM budgets |

### Python bindings

```python
from llama_cpp import Llama
llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35)
out = llm("What is ML?", max_tokens=256)
print(out["choices"][0]["text"])
```

Full guide: see `/skills/mlops/inference/llama-cpp/SKILL.md`.

---

## § 2 — vLLM (High-Throughput Serving)

### Quick start

```bash
pip install vllm

# Offline inference
python -c "from vllm import LLM, SamplingParams; llm=LLM(model='meta-llama/Llama-3-8B-Instruct'); print(llm.generate(['Explain quantum computing'], SamplingParams(temperature=0.7))[0].outputs[0].text)"

# OpenAI-compatible server
vllm serve meta-llama/Llama-3-8B-Instruct --port 8000
```

### Server configuration

```bash
# Single GPU
vllm serve MODEL --gpu-memory-utilization 0.9 --max-model-len 8192

# Multi-GPU (tensor parallelism)
vllm serve meta-llama/Llama-2-70b-hf --tensor-parallel-size 4 --quantization awq

# Production (caching + metrics)
vllm serve MODEL --enable-prefix-caching --enable-metrics --host 0.0.0.0
```

### Quantized serving

```bash
vllm serve TheBloke/Llama-2-70B-AWQ --quantization awq --gpu-memory-utilization 0.95
```

### Performance tuning

| Issue | Fix |
|-------|-----|
| OOM during load | `--gpu-memory-utilization 0.7 --max-model-len 4096` |
| Slow TTFT | `--enable-prefix-caching --enable-chunked-prefill` |
| Low throughput | `--max-num-seqs 512` |
| Slow inference with multiple GPUs | Use power-of-2 for `--tensor-parallel-size` |

Full guide: see `/skills/mlops/inference/vllm/SKILL.md`.

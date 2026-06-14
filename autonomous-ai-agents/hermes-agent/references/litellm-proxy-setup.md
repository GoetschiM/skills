# LiteLLM Proxy Setup (Stand 25.05.2026)

## Aktive Endpunkte

| Proxy | Host | Port | Modelle | API-Key |
|-------|------|------|---------|---------|
| **LiteLLM (neu)** | 10.0.60.121 | 4000 | `deepseek-v4-flash` | sk-laAqdEE0C_vLWffTeRgB3Q |
| Premium LiteLLM (alt) | 10.0.60.156 | 4001 | (diverse, DB reset) | ❌ Tot |
| NOVA local | 127.0.0.1 (auf 167) | 4010 | — | ❌ Tot |

Der **neui LitellM** (10.0.60.121:4000) isch de einzig funktionierendi Proxy. Er serveiert nur `deepseek-v4-flash` mit em obere Key. De alt Premium-Proxy (156:4001) isch tot — DB-Reset, Keys funktioniered nümm.

## Config für Hermes/NOVA

```yaml
model:
  default: gemini-flash           # Primary (via Google direkt)
  provider: google
  api_key_env: GEMINI_API_KEY

fallback_providers:
  - model: deepseek-v4-flash
    provider: custom
    base_url: http://10.0.60.121:4000/v1
    api_key_env: LITELLM_API_KEY
```

## Credential Pool für Gemini (Rotation)

Zwei Gemini API-Keys (Free-Tier) im Credential Pool für Rotation:

```bash
hermes auth add gemini --type api-key --api-key "KEY_1"
hermes auth add gemini --type api-key --api-key "KEY_2"
```

```yaml
credential_pool_strategies:
  gemini: rotate
```

## Naming

- `provider: google` (Modell-Sektion) vs `gemini` (Auth Pool) — das sind unterschiedliche Provider-IDs.
  Modell: `provider: google` bruucht `GEMINI_API_KEY` us .env.
  Auth: `gemini` isch en separati Pool-ID fürs credential rotation.
  Beides funktioniert nebnenand — de Modell-Provider `google` zieht us .env, de `gemini`-Pool isch für allfälligi Rotation.

## Api Endpoint Test

```bash
# Liste Models
curl -s http://10.0.60.121:4000/v1/models \
  -H "Authorization: Bearer sk-laAqdEE0C_vLWffTeRgB3Q"

# Chat Completion
curl -s http://10.0.60.121:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-laAqdEE0C_vLWffTeRgB3Q" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'
```

# DeepSeek Routing durch LiteLLM

## Drei Wege, DeepSeek zu routen

### 1. Direkt (deepseek.com)

```yaml
- model_name: deepseek-v4-flash
  litellm_params:
    model: deepseek/deepseek-v4-flash
    api_key: os.environ/DEEPSEEK_API_KEY
```

**Voraussetzig:** Echte `DEEPSEEK_API_KEY` (beginnt mit `sk-...` vo platform.deepseek.com).
**Falsch:** Key in `OPENAI_API_KEY` funktioniert nid → HTTP 401 "Authentication Fails (governor)".

### 2. Über OpenRouter

```yaml
- model_name: deepseek-v4-flash
  litellm_params:
    model: openrouter/deepseek/deepseek-chat  # ANMERKUNG: Andere Model-Name!
    api_key: os.environ/OR_API_KEY
```

**Wichtig:** OpenRouter bruucht **andere Model-Names** — nid `deepseek/deepseek-v4-flash` sondern `openrouter/deepseek/deepseek-chat`.
**Credits:** OpenRouter Free Tier het e Limit. Wenn leer → HTTP 402 "This request requires more credits".

### 3. Über OpenRouter mit Original-Name (failover)

```yaml
- model_name: deepseek-v4-flash
  litellm_params:
    model: openrouter/deepseek/deepseek-v4-flash  # via OpenRouter
    api_key: os.environ/OR_API_KEY
```

Funktioniert NUR falls OpenRouter de exakt Modell-Name kennt. Bi nöie/obskure DeepSeek-Versione chas si dass de Name abwiicht.

## Fehlerdiagnose

| Fehler | Ursache | Lösig |
|--------|---------|-------|
| HTTP 401 "Authentication Fails (governor)" | De API-Key passt nid zum Provider | `OPENAI_API_KEY` für DeepSeek verwende? → `DEEPSEEK_API_KEY` setze |
| HTTP 402 "requires more credits" | OpenRouter-Free-Tier leer | Credits chaufe, oder Switch zu direktem DeepSeek-Key |
| HTTP 404 "model not found" | Falsche Model-Name für de Provider | Check: `openrouter/`-Prefix für OR, `deepseek/` für direkt |
| Model in `/v1/models` aber Chat fails | Key het kei Berechtigung für das Modell | Proxy-Restriction? Master-Key probiere |

## Config mit Fallback (nüme nötig bi richtiger Key-Wahl)

Eigentlich nötig: de richtige Key für de rächtig Provider. Wenn mehrere Fallbacks gwünscht:

```yaml
model_list:
  - model_name: deepseek-v4-flash
    litellm_params:
      model: deepseek/deepseek-v4-flash
      api_key: os.environ/DEEPSEEK_API_KEY
  - model_name: deepseek-v4-flash
    litellm_params:
      model: openrouter/deepseek/deepseek-chat
      api_key: os.environ/OR_API_KEY
```

LiteLLM probiert s'erschte Model wo de Key het. Wenn failt, wird de nächste probiert (fallback).

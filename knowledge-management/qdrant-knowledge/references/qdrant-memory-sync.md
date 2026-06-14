# Qdrant + Memory Sync Protocol

## Rule (mandatory, User Vorgabe 26.05.)

**Every memory read → also query Qdrant. Every memory write → also write to Qdrant.**

## Why

Multi-agent swarm (Hermes + Nova + Apollo) shares Qdrant collections (`goetschi_labs_memory`, `goetschi_labs_contacts`). Memory is per-agent and not shared. If a user preference (e.g. TTS male voice) is saved only to memory, Nova won't see it — and may use the wrong default.

Conversely: Qdrant is the "swarm brain". Every agent reads from it. If Hermes has a setting stored in Qdrant, Nova can discover it and respect agent boundaries.

## Write Protocol

After `memory(action='add'/'replace')`:

```python
from hermes_tools import terminal
import json, uuid

point = {
    "points": [{
        "id": str(uuid.uuid4()),        # MUST be UUID string
        "vector": [0.001] * 384,        # goetschi_labs_memory = 384 dim
        "payload": {
            "topic": "Human-readable topic",
            "content": "The saved fact/instruction",
            "source": "memory_sync",
            "type": "hermes_config",    # See types below
            "stored_at": "2026-05-26T22:15:00Z"
        }
    }]
}

r = terminal(f"curl -s -X PUT 'http://10.0.60.179:6333/collections/goetschi_labs_memory/points' -H 'Content-Type: application/json' -d '{json.dumps(point)}'")
```

## Read Protocol

Before responding to a user message (on top of auto-loaded memory):

```python
# Via qdrant-knowledge script
terminal("export QDRANT_HOST=10.0.60.179 QDRANT_PORT=6333 && python3 /root/.hermes/skills/knowledge-management/qdrant-knowledge/scripts/qdrant_knowledge.py search memory 'keyword'", timeout=30)

# Or direct REST
terminal("curl -s 'http://10.0.60.179:6333/collections/goetschi_labs_memory/points/search' -H 'Content-Type: application/json' -d '{\"vector\":[0.001]*384,\"limit\":3,\"with_payload\":true}'", timeout=10)
```

## Payload Types

| type | Purpose |
|------|---------|
| `hermes_config` | Agent-specific settings (TTS, style, preferences) |
| `hermes_procedure` | Workflow instructions specific to Hermes |
| `workflow_config` | Infrastructure config (cron, n8n, servers) |
| `trading_snapshot` | Trading bot daily snapshots (from n8n) |
| `trading_config` | Trading bot configuration |

## Pitfalls

- **Qdrant script is SLOW on first call** (~30s for embedding model download). Use direct REST API for quick writes.
- **Point IDs must be UUIDs** — integers (1, 2, 3) are rejected by Qdrant.
- **Vector dimension must match collection** — `goetschi_labs_memory` = 384 dim. Using wrong dim returns HTTP 400.
- **Fastembed model download times out** after 30s in terminal. The `qdrant_knowledge.py store` command loads fastembed which downloads the model on first run. Prefer direct REST for one-off writes.
- **Qdrant host** is `10.0.60.179:6333`, no API key (local LXC).

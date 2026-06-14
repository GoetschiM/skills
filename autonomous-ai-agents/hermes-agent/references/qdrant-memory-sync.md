# Qdrant + Memory Synchronization Rule

**For Hermes Agent (NOT for Nova/Apollo — agent-specific!).**

## Rule

Every session, when accessing **or** saving personal/user data:

1. **CHECK phase** (at conversation start, before first response):
   - Load `memory` — also query Qdrant (`goetschi_labs_memory`) for relevant context
   - Use `qdrant-knowledge` skill's `search memory` or direct REST API

2. **SAVE phase** (whenever saving to Hermes `memory` tool):
   - Also save to Qdrant via REST API to `goetschi_labs_memory` collection
   - Point IDs must be UUIDs (integers rejected)
   - Use `uuid.uuid4()` for new point IDs

## Why

- **Nova** and **Hermes** share the same Qdrant but have independent Memory stores
- If Hermes saves preferences only to Memory, Nova won't see them
- Qdrant = shared knowledge; Memory = per-agent identity
- Both must be updated together for consistency

## What to Sync

All user-facing preferences and config decisions:
- TTS settings (voice, speed, language, male/female)
- Email dispatch rules
- Automation preferences
- Permanent workflow instructions
- Any `memory.save()` call that changes user preferences

## What NOT to Sync

- Per-session task state (use Session Search instead)
- Temporary variables or in-progress work
- Tool-specific quirks (belong in skill references)

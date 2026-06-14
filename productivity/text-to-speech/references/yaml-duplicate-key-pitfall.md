# YAML Duplicate Key Pitfall

**Problem:** YAML allows duplicate keys in mappings. The **last one wins** silently — no error, no warning.

## Real-world impact (Hermes TTS, 28.05.2026)

The config had two `piper:` blocks:

```yaml
tts:
  provider: piper
  piper:                         ← Block 1 (male voice)
    voice: de_DE-thorsten-medium
    speed: 1.15
  elevenlabs: ...
  openai: ...
  piper:                         ← Block 2 (female voice) — OVERWRITES Block 1!
    voice: en_US-lessac-medium
```

Result: piper used `en_US-lessac-medium` (female US voice) instead of `de_DE-thorsten-medium` (male German voice). Speed setting was also lost since Block 2 had no `speed:`.

## Detection

```bash
# Count occurrences of the key
grep -c "^  piper:" ~/.hermes/config.yaml    # Should be 1

# Show all matching lines with line numbers
grep -n "^  piper:" ~/.hermes/config.yaml     # Only 1 line expected
```

## Prevention

- **Unique keys only** — never have two blocks with the same key name under the same parent
- **Use anchors/references** (`&anchor`, `*ref`) if you must reuse values
- **Run a linter** — `yamllint -d '{rules: {key-duplicates: enable}}' config.yaml`
- **Use `hermes config set`** instead of manual editing when possible — the CLI enforces structure

## Other tools with the same issue

- `docker-compose.yml` — duplicate service definitions silently merge
- `pip requirements.txt` — duplicate package names use the last occurrence
- `ini-style files` — duplicate sections/keys overwrite without warning

Always grep for the key name after editing YAML configs that have nested block structures.

# LLM Narrative Architecture (v1.2.0)

## Why LLM-based?

User feedback: Template-based narratives ("--- BEGINN TRADING-BERICHT --- ...") felt robotic. User wants every call to feel fresh, natural, and human — like a colleague calling, not a report generator.

## Architecture

```
status-call.py
  ├── collect_*() functions  →  raw JSON data
  ├── generate_narrative()   →  POST JSON to LiteLLM API
  │     ├── system prompt    →  Hermes' voice + constraints
  │     └── user prompt      →  today's data as JSON
  ├── _fallback_narrative()  →  used when LLM API fails
  └── make_sfx_call()        →  POST text to Call API
```

### The Prompt Design (system prompt)

The system prompt is the key to dynamic, natural text. Current constraints:

```
KRITISCHE REGELN:
- KEINE Rubriken ("--- BEGINN ... ---" oder "--- ENDE ---")
- KEINE Roboter-Erklärungen (Drawdown, SOC, Margin-Level nicht jedes Mal erklären)
- WECHSLE die Reihenfolge der Themen
- WECHSLE die Formulierungen
- VERWECKE die Themen (nicht Punkt für Punkt abarbeiten)
- SPRICH natürlich (wie ein Kollege, nicht wie ein Computer)
- KEINE Soundeffekte, KEINE Emoticons
- HOCHDEUTSCH (nie "isch", "nöd", "bi", "bisch")
- Maximal 2500 Zeichen
- BAUE Bezug auf ("Heute scheint die Sonne..." oder "Die Bots haben sich ruhig verhalten")
```

### The Prompt Design (user prompt)

```
Heute ist {day_name}, der {date_str} um {time_str} Uhr.

Hier sind die aktuellen Daten als JSON:
{data_json}

Erstelle einen frischen, natürlichen Status-Bericht zum Vorlesen für Michel.
Variiere den Stil, die Reihenfolge und die Detailtiefe je nachdem was heute interessant ist.
```

### LLM Parameters

| Parameter | Value |
|-----------|-------|
| Model | `deepseek-v4-flash` |
| Temperature | 0.85 |
| Max tokens | 1500 |
| Timeout | 60s |

## Fallback: `_fallback_narrative()`

When LiteLLM is unreachable or returns errors, the script falls back to a simpler dynamic generator:

- Builds topic segments (Trading, Solar, Battery, Tesla, Jira, Weather, News)
- Shuffles topic order randomly
- Picks from multiple intro/outro variants
- Uses different phrasings per data state (high/low battery, good/poor solar)

This is still much better than the old fixed template because it at least varies structure.

## Future Improvements

- **Cross-call memory**: Pass previous call's narrative context so the LLM can say "letztes Mal war der Drawdown bei 9%, jetzt sind wir bei..." — user explicitly wants this ("Aufbau auf dem letzten Call")
- **Mood/personality toggle**: Let the user pick tone (chill, grumpy, excited, short)
- **News depth**: Currently only top 3 headlines. User might want longer summaries or specific categories.
- **Sound effect system**: User said "scheiße auf die Soundeffekte" — but might want subtle audio cues later (short beep between topics, not Portal-Gun whooshes)

## Testing

```bash
# Dry-run (no actual call)
python3 scripts/status-call.py --dry-run

# Only data (no narrative generation)
python3 scripts/status-call.py --only-data

# Real call
python3 scripts/status-call.py
```

The dry-run output shows exactly what the LLM produced — useful for iterating on the prompt without calling Michel.

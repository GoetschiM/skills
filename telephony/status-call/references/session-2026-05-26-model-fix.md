# Session 26.05.2026 — Modell-Fix und Call-Test

## Problem
`generate_narrative()` im `status-call.py` het Modell `deepseek-fast-1` agrüefe, aber de
LiteLLM-Key (sk-laAqdEE0C_vLWffTeRgB3Q) erlaubt nur `deepseek-v4-flash`.
→ HTTP 401: "key not allowed to access model"

## Fix
Modell-Name vo `deepseek-fast-1` uf `deepseek-v4-flash` gändered i dr POST-Request
vo `generate_narrative()`.

## Test
Dry-Run: ✅ Narrativ via Fallback (LLM het gfailed vor Fix)
Live Call: ✅ Call API (10.0.60.156:5002) het erfolgreich agrüefe
  - Voice: hermes → de-DE-ConradNeural
  - Dauer: ~1 Minute (495 Zeichen)
  - Asterisk: OK

## Live-Call-Output (26.05.2026 12:24)
```
Status: success
call_id: 20260526_122435
Anruf an: 0796459743
Prozessdauer: 5.4s
Narrativ: "Hallo Michel! Dienstag, 26. Mai 2026 - Zeit für dein Briefing.
           Die Solaranlage liefert 2475 Watt - eine Top-Produktion! ..."
```

## Data Summary (26.05.2026 12:24)
- Bot04 LIVE: Equity 15'408 EUR, Tag +16 EUR, 66 Positione, Winrate 44%
- Bot01 TEST: offline (ke Route zu 10.0.60.101)
- Solar: 2'475 W, Batterie 96%
- Wätter: klar, 26°C
- Tesla: nid am Lade
- Jira: 0 offeni/ghütig Tickets (GL-Projekt leer)
- News: Gleitschirmflieger-Unfall

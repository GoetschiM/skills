# Contact Display-Bug (gefixed 17.05.2026)

## Problem
`search contacts` im CLI (qdrant_knowledge.py) zeigt "?" statt Name.

## Ursache
De Search-Code used `payload.get("name")` — aber d'Contacts speichere unter `display_name`:
```python
# ALT (buggy)
name = payload.get("name") or payload.get("text", "?")

# NEU (fixed)
name = (payload.get("display_name") or payload.get("name") or
        f"{payload.get('first_name','')} {payload.get('last_name','')}".strip() or
        payload.get("text", "?"))
```

## Preview-Ausgabe (mit Names)
```
1. [0.65] Manuela Good
2. [0.49] Angelo
```

## Feld-Priorität (in search_contacts)
1. `display_name` — vollständige Name (Google-Kontakt)
2. `name` — Fallback für anderi Collections
3. `first_name + last_name` — für CSV-Import-Altdate
4. `text` — Memory-Fallback

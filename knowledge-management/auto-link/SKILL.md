---
name: auto-link
description: Automatisch Personen in Text/Kalender referenzieren und mit Qdrant-Kontakten verknüpfen
category: knowledge-management
tags:
  - qdrant
  - contacts
  - auto-link
  - personalization
---

# 🔗 Auto-Link: Personen-Referenzen automatisch verknüpfen

## Beschreibung
Auto-Link erkennt Personennamen in Kalender-Iiträg, Telegram-Nachrichten oder Konversationen und verknüpft sie automatisch mit bestehende Qdrant-Kontakten. So entsteht ein **vernetzter Wissensgraph**: später gsehsch sofort wenn öpper erwähnt wird, **wer** das isch und **welne Kontext** es scho geh het.

## Wie funktioniert's?
1. **Text analysiere** — Kalender-Iitrag oder Nachricht wird aaglueget
2. **Qdrant Contacts durchsueche** — Semantische Suche nach passende Personäname
3. **Kontext speichere** — Inhalt wird in Qdrant Memory gspeicheret, verknüpft mit Personäname
4. **Bei Zuekunftsfrage** — "Was isch mit Manuela passiert?" → "Motorrad zruggbringe am 17.05."

## Script
`/root/.hermes/scripts/auto-link.py`

### Usage
```bash
# Kalender-Ereignis
python3 auto-link.py --text "Motorrad zruggbringe mit Mutti Manuela" --source calendar

# Telegram-Konversation
python3 auto-link.py --text "Treffen mit Angelo um 14 Uhr" --source telegram

# Manuell
python3 auto-link.py --text "Hans Meier hüt am Namittag" --source manual
```

### Output
```json
{
  "text": "Motorrad zruggbringe mit Mutti Manuela",
  "source": "calendar",
  "contacts_found": ["Manuela Good"],
  "stored": true
}
```

## Integration
- **Google Calendar**: Nach `calendar create` wird `auto-link --source calendar` ufgruefe
- **Telegram**: Bei relevante Nachrichte wird `auto-link --source telegram` triggered

## Voraussetzig
- Qdrant Knowledge Manager v2.0+ (mit `goetschi_labs_contacts`)
- Qdrant API-Key in `/tmp/qdrant_api_key.txt`

## Pitfalls
- Mindestens 2 Wort-Kontakt für optimali Erkennig
- Kurzi Ein-Wort-Näme (z.B. "Franz") finded via Semantic Search
- Threshold 0.40 für Hauptsuche, 0.50 für Zweitsuche
- Memory wird immer gspeicheret, au wenn kei Person gfunge wird

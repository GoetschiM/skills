# Contact Phone/Email Lookup — Full Payload Retrieval

`qdrant_knowledge.py search contacts "Name"` zeigt NUR Namen (display_name/Score) — **keine Telefonnummern, E-Mails oder Notizen**.

## Warum

Der Suchscript erstellt Embeddings vom `embedding_text`-Feld und matched semantisch. Das Resultat enthält nur die `display_name` und `score` — restliche Payload-Felder (`phones`, `emails`, `notes`) werden nicht mit ausgegeben.

## Full Payload abrufen (RECOMMENDED)

Verwende die qdrant-client Python Library für vollständige Kontaktdetails:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="10.0.60.179", port=6333, timeout=30)

# ALLE Kontakte durchscrollen + Name-Filter
results = client.scroll(
    collection_name="goetschi_labs_contacts",
    limit=500,
    with_payload=True,
)

for point in results[0]:
    payload = point.payload
    name = payload.get("display_name", "UNKNOWN")
    
    if "suchbegriff" in name.lower():
        print(f"Name: {name}")
        phones = payload.get("phones", [])
        for p in phones:
            print(f"  Phone ({p.get('label','?')}): {p.get('value','')}")
        emails = payload.get("emails", [])
        for e in emails:
            print(f"  Email: {e.get('value','')}")
        print(f"  Labels: {payload.get('labels', '')}")
        print(f"  Notes: {payload.get('notes', '')}")
```

## Payload Schema

Siehe `references/contact-schema.md` für alle Felder.

Wichtigi Felder zum Nachschlage:
- `phones` — `[{"label": "Mobile|Work|Home", "value": "+41..."}]`
- `emails` — `[{"label": "* Andere|Work", "value": "..."}]`
- `display_name` — Vollständige Name
- `notes` — Freitext-Notizen
- `labels` — Google-Contact Labels

## Schnell-Check: "Git s'Telefon vo X?"

```python
client = QdrantClient(host="10.0.60.179", port=6333, timeout=15)
results = client.scroll("goetschi_labs_contacts", limit=500, with_payload=True)
for p in results[0]:
    payload = p.payload
    name = str(payload.get("display_name", "")).lower()
    if "suchbegriff" in name:
        phones = [f"{ph.get('value','')}" for ph in payload.get("phones", [])]
        print(f"{payload['display_name']}: {', '.join(phones)}")
```

# Qdrant Contact Schema — goetschi_labs_contacts

Die Contacts-Collection enthält 214 Points (Stand Mai 2026) mit folgendem Payload-Schema. Diese Felder wurden aus Google-Kontakten importiert und sind via Scroll-Endpoint abrufbar.

## Payload-Felder

| Feld | Typ | Beispiel | Beschreibung |
|------|-----|----------|-------------|
| `display_name` | string | "Manuela Good" | Vollständiger Anzeigename |
| `first_name` | string | "Manuela" | Vorname |
| `last_name` | string | "Good" | Nachname |
| `nickname` | string | "Mom" | Spitzname / Rufname |
| `relationship` | string | "family" | Beziehung zum User |
| `organization` | string | "" | Firma / Organisation |
| `job_title` | string | "" | Berufsbezeichnung |
| `department` | string | "" | Abteilung |
| `notes` | string | "" | Freitext-Notizen |
| `address` | string | "Küngoltstrasse, 4500 Solothurn, Schweiz" | Adresse |
| `birthday` | object | `{"month_day": "04-18"}` | Geburtstag (nur Monat+Tag) |
| `phones` | array | `[{"label": "Mobile", "value": "0787522893"}]` | Telefonnummern |
| `photo` | string | `https://lh3.googleusercontent.com/..."` | Profilbild-URL (Google) |
| `labels` | string | "ICE ::: Familie ::: * myContacts ::: * starred" | Google-Kontakt-Labels (::: getrennt) |
| `tags` | array | `["ICE", "Familie", "* starred"]` | Tags aus Labels gesplittet |
| `embedding_text` | string | "Manuela Good. Beziehung: Familie. Tags: ICE, Familie, * starred" | Embedding-Text |
| `type` | string | "person" | Kontakttyp |
| `source` | string | "google_contacts_csv" | Importquelle |
| `imported_at` | string | "2026-05-16T12:41:55.406824" | Import-Zeitstempel |

## API-Calls

### Scroll (alle Kontakte lesen)

```python
import requests
headers = {'api-key': 'KEY'}
url = 'http://10.0.60.121:6333'
resp = requests.post(f'{url}/collections/goetschi_labs_contacts/points/scroll',
    headers=headers,
    json={'limit': 500, 'with_payload': True, 'with_vector': False})
points = resp.json().get('result', {}).get('points', [])
```

### Count (Qdrant v1.13+)

```python
resp = requests.get(f'{url}/collections/goetschi_labs_contacts', headers=headers)
count = resp.json().get('result', {}).get('points_count', 0)  # NICHT vectors_count!
```

### Filter: Kontakte mit bestimmten Tags

```python
filter_cond = {"must": [{"key": "tags", "match": {"value": "Familie"}}]}
```

Bekannte Tags: `"ICE"`, `"Familie"`, `"* myContacts"`, `"* starred"`

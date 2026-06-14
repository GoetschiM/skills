# Family Contacts Schema — `contacts` Collection

Neben der Google-synchronisierten `goetschi_labs_contacts` Collection (siehe `contact-schema.md`) existiert eine separate **`contacts` Collection** für manuell angelegte Familien-Kontakte.

Diese Collection wird nicht aus Google importiert, sondern gezielt über Hermes/Qdrant-API befüllt.

## Übersicht

| Eigenschaft | Wert |
|-------------|------|
| Collection | `contacts` |
| Vector Dimension | 384 |
| Distance | Cosine |
| Host | `10.0.60.179:6333` |
| Aktuelle IDs | 10001–10009 |

## Payload-Schema (Family Person)

Anders als die Google-Import-Collection hat `contacts` kein festes CSV-Import-Schema. Jeder Eintrag wird manuell als JSON-Dokument mit folgender Struktur angelegt:

### Kernfelder

| Feld | Typ | Beispiel | Beschreibung |
|------|-----|----------|-------------|
| `type` | string | `"family_person"` | Fix auf `family_person` |
| `source` | string | `"hermes-agent"` | Erstellungsquelle |
| `display_name` | string | `"Conradin Götschi"` | Vollständiger Name |
| `last_name` | string | `"Götschi"` | Nachname |
| `relationship` | string | `"brother"` | Beziehung zum User |

### Kommunikation & Adresse

| Feld | Typ | Beispiel |
|------|-----|----------|
| `phones` | array | `[{"label": "Mobile", "value": "0789104964"}]` |
| `emails` | array | `[{"label": "Personal", "value": "koni.goetschi@gmail.com"}]` |
| `address` | string | `"Chrüzackerstrasse 1A, 4562 Biberist"` |

### Familie (Stammbaum-Verknüpfungen)

| Feld | Typ | Beispiel |
|------|-----|----------|
| `family.role` | string | `"brother"` |
| `family.spouse` | string | `"Karin Götschi"` |
| `family.children` | array | `["Leo Götschi"]` |
| `family.parents` | array | `["Doris Steinhauser", "Rolf Steinhauser"]` |
| `family.nickname` | string | `"Koni"` |
| `family.other_emails` | array | `["Conradin.Goetschi1@swisscom.com"]` |

## Liste der Kontakte (IDs 10001–10009)

| ID | Display Name | Rolle |
|----|-------------|-------|
| 10001 | Conradin "Koni" Götschi | Bruder (Bruder von Michel) |
| 10002 | Manuela Good | Mutter (Mam), G-O-O-D |
| 10003 | Ingrid Rowity | Tante / Gotti (Schwester von Manuela) |
| 10004 | Gido Good | Grossvater (Ne), Vater von Manuela + Ingrid |
| 10005 | Rosmarie Spiegel | Grossmutter (Nane), Frau von Gido |
| 10006 | David Rowity | Cousin (Sohn von Ingrid) |
| 10007 | Hadisa Rowity | Frau von David Rowity |
| 10008 | Fabrizio Liberio Rowity | Sohn von David + Hadisa |
| 10009 | Gino Rowity | Cousin (zweiter Sohn von Ingrid) |

## Spitznamen

| Alias | Person | Bedeutung |
|-------|--------|-----------|
| Koni | Conradin Götschi | Rufname |
| Mam | Manuela Good | Mutter |
| Ne | Gido Good | Grossvater väterlicherseits |
| Nane | Rosmarie Spiegel | Grossmutter väterlicherseits |
| Gotti | Ingrid Rowity | Patentante |

## API-Calls

### Neuen Kontakt erstellen (mit 384d Zero-Vector)

```python
import requests
Q = "http://10.0.60.179:6333"
v = [0.0] * 384  # Zero-vector für Manuell-Kontakte

payload = {
    "type": "family_person",
    "source": "hermes-agent",
    "display_name": "Neuer Kontakt",
    "last_name": "Name",
    "relationship": "family",
    "family": {
        "role": "cousin",
        "nickname": ""
    }
}

resp = requests.put(f"{Q}/collections/contacts/points", json={
    "points": [{"id": 10010, "vector": v, "payload": payload}]
})
```

### Alle Kontakte lesen

```python
resp = requests.post(f"{Q}/collections/contacts/points/scroll", json={
    "limit": 100, "with_payload": True, "with_vector": False
})
points = resp.json()["result"]["points"]
```

### Bestimmten Kontakt lesen

```bash
curl -s "http://10.0.60.179:6333/collections/contacts/points/10001"
```

### Kontakt updaten (Teil-Payload)

```python
resp = requests.put(f"{Q}/collections/contacts/points", json={
    "points": [{"id": 10001, "vector": v, "payload": {"display_name": "Neuer Name"}}]
})
```

## Unterschied zu goetschi_labs_contacts

| Aspekt | `goetschi_labs_contacts` | `contacts` |
|--------|--------------------------|------------|
| Quelle | Google Contacts Import (CSV) | Manuell via Hermes |
| Format | Google-People-API-Struktur | Custom Family-Schema |
| Embedding | FastEmbed (BAAI/bge-small-en-v1.5) | None (Zero-Vector) |
| Vektorsuche | ✅ Semantisch (384d Cosine) | ❌ Nur Payload-Filter |
| Felder | display_name, phones, emails, labels, tags, etc. | display_name, family.*, phones, emails |
| Anzahl | 214+ Points | 9 Points |
| Use Case | Adressbuch-Suche | Stammbaum / Familien-Struktur |

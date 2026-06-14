# Contact Merge Pattern — OSINT → Qdrant Contacts

## Problem
Wenn du OSINT-Date über en Person sammlisch oder de User dir Family-Kontakt-Infos git, existiert de Contact oft scho in Qdrant (z.B. via Google Contacts Sync). Under em falsche Name (Bsp: "Koni Götschi/Mobil" statt "Conradin Götschi").

## Solution
**NIE en neue Contact erstelle ohni vorher z'prüefe obs en scho git!**

### 1. Scroll Qdrant Contacts mit Name-Variante
```python
# Qdrant scroll — suech mit mehrere Name-Variante
- Vollständige Name: "Conradin Götschi"
- Kurzname: "Koni Götschi"
- Mit Zuesatz: "Koni Götschi/Mobil"
- Vorname-only: "Conradin"
- Ex-Partner: "Sternhauser"
```

### 2. Identität match
- **Email match** → same person
- **Phone match** → same person
- **Gravatar Hash match** → same person
- **Name similarity + address match** → same person

### 3. Merge statt replace
- Bestehende Payload (Phone, Email, Birthday) behalte — das sind verifizierti Date us Google Contacts
- Neui OSINT-Date (Adresse, LinkedIn, YouTube, Devpost, Family-Beziehige) dezuefüege
- Dedupliziere: gleichi Emails/Phones nöd dopplet speichere

### 4. Name-Update
- `name` Feld uf de vollständig name setze
- `notes` oder `payload` mit Aliase ergänze (z.B. "Auch bekannt als: Koni")

## Python Pseudocode
```python
def merge_contact(new_data, existing_contacts):
    """Merge new OSINT data with existing Qdrant contacts."""
    for ec in existing_contacts:
        # Email match
        if new_data.get('email') and ec['payload'].get('email') == new_data['email']:
            return _merge(existing=ec, new=new_data)
        # Phone match
        if new_data.get('phone') and ec['payload'].get('phone') == new_data['phone']:
            return _merge(existing=ec, new=new_data)
        # Name similarity
        if _name_similar(new_data.get('name', ''), ec['payload'].get('name', '')):
            return _merge(existing=ec, new=new_data)
    # No match → create new
    return _create(new_data)

def _merge(existing, new):
    """Merge payloads, existing wins for conflicting fields."""
    merged = dict(existing['payload'])
    for key, val in new.items():
        if key not in merged or not merged[key]:
            merged[key] = val
    return merged
```

## Real-World Example (24.05.2026)
- **Name:** Conradin "Koni" Götschi
- **In Qdrant under:** "Koni Götschi/Mobil" (Google Contacts Sync)
- **Neui OSINT-Date:** Adrüss (Chrüzackerstrasse 1A, 4562 Biberist), LinkedIn, YouTube, Devpost, Ex-Frau Karin, Sohn Leo
- **Merge:** Behalt Mobil + Email + Birthday us Qdrant, füeg Adrüss + Social Media + Family dezue

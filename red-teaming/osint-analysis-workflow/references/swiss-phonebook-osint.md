# Swiss Phonebook OSINT — Search.ch & ZIP.ch

## Use Case
Schwiizer Privatpersone finde, wo kei Social-Media-Präsenz hend oder wo d'Username nöd bekannt sind.

## Verfügbari Quelle

### 1. search.ch (Swisscom Directories)
- Grössts Schwiizer Telefonbuch
- URL: `https://search.ch/tel/`
- Privat-Personen-Einträg under `Götschi, Conradin und Karin - search.ch`
- Datasource: SwisscomDirectories
- API isch nöd öffentlich, aber Detail-Links sind direkt ufruefbar

**Patterns:**
```
# Suche über Name + Stadt
https://search.ch/tel/?name=Götschi&firstname=Conradin&city=Obergerlafingen

# Detail-Entry wenn Adrässe bekannt
https://search.ch/tel/<ort>/<strasse>-<nummer>/<vorname>-und-<name>

# Bsp: Obergerlafingen/Hauptstrasse-105/conradin-und-karin-goetschi
```

**Limitatione:** 
- Telefonnummer wird meistens nöd im HTML azeigt (nume 058-Business-Nummere)
- Privati Nummere sind nur über vCard oder ZIP.ch verfüegbar
- Data-Layer im HTML enthält: `EntryType`, `DetailEntryCity`, `OnlineEntryID`

### 2. ZIP.ch (Alternative zu search.ch)
- Besser für privati Festnetz-Nummere
- Enthält strukturierti Date im Google Tag Manager Data-Layer
- Auch Telefonnummer im Klartext

**Patterns:**
```
# Detail-Link
https://zip.ch/<lang>/gotschi-<vorname>-<strasse>-<ort>-<id>/

# Bsp: https://zip.ch/en/gotschi-conradin-chruzackerstrasse-biberist-vDOZ3p2dEm/
```

**Data-Layer extrahiere:**
```bash
curl -s "https://zip.ch/en/gotschi-..." | grep -oP 'entryStreet|entryNumber|entryCity|entryPostcode|entryRegion'
```

### 3. local.ch (Gschäfts-Nummere)
- Fokus uf Firme, aber au Privat-Persone
- Teil vo de Swisscom Directories Familie

## Swiss-spezifischi Namensvariatione

Schwiizer Telefonbüecher verwende oft phonetischi Schriibwiise:

| Richtige Name | Im Buech | Grund |
|---------------|----------|-------|
| Sternhauser | Steinhauser | Phonetisch ähnlich, Schribfäler i de Datebank |
| Götschi | Goetschi | oe = ö (ASCII-Fallback) |
| Müller | Mueller | ASCII-Normalisierig |
| Michel | Michel (glych) | Seltener variiert |

**Daher:** Immer mindestens 3 Variationene probiere:
1. Richtigi Schriibwiis (Sternhauser)
2. Phonetischi Variante (Steinhauser)  
3. ASCII-Fallback (oe statt ö)

## Privati vs Business-Nummere

| Präfix | Typ | Quelle |
|--------|-----|--------|
| 032 xxx xx xx | Festnetz (Region Solothurn/Bern) | ZIP.ch |
| 058 xxx xx xx | Business/Service-Nummer | search.ch |
| 079/076/078 | Mobile | Selte in Telefonbüecher |

## Typischi Use Cases

1. **Bruder/Schwester finde** — Familienaame + glyche Wohnort = Treffer
2. **Ehemaligi Partner** — Oft under glycher Adrässe no listed solang nöd uszüglet
3. **Chinds-Versorgig/Spielgruppe** — Adrässe vo Familie mit Chind
4. **Gschäftspartner** — Privatadrässe vo Inhaber/CEO finde

## Code-Beispiel: Person i mehrene Direktorien sueche

```python
import requests, re

def search_swiss_phonebook(firstname, lastname, city=None):
    results = {}
    
    # search.ch
    url = f"https://search.ch/tel/?name={lastname}&firstname={firstname}"
    if city:
        url += f"&city={city}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    results['search.ch'] = {
        'status': r.status_code,
        'found': firstname.lower() in r.text.lower() and lastname.lower() in r.text.lower(),
        'title': re.search(r'<title>(.*?)</title>', r.text, re.DOTALL)
    }
    
    return results
```

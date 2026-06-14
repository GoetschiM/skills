---
name: qdrant-knowledge
description: "Qdrant Knowledge Manager v2.0 — Semantische Kontakt- & Wissenssuche + Document-RAG (PDF → Qdrant + Minio)"
version: 2.0.0
category: knowledge-management
tags: [qdrant, vector-search, rag, document-processing, minio, knowledge-base, semantic-search]
related_skills:
  - paperless
prerequisites:
  python: "3.9+"
  pip:
    - fastembed
    - qdrant-client==1.13.3
    - minio
    - pymupdf
  env_vars:
    - QDRANT_HOST
    - QDRANT_PORT
    - QDRANT_API_KEY
    - MINIO_ENDPOINT
    - MINIO_ACCESS_KEY
    - MINIO_SECRET_KEY
---

# Qdrant Knowledge Manager v2.0 — Document RAG 🧠📄

Semantische Vektorsuche für **Kontakte**, **Wissen** und **Dokumente** (PDFs) – 
mit Original-Datei-Ablage in **Minio** für spätere Weiterverarbeitung (Paperless, Telegram, Mail, etc.).

## ♟️ Dual Memory Architecture (Hermes' Zweitgedächtnis)

Hermes hat zwei Gedächtnis-Ebenen — für optimale Performance ohne Informationsverlust:

| Ebene | Typ | Kapazität | Geschwindigkeit | Persistenz | Zweck |
|-------|-----|-----------|----------------|------------|-------|
| **Memory** (MEMORY.md) | Local KV | < 80% (~1.760 chars) | ⚡ Sofort | Session-übergreifend | Kurzfristige Fakten: Credentials, User-Preferences, Job-IDs, DB-Keys |
| **Qdrant** (goetschi_labs_memory) | Vector DB | Unbegrenzt (386+ Vektoren) | 🔄 1-2s Retrieval | Permanent | Tiefes Wissen: Erkenntnisse, Konfigurationen, Workflow-Beschreibungen, Kontext |

### MFG — Immer Qdrant + Memory zäme (User-Vorgabe 26.05., streng)

**FÜR HERMES & NOVA:** Jedes Mal wenn Memory glade oder gspeichere wird, MUSS Qdrant synchron devo greage werde.

#### Lesen (vor jeder Antwort)
1. Memory wird automatisch glade (System)
2. **Zuesätzlich:** Qdrant `goetschi_labs_memory` dursuche noch relevantem Kontext
3. Ersch dänn antworte

#### Schriibe (nach jedem Memory-Save)
1. Memory-Eintrag mache
2. **Gliche Inhalt via Qdrant REST API** i `goetschi_labs_memory` speichere
3. Payload: id (UUID), vector ([0.001]*384), payload: {topic, content, source, type, stored_at}

**Warum:** Hermes und Nova teiled Qdrant-Collections. Was nume im Memory isch, gseht de ander nid. Was i Qdrant isch, gsehn alli.

### Memory < 80% Regel (KRITISCH — User-Vorgabe)

Memory darf NIE über 80% (ca. 1.760 Chars) gehen. Bei Kapazitätsproblemen:
1. **Komprimieren**: Lange Einträge straffen (Cronjobs als Einzeiler, Properties abkürzen)
2. **Auslagern**: Entfernte Details gehören in Qdrant — nicht ins Memory
3. **Referenzieren**: Statt voller Credentials im Memory → "siehe Skill X/references/Y.md"
4. **Pruning**: Wenn ein Memory-Eintrag älter als 30 Tage ist und nicht mehr referenziert wird → löschen (Inhalt vorher in Qdrant sichern)

### Session-End Knowledge Push (Pflicht)

Am ENDE JEDER Sitzung (bevor Hermes "tschüss" sagt oder der User ein neues Thema aufmacht):

1. **Scan Memory**: Welche neuen Fakten/Erkenntnisse kamen in dieser Session?
2. **Search Qdrant** first: Prüfe ob das Wissen schon existiert (Vermeide Duplikate)
3. **Store in Qdrant**: `python3 qdrant_knowledge.py store "Eingängiger Titel: Zusammenfassung..." --type note --source system`
4. **Prune Memory**: Falls Memory über 80%, komprimiere/verschiebe alte Einträge

Typen die für Session-Wissen sinnvoll sind:
- `note` — Kurze Erkenntnisse, Learnings
- `procedure` — Workflows, Abläufe (z.B. Cronjob-Struktur)
- `reference` — Konfigurationen, API-Details
- `config` — System-Einstellungen, Gateway-Config

### Regelmässige Qdrant Reads (genauso wichtig wie Writes)

Vor jeder grösseren Aktion (Debugging, Neueinrichtung, Planung):
1. `python3 script search memory "Suchbegriff"` — finde relevantes Vorwissen
2. Lies Qdrant-Einträge BEVOR du neu entwickelst — vermeidet Redundanz
3. Nutze Qdrant als "institutional memory" für Entscheidungen die du vor Wochen getroffen hast

**Faustregel:** Wenn du das Gefühl hast "das hatten wir doch schon mal" → Qdrant search zuerst, Memory second.

### Memory → Qdrant Sync Cron

Ein täglicher Cron (`cc603ef059ee`, täglich 07:00 CH) liest das aktuelle Memory und speichert neue/geänderte Erkenntnisse dedupliziert in Qdrant:

```
Schedule: 0 5 * * * (07:00 CH)
Skills: knowledge-management/qdrant-knowledge
Deliver: local (nur Log)
```

Damit ist sichergestellt dass kein Wissen verloren geht — auch wenn Memory-Einträge komprimiert oder gelöscht werden.

## 🌐 Architektur

```
Telegram 📎 ──┐
Mails 📧 ─────┤
PDFs 📄 ──────┤──> Text-Extraktion ─> Chunking ─> Embedding ─> Qdrant Memory
Uploads 📁 ───┘                         │                           │
                                         └──> Minio documents/ ─────┘
                                               ├── rechnungen/
                                               ├── vertraege/
                                               ├── handbuecher/
                                               ├── korrespondenz/
                                               └── sonstiges/
                                               
→ Jeder Agent kann via `search memory` oder `get doc <id>` Dokumente finden & abrufen
→ Original-Datei liegt zentral in Minio für Paperless, Telegram-Versand, Mail-Anhang
```

## Goetschi Labs Feature Workflow

Wenn du ein neues Feature implementiersch — egal ob Skill, Backup-Script, Calendar-Integration oder Asterisk-Config — **immer in dieser Reihenfolge**:

### Schritt 1: ⚙️ Implementieren
Machs laufe. Testing inklusive. Nöd dokumentiere, nöd abspeichere, sondern **zersch funktionierts**.

### Schritt 2: 📝 Dokumentieren — 4-fach-Doku
- **Confluence** (Wiki) — Feature-Seite erstelle mit allne Settings, Parameter, Use Cases
- **Notion** (Knowledge Base) — Gleichi Info, für schnelle Agenten-Zuegriff
- **Obsidian** (Vault) — Note in `3-Infrastruktur/` oder passendem Ordner ablege mit Wikilinks zu verwandte System
- **Qdrant** (goetschi_labs_memory) — Siehe Schritt 3 unten

### Schritt 3: 🧠 Qdrant Memory speichere
```bash
cd /root/.hermes/skills/knowledge-management/qdrant-knowledge
python3 scripts/qdrant_knowledge.py store "Dein Feature-Kontext" --type documentation --source system
```
Damit alli Agenten (Hermes, Nova, Apollo) über's Schwarmwisse drauf zugriffe chönd.

### Schritt 4: 📦 Skill/MiniO
- Skill erstelle/update (`skill_manage`)
- Skill auf **MinIO hochlade** (`/data/swarm-skills/<category>/<name>/`)
- Scripts und Referenzen mitneh

### Schritt 5: 🎫 Jira-Ticket
- **TEAM-Ticket** erstelle/update (damit alli Agenten im Schwarm Bescheid wend)
- Ticket kommentiere: Status, Dateipfad, Confluence/Notion-Links

### Warum?
- **Alles für alli zugänglich** — kein Wissen geht verlore
- **Jeder Agent chan nahtlos witerarbeite** — Nova oder Apollo gsehn genau was gmacht worde isch
- **Konsequente Doku** — am Schluss isch alles i Qdrant, Confluence, Obsidian, Notion + MinIO

### Pitfalls
- **NIE Schritt 5 vor Schritt 1** — Ticket erstelle ohne Implementation isch nutzlos
- **NIE Schritt 3 vergässe** — Qdrant isch de zentrali Schwarm-Speicher. Fehlts, wend anderi Agenten nüt devo
- **Alli 5 Schritt zwingend** — au "chliini" Features. D'Chronologie isch wichtig

## Installation

### 1. Hermes-Skill laden (empfohlen)
```bash
# In Hermes-Session:
skill_view(name='knowledge-management/qdrant-knowledge')

# Oder falls Hermes-Skill-System:
hermes skill install knowledge-management/qdrant-knowledge
```

### 2. Direkt von Minio (für andere Agenten ohne Hermes)
```bash
# In ein Verzeichnis Deiner Wahl:
SKILL_DIR="./qdrant-knowledge"
mkdir -p $SKILL_DIR/scripts
curl -o $SKILL_DIR/SKILL.md \
  http://10.0.60.106:9000/swarm-skills/knowledge-management/qdrant-knowledge/SKILL.md
curl -o $SKILL_DIR/scripts/qdrant_knowledge.py \
  http://10.0.60.106:9000/swarm-skills/knowledge-management/qdrant-knowledge/scripts/qdrant_knowledge.py
chmod +x $SKILL_DIR/scripts/qdrant_knowledge.py
```

### 3. Abhängigkeiten installieren
```bash
pip install fastembed qdrant-client==1.13.3 minio pymupdf
```
### 4. Umgebungsvariablen setzen

```bash
# Qdrant (Pflicht)
export QDRANT_HOST=10.0.60.179
export QDRANT_PORT=6333
export QDRANT_API_KEY=""   # Lokaler LXC — kein API-Key nötig

# Minio (für Document-RAG, optional für reine Text-Suche)
export MINIO_ENDPOINT=10.0.60.106:9000
export MINIO_ACCESS_KEY=admin
export MINIO_SECRET_KEY=Louis_one_13
```

> **Hinweis (seit 23.05.):** Qdrant läuft als eigener LXC (10.0.60.179) uf pve01, MinIO als LXC (10.0.60.106). Beide Services sind bare-metal, kein Docker mehr. Qdrant hat keinen API-Key (lokal).

## 📋 CLI-Befehle

### 🔍 Suchen

```bash
# Kontakte semantisch suchen
python3 qdrant_knowledge.py search contacts "Klempner in Solothurn"

# ⚠️ search contacts zeigt NUR Namen (kein Telefon/Email).
# Für vollständigi Payload-Date (Phone, Email, Notizen):
# Siehe references/contact-phone-lookup.md

# Wissen semantisch suchen
python3 qdrant_knowledge.py search memory "Docker-Infrastruktur"
python3 qdrant_knowledge.py search memory "Rechnung Qdrant"
```

### 💾 Wissen speichern

```bash
# Text-Wissen speichern
python3 qdrant_knowledge.py store "Neuer Wissenseintrag..." --type guide --source system

# Typen: guide, documentation, config, procedure, reference, faq, note
# Quellen: system, manual, telegram, mail, file
```

### 📄 Dokument (PDF) verarbeiten

```bash
# PDF verarbeiten → Text extrahieren → Chunking → Embedding → Qdrant + Minio
python3 qdrant_knowledge.py store file /pfad/zum/dokument.pdf --category rechnungen

# Verfügbare Kategorien: rechnungen, vertraege, handbuecher, korrespondenz, sonstiges
```

### 📂 Dokumente verwalten

```bash
# Alle gespeicherten Dokumente auflisten
python3 qdrant_knowledge.py list documents

# Original-Dokument aus Minio herunterladen
python3 qdrant_knowledge.py get doc <doc_group_id>        # → /tmp/qdrant_retrieved/<filename>
```

### ℹ️ System-Info

```bash
# Collections-Status und Systemübersicht
python3 qdrant_knowledge.py info

# Minio documents/ Bucket einrichten (einmalig)
python3 qdrant_knowledge.py setup minio
```

## 🏗️ Collections

| Collection | Punkte | Dimension | Distance | Beschreibung |
|---|---|---|---|---|
| `goetschi_labs_contacts` | 215 | 384 | Cosine | Semantische Kontaktsuche (Google-Kontakte) |
| `goetschi_labs_memory` | 386+ | 384 | Cosine | Wissensdatenbank + Dokument-Chunks (inkl. Paperless + Memory-Sync) |

## 📦 Minio-Struktur

```
minio://documents/
├── rechnungen/            ← Rechnungen, Zahlungsbelege
│   └── YYYY-MM/           ← Monats-Ordner
├── vertraege/             ← Verträge, Agreements
├── handbuecher/           ← Anleitungen, Manuals
├── korrespondenz/         ← Briefe, Mails
└── sonstiges/             ← Rest

minio://swarm-skills/
└── knowledge-management/
    └── qdrant-knowledge/  ← Dieser Skill
```

## 🔄 Automatisierte Paperless-Pipeline

Paperless-Dokument werde automatisch via Cronjob `paperless-pipeline` (täglich 03:00) in Qdrant + MinIO indexiert:

```
Paperless API → download PDF → MinIO upload → qdrant_knowledge.py store
```

Jedes Dokument bechunnt type=document, source=paperless und isch mit em MinIO-Pfad verlinkt.
Agents chönd via `search memory "Papeless Dokumenttitel"` druf zuegriefe.

**Siehe au:** `knowledge-management/paperless/references/pipeline-workflow.md`

## 🔄 Workflow für Agenten

### Dokument empfangen & verarbeiten
1. Datei erhalten (Telegram / Mail / Upload)
2. `store file <path> --category <typ>` aufrufen
3. → Text in Qdrant (semantisch durchsuchbar)
4. → Original in Minio (für Retrieval)

### Dokument suchen & senden
1. `search memory "Suchbegriff"` → findet passende Chunks mit `source_path`
2. `get doc <doc_group_id>` → lädt Original aus Minio
3. Datei per Telegram/Mail versenden

## 🧪 Beispiel-Session

```bash
# 1. Status checken
python3 qdrant_knowledge.py info

# 2. PDF verarbeiten
python3 qdrant_knowledge.py store file /tmp/rechnung.pdf --category rechnungen

# 3. Suchen
python3 qdrant_knowledge.py search memory "Elektrizitätsrechnung"

# 4. Gefundenes Dokument abrufen
python3 qdrant_knowledge.py get doc a1b2c3d4-e5f6-...

# 5. Datei an User senden
# → Datei liegt unter /tmp/qdrant_retrieved/rechnung.pdf
```

## ⚙️ Konfiguration (Umgebungsvariablen)

| Variable | Standard | Beschreibung |
|---|---|---|
| `QDRANT_HOST` | `10.0.60.179` | Qdrant-Server LXC |
| `QDRANT_PORT` | `6333` | Qdrant-REST-Port |
| `QDRANT_API_KEY` | `""` | Qdrant-API-Key (lokal LXC = kein Key) |
| `MINIO_ENDPOINT` | `10.0.60.106:9000` | Minio-LXC-Endpoint |
| `MINIO_ACCESS_KEY` | Aus `.env`-File | Minio-User (admin) |
| `MINIO_SECRET_KEY` | Aus `.env`-File | Minio-Passwort (Louis_one_13) |
| `DOCUMENTS_BUCKET` | `documents` | Minio-Bucket für Dateien |

## 📧 Gmail-Integration

PDF-Anhänge aus Gmail automatisch extrahieren, in Qdrant + Minio verarbeiten:

```bash
# Installation (einmalig)
pip install google-api-python-client google-auth-oauthlib

# Gmail-Token muss existieren unter /root/.hermes/google_token.json
# oder symlink: ln -sf /opt/data/home/.hermes/google_token.json /root/.hermes/

# Gmail-PDFs verarbeiten
cd scripts/
export QDRANT_API_KEY="..."
python3 gmail_to_qdrant.py <gmail_message_id> [category]
```

**Google OAuth-Setup:** Siehe `productivity/google-workspace` Skill.

> **Tipp:** Gmail-Nachrichten mit PDF-Anhang finden via:
> `python3 /path/to/google_api.py gmail search "has:attachment filename:pdf newer_than:30d"`

### 📂 Referenzen

| Datei | Inhalt |
|-------|--------|
| `references/contact-merge-pattern.md` | OSINT-Date mit existierende Qdrant Contacts merge (statt neue erstelle) |
| `references/contact-schema.md` | Goetschi Labs Contact Payload Schema — alle Felder, API-Calls, Filter |
| `references/qdrant-api-pitfalls.md` | Qdrant API-Versionsunterschiede, Timeout, API-Key-Handling |
| `references/minio-docker-upload.md` | Workaround wenn S3-API AccessDenied gibt |
| `references/gmail-integration.md` | Gmail-Document-RAG Pipeline: Token, Batch, API-Besonderheiten, Cronjob |
| `scripts/gmail_to_qdrant.py` | Gmail-PDFs → Qdrant + Minio Pipeline |
| `references/family-contacts-schema.md` | Family-Stammbaum: `contacts` Collection (IDs 10001-10009), Payload-Schema, API-Calls, Spitznamen |
| `references/contact-phone-lookup.md` | Contact Phone/Email Full Payload Retrieval — Hol dir Telefonnummern + E-Mails via qdrant-client API |
| `references/project-search-workflow.md` | Multi-Source Project/Person Search — Reihenfolge + Verhalten für Qdrant/Confluence/Notion/Jira/Obsidian/Drive |

## 📞 Contact Sourcing Protocol — Duplicate Prevention

**User-Regel:** Bevor du en Kontakt speichersch (Qdrant, Obsidian, Google, Notion), immer zersch **Google Kontakte** und **Notion** prüefe, ob de Kontakt scho existiert!

### Prio (höchsti zersch)
1. **Google Kontakte** — primärs Adressbuch, isch autoritativ
2. **Notion** — `Kontakte / Adressbuch` Page under Teamspace
3. **Qdrant** — `goetschi_labs_contacts` Collection
4. **Obsidian** — `2-Kontakte/` Notes

### Pitfalls
- **Voice-Input Name Corrections:** Nach Voice-Input (Telegram-Sprachnochricht) chönd Name verballhornt werde (Bsp: "Geno" → "Gino", "God" → "Good"). Immer NAME vom User nomol bestätige lah bevor en Kontakt gspicheret wird!
- **Google Contacts Write Scope:** De Google OAuth Token bruucht `contacts.readonly` für Lese-Zugriff. Für Schriibe muess de Scope uf `contacts` (write) erwiiteret werde via `$GSETUP --revoke` + Neuauth (siehe `productivity/google-workspace` Skill)
- **NIE blind mergen — User fragen:** Bi Konflikt (Name/Telefon/Email nöd eindeutig) immer de User entscheide lah. Siehe `references/contact-merge-pattern.md` für dedizierti Merge-Logik.

## 🔗 Verwandte Systeme

- **Jira:** GL-39 (Kontakt-Datenbank), GL-36 (Schwarmwissen), GL-30 (Integrationen)
- **Confluence:** [Qdrant Knowledge Manager](https://goetschi.atlassian.net/wiki/spaces/~5a75b5612d61371e861f4dae/pages/30310401/Qdrant+Knowledge+Manager+Semantische+Kontakt-+Wissenssuche)
- **Notion:** Knowlage Base → 🧠 Qdrant Knowledge Manager
- **Minio:** `swarm-skills/knowledge-management/qdrant-knowledge/`
- **Minio Docker-Upload:** Siehe `references/minio-docker-upload.md` — Workaround für S3-AccessDenied

## 🚧 Roadmap

- [x] Semantische Kontaktsuche
- [x] Semantische Wissenssuche
- [x] Wissen speichern (CLI)
- [x] Document-RAG (PDF → Qdrant + Minio)
- [x] Minio-Dokumenten-Ablage (strukturiert nach Kategorien)
- [x] Dokument-Retrieval (Original aus Minio laden)
- [x] Automatisches Wissen-Speichern aus Mails (Gmail-PDF-Pipeline)
- [x] **Auto-Linking (TEAM-14):** Kalender-/Konversations-Erwähnige von Personen → mit Qdrant-Kontakt verknüpfe + Kontext speichere (`auto-link.py`)
- [ ] Telegram-Commands `/kontakt` und `/wissen`
- [x] 📄 **Paperless-Integration (TEAM-25):** Paperless-Dokumente → Qdrant semantisch durchsuchbar + MinIO zentrali Ablage. Cronjob `paperless-pipeline` täglich um 03:00 syncet Paperless-API-Daten nach MinIO + Qdrant.
- [x] 🧠 **Memory→Qdrant Sync Cron (22.05.):** Täglicher Cron (07:00 CH) liest Memory und speichert dedupliziert in Qdrant goetschi_labs_memory. Hermes' sekundäres Gedächtnis.
- [x] ♟️ **Dual Memory Architecture (22.05.):** Memory < 80% Regel + Session-End Knowledge Push + regelmässige Qdrant Reads. Workflow im Skill dokumentiert.
- [ ] Auto-Klassifizierung von Dokumenten

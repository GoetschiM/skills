# Paperless-ngx Architektur (18.05.2026)

## Vorbemerkung: S3-Backend

Paperless-ngx **v2.20.15 unterstützt KEIN natives S3-Backend** trotz vorhandener Env-Vars.
Die Umgebungsvariablen `PAPERLESS_STORAGE_BACKEND=s3`, `PAPERLESS_S3_*` werden zwar an den
Container übergeben, aber von der Applikation **NICHT ausgewertet** (die STORAGES-Django-Konfig
bleibt auf `FileSystemStorage`). Installierte Pakete checken: `boto3`, `django-storages` fehlen
typischerweise.

Daher: **Hybride Architektur** — Paperless speichert lokal, MinIO + Qdrant sind separate Layer.

## Aktuelle Architektur (18.05.2026)

```
               Dokument (Mail/Telegram/Upload/API)
                        │
                        ▼
         ┌──────────────────────────────┐
         │      Paperless-ngx           │
         │  10.0.60.121:8015 (Dokploy)  │
         │  ┌────────────────────────┐  │
         │  │ Local Storage          │  │
         │  │ /srv/paperless/media/  │  │
         │  │   documents/originals/ │  │
         │  │   documents/archive/   │  │
         │  │   documents/thumbnails/│  │
         │  └────────────────────────┘  │
         └──────────┬───────────────────┘
                    │ Paperless REST API
                    │ (http://localhost:8015/api/)
                    ▼
         ┌─────────────────────────────────────┐
         │        Paperless Pipeline            │
         │    (Cronjob: 0 */6 * * *)            │
         │    skills: paperless, qdrant-knowledge│
         │                                       │
         │  1. curl API → list docs + metadaten  │
         │  2. download PDF + metadata JSON       │
         │  3. upload to MinIO → documents/      │
         │  4. qdrant_knowledge.py store          │
         └──────┬──────────────────────┬─────────┘
                │                     │
                ▼                     ▼
    ┌──────────────────┐   ┌──────────────────┐
    │     MinIO S3      │   │  Qdrant Vektor-   │
    │ 10.0.60.121:9000  │   │  DB 10.0.60.121   │
    │                   │   │  :6333             │
    │ Buckets:          │   │                   │
    │  documents/       │   │ goetschi_labs_    │
    │    paperless/     │   │ memory (64+ pts)  │
    │  paperless/       │   │  - source: paper- │
    │  swarm-skills/    │   │    less           │
    └──────────────────┘   │  - type: document  │
                           └──────────────────┘
```

## Zwei Instanzen

| Instanz | URL | Status | Credentials | Nutzung |
|---------|-----|--------|-------------|---------|
| **LXC (Original)** | `10.0.40.30:8000` | ✅ läuft, API erreichbar | ❌ unbekannt — Michel muss API-Token generiere | Produktiv (Ziel) |
| **Dokploy (Hermes)** | `10.0.60.121:8015` | ✅ läuft, sync cron aktiv | ✅ `paperless-admin` / env-File | Fallback + Pipeline |

## Pipeline-Konfiguration

### Cronjob (Hermes)
- Name: `paperless-pipeline`
- Schedule: `0 */6 * * *` (alli 6 Stund)
- Skills: `paperless`, `qdrant-knowledge`
- Action: Paperless API abfroge → neu! Dokument download → MinIO upload → Qdrant vectorize

### MinIO-Struktur
```
documents/paperless/
├── <id>-<title_safe>.pdf           # Original-PDF
└── <id>-<title_safe>.meta.json     # Paperless-Metadaten
```

### Qdrant-Struktur
- Collection: `goetschi_labs_memory`
- Type: `document`
- Source: `paperless`
- Text: Paperless Title + Content + MinIO-Path

## Credentials

### Paperless (Dokploy)
- Admin: `paperless-admin` / `E8UfVSsHtReHQUmwtKLlbk3y`
- API-Token: über Token-Endpoint abrufbar
- Env-File: `/root/.hermes/paperless.env`

### MinIO
- URL: `10.0.60.121:9000`
- Access: `minioadmin` / `pzu40uohwq4xlvic`
- Buckets: `documents/`, `paperless/`, `swarm-skills/`

### Qdrant
- URL: `10.0.60.121:6333`
- API Key: `zhoetb44jxvowh41gzo7qhlbvuyqtef2`
- Collections: `goetschi_labs_memory`, `goetschi_labs_contacts`

## Wie d'Agents Dokument finde

1. **Qdrant-Suche**: `python3 qdrant_knowledge.py search memory "Suchbegriff"`
   → findet Paperless-Dokument mit Score + MinIO-Pfad

2. **MinIO-Download**: PDF us documents/paperless/ abhole über
   - mc CLI (uf Dokploy-Host)
   - S3-API (überall wo boto3/minio lib installiert isch)

3. **Paperless-Direkt**: REST API für Volltextsuche / Upload / Tag-Verwaltig

## Verwandti Pipeline-Cronjobs

| Cronjob | Schedule | Beschrieb |
|---------|----------|-----------|
| `paperless-pipeline` | 0 */6 * * * | Paperless → MinIO + Qdrant |
| Hermes MinIO Backup | 0 3 * * * | Hermes-Konfig nach MinIO |
| Schwarm Skill-Sync | 0 2 * * * | Skills via MinIO sync |

## Verwandti Tickets

- **GL-29:** Paperless-ngx API-Anbindung — ✅ abgschlosse
- **TEAM-19:** Paperless uf 10.0.40.30 — Produktiv-Setup
- **TEAM-25:** Paperless + MinIO — Zentrale Doku-Ablage für alli Agenten

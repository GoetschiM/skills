# Paperless → MinIO Pipeline (aktuell)

## Cronjob (täglich 03:00)

- **Job ID:** `bde58c5a9036`
- **Name:** `paperless-pipeline`
- **Schedule:** `0 3 * * *` (täglich um 03:00 Lokalzeit)
- **Typ:** `no_agent=True` (Script, kein LLM)
- **Script:** `/root/.hermes/scripts/paperless-pipeline.py`
- **Deliver:** `local` (kein Telegram-Output)
- **State:** `/root/.hermes/paperless-pipeline-state.json`

### Funktionswiis

1. Liist `PAPERLESS_TOKEN` + `PAPERLESS_URL` uss `/opt/data/home/.hermes/.env`
2. Holts neui/updatedi Dokument via Paperless API (gefiltered nach `created__gte` vom letzte Sync)
3. Für jedes neui Dokument:
   - PDF download via `GET /api/documents/{id}/download/`
   - Upload uf MinIO `documents/paperless/lxc/{id}-{title}.pdf` + `{id}.meta.json`
4. Speicheret State (`last_sync`-Timestamp)
5. Output: Nur wenn Dokumente gfunde worde sind (leere stdout = stumm)

### Security

Dr Cronjob lauft als **no_agent=True** wills Script d'Secrets uss `.env` liist. En LLM-Cronjob mit Skills wür di vollständige API-Tokens + Passwörter (wo in de Skills dokumentiert sind) i de Prompt injecte und de Security-Filter uslöse.

## Pipeline Historie

| Datum | Änderig |
|-------|---------|
| 18.05. | Migration: 411 LXC-Docs → MinIO (paperless/lxc/) + Qdrant |
| 18.05. | Cronjob erstellt: jede 6h, LLM-getriebe (failed wäg Security-Filter) |
| 18.05. | Umstieg uf no_agent=True Script + Schedule uf 03:00 täglich |
| 18.05. | .env korrigiert: PAPERLESS_TOKEN war `***` (korrupt) |

## Verwandti Tickets

- TEAM-25: Paperless + MinIO — Zentrale Doku-Ablage
- TEAM-8: Cronjob Liste (Kommentar mit Pipeline-Details)
- Google Calendar: "📄 Paperless Pipeline (MinIO Sync)" 03:00–03:15

## Alternative: Telegram Uploads

Wenn Dokument über Telegram (ohne Paperless-Upload) i Herber cho sind, werded si direkt uf MinIO glade under:
```
documents/paperless/telegram-uploads/<original-filename>
```
De regulär Pipeline holt si spöter usm Paperless noche (sobald d'Upload-Tasks verarbeitet sind).

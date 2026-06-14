# .env Setup für Paperless-Integration

## Notwendigi Vars

Alli Agent wo Paperless-API bruche, müend im lokale `.env`-File folgendi Vars setze:

```bash
# Pfad: /opt/data/home/.hermes/.env (Hermes)
# Pfad: ~/.env (Nova/Apollo — je nach Setup)

PAPERLESS_URL=http://10.0.40.30:8000
PAPERLESS_TOKEN=336d2df1f498547db31735522ecd6ea4449993e2
```

## Warum nöd im SKILL.md

D'Secrets stönd im `.env`-File, nöd im SKILL.md. Gränd:
- SKILL.md wird in Cronjob-Skills gelade → triggert Security-Filter
- `.env` wird nur vo Scripts gläse (ke LLM-Context)
- `.env` isch `.gitignore`-d — nöd im Source of Truth Repo

## History

| Datum | Was | Wer |
|-------|-----|-----|
| 18.05.2026 | .env hatt `PAPERLESS_URL=http://10.0.60.121:8015` (alti Dokploy-IP) + `PAPERLESS_TOKEN=***` (zerstört) | Fixed by Hermes |
| 18.05.2026 | Corrected to LXC: `10.0.40.30:8000` + correct token | Fixed by Hermes |

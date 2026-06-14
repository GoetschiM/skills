# S3 Backend Discovery — Paperless-ngx v2.20.15

## Finding

Paperless-ngx v2.20.15 (ghcr.io/paperless-ngx/paperless-ngx:2.20.15)
does **not** support S3 as a storage backend through environment variables.

## What was tried

1. Set `PAPERLESS_STORAGE_BACKEND=s3` in docker-compose environment
2. Set all `PAPERLESS_S3_BUCKET_NAME`, `PAPERLESS_S3_ENDPOINT`, `PAPERLESS_S3_ACCESS_KEY`, etc.
3. Confirmed env vars were present in the running container (`docker exec env | grep S3`)
4. Checked Django STORAGES config from inside the container — still `FileSystemStorage`
5. Grepped the Paperless source for STORAGE_BACKEND handling — no matching code path
6. Checked installed packages — `boto3` and `django-storages` not found

## Root Cause

The `PAPERLESS_STORAGE_BACKEND` env var is not read by Paperless 2.20's
settings.py. Django's STORAGES dict is hardcoded with `FileSystemStorage`.
No S3 support was built into this release.

S3 support was researched but appears to require:
- Installing `django-storages[boto3]` in the container (custom Dockerfile)
- Overriding the STORAGES setting in a custom settings file
- This was deemed too fragile for production; hybrid architecture chosen instead

## Resolution

Hybrid architecture:
- Paperless stores locally (`/srv/paperless/media/`)
- MinIO sync runs as separate pipeline (Paperless API → download → upload to MinIO)
- Qdrant for text search

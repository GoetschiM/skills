# Sandbox ArrStack Deployment — 2025-05-31

Deployed on LXC 110 (10.0.60.136), managed via Dokploy project "media-arrstack".

## Services

| Service | Port | Default Login | Notes |
|---------|------|--------------|-------|
| qBittorrent | **8081** | admin / adminadmin | Extern 8081 → intern 8080 (talk-gateway blockiert 8080) |
| Prowlarr | 9696 | — | Indexer-Sync-Zentrale |
| Sonarr | 8989 | — | DB-Migration beim ersten Start: 30-60s |
| Radarr | 7878 | — | DB-Migration beim ersten Start: 30-60s |

## Port-Konflikte

- Port **8080** wurde durch `talk-gateway` Container belegt
- Lösung: `ports: ["8081:8080"]` im compose (intern behält qBittorrent 8080)

## Paths

```
/opt/media-stack/
├── docker-compose.yml        # Aktuell laufende Compose
├── qbittorrent/config/
├── prowlarr/config/
├── sonarr/config/
├── radarr/config/
├── downloads/
├── tv/
└── movies/
```

## Dokploy Integration

- **Dokploy Projekt:** `media-arrstack`
- **Compose Service:** "Media ArrStack" (Raw-Provider, composeFile in Postgres DB)
- **Dokploy DB ID:** `8Ovr2w0M0mCUdf934d5va`
- **Status:** Compose ist in Dokploy registriert, aber de Raw-Tab funktioniert nöd (v0.29.5 Bug). Compose-Content via DB-Workaround direkt i d'Postgres-Tabelle `compose.` gschribe.

## GitOps

- Compose-File: `GoetschiM/gl-stack` → `dev/media-stack/docker-compose.yml`
- Branch-Strategie: dev = Sandbox, main = Production
- Zugriff via GitHub API (mit GITHUB_TOKEN aus Umgebung):
  ```bash
  curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/GoetschiM/gl-stack/contents/media-stack/docker-compose.yml?ref=dev" \
    | python3 -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"
  ```
- ⚠️ **Kein `WEBUI_PASSWORD`-Env-Var im Compose** — qBittorrent verwendet temporäres Passwort pro Session. Zum Fixen: `WEBUI_PASSWORD=<pw>` in die Umgebungsvariablen des qBittorrent-Services aufnehmen.

## Confluence

- https://goetschi.atlassian.net/wiki/spaces/~goe/pages/40271874/

# Browserless Port Change (14.05.2026)

## Situation
Browserless Container (`goetschi-labs-browserless-lelgmv-browserless-1`) hatte nur `expose: 3000` + Traefik — kein Host-Port. User wollte direkten Zugriff via `10.0.60.121:3005`.

## Lösung
Docker-compose.yml editiert und `ports: - "3005:3000"` hinzugefügt.

### Docker-compose.yml Pfad
`/etc/dokploy/compose/goetschi-labs-browserless-lelgmv/code/docker-compose.yml`

### Vorher
```yaml
services:
  browserless:
    image: ghcr.io/browserless/chromium:latest
    environment:
      TOKEN: ${BROWSERLESS_TOKEN}
    expose:
      - 3000
    # ...traefik labels...
```

### Nachher
```yaml
    ports:
      - "3005:3000"
    expose:
      - 3000
```

### Redeploy
```bash
cd /etc/dokploy/compose/goetschi-labs-browserless-lelgmv/code
docker compose up -d --remove-orphans
```

## Resultat
- Container zeigt: `0.0.0.0:3005->3000/tcp`
- Port 3005 LISTEN via docker-proxy
- Browserless antwortet: `/docs` → 301, `/` → 404 (normal)
- Token: `rqwhefqph8fms7vv`

## Gelernt
- Traefik + expose = Standard bei Dokploy. Port-Publishing ist zusätzlich.
- Container wird **recreated** (nicht nur restart).
- `docker compose up -d --remove-orphans` für sauberes Update.
- Browserless Health-Endpoints: `/docs` (301) und `/function` (301).

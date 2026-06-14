# NextCloud — Bind-Mount blockiert Erstinstallation (GL-91)

## Problem

NextCloud (nextcloud:33.0.3.2-apache) auf Dokploy (10.0.60.121) lässt sich nicht installieren. Der Docker-Entrypoint-Init (rsync + `occ maintenance:install`) schlägt fehl mit:

```
Cannot create or write into the data directory /var/www/html/data
```

## Ursache

Ein Bind-Mount im Docker Compose:
```yaml
volumes:
  - /data/shared-watchfolder:/var/www/html/data/michel/files/Watchfolder
```

erzeugt beim ersten Start automatisch die Zwischenverzeichnisse (`data/michel/files/`) als **root:root**. Der Entrypoint-Init will danach das `data/`-Verzeichnis mit www-data initialisieren, scheitert aber an den root-Besitzverhältnissen.

## Fix (Schritt für Schritt)

```bash
# 1. Bind-Mount aus docker-compose.yml entfernen (Abschnitt volumes:)
# 2. Alles platt machen — Container + Volumes
docker compose down -v

# 3. Clean deployen
docker compose up -d

# 4. Warten bis Init abgeschlossen (~30-60s)
#    Log-Check: "Starting nextcloud installation" -> Apache startet -> OK
docker logs code-nextcloud-1 --tail 10

# 5. Verifizieren
docker exec code-nextcloud-1 php /var/www/html/occ status
# -> installed: true, version: 33.0.3.2

# 6. Bind-Mount wieder ins compose einfügen
# 7. Container mit Mount recreieren
docker compose up -d
```

## Wichtige Erkenntnisse

- **`docker compose down -v` löscht ALLE named volumes** — inkl. DB-Daten. Nützlich für clean start, aber zerstört vorhandene Daten.
- **`docker restart` reicht nicht** — der Bind-Mount bleibt aktiv und recreiert die root-Ordner bei jedem Start.
- **Init dauert** — der Entrypoint rsynct zuerst die App-Files von `/usr/src/nextcloud/` nach `/var/www/html/`, dann läuft OCC. Während dieser Zeit ist OCC nicht nutzbar (Prozesse hängen im `D`-Status = uninterruptible sleep durch flock).
- **OCC-Timeout beim Init:** Versuche `occ status` während des Inits geben keinen Fehler, sondern hängen einfach — weil der flock auf `/var/www/html/nextcloud-init-sync.lock` exklusiv vom Entrypoint gehalten wird.

## GL-91 (Referenz-Ticket)

https://goetschi.atlassian.net/browse/GL-91
Confluence-Doku: https://goetschi.atlassian.net/wiki/spaces/~goe/pages/35880981

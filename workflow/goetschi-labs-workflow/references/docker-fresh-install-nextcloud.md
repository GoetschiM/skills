# NextCloud Docker Fresh-Install — Volume Pitfall (GL-91)

## Ausgangslag
NextCloud 33.0.3.2 uf Dokploy 10.0.60.121. Erste Deploy het Bind-Mount `/data/shared-watchfolder` → `/var/www/html/data/michel/files/Watchfolder` enthaltet.

## Problem-Chain
1. Docker-Compose startet Container
2. Init-Script (`entrypoint.sh`) checkt `/var/www/html/data/` — falls leer → auto-install
3. Bind-Mount het `/data/michel/` scho als **root:root** erstellt (weil Host-Ordner root:root isch)
4. OCC Install-Check sieht: User-Ordner existiert → nimmt a scho installiert → tried `upgrade` statt `install`
5. OCC gibt Fehler: "Can't create or write into the data directory"
6. Auch wenn mer `rm -rf /var/www/html/data/*` macht — Volume isch dirty, Init-Schritt wird übersprunge

## Fehlerbeobachtig (Diagnose)
```bash
# Symptom 1: Install schlaft
docker exec code-nextcloud-1 php /var/www/html/occ status
# → segfault / empty → nöd installiert, aber blocked

# Symptom 2: OCC maintenance:install schlaft
# "Directory /var/www/html/data/michel/ already exists"
# → root:root → falschi Permissions

# Symptom 3: Auch nach rm -rf geht's nöd
# → Init-Script überspringt Install Schritt will's Daten detektiert het
```

## Lösig
```bash
# 1. Container stoppe
docker compose down

# 2. ALLI Volumes plattmache (DATA + DB + Init-Lock!)
docker compose down -v

# 3. Frisch deploye OHNE Bind-Mount (oder uf Port 80 ohni externes Volume)
docker compose up -d

# 4. Warte bis Auto-Install fertig (30-60s)
watch -n 5 "docker logs code-nextcloud-1 --tail 5"

# 5. Bestätige
docker exec code-nextcloud-1 php /var/www/html/occ status
# → installed: true
# → version: 33.0.3.2

# 6. ERST JETZT Bind-Mount zuefüege + Container neustarte
docker compose up -d
```

## Warum `down -v` wichtig isch
`docker compose down -v` löscht NUR named volumes (data + db). Named volumes sind isoliert und chönd nöd einzeln gräumt werde. Wenn de Container vorher glofe isch, blibt d'DB voll und d'Data-Directory beschriibe — au wenn ich's noemol deploye.

ALTERNATIV: `docker compose down` + Volume manuell löschä:
```bash
docker volume ls | grep nextcloud
docker volume rm <volume-name>
```

Aber `down -v` isch sicherer und schneller.

## Nid funktioniert händ
- ❌ Container neustarte
- ❌ DB löschä + OCC maintenance:install
- ❌ rm -rf /var/www/html/data/
- ❌ Config löschä + Container restart (Auto-Init überspringt Schritt)
- ❌ DB-Reset + OCC install (files exist for user)
- ❌ DB-Reset + fsck (root:root blibt)

## Erkenntnis
**"Frisch installieren" bedeuteted im Docker-Kontext: `docker compose down -v` + usem gliche Compose wieder ufsetze.** Alles anderi isch Flickwerk wo zu (minütelange) Debugging-Sessions füehrt.

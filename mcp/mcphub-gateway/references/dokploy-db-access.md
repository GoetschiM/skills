# Dokploy — Admin-Passwort & PostgreSQL-Zugriff (LXC 100)

## Service-Info

- **URL:** `http://10.0.60.121:3000` (Dokploy Web-UI)
- **Host:** LXC 100 uf pve01 (10.0.60.10)
- **Docker Container:** `dokploy-postgres.1.<hash>` (PostgreSQL 15)
- **DB Name:** `dokploy`
- **DB User:** `dokploy`

## Passwort-zurücksetze / Check

Dokploy speicheret Passwort als **bcrypt Hash** i de `account` Table:

```sql
SELECT a.account_id, a.provider_id, a.password, a.user_id, u.email
FROM "account" a
JOIN "user" u ON a.user_id = u.id;
```

Einzige Weg Passwort z'häschtle: Hash us em `account.password` feld usläse und mit bcrypt prüefe. Es git kein Passwort-Reset-API-Endpunkt (nume über "Lost your password?" Link).

## Zugriff via Proxmox

```bash
# Über Proxmox Host (10.0.60.10, PW: Riotstar_PROXMOX_13)
sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10

# In LXC 100 + in Dokploy-Postgres-Container
pct exec 100 -- docker exec dokploy-postgres.1.<hash> \
  psql -U dokploy -d dokploy -c '<SQL>'

# Tabellen azeige
pct exec 100 -- docker exec dokploy-postgres.1.<hash> \
  psql -U dokploy -d dokploy -c '\dt'

# User + Account abfrage
pct exec 100 -- docker exec dokploy-postgres.1.<hash> \
  psql -U dokploy -d dokploy -c \
  'SELECT a.account_id, a.provider_id, a.password, u.email FROM "account" a JOIN "user" u ON a.user_id = u.id;'
```

## Wichtig! Admin-User

Nur eimolige User: **michelgoetschi@gmail.com** (einzigi E-Mail i DB).

`sessions` Table isch gläert (alli Tokens expired, letzti Session: April 2026).

## Generic Pattern: Docker-Postgres Password Reset über LXC

Das Pattern funktioniert für **all Dienste uf Proxmox LXCs** wo PostgreSQL bruuched.

### Prinzipschritte (am Bischpil Coolify):

1. **LXC + Container identifiziere** — via Proxmox Host:
   ```bash
   sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10
   pct list  # LXC IDs
   pct exec <LXC_ID> -- docker ps --format '{{.Names}} {{.Image}} {{.Ports}}'
   ```

2. **DB-Container + Tabellenname finde:**
   ```bash
   pct exec <LXC_ID> -- docker exec <db-container> psql -U <user> -d <db> -c '\\dt'
   ```

3. **Bcrypt-Hash GENERIERE — NUR vom Hermes-Container (wo bcrypt installiert isch):**
   ```bash
   # Immer uf Hermes-Container generiere, nöd uf ZiellXC (döt het's selte Python+bcrypt)
   python3 -c "
   import bcrypt
   pw = b'Michel2026_Coolify'
   print(bcrypt.hashpw(pw, bcrypt.gensalt()).decode())
   "
   ```
   ⚠️ **NIE** `pip3 install bcrypt` uf em ZiellXC — döt isch meistens kei pip installiert. Hash lokal generiere und per SQL übergeh.

4. **SQL-Update mitem Hash usfööhre (via SSH):**
   ```bash
   # HASHS uf Hermes generiere, denn per SSH via Shell webergeh
   HASH='$2b$12$...'  # Output vo Schritt 3
   sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10 \
     "pct exec <LXC_ID> -- docker exec <db-container> psql -U <user> -d <db> -c \\\"UPDATE users SET password = '\$HASH' WHERE id = 0;\\\""
   ```
   ⚠️ **Pitfall:** D'`$` im bcrypt-Hash müend escaped werde (`\$`) wenn si im double-quoted SSH-Befehl stönd. Single-quotes im Befehl verhindere das.

5. **Verify:**
   ```bash
   sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10 \
     "pct exec <LXC_ID> -- docker exec <db-container> psql -U <user> -d <db> -c \\\"SELECT email, substring(password, 1, 30) FROM users;\\\""
   ```

### Betroffeni Services uf LXC 100 (Dokploy Prod)

- **Dokploy:** `docker exec dokploy-postgres.1.<hash>` → DB: dokploy, Table: `account` (Spalte: `password`)
- **Nextcloud:** Cloud-Instanz (DB uf externem Container VM201, nöd uf LXC 100)
- **Paperless:** DB i eignerem Container
- **n8n:** DB i eignerem Container

### Betroffeni Services uf LXC 118 (Coolify)

- **Coolify:** `docker exec coolify-db psql -U coolify -d coolify` → Table: `users` (Spalte: `password`). Port: 8000 (intern 8080).
- Nu ei User: `michelgoetschi@gmail.com` (ID = 0)
- **Login-API nicht unter /api/v1/login!** Coolify API-Endpoint isch `/api/v1/auth/login` (Dokploy nutzt NextAuth under `/api/auth/callback/credentials`). Wenn Login via API nöd klappt, isch Browser-UI de einfacher Weg.
- Kei API-Tokens in `personal_access_tokens` Table vorhande

Prüef zersch mit `docker ps --format '{{.Names}} {{.Image}}'` welli Container laufed, denn d'DB-Struktur via `\\dt` erkunde.

---
name: proxmox-password-reset
version: 1.0.0
category: devops
description: Passwörter i Docker-DB-Containere zrugsetze via Proxmox-Host — für Dokploy, Coolify, Nextcloud und anderi Docker-DB-Dienst.
tags:
  - password reset
  - dokploy
  - coolify
  - postgres
  - proxmox
  - bcrypt
triggers:
  - passwort zrugsetze
  - password reset
  - dokploy login
  - coolify login
  - vergässe passwort
  - forgotten password
  - db password
related_skills:
  - proxmox-lxc
  - dokploy
---

# Proxmox DB Password Reset

## Übersicht

Wenn de Admin-Password für en Docker-basierti Service (Dokploy, Coolify, Nextcloud) vergässe oder nöd bekannt isch, chan mer's via Proxmox direkt i de PostgreSQL-DB zurücksetze.

**Voraussetzig:** SSH-Zugriff uf Proxmox Host (10.0.60.10) mit `sshpass` oder SSH-Key.

## Generisches Vorgehe

### 1. Container + DB finde

```bash
# LXC liste
sshpass -p '<proxmox_pw>' ssh root@10.0.60.10 "pct list"

# Docker Container aaluege
sshpass -p '<proxmox_pw>' ssh root@10.0.60.10 "pct exec <vmid> -- docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

### 2. User-Tabell finde

```bash
# Welchi Tabellä sind da?
sshpass -p '<proxmox_pw>' ssh root@10.0.60.10 "pct exec <vmid> -- docker exec <db_container> psql -U <user> -d <db> -c '\dt'"

# User-Tabell (typischerwiis: users, user, account)
sshpass -p '<proxmox_pw>' ssh root@10.0.60.10 "pct exec <vmid> -- docker exec <db_container> psql -U <user> -d <db> -c 'SELECT email, id, substring(password,1,20) FROM users;' 2>/dev/null || SELECT email, id FROM account;"
```

### 3. Bcrypt-Hash generiere

```bash
python3 -c "
import bcrypt
print(bcrypt.hashpw(b'<NeusPasswort>', bcrypt.gensalt()).decode())
"
```

### 4. Password update

```bash
# Bekannte User-ID
sshpass -p '<proxmox_pw>' ssh root@10.0.60.10 "pct exec <vmid> -- docker exec <db_container> psql -U <user> -d <db> -c \"UPDATE <table> SET password = '<hash_von_schritt_3>' WHERE id = '<user_id>' OR email = '<email>';\""
```

## Fall: Dokploy

```bash
# Container ID finde
DOKLOY_DB='dokploy-postgres.1.ri7tt1hr3jdjf5sn0uteo0hod'

# User uslese
sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10 \
  "pct exec 100 -- docker exec $DOKLOY_DB psql -U dokploy -d dokploy -c 'SELECT u.email, a.user_id FROM \"user\" u JOIN account a ON u.id = a.user_id;'"

# Hash generiere + Update (mach i zwei Schritt wäge Shell-Escaping)
python3 -c "import bcrypt; print(bcrypt.hashpw(b'<NeusPW>', bcrypt.gensalt()).decode())"

sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10 \
  "pct exec 100 -- docker exec $DOKLOY_DB psql -U dokploy -d dokploy -c \"UPDATE account SET password = '<generierte_hash>' WHERE user_id = '<user_id>';\""
```

**DB-Container Name cha wechsle** — immer zersch `docker ps | grep dokploy.*postgres` mache.

## Fall: Coolify

```bash
# User finde (immer ID=0)
sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10 \
  "pct exec 118 -- docker exec coolify-db psql -U coolify -d coolify -c 'SELECT id, email FROM users;'"

# Hash generiere
python3 -c "import bcrypt; print(bcrypt.hashpw(b'<NeusPW>', bcrypt.gensalt()).decode())"

# Update
sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10 \
  "pct exec 118 -- docker exec coolify-db psql -U coolify -d coolify -c \"UPDATE users SET password = '<hash>' WHERE id = 0;\""
```

**Hinweis:** Coolify API-Endpoint isch `/` (nöd `/api/v1/login`). De Login-Endpoint für curl:
```bash
curl -X POST http://10.0.60.139:8000/ -d '{"email":"x","password":"y"}'
```

## ⚠️ Pitfalls

| Problem | Lösung |
|---------|--------|
| **Shell-Escaping vom Hash** | Hash in Variable speichere, nöd direkt i SQL setze. Bcrypt-Hash enthält `$` wo d'Shell interpretiert |
| **DB-Container Name wechselt** | Immer zersch `docker ps | grep` vor em Update |
| **Kei pip/bcrypt uf LXC** | Python3 bcrypt uf em Host (Hermes-Container) installiert — Hash dert generiere, per Copy-Paste i SQL |
| **Dokploy: "user" Table mapped mit "User"** | PostgreSQL isch case-sensitive — `FROM "user"` mit Anführigszeiche |
| **Tabell-Namenskonvention** | Dokploy = `account`, Coolify = `users` — nöd identisch |
| **Vor update immer Verify** | Zersch `SELECT...` zum Prüefe obs de richtig User isch, ERST DERN update |

## Verifikation

Nach em Update:

```bash
# 1. DB prüefe
docker exec <db> psql -U <user> -d <db> -c "SELECT substring(password,1,20) FROM <table> WHERE id = '<id>';"

# 2. Login probiere (curl)
curl -s -X POST http://<service>:<port>/<login_endpoint> \
  -H "Content-Type: application/json" \
  -d '{"email":"<email>","password":"<neus_pw>"}'
```

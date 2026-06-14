---
name: wordpress-growpro
description: "WordPress Site-Management für grow-pro.ch — REST API via Application Passwords. Posts lesen/erstellen/bearbeiten, Kommentare moderieren, Medien hochladen."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
---

# WordPress grow-pro.ch — Hermes Skill

**Site:** [grow-pro.ch](https://grow-pro.ch) (Indoor Growing / Pflanzenbau)  
**REST API:** `https://grow-pro.ch/wp-json/wp/v2/`  
**Auth:** Application Password (Basic Auth) — siehe Credentials unten  
**User:** `michel` (ID 1, Admin)  
**App PW:** `C6th 002Q XFUk 7ocq IvL3 Cv76`  
**Database:** `d03daaca` (grow-pro) auf All-Inkl  

## Voraussetzungen

### 1. Application Password erstelle (einmalig)

Im wp-admin machen:
1. `wp-admin` -> `Users` -> `michel` -> `Application Passwords` (ganz unde)
2. Application Name: `Hermes Agent`
3. Password kopiere (wird nur einmal zeigt!)

### 2. Credentials sicher ablege

```bash
echo 'WP_GROWPRO_USER="michel"' >> /opt/data/home/.hermes/.env
echo 'WP_GROWPRO_APP_PW="<generiertes-password>"' >> /opt/data/home/.hermes/.env
```

### 3. Test Auth

```bash
curl -s -u "michel:APPLICATION_PASSWORD" https://grow-pro.ch/wp-json/wp/v2/posts
```

## API-Operatione

### Posts — lese (public)

```bash
# Alli Posts (public, ohni Auth)
curl -s "https://grow-pro.ch/wp-json/wp/v2/posts?per_page=20&orderby=date"

# Einzelne Post
curl -s "https://grow-pro.ch/wp-json/wp/v2/posts/ID"

### Posts — erstelle (braucht Auth)

```bash
curl -s -u "michel:APP_PW" \
  -X POST "https://grow-pro.ch/wp-json/wp/v2/posts" \
  -H "Content-Type: application/json" \
  -d '{"title":"Titel","content":"Content...","status":"draft","categories":[1]}'

### Posts — update

```bash
curl -s -u "michel:APP_PW" \
  -X POST "https://grow-pro.ch/wp-json/wp/v2/posts/ID" \
  -H "Content-Type: application/json" \
  -d '{"title":"Neuer Titel","status":"publish"}'

### Posts — löschen

```bash
curl -s -u "michel:APP_PW" \
  -X DELETE "https://grow-pro.ch/wp-json/wp/v2/posts/ID"
```

### Kommentare — moderiere (braucht Auth)

```bash
# Alli Kommentare
curl -s -u "michel:APP_PW" \
  "https://grow-pro.ch/wp-json/wp/v2/comments?status=hold&per_page=20"

# Kommentar approve (status=approve)
curl -s -u "michel:APP_PW" \
  -X POST "https://grow-pro.ch/wp-json/wp/v2/comments/ID" \
  -H "Content-Type: application/json" \
  -d '{"status":"approve"}'

# Kommentar spam markiere
curl -s -u "michel:APP_PW" \
  -X POST "https://grow-pro.ch/wp-json/wp/v2/comments/ID" \
  -H "Content-Type: application/json" \
  -d '{"status":"spam"}'

# Kommentar löschen
curl -s -u "michel:APP_PW" \
  -X DELETE "https://grow-pro.ch/wp-json/wp/v2/comments/ID?force=true"
```

### Medien hochlade (braucht Auth)

```bash
curl -s -u "michel:APP_PW" \
  -X POST "https://grow-pro.ch/wp-json/wp/v2/media" \
  -H "Content-Disposition: attachment; filename=image.jpg" \
  -H "Content-Type: image/jpeg" \
  --data-binary @/pfad/zum/bild.jpg
```

### Kategorien — lese (public)

```bash
curl -s "https://grow-pro.ch/wp-json/wp/v2/categories?per_page=50"
```

## Bekannti Kategorie

- ID 1: Allgemein (4 Posts)

## WooCommerce API

Falls nötig: WooCommerce REST API bruucht **Consumer Key + Consumer Secret** (muss im WooCommerce-Plugin generiert werde):
- Endpoint: `https://grow-pro.ch/wp-json/wc/v3/`
- Auth: Basic Auth (Consumer Key : Consumer Secret)

## Sicherheitshinwis

- Application Password isch volle Admin-Zuegriff
- NIE in öffentliche Chats oder Tickets poste
- Nume via `.env` oder Qdrant sichere
- **NIE** Posts/Kommentare löschen ohni Michels OK
- **Security-Scans nie hybrid/bruteforce** — nur stealthy (READ-ONLY)
- Scan-Ergebnisse nur im GL-Problem-Ticket dokumentiere, nie in öffentlichem Chat

## Security-Quick-Scan (via WPPrrobe)

Bevor du en Security-Scan machsch: **NUR Stealthy (READ-ONLY) Mode**. Kei Brute-Force, kei Schribzugriff. WPPrrobe isch e Go-Binary wo **lokal** installiert wird — kein Kali-LXC nötig.

```bash
# Installation (einmalig)
curl -sL -o /usr/local/bin/wpprobe \
  "https://github.com/Chocapikk/wpprobe/releases/download/v0.11.8/wpprobe_v0.11.8_linux_amd64"
chmod +x /usr/local/bin/wpprobe

# Vuln-Datenbank lade (vor erstem Scan)
wpprobe update-db

# Scan ausführen (NUR stealthy!)
wpprobe scan -u https://grow-pro.ch --mode stealthy -o /tmp/wpprobe-results.json

# Nach Scan: Ergebnisse in GL-Ticket dokumentiere (Issue-Typ: Problem, Priority Highest)
```

**Wichtigste Scan-Prinzipie:**
- `--mode stealthy` = REST API only (keine HTTP-Fuzzing)
- `--mode hybrid` = + Bruteforce — **nur nach Michels OK**
- Vor erstem Scan immer: `wpprobe update-db` (lädt Wordfence-Vuln-DB)
- Nach Updates (Plugins) → Neu-Scan zur Verifikation

**Bekannti Plugins uf grow-pro.ch (Stand 09.06.2026, Scan GL-143):**
- royal-elementor-addons 1.3.75 — 🔴 Critical (CVE-2023-5360, File Upload)
- elementor 3.15.3 — 🟠 High (RCE via Template)
- elementskit-lite 2.9.1 — 🟠 High (Local File Inclusion)
- essential-addons-for-elementor-lite 5.8.7 — 🟠 High (Privilege Esc)
- woocommerce 8.0.5 — ⚠️ Veraltet (aktuell 9.x)

## Referenze

- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [WPPrrobe GitHub](https://github.com/Chocapikk/wpprobe)
- Ticket: SUP-31 (https://goetschi.atlassian.net/browse/SUP-31)
- GL-143: Security Scan grow-pro.ch (https://goetschi.atlassian.net/browse/GL-143)
- Database: d03daaca auf All-Inkl (grow-pro.ch)
- Qdrant: wordpress-growpro (credentials + infos)
- Confluence: 🚨 System-Credentials & Endpunkte (35717121)
- Skill: kali-container (WordPress-Sektion mit WPProbe + WPScan)

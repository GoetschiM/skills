---
name: osint-analysis-workflow
title: OSINT Analysis Workflow
description: Vollständige OSINT-Analyse uf en Person/Username — von de Rohdate zum fertige Report inkl. Cross-Referencing, Multi-Identity-Analyse und Telegram-Output
version: 2.1.0
author: Hermes
trigger: Wenn en User en OSINT-Analyse wot — uf en Person, Username oder Email. Mehreri Usernames werded automatisch cross-referenced.
---

# OSINT Analysis Workflow (Kali Container)

## Use Case
Vollständige Open-Source Intelligence-Analyse uf en Person/Username.
Lauft exklusiv über de Kali-Container uf Apollo (10.0.60.156).
Git dtailed platform API quirks + workarounds i de Kali-Container Reference: `skill_view(name='devops/kali-container', file_path='references/osint-person-runbook.md')`

## Prerequisites
- Kali Container lauft (`docker ps | grep kali`)
- Login: `ssh root@10.0.60.156` → `docker exec kali bash -c '<cmd>'`
- Internetzugriff über Kali-Container
- **Script-Muster verwende, keine Inline-Bash mit escaped Quotes!** (lueg Step 2)

## Decision Tree (Welleche Schritt zersch?)

```
User seit Username    → Sherlock (1. Priorität — schnell, 400+ Platforme)
User seit Email       → holehe (1. Priorität — 121 Websites in ~4s)
User seit Domain      → whois + theHarvester (1. Priorität)
User seit Personename → Swiss Phonebook (search.ch, ZIP.ch) — CH-Privati sind selte uf Sherlock/SoMe
User seit beide       → Sherlock + holehe parallel

Deep-Dive-Abfolge wenn Sherlock 52+ Treffer het:
  Phase 1: Gravatar → GitHub → GitLab → Docker Hub (Identitäts-Check)
  Phase 2: Steam → Wikipedia (Öffentlichi Profile mit Location/Zeit)
  Phase 3: YouTube oEmbed → Reddit old (Meistens privat — Trozdem prüefe)
  Phase 4: holehe auf vermueteti Emails (Bestätigt Account-Plattform-Zuordnig)
  Phase 5: Cross-Reference zwüsche allne Usernames + Emails
  Phase 6: Devpost — Software-Devs hend det Portfolio (GitHub-Refs, Skills)
```

## Step-by-Step

### 0️⃣ Vorbereitung: Script-Exec-Pattern
**NIE escaped Python in Docker exec chasch verwende!** Schrib en Script-File, kopier ihn in Kali und füehr ihn det us:

```bash
docker cp /tmp/<script>.py kali:/root/<script>.py
docker exec kali python3 /root/<script>.py
```

Oder wenns eifache Bash-Befähl sind, direkt:
```bash
docker exec kali bash -c '<eifache bash-befähl>'
```

### 1️⃣ Sherlock — Username-Suche (400+ Plattforme)
`docker exec kali sherlock <username>`
- Output: `[+] URL` (existiert) oder `[-]` (nöd gfunde)
- **Interpretation:** `[+]` heisst nöd dass Inhalt sichtbar isch — vil Platforme sind privat
- Dauer: ~2 Min für 400+ Plattforme
- Wichtigi Fundstellene: GitHub, GitLab, Reddit, Steam, Telegram, YouTube, Gravatar, TryHackMe, Docker Hub

### 2️⃣ theHarvester — Email/Subdomain-Enumeration
`docker exec kali bash -c 'theHarvester -d <domain> -b yahoo,linkedin'`
- **ACE:** `theHarvester` mit grossem H, nöd `theharvester` (command not found!)
- Google/Bing werded vo Kali blockiert → `-b yahoo,linkedin` verwende
- Nöd `-b all` — das schickt alli Sources inkl. blockierti → partial failure

### 3️⃣ holehe — Email-Registrierungs-Check
`docker exec kali bash -c 'holehe <email>'`
- Dauer: ~4s für 121 Websites
- Output: `[+]` = registriert, `[-]` = nöd, `[x]` = rate-limited
- **Priorisiere `[+]`-Resultat** für Deep-Dives (lass rate-limited links liege)

### 4️⃣ whois + DNS — Domain-Infos
```bash
docker exec kali whois <domain>
docker exec kali dig MX <domain>    # MX, TXT, NS statt dig ANY (wird blockiert)
docker exec kali dnsrecon -d <domain> -t std
```
- `.ch`-Whois redacted (GDPR) → nur Nameserver + Registrier-Datum
- `dig ANY` vo Cloudflare-DNS → `NOTIMP` → einzelni Record-Typen abfrage

### 5️⃣ whatweb — Website-Fingerprinting
`docker exec kali whatweb <domain>`

### 6️⃣ Gravatar — Identity-Anchor
```bash
curl -s "https://gravatar.com/<username>.json"
docker cp kali:/tmp/gravatar_<hash>.jpg /root/gravatar_<hash>.jpg
```
- Glyche Gravatar-Hash über verschideni Platforme → **Beweis für glychi Person**
- Bild via MEDIA: /path im Output azeige
- Hash: SHA256 vo de Email (lowercase)

### 7️⃣ GitHub — De Jackpot
```bash
NAME=<username>
# Profile
curl -s "https://api.github.com/users/$NAME"
# Repos (sorted by update — wichtig!)
curl -s "https://api.github.com/users/$NAME/repos?per_page=50&sort=updated"
# Starred → Interesse-Landkarte
curl -s "https://api.github.com/users/$NAME/starred?per_page=20"
# Events → Wat macht d Person aktuell?
curl -s "https://api.github.com/users/$NAME/events?per_page=10"
# Following → Nur 1 Follower? Das isch en Signal!
curl -s "https://api.github.com/users/$NAME/following"
```
- **Fork-Erkennig:** `repo.fork` unterscheidet eigeni Arbeit vom Fork
- **Nur 1 following** → Verbindig googele (war DayZ-Dev in eusem Fall)
- Rate-Limit: 60 req/h ohni Token

### 8️⃣ Steam — Öffentlichs Profil mit Location!
```bash
curl -s "https://steamcommunity.com/id/<username>/?xml=1"
```
- **Wichtigi Felder:** steamID64, memberSince, location, onlineState, vacBanned, avatarIcon/Medium/Full
- Wenn `<privacyState>public</privacyState>` → alles iigsähbar
- Steam-Spiele: `games/?xml=1` — meistens privat

### 9️⃣ Wikipedia / GitLab / Docker Hub / Devpost
```bash
curl -s "https://en.wikipedia.org/w/api.php?action=query&list=users&ususers=<username>&format=json"
curl -s "https://gitlab.com/api/v4/users?username=<username>"
curl -s "https://hub.docker.com/v2/users/<username>/"
curl -s "https://devpost.com/<username>"        # Software-Portfolio, GitHub-Refs, Skills
```
- Wikipedia: Editcount + Registration-Date + groups (blocked?)
- GitLab: Gravatar-Hash glych wie GitHub → Cross-Reference
- **Devpost:** Enthält oft versteckti GitHub-Refs, Tech-Stack-Agab, Standort. User-Agent darf au generic si.

### 🔟 Swiss Phonebook OSINT — CH-Privati finde
**Wichtig für Schwiizer Persone!** Vili CH-Bürger hend kei Social-Media-Präsenz, sind aber im Telefonbuech.

#### search.ch / local.ch
```bash
# Direkti URL mit Name + Stadt
curl -s "https://search.ch/tel/?name=<Name>&firstname=<Vorname>&city=<Ort>"
# Oder wenn d'Adrässe bekannt isch, als Detail-URL ufböue:
# https://search.ch/tel/<ort>/<strasse>-<nummer>/<vorname>-und-<name>
# Lueg im HTML nach "Götschi, Conradin und Karin"
```

#### ZIP.ch — Alternative zu search.ch
```bash
# https://zip.ch/<lang>/gotschi-<vorname>-<strasse>-<ort>-<id>/
# Enthält vollständigi Adrässe + Telefonnummer
# Data-Layer im HTML enthält strukturierti Date:
#   entryStreet, entryNumber, entryCity, entryPostcode, entryRegion
```

**Erwartete Issue:** search.ch zeigt d'Telefonnummer nöd immer im HTML — det sind meistens Business-Nummere (058...). **ZIP.ch isch de besseri Source** für privati Festnetz-Nummere.

**Namensvariatione:** Schwiizer Telefonbüecher verwende oft phonetischi Schriibwiise oder alti Nämensforme. Z.B. "Sternhauser" → "Steinhauser". Immer mehreri Schriibwiise probiere!

**Mehrfach-Adrässe:** E Person chan unter verschiedene Adrässe i verschidene Direktorien uftauche (Wohnadrässe + alternative Adrässe). Alli notiere und cross-reference.

Detailierti Befähl und Use-Cases: `references/swiss-phonebook-osint.md`

### 1️⃣1️⃣ Proaktiv goe: Was tue wenn's «Kei Date» seit?
**User-Erwartig:** Nöd eifach «privat» akzeptiere — alternativi Wäg probiere!

| Plattform | Wenn Blockiert | Alternative |
|-----------|----------------|-------------|
| Reddit | API blockiert | `old.reddit.com` (toleranter), Google `site:reddit.com {username}` |
| YouTube | @channel existiert nöd | `oembed` probiere, Search-API fyr Mentions |
| LinkedIn | Komplett blockiert (999) | Devpost für Software-Devs, YouTube für Content-Creators. Sherlock bestätigt nur Existenz. |
| Spotify | Profil privat | Sherlock-Bestätigig isch scho en Fund |
| Pinterest | Kei Inhalt | Sherlock-Bestätigig notiere |
| Shodan | API-Key fehlt | `shodan init` erwähne, alternativ curl |
| Devpost | — | Enthält Software-Portfolio, GitHub-Refs, Tech-Skills, Standort. Immer probiere für Entwickler.

### 1️⃣2️⃣ Cross-Referencing (Mehreri Identitäte)
Wenn en User zwei+ Usernames het (z.B. «michelgoetschi» + «radislione»):

1. **Gravatar-Hash vergliche** — glyche Hash = glychi Person über alli Platforme
2. **Email-Hash vergliche** — GitHub + GitLab + Gravatar use glyche Email? → Beweis
3. **Überlappendi Plattforme notiere** — Reddit, GitHub, Spotify etc. uf beide Usernames
4. **GitHub Following analysiere** — wer wird gfollowered? Was seit das über Interesse?
5. **Zeitachse erstelle** — wänn sind welchi Accounts erstellt worde? → Identity-Entwicklung

Konkretes Bischpiu: `references/osint-crossref-radislione.md`

### 1️⃣3️⃣ Gravatar-Bild us em Container hole
```bash
# Im Container: Bild id Container-TMP speichere
curl -s -o /tmp/gravatar_<hash>.jpg "https://2.gravatar.com/avatar/<hash>?s=512"

# Uf Host kopiere
docker cp kali:/tmp/gravatar_<hash>.jpg /root/gravatar_<hash>.jpg

# Im Output: MEDIA:/root/gravatar_<hash>.jpg
```

## Pitfalls (Session-Erfahrige)
- **theHarvester mit falschem Case** → command not found. Immer `theHarvester` (capital H)
- **dig ANY vo Cloudflare** → `NOTIMP`. Einzelni Record-Typen (MX, TXT, NS, SOA, A) verwende
- **Python f-Strings in Docker exec** → SyntaxError dur escaped Quotes. Immer Script-File schribe!
- **GitHub API 60 req/h** → Alles in eim Script sammle statt einzeln ufruefe
- **Reddit blockiert** → old.reddit.com isch toleranter, aber au nöd garantiert
- **Sherlock-Resultat interpretiere** → `[+]` heisst nöd Inhalt sichtbar, nume Account existiert
- **Götschi AG usefiltere** — Gleichnamigi Familie-Unternehmen nöd mit Person verwechselbar
- **holehe rate-limited** → `[x]` links liege, nume `[+]`-Resultat deep-dive
- **LinkedIn komplett blockiert** → Status 999 (LinkedIn-Bot-Detection). Selbst Google Cache funktioniert nöd. Alternativ: Devpost/YouTube/andere Platforme für Profil-Infos nutze. Sherlock chan LinkedIn-Bestätigig lieferen aber kein Inhalt.
- **YouTube @-Handle nöd via oEmbed** → `youtube.com/@username` funktioniert nöd mit oEmbed-API. Stattdessen d'Channel-Page direkt parsen oder Search-API bruche.
- **search.ch Telefonnummern unvollständig** → D'HTML-Seite zeigt oft nur Business-Nummere (058...). Privati Festnetz-Nummere sind über ZIP.ch oder seltener über d'vCard-Datei findbar.
- **Qdrant-Contacts prüefe VOR neuem Contact erstelle!** — Oft existiere Kontakt scho unter abwiichendem Name (z.B. "Koni Götschi/Mobil" statt "Conradin Götschi"). Immer Qdrant goetschi_labs_contacts vor em Speichere scrolle, mängisch mit Name-Variante suech (Kurzname, Kosename, mit/ohni Mobil-Zuesatz). Merged OSINT-Date mit existierendem Contact, ersetz nöd!

## Report Output Format
**Kei HTML-Tabälle!** Telegram unterstützt nur:
```
## Header
- Bullet-Point
- **Fett** / *Kursiv* / ~Durchgestriche~ / ||Spoiler||
- `Code`
- MEDIA:/path (Bild azeige)
```

**Struktur:**
1. Gravatar-Bild per MEDIA: am Afang (sofortige Identitäts-Check)
2. Kategoriesierti Resultat: GitHub → Steam → Email → Social Media → DNS/Whois
3. Cross-Reference zwüsche Identitäte am Schluss
4. Kernerkenntnis zum Schluss

## Verification
- Sherlock = `[+]` + URL (Account existiert)
- holehe = `[+] Email used` (Email aktiv uf Plattform)
- GitHub = HTTP 200 mit "login"-Feld
- Steam = `<profile>` mit `<steamID64>`
- Gravatar = displayName + profileUrl
- Cross-Reference = Glyche Gravatar-Hash über 2+ Platforme

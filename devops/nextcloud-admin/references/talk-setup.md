# Nextcloud Talk — Full Integration Reference

Status: ✅ **Operational** (30.05.2026)
Nextcloud: 33.0.3 | Talk: v23.0.5 | PHP: 8.4

## Architecture

- **NC Container**: code-nextcloud-1 (Apache + PHP-FPM, port 8080→80)
- **DB Container**: code-db-1 (PostgreSQL 16 Alpine)
- **DB Credentials**: user=oc_admin, db=nextcloud, host=db (internal Docker)
- **API Base**: `http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v`
  - Chat: `v1/chat/{token}` ✅
  - Room: `v4/room` ✅
  - v3/v4/chat → Error 998 ❌

## Users

| User | Password | Role |
|------|----------|------|
| michel | NextCloud123! | Admin |
| Hermes | Hermes_Talk_2026! | Bot |
| Nova | Nova_Talk_2026! | Bot |
| Apollo | Apollo_Talk_2026! | Bot |

All created via `occ user:add` — NIE per SQL direkt, weil SQL inserts d'oc_accounts-Table und uid_lower-Spalte nöd richtig befüllt.

## Room

- **Name**: Hermes-Lab
- **Token**: `iytt2n7g`
- **Room ID**: 1
- **Type**: 3 (Public Group)
- **Participants**: michel, Hermes, Nova, Apollo
- **Bot**: Hermes (ID 1, registered via talk:bot:create)

## Debugging Journey (Login fix)

### Problem
User via SQL aagleit (`INSERT INTO oc_users`). `curl -u Hermes:Hermes_Talk_2026!` → 401. `occ user:resetpassword Hermes` → "User does not exist". `occ user:list` → zeigt nur michel. Trotzdem sind d'User i de DB gsi (`SELECT * FROM oc_users`).

### Root Cause
3 Sachlig hend gfehlt:

1. **`uid_lower`-Spalte leer** — Nextcloud sucht bi Login nach uid_lower. SQL inserts hend das Feld leer gloh. `occ user:add` setzt automatisch `uid_lower=LOWER(uid)`.

2. **`oc_accounts`-Eintrag fehlt** — Nextcloud 33 bruucht en zusätzliche Metadate-Iitrag in de oc_accounts-Table. Ohne dä wird de User vo de Auth-Backend nöd erkannt (obwohl er i de DB isch).

3. **Falsches Hash-Format** — Bcrypt (`$2y$12$...`) ohni Version-Prefix. NC 33 bruucht Argon2id mit Prefix `3|$argon2id$v=19$m=65536,t=4,p=1$...`.

### Fix
1. User aus DB lösche (alle 3 Tabellen: oc_users, oc_group_user, oc_accounts)
2. Neu via `occ user:add` erstelle (handelt alles richtig)
3. Password via PHP im Container generiere (`PASSWORD_ARGON2ID`)

## Slow PHP Problem

Nextcloud PHP isch extrem langsam (Apache + PHP-FPM lädt s'ganze Framework).

- `occ`-Commands bruuched 30-180s — IMMER `timeout 180` setze!
- `curl` API calls bruuched 30-60s — immer `--max-time 60`
- Einzig `/status.php` isch schnell (läd kei Framework)
- "kein Output" vom curl heisst nöd automatisch Fehler — oft isches eifach z'langsam gsi

## Talk Tables (v23.0.5 on NC 33)

App `spreed` enabled = Version 23.0.5.

Korrekti Tables (nach vollständigem app:enable):
- `oc_talk_attendees` — participants
- `oc_talk_rooms` — rooms
- `oc_talk_sessions` — active sessions
- `oc_talk_participants` — participant states
- `oc_talk_room_types` — room type definition
- (30+ tables total)

Wenn nume `oc_spreedme_rooms` + `oc_spreedme_room_participants` existiered → App isch nöd korrekt installiert (falschi Version oder Migration nöd duregloffe). Lösung: disable + re-enable.

## Gateway Integration (Pending)

Hermes Agent cha aktuell **manuell** über Talk kommuniziere (via curl API). 
Für **automatischi** Integration (Hermes reagiert uf Talk-Nachrichte):

1. **Talk Bot Webhook** — Nextcloud ruft en URL uf wenn öpper @Hermes erwähnt
   - Bruucht en stabil erreichbare HTTP-Endpoint (z.B. uf Apollo LXC)
   - Vorteil: Echtzit, kein Polling
   
2. **Polling** — Hermes holt regelmässig nöii Nachrichte via API
   - Einfacher umsetzbar
   - Bruucht en Cron-Job
   - `curl -u "Hermes:..." "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v1/chat/iytt2n7g?lookIntoFuture=1"`

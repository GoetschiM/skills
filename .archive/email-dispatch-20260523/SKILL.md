---
name: email-dispatch
description: "⚠️ DEPRECATED — replaced by productivity/email-classifier. Kept for reference only."
version: 2.0.0-deprecated
author: hermes
license: MIT
platforms: [linux]
prerequisites:
  skills: [google-workspace]
  commands: []
  credential_files:
    - path: "~/.hermes/google_token.json"
      description: "Google OAuth2 token (must be valid, not expired)"
    - path: "~/.hermes/.env"
      description: "TELEGRAM_BOT_TOKEN, NOTION_API_KEY, ATLASSIAN_TOKEN"
metadata:
  hermes:
    tags: [Email, Dispatch, Sorting, Invoices, Gmail, IMAP]
---

# ⛔ DEPRECATED — Email Dispatch

**This skill is superseded by `productivity/email-classifier`.**

The old cron + Notion-Only system was replaced on 22.05.2026 with a manual-learning approach:
- **No cron** — Michel says "prüf mal d'Mails" when ready
- **No Notion DB** — decisions via audio/text directly
- **Qdrant learning** — every decision is stored, rules build up over time
- See `productivity/email-classifier` for the current system

---

# Email Dispatch (Legacy documentation below)

## Architecture

```
Gmail API (Google Workspace Skill)
        │
        ▼
Dispatch Approval Script (Python, cron-driven)
        │
        ├── Notion Approval DB Check → Approved? → Dispatch
        │                                  ↘ Unknown? → Notion page created (full email body in markdown)
        │                                               → Michel approves/rejects IN Notion
        ├── Content Categorizer (keywords → category detection)
        └── GL Ticket Creator (security alerts → auto Jira)
```

## Core Principle

**Michel does everything in Notion.** No Telegram buttons, no text commands.
When an unknown sender appears, Hermes creates a Notion page with the full
email body embedded as markdown. Michel opens the Notion DB entry, reads the
email right there, and sets Status to Approved or Rejected. The 4-hour cron
dispatch processes whatever Status it finds.

## Reference Files

- `references/dispatch-rules.md` — The user's actual dispatch rules (sender list, actions, exceptions)
- `references/content-categorization.md` — Keyword-based category detection for auto-classifying emails

## Prerequisites

1. **Google Workspace** skill's OAuth setup must be completed — the dispatch script uses the Google API directly (`google_api.py`), not IMAP/Himalaya
2. **Google OAuth token** must be valid (`setup.py --check` should print AUTHENTICATED)
3. **Telegram Bot Token** in `.env` — `TELEGRAM_BOT_TOKEN` (used for inline keyboard approval)
4. **Notion API Key** in `.env` — `NOTION_API_KEY` (used for Approval DB queries)

## OAuth Renewal (when token expires)

If the dispatch script fails with `invalid_grant: Token has been expired or revoked`:

```bash
GSETUP="python3 /root/.hermes/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --auth-url --services email
# Send the URL to the user → they open in browser, authorize, paste back the redirect URL
# IMPORTANT: The user MUST visit THIS EXACT URL (not a previous one) — PKCE state must match
$GSETUP --auth-code "THE_URL_OR_CODE"
$GSETUP --check  # should print AUTHENTICATED
```

**PKCE-Trick:** If the user sends back a code from a PREVIOUS auth URL, it fails with `Invalid code verifier`. Always generate a fresh `--auth-url` and make sure the user uses THAT specific one (not one from a previous attempt).

The token auto-refreshes after this. The dispatch script reads from `~/.hermes/google_token.json` via the Google API wrapper.

## Notion-Referenze

Dispatch-Regle sind in Notion dokumentiert. **Immer zerst Notion prüefe, nid nöi schriibe!**
- **«E-Mail Dispatcher v1.0»** — `https://www.notion.so/E-Mail-Dispatcher-v1-0-36581c83f6d9814cb121f272de444c0f`
- **«Dispatch Notizen»** — `https://www.notion.so/Dispatch-Notizen-35f81c83f6d980b798f7ecbdd17c0a77`
- **Confluence** — `https://goetschi.atlassian.net/wiki/spaces/~5a75b5612d61371e861f4dae/pages/31752193/`

## Michels Spezifischi Regle (Stand: 21.05.2026)

Notion-Page mit vollständige Regle: «E-Mail Dispatcher» — `https://www.notion.so/E-Mail-Dispatcher-36581c83f6d981f0825df2c11513b79f`

### 🔴 IMMER LÖSCHE (Trash)
Sender (domain/Name) wo sofort trashed werde:
- `ricardo.ch` — au Such-Treffer
- Sim Ultimate, Bitpanda, Rewe
- `calendar-notification@google.com` — alli Google Kalender-Notifies
- Google Local Share, Google One, Google AI Pro
- `linkedin.com` — generell (vorher Profil-Besucher notiere!)
- Atlassin, Switch, Constellation, Wordfans Activity
- `notifications.ui.com`, `ui.com` — alli UniFi-Notifies (Threat Detected, Admin, Academy, Produkt-Updates)
- `newsletter.digitec.ch`, Digitec
- `noreply@steampowered.com`, Steam
- `wordpress@grow-pro.ch`, WordPress Auto-Update
- `notifications.digitalparking.ch`, Parkingpay
- `notification.helvetia.ch`, Helvetia

### 📄 RECHNIGE — PDF extrahiere + trashed
Vor em Trash: PDF-Attachments extrahiere und unter `/root/.hermes/invoices/` speichere.
- **Just Eat** (`no-reply@order.just-eat.ch`)
- **Ricardo** (au No Reply — PDF useziehe!)
- **Paddle** (`help@paddle.com`) — Teslemetry-Rechnige
- **Swisscom** (`noreply@bill.swisscom.com`)
- **Google Cloud / Google Payments** (`payments-noreply@google.com`)
- **Amia Parking Bay** — Parkrechnige

### ⚠️ BEHALTE + MICHEL INFORMIERE
- **Moto Poschung** (`info@motoposchung.ch`) — NUR wenn DE/CH-DE! Englisch = löschä
- SSL-Zertifikat-Renewal (`xpertcom.ch`) — HIGH PRIORITY
- Wichtigi Kunden-Aafrage, Business-Mails

### ❓ UNSICHER — NACHTRAGE
- SLA Kunde-Status-Mails ("SLA Customer --- [Success]")
- "You have alerts", "Rechnung für Microsoft 365"
- Alles wo nöd klar in obigi Kategorie fallt

### 👤 LINKEDIN Profil-Besucher
Vor Löschig vo LinkedIn-Mail: Aazahl Profil-Besucher + wichtigi Details (Arbeitgäber, Rolle) in Memory notiere.

## Dispatch Rules (Pattern)

Rules match on **sender domain/name** (case-insensitive). Each rule has:
- `senders`: list of identifiers (domain or name substring)
- `action`: `delete` (archive+trash), `invoice` (extract PDF + save under Rechnungen), `notify` (tell user), `unsure` (ask Michel)
- `condition`: optional — e.g. "only if German language" or "if no PDF attachment"

### Rule Evaluation Order

1. **Invoice** rules checked first (extract PDF even from otherwise-noise senders like Ricardo)
2. **SSL/High-Prio** — e.g. "RENEWAL ALERT: Your SSL certificate is expiring" → inform Michel immediately
3. **Notify** rules checked second (important senders → Telegram DM)
4. **Unsure** — SLA Mails, Backup Reports ("SLA Customer --- [Success]"), "You have alerts", "Rechnung für Microsoft 365" → ask Michel
5. **Delete** rules last (everything else = noise)
6. Unmatched emails → **ask user** (unknown sender)

## Invoice Extraction

When an email matches an `invoice` rule or has a PDF attachment:
1. Download the email's attachments (PDFs)
2. Extract sender, date, amount (if available from body)
3. Save PDF to the user's Rechnungen storage location
4. Log the extraction

## Scripts

- `scripts/dispatch_approval.py` — Active dispatch runner (v2.0, Notion-Only)
- `scripts/email-dispatch.py` — Legacy version (Himalaya-based, deprecated)
- `scripts/dispatch_processed.json` — Auto-generated set of processed email IDs (dedup)

## 🛂 Dispatch Approval System v2.0 (SUP-32)

Jede Absender + Topic muss vo Michel approve werde bevor dispatched wird. D'Notion-DB isch d'Whitelist.

### Michels Workflow

**Michel macht ALLES i Notion.** Kei Telegram-Buttons, kei Text-Kommandos.

1. Hermes erstellt e **Notion Page** für unbekannti Absender — mit **VOLMEM E-Mail-Body** im Page-Inhalt
2. Michel öffnet de **Notion DB-Eintrag**, list d'Mail, setzt **Status**:
   - **Approved** + **Action: Dispatch** → wird bim nächste Run verarbeitet
   - **Approved** + **Action: Delete** → Mail wird glöscht
   - **Approved** + **Action: Ticket** → GL-Jira-Ticket wird erstellt
   - **Approved** + **Action: Ordnen** → Mail wird i Gmail-Label verschobe
   - **Rejected** → Mail wird trashed
   - **Pending Approval** → nüt passiert (wartet)
3. De Cron-Run alli 12h verarbeitet den Stand

### Neui DB-Property

| Fäld | Type | Zweck |
|------|------|-------|
| **Betreff** | rich_text | Originale Mail-Betreff |
| **Vorschau** | rich_text | Body-Vorschau uf de DB-Ansicht |
| **Kategorie** | select | Newsletter/Rechnung/Security/Notification/Other |
| **Ziel-Ordner** | rich_text | Gmail-Label (z.B. "Invoices") |

De **ganzi Mail-Body** isch im **Page-Inhalt** (Markdown) — Michel cha d'Page öffne und d'Mail richtig lese.

### Content-basierts Category-Matching

Automatischi Kategorie-Erkennig:
- **Rechnung** — Invoice, Rechnung, Zahlung, Subscription
- **Security** — Threat, Alert, Admin Accessed, Intrusion → auto-ticket
- **Newsletter** — Newsletter, Weekly, Promotion, Rabatt
- **Notification** — Status, Delivery, Update, Maintenance
- **Other** — Alles andere

### Script

`scripts/dispatch_approval.py` — Version 2.0 (Notion-Only).

Features:
- **10 Mails max pro Run**
- **Full Email Body als Page-Content** (nid nume i Properties-Fälder)
- **Content-basierts Category-Matching** (Rechnung/Security/Newsletter/Notification)
- **Kei Telegram-Interaktio** — alles über Notion
- **GL-Ticket**: Bi "Ticket" wird automatisch es Jira-Ticket im GL-Projekt erstellt (Issue-Type: Problem)
- **Nachricht an Michel**: Kei — er checkt eifach d'Notion-DB

### Cron (v2.0)

- **Schedule**: `0 4,16 * * *` (alli 12 Stund um 04:00/16:00 UTC)
- **Job-ID**: `7c6be7c02d3f`
- **Stiller Lauf**: Kei Telegram-Nachricht — nume Logging
- **Workdir**: `/opt/data/home/.hermes`

### Flow (v2.0 — vereinfacht)

```
Neui Mail i de Inbox (Google API, max 10)
      │
      ▼
Absender + Inhalt in Approval DB checke
      │                    │
      ├─ Bekannt ──────────┤
      │   ├─ Approved      │
      │   │   └→ Dispatch/Delete/Ticket/Ordnen
      │   ├─ Rejected      │
      │   │   └→ Trash     │
      │   └─ Pending       │
      │       └→ Skip      │
      │                    │
      └─ Unbekannt ────────┘
              │
              ▼
      Notion Page erstelle mit VOLMEM Body
      (Absender, Betreff, Kategorie, ganzi Mail)
              │
              ▼
      Michel öffnet d'Page i Notion
      → list d'Mail → setzt Status
              │
              ▼
      Nöchste 12h-Cron-Run verarbeitets
```

### Notion DB

**DB:** «🛂 Dispatch Approval» — `https://www.notion.so/36881c83f6d98120826ae435125b295a`
**DB-ID:** `36881c83-f6d9-8120-826a-e435125b295a`
**DS-ID:** `36881c83-f6d9-8172-b140-000b297e228b`

### Properties

| Property | Type | Beschrieb |
|----------|------|-----------|
| **Absender** | title | E-Mail-Adresse oder Domain |
| **Topic/Subject** | rich_text | Betreff-Pattern (odr «All» für alli) |
| **Betreff** | rich_text | Originale E-Mail-Betreff |
| **Vorschau** | rich_text | Body-Vorschau |
| **Kategorie** | select | Newsletter / Rechnung / Security / Notification / Other |
| **Ziel-Ordner** | rich_text | Gmail-Label/Folder |
| **Action** | select | Dispatch / Delete / Ticket / Ordnen / Pending / Invoice / Notify / Unsure / PDF Extract |
| **Status** | select | Pending Approval -> Approved -> Rejected |
| **Michels Notiz** | rich_text | Michels Kommentar |
| **Erste Nachricht** | rich_text | Ersti Email-Vorschau (damit Michel entscheide cha) |
| **Häufigkeit** | number | Wie oft scho gfunde |
| **Datum hinzugefügt** | date | Erstellt am |
| **Datum Approve** | date | Approve-Datum |
| **Letzter Dispatch** | date | Letschti Verarbeitig |

### DB abfrage (Notion API)

- **Sender Matching**: Match per Domain (`notifications.ui.com` in Absender) oder per Name-Substring. Nöd per exact Match — ebe wil d'Notion-Title chemisch gsäubert wird (ohne `<`, `>`, `"`).
- **Topic Matching**: Wänn Topic-Pattern leer oder «All» → matcht alli. Suscht: `pattern in subject.lower()`.
- **5-Mail-Limit**: Max 5 unread Mails pro Run (konfigurierbar). Nöd verarbeiteti Mails blibed unread und werde bim nächste Run wider gfunde.
- **Kei Duplikat**: Sobald e Mail per Action verarbeitet isch, wird d'ID i `dispatch_processed.json` gtracked.

### DB abfrage (Notion API)

```bash
source /opt/data/home/.hermes/.env
DS_ID="36881c83-f6d9-8172-b140-000b297e228b"

# Alli Pending Einträg
curl -s -X POST "https://api.notion.com/v1/data_sources/$DS_ID/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"property":"Status","select":{"equals":"Pending Approval"}}}'

# Alli Approved Einträg
curl -s -X POST "https://api.notion.com/v1/data_sources/$DS_ID/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"property":"Status","select":{"equals":"Approved"}}}'
```

### Eintrag approve/reject

```bash
# Approve
curl -s -X PATCH "https://api.notion.com/v1/pages/{PAGE_ID}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties":{"Status":{"select":{"name":"Approved"}},"Datum Approve":{"date":{"start":"2026-05-22"}}}}'

# Reject
curl -s -X PATCH "https://api.notion.com/v1/pages/{PAGE_ID}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties":{"Status":{"select":{"name":"Rejected"}}}}'
```

### DB Cleanup (Maintenance)

Wenn alti Regle-Einträg (ohni Mail-Body) sich aasammlen, chasch si so säubern:

1. **Prüef alli Einträg**: Query all entries from the DS, check `Erste Nachricht` (rich_text field length) AND page markdown (`GET /pages/{id}/markdown` > 100 chars)
2. **Lösch alti Regle**: If `Erste Nachricht` is empty AND no page markdown content AND count=0 → archive via `PATCH /pages/{id} {"archived": true}`
3. **Verify mit Live-Endpoint**: Nach em PATCH immer via `GET /pages/{id}/properties/Status` prüefe — nid via DS Query (die isch gecached!)
4. **Body-Length heuristics**: A `Erste Nachricht` mit ≤50 chars wo wie en Regel tönt (z.B. "Moto Poschung — NUR DE/CH-DE behalte") isch en Regle, kei Mail. Lösche — nöii Mails erstelled frische Einträg mit vollem Content.

### Bestehendi Einträg (Stand: 22.05.2026)

Alti 26 Regle-Einträg (ohni Mail-Body) us de Dispatch-Importe **sin glöscht** (22.05.2026).
Jetzige Stand: 2 Pending-Approval-Einträg (Spotify Datenschutz, LinkedIn Martin Geidl) — beidi mit vollem E-Mail-Body.

Michel macht alles i Notion: Eintrag öffne → Body läse → Status + Action setze.

## Pitfalls

- **Google OAuth expires/revokes periodically** — check `setup.py --check` regularly. If expired, re-run OAuth flow (Steps 3-5 from google-workspace skill)
- **⚠️ CRITICAL: SEND ALL MESSAGES IN HERMES CHAT, never @Radislione_NovaBot** — Michel ONLY interacts in his Hermes chat (chat ID 322663922). The @Radislione_NovaBot bot (TELEGRAM_BOT_TOKEN) exists in a SEPARATE chat with Michel. Inline keyboard messages sent via Bot API are invisible to Michel in his normal chat. The dispatch script (v1.2+) uses text-based commands sent via the cron agent's `send_message` tool (Telethon MTProto, same bot as Hermes) to deliver approval requests directly in Michel's active chat. The Bot API is ONLY used behind the scenes for: checking Michel's text replies (via getUpdates polling), the 5h timeout notification, and callback query acknowledgment. **Never send user-facing messages via @Radislione_NovaBot's sendMessage.**
- **Telegram callback_data is limited to 64 bytes** — Use short_id (first 16 hex chars of Notion UUID) instead of full page_id. Store mapping in `dispatch_idmap.json`.
- **Inline keyboard callbacks persist in Telegram** — `getUpdates` returns OLD callbacks if `offset` isn't managed. The script uses `offset: -100` which may re-process old callbacks; only unique processing via Notion DB status prevents double-processing.
- **Date comparison bug in 5h timeout** — The timeout check must use `now - created >= timedelta(hours=5)`, NOT `created.date() >= now.date()`. Date-only comparison fires for ALL same-day entries regardless of actual age, causing tickets to be created 5 minutes after creation instead of 5 hours. Always compare full datetime objects with timedelta.
- **GL project uses Problem/Question/Suggestion, NOT Task** — Jira GL project only supports IssueTypes: "Problem", "Question", "Suggestion". Attempting issuetype "Task" returns HTTP 400. Always use "Problem" for automated/timeout tickets. To discover valid types: `curl -s -u "${ATLASSIAN_EMAIL}:${ATLASSIAN_TOKEN}" "https://goetschi.atlassian.net/rest/api/3/issue/createmeta/{projectId}/issuetypes" | jq '.values[].name'`
- **State-file cleanup for testing** — Between test runs clear persistent state: `rm -f /opt/data/home/.hermes/scripts/dispatch_processed.json dispatch_cb_offset.txt dispatch_notion_idmap.json dispatch_idmap.json`. Without this the script reuses old offsets/sets and skips already-processed emails.
- **Security alerts = auto GL Ticket** — When subject matches threat/security/alert patterns ("UniFi Threat Detected", "Admin Accessed" etc.) set status to "Approved" + action "Ticket" immediately. Don't wait for Michel's approval on security events.
- **Invoice extraction**: Only process invoices once per email — use a processed_mail_ids log file to avoid duplicates
- **Rate limits**: Gmail API has quota limits (~2500 requests/day). The script fetches max 5 emails per run to stay under quota.
- **Delete vs Archive**: Gmail trash is reversible for 30 days. The script uses `--add-labels TRASH` via the Google API.
- **Sender matching must be fuzzy**: Notion cleans angle brackets and quotes from title fields, so exact sender matches fail. Always match by domain (`domain in absender`) or substring (`absender in sender_str`).
- **Notion DS Query returns CACHED data** — The `/v1/data_sources/{id}/query` endpoint uses a compiled index that can be STALE for up to minutes after a write. When you PATCH a page property (like Status), the DS query may still show the OLD value. **Always verify writes via live endpoints:**
  - Live: `GET /v1/pages/{id}/properties/Status` — real-time property value
  - Live: `GET /v1/pages/{id}` — response's `properties.Status.select.name` is real-time
  - Stale: `POST /v1/data_sources/{id}/query` — can return cached data for seconds-to-minutes
  - During cleanup: PATCH first, verify via live endpoint, THEN query DS for full listing

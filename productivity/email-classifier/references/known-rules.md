# Known E-Mail Rules (Qdrant-backed)

Stand: 26.05.2026 — nach Session #4

## Gelernti Regle (25.05.2026 — Session #2 + #3)

| Sender | Pattern | Action | Michel-Zitat |
|--------|---------|--------|--------------|
| `noreply@tm.openai.com` | OpenAI API Budget-Alert (25% / $1.25 von $5 erreicht) | 🎫 TICKET + Archive (Ordner: "OpenAI Budget") | *"ist wichtig und in eine Ordner Speichern"* |
| `info@ricardo.ch` | Smarthome-Angebote, Elektro-Skateboard, Newsletter | 🗑️ DELETE | *"kannst du immer löschen"* |
| `noreply@locanto.ch` | 63 neui Kontaktanzeige Solothurn, Regionale Kleinanzeigen | 🗑️ DELETE | *"kannst du immer löschen"* |
| `calendar-notification@google.com` | Google Kalender-Benachrichtigige (Morgen-Briefing, Weckruf, Cron-Reminder, Geburtstagsparty-Erinnerig) | 🗑️ DELETE | *"Kalender sind so Rewinder-Mails, die kannst du löschen"* |
| `noreply@dreamstime.com` | Stock Photo Newsletter (June Stock Photo Trends) | 🗑️ DELETE | *"1" (DELETE)* |
| `no-reply@notifications.ui.com` — **Threat Detected** | A network intrusion attempt from X.X.X.X to Y.Y.Y.Y has been detected | 🎫 TICKET + ARCHIVE | *"die darfst du nicht löschen Ticket erstellen bei Goetschi Labs und archivieren"* |
| `no-reply@notifications.ui.com` — **Admin Accessed** (hassio) | Admin: hassio, IP: 10.0.60.167 — Access via console's IP | 🗑️ DELETE | *"bim user hassio unddem darfsch lösche"* |

## Us Session #5 (26.05.2026 — Abend-Batch)

| Sender | Pattern | Action | Michel-Zitat |
|--------|---------|--------|--------------|
| `messages-noreply@linkedin.com` | LinkedIn Job-Empfehlung (Helpdesk bei FTREUSE) | 🗑️ DELETE | *\"1\"* |
| `notifications-noreply@linkedin.com` | LinkedIn Weekly Analytics (Impressions, Performance) | 🗑️ DELETE (Qdrant-Regle) | *\"kurz ins Qdrant speicher und dan löschen\"* |
| `messages-noreply@linkedin.com` | LinkedIn Personen-Empfehlung (Christoph Aeschlimann) | 🗑️ DELETE | *\"1\"* |
| `sanitas-campaigns@sanitas.com` | Sanitas Newsletter (Gehirn fit, Gesundheits-Tipps) | 🗑️ DELETE | *\"Sanitas Newsletter immer löschen\"* |
| `no-reply@notifications.ui.com` — **Threat Detected (Apollo)** | 5x identischi Alerts: Intrusion Apollo e3:c7 → 10.0.40.30 (innert 2 Sek.) | 🎫 TICKET GL-98 (1 Ticket für alli 5) | *\"3\"* |

## Bulk-Identical Threat Handling (neu 26.05.2026)

Wenn **5+ identischi Threat-Mails** innerhalb weniger Sekunde vom **gliiche Thread** chömed:
1. Zeig **nur die ersti** dem Michel mitem Vorschlag TICKET
2. Erstell **1 Ticket** für alli (nid pro Mail)
3. Archivier alli Mails (nume UNREAD-Label entferne, nöd löschä)
4. Within-Batch: Die andere 4 identische Threat-Mails automatisch gliich verarbeite

Bispiel: UniFi Threat Detected — 5 Mails innert 2s, alli glich (Apollo→10.0.40.30) → **1 Ticket GL-98**, alli archiviert.

## Us Session #4 (26.05.2026)

| Sender | Pattern | Action | Michel-Zitat |
|--------|---------|--------|--------------|
| `mailings@mailings.sbb.ch` | SBB Newsletter/Promotion (31DAYS Challenge, Gratis-GA) | 🗑️ DELETE | *"1"* |
| `noreply@steampowered.com` | Steam Wunschlisten-Angebot (RIDE 5 -80%) | 🗑️ DELETE | *"1"* |
| `messages-noreply@linkedin.com` | LinkedIn Empfehlung "Personen die Sie vielleicht kennen" | 🗑️ DELETE | *"1"* |
| `updates-noreply@linkedin.com` | LinkedIn Network Activity Feed (Posts, Reactions, Comments) | 🗑️ DELETE | *"1"* |
| `info@motoposchung.ch` — **Wordfence Weekly** | Wordfence Security Summary (wöchentlich, Blocked IPs, Updates) | 🗑️ DELETE | *"1"* |
| `no-reply@notifications.ui.com` — **Threat Detected 26.05.** | Intrusion 45.9.168.16 → 10.0.40.30 | 🎫 TICKET GL-94 | *"3"* |
| `noreply@tm.openai.com` — **OpenAI Budget 25%** 26.05. | 25% ($1.25) von $5.00 Budget erreicht (org-jAzOrBls9fbK8QgVuVhlQkd5) | 🎫 TICKET GL-95 | *"3"* |

## ✅ Within-Batch Auto-Apply (neu 26.05.2026)

Michel bestätigt: Wenn innert em gliiche Batch e Mail-Type bestätigt isch (gleiche Sender + gliichi Mail-Art), sölled nöchschgliichi Mails **automatisch** verarbeitet werde ohni nochezfroge.

Bispiel us Session #4:
1. Google Kalender "Tokio Schließt" → Michel: DELETE ✅ (ersti, mit Frog)
2. Google Kalender "Tokio Öffnet" → **Auto-DELETE** ohni Frog (gliche Typ)
3. Google Kalender "Besuch bei Denise" → **Auto-DELETE** ohni Frog (gliche Sender-Type)

Gilt NUR für dä Batch — nächschte Batch zeigt wieder + frögt.

## Us Session #1 (22.05.2026)

| Sender | Pattern | Action |
|--------|---------|--------|
| `noreply@spotify.com` | Datenschutz-/Privacy-Updates | 🗑️ DELETE |
| `linkedin.com` | Reaktions-Notifications | 🗑️ DELETE |
| `no-reply@notifications.ui.com` — **Admin Access** | Admin: NOVA/Hermes, IP: 10.0.60.167 | 🗑️ DELETE |
| `no-reply@notifications.ui.com` — **Threat Detected** | Network intrusion attempt detected | 🎫 TICKET (GL-71) |

## Us Session #7 (27.05.2026 — Nomitag-Batch)

| Sender | Pattern | Action | Michel-Zitat |
|--------|---------|--------|--------------|
| `noreply+f9a6790@id.atlassian.com` | Atlassian — Nova-Bot + HenryBot Service Account Löschig | 🎫 TICKET GL-109 | *\"3\"* |
| `security@info.n8n.io` | n8n — Security Update (HIGH: Python Sandbox Escape, MEDIUM: Git Sandbox Bypass) | 🎫 TICKET GL-110 | *\"3\"* (n8n 2.21.7 betroffen, patched 2.21.8) |
| `mia.king@hubdrive.com` | Hubdrive — HR-Software Marketing Newsletter | 🗑️ DELETE | *\"1\"* |
| `no-reply@jsm-notifications.atlassian.net` | Jira — On-Call Rotation Demo | 🗑️ DELETE | *\"1\"* |
| `no-reply-appdev@appstore.amazon.com` | Amazon Appstore — Developer Account Identity Verification (Reminder) | ? | Offe |

**n8n Security-Check (neu):** Bi n8n-Security-Advisories immer Container-Version prüefe: `docker exec <container_name> n8n --version` uf 10.0.60.121. Wenn < patched → TICKET + Upgrade-Empfehlig.

## Us Session #6 (27.05.2026 — Morge-Batch)

| Sender | Pattern | Action | Michel-Zitat |
|--------|---------|--------|--------------|
| `mail.ochsnersport.ch` | OCHSNER SPORT — Newsletter / Werbung (CLUB PRICE: 20% auf alle Schuhe) | 🗑️ DELETE | *"1"* |
| `noreply@github.com` | GitHub — Claude App permission request | 🗑️ DELETE | *"1"* |
| `CloudPlatform-noreply@google.com` | Google Cloud — TLS Certificate Update (ECDSA, Frist 15.06.2026) | 🗑️ DELETE | *"1"* |
| `mail@spectravest.ch` | Spectravest — SpectraNews Investment-Newsletter | 🗑️ DELETE | *"1"* |
| `invoice+statements@mail.anthropic.com` | Anthropic — Claude Pro Subscription Receipt ($21.62) | 🗑️ DELETE | *"1"* |
| `no-reply@mail.anthropic.com` | Anthropic — Welcome to Pro plan (Subscription Confirmation) | 🗑️ DELETE | *"1"* |
| `notifications@link.com` | Link/Stripe — New login from Windows(Edge), Basel | 🎫 TICKET GL-108 | *"im schlimmstenfalls ticket eröffnen"* |
| `info@ricardo.ch` | Ricardo — Favoriten-Endet-Bald (Tesla Model 3 Schublade) | 🗑️ DELETE | *"1"* (confirmiert, bekannti Regle) |

**Link-Login-Investigation (neu 27.05.2026):**
Beim Link/Stripe-Login-Notification isch Timing-Korrelation entscheidend. D'Anthropic Pro-Anmeldung (Welcome + Receipt) isch ZITGLEICH (10:06 MESZ) mit de Link-Login-Notification iitroffe. Stripe-Checkout het de Link-Login triggered. Standort "Basel" = Stripe-Server-Standort, nöd Michels reali IP. Siehe `known-threat-patterns.md` → Stripe/Link.

## Wichtig: Gleiche Sender, anderi Regle!

`notifications.ui.com` het **zwei** komplett unterschiedlichi Mail-Arte:
1. **"Threat Detected"** + Intrusion → ⚠️ TICKET + ARCHIVE
2. **"Admin Accessed"** + hassio/NOVA/Hermes → 🗑️ DELETE

**Merksatz:** Nume dr vollständig Body (nid Snippet/Sender) zeigt was würkli los isch.

## Zusätzliche Regle-Typologie

| Typ | Beispiele | Verhalte |
|-----|-----------|----------|
| 🔔 **Budget/Usage** | OpenAI Budget (tm.openai.com) | Immer TICKET + archiviert, nie glöscht |
| 🛒 **E-Commerce Newsletter** | Ricardo, Dreamstime, Spotify | Immer DELETE (sofern Michel bestätigt) |
| 📣 **Kleinanzeigen** | Locanto | Immer DELETE |
| 🔐 **Security Alert** | UniFi Threat Detected (notifications.ui.com) | Immer TICKET + ARCHIVED |
| 🖥️ **Admin-Login** | UniFi Admin Accessed (hassio/NOVA) | Immer DELETE |
| 📅 **Kalender** | calendar-notification@google.com | Immer DELETE |

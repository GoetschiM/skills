---
name: email-classifier
description: "E-Mail-Dispatch V2: Hermes scannt ALLI unglesene Mails, auto-delete mit etablierte Regle (ungeniert!), zeigt nöii einzeln."
version: 2.7.0
author: hermes
tags: [email, classification, learning, qdrant, obsidian, manual-dispatch]
related_skills:
  - qdrant-knowledge
  - google-workspace
  - obsidian
prerequisites:
  skills:
    - qdrant-knowledge
    - google-workspace
    - obsidian
  credential_files:
    - path: "~/.hermes/google_token.json"
      description: "Google OAuth2 Token (Gmail API)"
    - path: "~/.hermes/.env"
      description: "Umgebungsvariable (Notion, Jira, Telegram)"
---

# 📬 E-Mail Classifier V2 — Einzel-Mail Dispatch mit Inhalt-Check + Obsidian

**🔴 KRITISCHE REGLE (Stand 29.05.2026 — Michels Korrekture kumulativ):**
**1. BATCH-SCAN ZERSCHT, denn auto-apply, denn zeigt Rest einzeln.** Sinn: Alli Mail uf einmal hole (max 10), schnäu scannä, etablierti Regle "ungeniert" aawende (löschä/Ticket erstelle ohni froge), und denn nume die nöie/unbekante einzeln vorzeige. Michel het das am 29.05. explizit so gseit: "bitte schon immer kurz alle anschauen um diese welche du schon kennst und die regel heisst ungeniert löschen kannst du das jedesmal kurz machen und mir wie auch schon jetzt 5 Mail nacheinander zeigen".
**2. GANZE Inhalt läse - nid nume Snippet/Betreff/Absender!** `gmail get` lieferet oft leere Body (`body: ""`), muesch via Raw MIME extrahiere.
**3. KEI Eigeninitiative — AUSSER bei etablierte Security-Regle!** Zitat Michel: "ich möchte nicht, dass du irgendwie selbstständig was entscheidest". Das gilt für Marketing, Newsletter, Kalender, App-Notifications. ABER: s'gid etablierti Security-Rule wo Michel ERWARTET dass mes ohni froge mach (lueg ESTABLISHED AUTO-APPLY RULES). Bi dene: sofort usfüehre + im Chat nur erwähne was passiert isch.
**4. Gliiche Sender = nid gliichi Mail-Art!** `notifications.ui.com` sendet Threat (TICKET) UND Admin-Login (DELETE). Nume vollständige Body zeigt's.
**5. Within-Batch Auto-Apply (26.05.):** Wenn Michel innert em gliiche Batch e Typ bestätigt het (gleiche Sender + gliichi Mail-Art), dörfsch du ali nöchschgi identische Mails automatisch verarbeite ohni nochezfroge. Bispiel: Google Kalender "Tokio" bestätigt als DELETE -> nöchschti Tokio-Mail automatisch gliich. Das gilt NUR für dä Batch - nöd für nöchi Batch. Nöchi Batch zeigt wieder + frögt.

## ✅ ESTABLISHED AUTO-APPLY RULES (kei Nachfrog nötig — Michel erwartets "ungeniert!")

Selli Pattern si so etabliert, dass mer sie OHNI Froge "ungeniert" usfüehrt (Michels Wort am 29.05.2026). D'Mail wird im Chat nur im Batch-Überblick erwähnt, nid einzeln nochegfragt.

| Pattern | Aktion | Merksatz |
|---------|--------|----------|
| UniFi Threat Detected (notifications.ui.com, Body "intrusion attempt") | 🎫 TICKET GL-xxx + Archive + Deep Analysis | Security — immer Ticket |
| UniFi Admin Accessed → Source = hassio (NOVA) | 🗑️ DELETE | Bekannti Admin-Aktion |
| Ricardo Treffer (info@ricardo.ch) | 🗑️ DELETE | "ricardo/locanto/dreamstime=DELETE" |
| Locanto (info@locanto.ch) | 🗑️ DELETE | "ricardo/locanto/dreamstime=DELETE" |
| Dreamstime | 🗑️ DELETE | "ricardo/locanto/dreamstime=DELETE" |
| LinkedIn (security-noreply@linkedin.com) | 🗑️ DELETE | Dispatch Regle etabliert |
| Kalender/Calendar-Notifications (google.com) | 🗑️ DELETE | Dispatch Regle etabliert |
| OpenAI Budget-Mails | 🎫 TICKET GL-xxx + Archive | Budget-Überwachig |
| Anthopic | 🗑️ DELETE | Nur Abo-Bestätigige |
| Spectravest | 🗑️ DELETE | Dispatch Regle |
| Hubdrive | 🗑️ DELETE | Dispatch Regle |
| n8n Security | 🎫 TICKET GL-xxx | Security Update-Meldig |
| Decathlon (noreply-ch@service.decathlon.com) | 🗑️ DELETE + label "Shopping" | Welcome/onboarding-Mails (30.05.2026) |

**Wichtig:** Alli andere Mails (Marketing, Newsletter, App-Notifications, Rechnige, System-Mails, unbekannti Absender) zeige + froge wie gwohnt. D'Regle #2 (Kei Eigeninitiative) gilt für die.

## 🔁 Workflow (29.05.2026 — Batch-Scan-First)

### 1. Michel seit: *"Hermes, prüf mal d'Mails"* oder *"EMS prüfen"*
### 2. Hermes holt **ALLI unglesene Mails** us Gmail (max 10 uf eimal)
### 3. 📖 Batch-Scan: für JEDI Mail vollständige Inhalt läse (zwingend!)
   a) **Gmail Search** → Liste vo allne unglesene Mails hole
   b) Für jedi einzelni: vollständige Body via `gmail_get` extrahiere
   c) **NIE nume Snippet/Betreff beurteile** — gleiche Sender = nid gliichi Mail-Art!
### 4. Kategorisiere:
   a) **ESTABLISHED AUTO-APPLY** → sofort usfüehre ohni Froge ("ungeniert!")
   b) **Within-Batch Auto-Apply** → wenn im gliiche Batch scho entschide (gleiche Sender + gliichi Mail-Art)
   c) **Nöi/Unbekannt** → für Einzel-Vorzeige merke
### 5. Batch-Ergebnis Michel zeige:
   - **Auto-Apply Teil:** Churzi Liste vo de automatisch erledigte Mails
   - **Nöi/Unbekannt:** Jedidi einzeln mit Tabelle + Optione
### 6. Für jedi nöii Mail einzeln:
   - Mail in Tabelle präsentiere (Von, Betreff, Datum)
   - **Vollständige Inhalt** (nid nume Snippet!)
   - Optione: 1️⃣ 🗑️ DELETE, 2️⃣ 👀 SHOW, 3️⃣ 🎫 TICKET, 4️⃣ 📄 PROCESS
   - **NEU: "🔖 merken und löschen"** — Wenn Michel \"merken\" odr \"save first\" vor DELETE seit, denn: (a) Obsidian-Notiz in 2-Notizen/ erstelle, (b) Qdrant store mit type=note, (c) denn trashing. Bispel: Google Maps Local Guides Weekly am 29.05.\n   - Michel entscheidet → sofort usfüehre\n### 7. ⚡ Within-Batch Auto-Apply: Wenn Michel innert em gliiche Batch e Typ bestätigt het (gleiche Sender + gliichi Mail-Art), dörfsch du ali nöchschgi identische Mails automatisch verarbeite ohni nochezfroge. Gilt NUR für dä Batch.
### 8. Regle in Qdrant speichere (NUR vom Michel explizit bestätigte Entscheid)
### 9. Dispatch abschlüsse mit **"TT"** (Muss! Michel erwartet's)

**🔴 KRITISCH:**
- Batch-Scan = alli uf einmal hole. Entscheid = immer einzeln (usser auto-apply).
- Auto-Apply = NUR für ESTABLISHED AUTO-APPLY RULES + Within-Batch.
- Alles andere = zeige + froge. Kei Eigeninitiative!
- **TT am Endi nid vergässe! (Michel erinnert am 29.05.)**

## 📋 Konkreter Chat-Flow (mit vollständigem Inhalt)

```
🧠 Hermes: 📬 Mail #1/5
| | |
|---|---|
| **Von** | UniFi OS, UDM Pro <no-reply@notifications.ui.com> |
| **Betreff** | UDM Pro: Threat Detected 🚨 |
| **Datum** | Heute, 04:11 Uhr |

**Vollständige Inhalt:**
```
Notification - A network intrusion attempt
from 45.9.168.16 to 10.0.40.30 has been detected.

If you need additional help, please visit
https://account.ui.com/requests
Regards, The Ubiquiti team
```

───────────────
❓ Was söll ich mache?
  1️⃣ 🗑️ DELETE
  2️⃣ 👀 SHOW (meh Details)
  3️⃣ 🎫 TICKET (Jira-Issue)
  4️⃣ 📄 PROCESS (archive/speichere)

🫵 Michel: "3"

🧠 Hermes: ✅ GL-90 erstellt + archiviert
────────────────
📬 Mail #2/5
...
```

## 🔮 Wissensquellen (Prüf-Reihefolg)

| Schritt | Quelle | Methode | Zweck |
|---------|--------|---------|-------|
| 1 | Qdrant (Sender) | `qdrant_knowledge.py search memory "EMAIL RULE: <sender>"` | Domain-basierti Regle |
| 2 | Qdrant (Inhalt) | `qdrant_knowledge.py search memory "<subject + snippet>"` | Semantischs Matching |
| 3 | Obsidian | `obsidian` skill → search notes über Absender/Thema | Kontext (z.B. "Vertrag gekündigt") |
| 4 | Memory (persistent) | `session_search` | Korrekturen us frühnere Sessions |

## 📦 Speicher-Format (Qdrant)

```bash
cd /root/.hermes/skills/knowledge-management/qdrant-knowledge && \
python3 scripts/qdrant_knowledge.py store \
  "EMAIL RULE: <sender> — <pattern/muster> => <ACTION>. \
   Michel: '<zitat>' Source: <date> Context: <zusatzinfo>" \
  --type rule --source user
```

```bash
cd /root/.hermes/skills/knowledge-management/qdrant-knowledge && \
python3 scripts/qdrant_knowledge.py store \
  "EMAIL RULE: <sender> — <pattern/muster> => <ACTION>. \
   Michel: '<zitat>' Source: <date> Context: <zusatzinfo>" \
  --type rule --source user
```

**Zuesatz-Info im Context-Feld:**
- Obsidian-Fundstell: "ObsidianNote: 2-Kontakte/Telekom.md"
- Inhalt-Match: "Subject enthielt 'Rechnung' UND Body enthielt 'CHF'"
- Absender-Domain: "telekom.de (never known before)"

## ✅ Batch-Erfolg (22.05.2026 — V1 noch Batch)

| # | Mail | Entscheid | Resultat |
|---|------|-----------|----------|
| 1 | Spotify — Datenschutz-Update | DELETE | 🗑️ Trashed |
| 2 | LinkedIn — Martin Geidl Reaktion | DELETE | 🗑️ Trashed |
| 3 | UniFi Admin Access (NOVA) | DELETE | 🗑️ Trashed |
| 4 | UniFi Admin Access (Hermes) | DELETE | 🗑️ Trashed |
| 5 | UniFi Threat Detected 🚨 | TICKET | 🎫 GL-71 created |

**Regle gelernt us Batch #1:** Siehe `references/known-rules.md`

## 🔄 Lifecycle einer Regle

| Stufe | Vertraue | Verhalte |
|-------|----------|----------|
| 🆕 Neu | 0x | Mail zeige + "❓ Was söll ich mache?" (kei Vorschlag) |
| 🔄 Wiederholig | 1-2x | Zeige + Vorschlag ("laut Regle: DELETE?") |
| 🗑️ Bewährt | 3x+ | Zeige + Vorschlag + "✅ Regle bestätigt: Aktiv vorschlage?" |
| 🚨 Security Etabliert (ESTABLISHED AUTO-APPLY) | Bekannt | **Auto-Apply ohne Froge!** Ticket erstelle, archivier, erwähn im Chat. Michel erwartet's — lueg ESTABLISHED AUTO-APPLY RULES. |

**Regle für alli nöd-Security-Mail (Marketing, Newsletter, Kalender, Apps):** Au 100x bestätigti Regle = MICHEL entscheidet immer. Nüt ohni sis OK.
- Einzige Chat: **Telegram 322663922**
- Stop-Befehl: *"dispatch stopp"* → sofort alles pausiere + Meldig

## 📋 Konkrete Befehle

### Mail-Details (Vollständige Inhalt — 3 Methodä)

**Methode A: Einfachi Mails (meistens gnueg)**
```bash
GAPI="python3 /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI gmail get <id>
# Output: {id, from, subject, body: "vollständiger Text..."}
```

**Methode B: Leere Body (`body: ""` — z.B. UniFi Mails)**
Die Google-api.py git leere Body zrugg. Muesch via Raw MIME extrahiere:
```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email import policy
from email.parser import BytesParser
import base64

TOKEN_PATH = '/root/.hermes/google_token.json'
creds = Credentials.from_authorized_user_file(TOKEN_PATH)
if not creds.valid:
    creds.refresh(Request())
service = build('gmail', 'v1', credentials=creds)
msg = service.users().messages().get(userId='me', id='MSG_ID', format='raw').execute()
raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
mime_msg = BytesParser(policy=policy.default).parsebytes(raw)

body = ''
if mime_msg.is_multipart():
    for part in mime_msg.walk():
        if part.get_content_type().startswith('text/plain'):
            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
            break
else:
    body = mime_msg.get_payload(decode=True).decode('utf-8', errors='replace')
print(body)
```

**Methode C: Attachments extrahiere**
Lueg `google-workspace` Skill → Gmail Attachments (raw MIME)

### Mail-Details (Inhalt)
```bash
$GAPI gmail get <id>
```

### Inhalt analysiere + Entscheide
```bash
# Qdrant-Suche über Inhalt
cd /root/.hermes/skills/knowledge-management/qdrant-knowledge && \
python3 scripts/qdrant_knowledge.py search memory "<Betreff> — <Snippet>"

# Obsidian-Suche (über obsidian skill)
# skill_view("obsidian") nutze für search
```

### Mail verarbeite: Gmail REST API direkt (empfohlen — funktioniert immer)

**ACHTUNG:** Es git KEI `gmail_trash` / `gmail_modify` Tool im Google MCP Server. Lösch-Operatione müend via Gmail REST API direkt mit OAuth-Token usgeführt werde.

```bash
# 1. Token refreshe (us google_token.json)
TOKEN=$(curl -s -X POST 'https://oauth2.googleapis.com/token' \
  GOOGLE_CLIENT_SECRET_2](
  -d 'refresh_token=GOOGLE_REFRESH_TOKEN' \
  -d 'grant_type=refresh_token' | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))")

# 2a. Einzelni Mail träshe
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/MAIL_ID/trash"

# 2b. Ganse Thread träshe (alli Mails im Thread uf ei Mal!)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/threads/THREAD_ID/trash"

# 2c. Als gläse markiere (remove UNREAD label)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/MAIL_ID/modify" \
  -d '{"removeLabelIds": ["UNREAD"]}'

# 2d. BatchDelete (permanent! — nur wenn sicher)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/batchDelete" \
  -d '{"ids": ["ID1", "ID2", ...]}'
```

**Hinweis:** `client_id`, `client_secret` und `refresh_token` sind fix für die Google OAuth App. Wenn de Token abgloffe isch (invalid_grant), lueg Recovery-Shortcut under Pitfalls (MCP Server Token kopiere).

### Mail verarbeite (Alt: Google API Script — Token abglofe Stand Mai 2026)

```bash
GAPI="python3 /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
# DELETE (Trash)
$GAPI gmail modify <id> --add-labels TRASH
# Als glese markiere
$GAPI gmail modify <id> --remove-labels UNREAD
```

### Regle in Qdrant speichere
```bash
cd /root/.hermes/skills/knowledge-management/qdrant-knowledge && \
python3 scripts/qdrant_knowledge.py store \
  "EMAIL RULE: <sender> — <pattern> => <ACTION>. Michel: '<zitat>' Source: <date>" \
  --type rule --source user
```

### Regle sueche
```bash
cd /root/.hermes/skills/knowledge-management/qdrant-knowledge && \
python3 scripts/qdrant_knowledge.py search memory "EMAIL RULE: <sender>"
```

### Jira-Ticket (für Security)
```bash
cat > /tmp/ticket.json << 'JSONEOF'
{
  "fields": {
    "project": {"key": "GL"},
    "issuetype": {"name": "Problem"},
    "summary": "Security Alert: <Betreff>",
    "description": {
      "type": "doc", "version": 1,
      "content": [
        {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Auto-generated from Email Dispatch"}]},
        {"type": "paragraph", "content": [{"type": "text", "marks": [{"type": "strong"}], "text": "Subject:"}, {"type": "text", "text": " <Betreff>"}]},
        {"type": "paragraph", "content": [{"type": "text", "marks": [{"type": "strong"}], "text": "From:"}, {"type": "text", "text": " <Absender>"}]}
      ]
    }
  }
}
JSONEOF
source /opt/data/home/.hermes/.env
curl -s -u "michelgoetschi@gmail.com:${ATLASSIAN_TOKEN}" \
  -X POST "https://goetschi.atlassian.net/rest/api/3/issue" \
  -H "Content-Type: application/json" \
  -d @/tmp/ticket.json
```

## 🔍 Security Notification Investigation Protocol (non-UDM)

**Wann?** Wenn en Security-Notification-Mail iitrifft, wo KEI UDM Threat isch — z.B.:
- Login-Benachrichtigunge (Link, Google, GitHub, Stripe)
- Passwort-Änderige
- Neue Device-Logins
- App-Berechtigungs-Akzeptierige

### Untersuchigstechnike

**1. Timing-Korrelation (wichtigsti Methode!)**
Check OB anderi Mails ZUM GLIICHE ZITPUNKT (selbe Minute!) iitroffe sind:

```python
# Suche nach Mails mit ähnlichem Timestamp
results = service.users().messages().list(
    userId='me', 
    q='is:unread after:2026/05/27 before:2026/05/28',
    maxResults=50
).execute()
```

**Erfahrigswert:** Wenn en Login-Notification ZITGLEICH mit ere Bezahl-Bestätigung / Subscription-Mail / OAuth-Flow-Mail iitrifft, isch de Login warschinlich **durch de Zahligs- oder OAuth-Flow triggered** worde — nöd en unbefugte Zugriff.

**2. Absender-Check (genau hieluege)**
- Stripe/Link verwended `notifications@link.com` für Login-Notifications
- Stripe-Server-Standort (z.B. Basel) isch **NID** de reali User-Standort — das isch de Server wo de Stripe-Checkout usegführt het
- Stripe Event ID (im `X-Stripe-EID`-Header) cha zur Traceability bruucht werde

**3. Geolocation-Fehler erkennen**
- Stripe/Link zeigt Server-Standort, nöd End-User-IP
- "Windows (Edge)" als Device chan en **Headless-Browser/Selenium** vo Stripe si, nöd en echte Browser
- OTP-Verifizierung heisst: OTP isch as GEGEBENI Nummer gschickt worde — das chan au en automatisierte Stripe-Webhook si

**4. Entscheid finde**
| Szenario | Entscheid |
|----------|-----------|
| Login-Notification + kei korrelierendi Aktivität | 🎫 TICKET — mögliche Account-Takeover |
| Login-Notification + zeitglichi Subscription-Zahlig | 📄 TICKET (zur Doku) + Account selbst prüefe lah – warschinli Stripe-Checkout-Trigger |
| Login-Notification + Michel sait "isch nid normal" + kei Korrelation | 🎫 TICKET (Security-Vorfall) |

**5. Doku im Ticket (wenn TICKET)**
Im Ticket-Kommentar dokumentiere:
- Timing: Welchi andere Mails sind zur gliiche Ziit iitroffe?
- Korrelation: Subscription / Payment / OAuth-Flow?
- Stripe Event ID (us Header `X-Stripe-EID`)
- Geolocation-Hinweis: "Server-Standort, nöd User-Standort"
- Empfehlig: Account uf app.link.com/activity prüefe

**6. Account-Prüef-Schritt (Michel mitdeile)**
Nach Ticket-Erstellig: Michel sage, dass er selber uf de entsprechende Plattform (link.com, github.com, etc.) d'Login-Aktivität prüefe söll — de Security-Check cha mer nid automatisierte, will mir d'Passwörter/sensitive Sitzige nid hei.

## 🔍 UDM Threat Deep Analysis Protocol

**Wann?** Nachdem en UDM Threat Detected Mail verarbeitet + e Jira-Ticket erstellt worde isch (via email-classifier flow). De Michel erwartet denn en tiefgehendi Analyse im Ticket.

### Analyse-Schritte (im Ticket-Kommentar dokumentiere)

**1. Externi IP (Source) prüefe:**
```bash
curl -s https://ipinfo.io/<IP>/json | python3 -m json.tool
```
→ Hostname, Standort, AS-Organisation notiere

**2. Interni IP (Target) identifiziere:**
- Ping test: `ping -c 2 -W 2 <IP>` — isch Host erreichbar?
- Portscan (nmap): `nmap -sT -P0 -p 22,80,443,8080 <IP>` — was lauft druff?
- ARP-Tabelle: `ip neigh show` (nume gliichs Subnetz)
- Home Assistant: `curl -s http://10.0.60.111:8123/api/states` — Entitäten mit IP checke
- SSH zu bekannte Hosts: root@10.0.60.167 (Louis_one_13) oder 10.0.60.121

**3. Risikobewertig:**
- UDM IDS/IPS het Traffic blockiert → Grundschutz aktiv ✅
- Externi IP-Typen:
  - CDN-Perf-Test (cdn-perfprod.com, Budapest) → FALSE POSITIVE 🟢
  - Bekannte Scanner-Hosts (Shodan, Censys) → Niedrig 🟡
  - Unbekannt/neu → Mittel 🟠
- Interni Source-IPs (z.B. 10.0.20.x IoT → 10.0.10.x Server) → **Vermuetlig HA-Kommunikation** 🟠 → Beobachte, nid schliesse
- Interni Source-IPs, die IMERNOCH in mehrere Incidente uftauche (z.B. 10.0.20.45) → Beobachtigswürdig 🔴

**4. Ticket-Kommentar mit strukturierte Analyse:**
Format:
```
🔍 TIEFGEHENDE UDM THREAT ANALYSE

📅 Incident: <Datum+Zeit>
🔹 Source: <IP> (<Hostname/Standort/AS>)
🔹 Target: <IP> (<VLAN/Identität>)
🔹 Detected by: UDM Pro IDS/IPS

─── EXTERNE IP ANALYSE ───
• Hostname: <ipinfo hostname>
• Standort: <ipinfo city/region/country>
• AS: <ipinfo org>
• Typ: <Klassifizierung>

─── INTERNES TARGET ───
• Ping: ✅/❌
• Ports: <Ergebnisse>
• Gerätetyp: <Vermutung>

─── RISIKOBEWERTUNG ───
⚠️ WAHRSCHEINLICHKEIT: HOCH/MITTEL/NIEDRIG
• <Begründung>

**Bekannti False-Positive-Quelle:**
`cdn-perfprod.com` (Hostname hu*.eu.node.cdn-perfprod.com, AS211619 MAXKO d.o.o., Budapest) — CDN Performance Test Node. Diese Server scannen zufälligi IP-Range für Latenzmessige. Immer FALSE POSITIVE 🟢. Ticket cha direkt gschlosse werde.

─── EMPFEHLUNG ───
1. <Aktion 1>
2. <Aktion 2>

### 🔐 Link/Stripe-Login-Notification (Verdacht: Stripe-Checkout-Trigger)

Wenn e **Link (Stripe)**-Login-Notification chunnt und Michel seit er heb nid ignloggt:
1. **Timing prüefe:** Gits zitgliichi Aktivitäte (Zahlig, Abo-Bestätigig) wo Stripe-Checkout triggered het?
2. **Standort relativ:** "Basel" isch de Stripe-Server-Standort (nöd Michels reali IP)
3. **Wenn Payment-Checkout-Match:** Ticket erstelle + d'Korrelation dokumentiere (False-Alarm-Verdacht)
4. **Wenn kei Match:** Ticket + Empfehlig: Link-Account prüefe + Passwort ändere

**Leitfrag:** Isch d'Mail zitglitch mitere Transaktion (Anthropic/Zahlungsbestätigig) iitroffe? Wenn ja → False Positive (Stripe-Trigger).

**5. Ticket schliesse (bi FALSE POSITIVE):**
Wenn d'Analyse ergit, dass es en False Positive isch (z.B. CDN-Performance-Tester, interni HA-Kommunikation):
1. Kommentar mit vollständiger Analyse im Ticket hinterlegge
2. Jira Transition: `Beginnen` (ID **11** → In Arbeit), denn `Vollständig` (ID **21** → Erledigt)
   ```bash
   # Schritt 1: In Arbeit
   curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN" \
     -X POST "https://goetschi.atlassian.net/rest/api/3/issue/GL-XXX/transitions" \
     -H "Content-Type: application/json" \
     -d '{"transition": {"id": "11"}}'
   # Schritt 2: Erledigt
   curl -s -u "$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN" \
     -X POST "https://goetschi.atlassian.net/rest/api/3/issue/GL-XXX/transitions" \
     -H "Content-Type: application/json" \
     -d '{"transition": {"id": "21"}}'
   ```
```

5. **Verwandti Incidents checke:**\nGlichi externi IP in andere Tickets? Glichi interni Source-IP? → Cross-Reference im Kommentar erwähne.\n\n### 🧠 Interni Threat-Quelle (IoT→Server VLAN) — möglicherwiis legitimer Traffic

Wenn en interni IP usem IoT-VLAN (10.0.20.x) en Server-VLAN-Host (10.0.10.x) adresiert, **chönt das legitimi HA-Kommunikation si** — IoT-Gerät (Shelly, Kamera, Sensor) wo uf Home Assistant zugreift. UDM IDS markiert das fälschlicherwiis als Threat.

**Merksatz:** Nid jede interni Threat isch würkli bösartig. Wänn gliichs Gerät widerhollt uftaucht → via UDM MAC-Tabelle identifiziere. Suscht: Ticket erstelle + beobachte.

### 🔄 Bulk-Identical Threat Handling (5+ Mails, ei Ursache)\n\nWenn **mehreri identischi Threat-Mails** innert paar Sekunde vom gliiche Thread chömed:\n\n1. Zeig **nur 1 Mail** dem Michel (repräsentativ, mit Hiwis uf d'Anzahl)\n2. Erstell **1 Ticket** für alli (nid pro Mail!) — Ticket-Summary erwähnt \"5x in 2s\"\n3. Archivier alli Mails (`--remove-labels UNREAD`, nöd TRASH)\n4. Within-Batch Auto-Apply: Die andere identische Threat-Mails automatisch gliich\n\n**Grund:** Das sind meischtens NMAP-Scan-Welle oder IDS-Bursts vom gliiche Uslöser. Mehri Tickets bringed nüt, verwirred nume.\n\nBeispiel: 5x \"UDM Pro: Threat Detected — Apollo→10.0.40.30\" innert 2s → **1 Ticket GL-98**, alli archiviert.\n\nSiehe au `references/known-rules.md` → Bulk-Identical Threat Handling.

Siehe au `references/known-threat-patterns.md` → Bekannti Threat-Patterns (cdn-perfprod False Positive, interni HA-Kommunikation) + Jira Workflow Transition-IDs.

Siehe au `references/udm-threat-analysis-2026-05-26.md` für es vollständigs Analyse-Beispiel us de Session mit **externer Quelle**, und `references/internal-threat-analysis.md` für **interne Quelle** (Apollo/Kali → IoT-VM).

**Bekannti False-Positive-Pattern:** `references/known-threat-patterns.md` — CDN-Performance-Test-Nodes (cdn-perfprod.com), Shodan/Censys-Scanner, und anderi harmlosi Internet-Rausche-Quelle. Immer vor Ticket-Erstellig prüefe obs en bekannte False Positive isch.

Siehe au `references/false-positive-cdn-test-nodes.md` — bekannti CDN-Performance-Test-Nodes wo falschi Alarme uslöse.

Siehe au `references/apollo-self-scan-threat-pattern.md` — wenn Hermes selber via Kali-Container internal scannt, generiert das UDM-False-Positives ("Apollo e3:c7"). Immer DELETE, nie Ticket.

### Referenzierte Tools
- `ipinfo.io` — Externi IP-Geolokalisierig (kein API-Key nötig für Basis-Abfrage)
- `nmap` — Portscan (uf Kali-Container 10.0.60.156 installiert)
- `ping` — Host-Erreichbarkeit
- Home Assistant API — IoT-Geräte-Identifikation
- SSH → 10.0.60.167 (Asterisk/Nova), 10.0.60.121 (Dokploy) — ARP/Netzwerk-Checks

## ⚠️ Pitfalls

- **GOOGLE TOKEN EXPIRED: Beidi Wege blockiert.** Beidi Methodä (Google API via google_token.json + Himalaya IMAP) sind am gliiche `google_token.json`-File bunde. Himalaya brucht `/root/.local/bin/google-access-token` als IMAP-Password-Command — das nutzt di gliichi OAuth-Auth. Wenn eine failt (`invalid_grant: Token has been expired or revoked.`), failt beidi.

  **RECOVERY-SHORTCUT (seit 29.05.):** Bevor du de Michel mit re-auth beläschtigsch — prüef ob de Google MCP Server Token no funktioniert. De MCP Token (gliichi OAuth App, selbi client_id) wird im Volume `/opt/data/google-mcp-server/data/token.json` ghalte und het en frische refresh_token. Wenner no gültig isch:
  ```bash
  # 1. MCP Token refreshe und kopiere
  python3 -c "
  from google.auth.transport.requests import Request
  from google.oauth2.credentials import Credentials
  creds = Credentials.from_authorized_user_file('/opt/data/google-mcp-server/data/token.json')
  if not creds.valid and creds.refresh_token:
      creds.refresh(Request())
  import json
  with open('/opt/data/google-mcp-server/data/token.json', 'w') as f:
      f.write(creds.to_json())
  " 2>&1
  cp /opt/data/google-mcp-server/data/token.json /root/.hermes/google_token.json
  ```
  **Das spartet de ganze Browser-Auth-Flow** wil beidi Token di gliichi OAuth App nutzed (client_id: `983053334079-...`). Nur wenn au de MCP Token expired isch: denn starte de re-auth flow (lueg google-workspace Skill Steps 3-5). Fix: Browser-Auth-URL generiere, Michel lost sich i, git Redirect-URL zrugg.
- **🔴 Batch-Scan ≠ Batch-Entscheid.** Alli Mail uf einmal hole + überblicke = okay. Entscheide immer einzelig (d'usser auto-apply). NIE mehreri Mail ohni Michels Zustimmig löschä wo nid explizit etabliert sind.
- **"ungeniert löschen"** = NUR für ESTABLISHED AUTO-APPLY RULES. Kei Eigeninitiative bi nöie/unbekante Sender!
- **TT am Endi nid vergässe** — Michel erinnert am 29.05.2026 explizit dra.
- **Within-Batch Multi-Threat: Identischi Security-Alerts (>2 in <10s) = 1 Incident** — Wenn 5x identischi "Threat Detected"-Mails innerhalb von 2 Sekunden chömed (wie GL-98 am 26.05.), zeig EINE devor und erwähn wie viel total. Erstell EIN Ticket, archivier alli. Das sind NMAP-Scan-Wellen, kein Incident-Flood. — z.B. Google Kalender "Tokio" nach erschter Bestätigig. Aber nöd für anderi Kalender-Mail-Type, nöd für anderi Sender, nöd über Batch-Gränze weg. Gliiche Sender mit anderem Inhalt (UniFi Threat vs. Admin Access) = immer nochefroge.
- **🔴 GANZE Inhalt läse, nid nume Snippet/Betreff/Absender** — Michel bestoht druf. Gliiche Sender (z.B. notifications.ui.com) chan Threat ODER Admin-Login si. Nume dr vollständig Body zeigt was würkli los isch.
- **🔴 Kei Eigeninitiative — AUSSER bei ESTABLISHED AUTO-APPLY RULES** — "Ich möchte nicht, dass du irgendwie selbstständig was entscheidest." Das gilt für Marketing/Newsletter/Kalender/Apps/Notifications. ABER: UniFi Threat = immer TICKET + Deep Analysis, das erwartet Michel ohni Froge (lueg ESTABLISHED AUTO-APPLY RULES).
- **Raw MIME nötig bi leere Body** — `gmail get` lieferet `body: ""` bi Mails wo via Template/Variable gsändet sind (UniFi, System-Mails). Muesch via Python format='raw' + BytesParser extrahiere (Methode B under Mail-Details).
- **GL Jira: IssueType "Problem"** — NIE "Task" (GL-Projekt erlaubt nur Problem/Question/Suggestion)
- **Jira ADF Format** für description zwingend — API v3 akzeptiert kein Markdown. Immer via Datei senden (`-d @/tmp/ticket.json`)
- **Inhalt-Check isch wichtig** — gleiche Absender, anderes Thema = als nöi behandlet
- **Obsidian immer prüefe** — es chönt en Notiz geh: "Telekom Vertrag endet 31.03."
- **Qdrant-Suche isch semantisch** — "Threat Detected" findet au "Intrusion Attempt"
- **Security Alerts = immer Ticket-Vorschlag** — Threat/Intrusion nie löschä, au wenn Michels OK no usstoht
- **Stop-Befehl beachte** — "dispatch stopp" → sofort pausiere
- **Jira API Endpunkt:** `/rest/api/2/search` und `/rest/api/3/search` sind TOT (410/200+leer). Korrekt isch NUR `/rest/api/3/search/jql` (GET odr POST mit `jql=`). Git's Problem mit 0 Tickets → zersch d'API-URL prüefe!
- **Jira API `total`-Feld:** `/rest/api/3/search/jql` lieferet korrekt `total: N` zrugg. Wenn `total: None` chunnt, isch d'JQL-Syntax falsch odr de Endpunkt falsch. Nöd uf `isLast` verlah. 

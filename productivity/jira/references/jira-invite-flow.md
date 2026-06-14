# Atlassian Jira Invite & Account Flow

> Erfahrungen us em 23.05.2026 — hermes@radislione.net iilade zu goetschi.atlassian.net

## Wie en Invite funktioniert

1. **Michel (Admin)** gaht i Jira Admin → Users → Invite user → git `hermes@radislione.net` ii
2. **Atlassian schickt E-Mails** vo `noreply@po.atlassian.net` / `noreply+*@id.atlassian.com`:
   - "You've been invited to Jira Service Management" (Willkomme)
   - "[Action required] Michel G. invited you to Jira 🚀" (Accept invite)
   - "You've been made a user access admin" (Empfangeni Rächt)
3. **Tracking-Redirect:** `track.atlassian.com/tracking/{uuid}` → 302 → `id.atlassian.com/signup/invite?signature={JWT}&infoCode=invitedUser&...`
4. **Signup-Page** isch e **React SPA** (id-frontend.prod-east.frontend.public.atl-paas.net)
   - Bietet Login (falls scho Account) oder Account-Erstellig (falls neue Email)
   - Title: "Log in with Atlassian account"
5. **Account-Erstellig** brucht:
   - Email (pre-filled)
   - Passwort (vom Invite-Empfänger)
   - JavaScript-Browser (React SPA)

## Bekannti Limitatione (Stand Mai 2026)

### 1. Kei reini REST-API für Invite-Accept

Atlassian stellt **keine öffentliche REST-API** zur Verfüegig, um en Invite programmatisch z'acceptiere (ohni Browser).

| Endpoint | Status | Bemerkig |
|----------|--------|----------|
| `POST id.atlassian.com/api/v1/invite/accept` | HTTP 200 | Lieferet SPA-HTML, kei JSON — nüt zum verarbeite |
| `POST api.atlassian.com/admin/v1/orgs/{org}/invitations/accept` | HTTP 401 | Brucht Auth-Token vom eingloggte User |
| `POST goetschi.atlassian.net/rest/api/3/user` | HTTP 401 | Brucht Jira-Admin-Auth (Cookie oder Basic Auth) |

### 2. Browser-Pflicht

D'Signup-Page uf `id.atlassian.com` isch es **React SPA** (Client-seitig presse). Ohni JavaScript-Browser:
- **curl + Python requests** → chunt nume HTML-Shell ( `<div id="root"></div>` + CSS/JS-Bundles)
- **Playwright headless_shell** (23.05.2026 getestet) → seit "Log in with Atlassian account" aber rendert **0 interactive elements** → Browser-Detection / Antibot-Mechanismus
- **Browserless (full Chromium)** → unbekannt (isch zum Test-Zitpunkt nöd gstartet gsi)

✅ **Nur echte Browser** (oder Browserless mit vollem Chromium, nöd headless_shell) chönnd das rendere.

### 3. Was stattdesse

**Option A:** De **Admin** (Michel) acceptiert d'Invite im Jira Admin Panel:
   → Admin → Users → Pending invites → Accept für hermes@radislione.net

**Option B:** De **Invite-Empfänger** (Hermes) macht's über e Browser + git es Passwort a.

**Option C:** De **Admin** fügt de User via REST API direkt zue (ohni Invite):
   ```bash
   curl -s -X POST -u "$AUTH" \
     -H "Content-Type: application/json" \
     "https://goetschi.atlassian.net/rest/api/3/user" \
     -d '{"emailAddress": "hermes@radislione.net", "products": []}'
   ```
   → Brucht **Admin-Rechte** + **Basic Auth** (API-Token vom Admin).
   → Type: "Customer" oder "Service Desk" etc.

### 4. Jira REST API User Endpoints (Admin)

Mitem **Admin-API-Token** (vom guetschi.atlassian.net-Admin) chama User verwalte:

**User suche:**
```bash
curl -s -u "$AUTH" "https://goetschi.atlassian.net/rest/api/3/user/search?query=hermes"
```

**User zu Jira zuefüege (ohni Invite):**
```bash
curl -s -X POST -u "$AUTH" \
  -H "Content-Type: application/json" \
  "https://goetschi.atlassian.net/rest/api/3/user" \
  -d '{"emailAddress": "hermes@radislione.net", "displayName": "Hermes Agent", "notification": true}'
```

**Product Access zuewise:**
```bash
curl -s -X POST -u "$AUTH" \
  -H "Content-Type: application/json" \
  "https://api.atlassian.com/admin/v1/orgs/{orgId}/users/{accountId}/products" \
  -d '{"products": ["jira-software", "jira-servicedesk"]}'
```

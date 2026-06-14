# Google OAuth Client Secrets (Credentials)

## Source

De Notion-Page [OAuth-Client erstellt](https://www.notion.so/OAuth-Client-erstellt-30981c83f6d9804f8a22e84ee0542689)
(Page-ID: `30981c83f6d9804f8a22e84ee0542689`) enthält Credentials für zwei OAuth Clients.
Zusätzlich isch pro Client en `client_secret_*.json` via Notion File-Attachment aaghänkt.

**Kei Google Cloud Console Download nötig!** Alles steit im Klartext uf dere Notion-Page.

## Client 1 (Alt — vom 16.02.2026)

```
Client-ID:      GOOGLE_CLIENT_ID_1
Clientschlüssel: GOOGLE_CLIENT_SECRET_1
Erstellt:        16.02.2026, 17:42:46 GMT+1
Status:          Aktiviert (aber nid im Iisatz)
```

→ **NICHT im Einsatz.** War en erschte Versuch, nid mit Hermes verbunde.

## Client 2 (Aktiv — vom 23.02.2026 ✅ deployed)

```
Client-ID:      GOOGLE_CLIENT_ID_2
Clientschlüssel: GOOGLE_CLIENT_SECRET_2
Erstellt:        23.02.2026, 14:40:44 GMT+1
Status:          Aktiviert (im Iisatz)
```

→ **DAS isch de Client wo de MCP Server verwendt.**
→ Referenziert im deployed `client_secret.json` im Volume.

## Wiederherstellung

Wenn `client_secret.json` us em Volume verlore goht (z.B. neus Volume):

```bash
# 1. Notion-Page lese → Client-ID + Secret extrahiere
curl -s "https://api.notion.com/v1/pages/30981c83f6d9804f8a22e84ee0542689/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"

# 2. JSON baue
cat > /opt/data/google-mcp-server/data/client_secret.json << 'EOF'
{"installed":{"client_id":"GOOGLE_CLIENT_ID_2","project_id":"meinlokalerbot","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"GOOGLE_CLIENT_SECRET_2","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
EOF
```

## Sicherheitshinweis

D'Credentialsinfo uf dere Notion-Page sind **NÖTIG für de Betrieb** vom Google MCP Server
— ohni chame kein neue OAuth-Token hole. Trotzdem nid i öffentliche Referenze oder in
Skill-Memory dokumentiere (nume in Notion + Volume).

Dä Skill `google-mcp-server` referenziert sie im SKILL.md mit Platzhalter — s'echte
Secret liit NUR im Volume und uf dere Notion-Page.

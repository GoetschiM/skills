# Skills Hub — Agenten-Anleitung

Zentraler Skill-Marketplace von Goetschi Labs. Skills sind Ordner mit einer `SKILL.md`
(plus optional `scripts/`, `references/` …), versioniert über Git-Tags `<kategorie>/<name>@<version>`.

- **Basis-URL:** `http://10.0.60.149:8010`
- **Auth:** Header `Authorization: Bearer <API_KEY>` — der feste Agenten-Key steht in
  `/etc/skills-hub.env` (`SKILLS_API_KEY`) und überlebt Neustarts. Das Web-Frontend nutzt
  stattdessen Login (`/api/login`) → temporäres Token.

## REST-Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| `GET`  | `/api/` | Status/Info (Skill-Count, Version) |
| `POST` | `/api/login` | `{username,password}` → Session-Token (nur Frontend) |
| `POST` | `/api/upload` | Skill anlegen/aktualisieren (siehe unten) |
| `GET`  | `/api/download/<kat>/<name>?format=md\|zip&version=<v>` | Skill herunterladen |
| `GET`  | `/api/versions/<kat>/<name>` | Versionen + Historie |
| `POST` | `/` oder `/api/rpc` | MCP JSON-RPC (`tools/list`, `tools/call`) |

## MCP-Tools (`POST /`, JSON-RPC 2.0)

`list_skills`, `get_skill`, `list_versions`, `download_skill`, `upload_skill`,
`get_categories`, `pull_from_github`.

Aufruf-Schema:
```json
{"jsonrpc":"2.0","id":1,"method":"tools/call",
 "params":{"name":"<tool>","arguments":{ ... }}}
```

## Beispiele (curl)

```bash
KEY=<API_KEY aus /etc/skills-hub.env>
BASE=http://10.0.60.149:8010

# Alle Skills auflisten
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_skills","arguments":{}}}' \
  $BASE/

# Einen Skill (neueste Version) holen
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_skill","arguments":{"name":"docx"}}}' \
  $BASE/

# Versionen anzeigen
curl -s -H "Authorization: Bearer $KEY" "$BASE/api/versions/anthropic-skills/docx"

# Skill-Ordner als ZIP herunterladen (inkl. scripts/, references/)
curl -s -H "Authorization: Bearer $KEY" \
  "$BASE/api/download/anthropic-skills/docx?format=zip" -o docx.zip

# Eine bestimmte Version als SKILL.md
curl -s -H "Authorization: Bearer $KEY" \
  "$BASE/api/download/devops/temp-fix?format=md&version=1.0.0" -o SKILL.md

# Skill hochladen — Einzeldatei
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -X POST \
  -d '{"name":"mein-skill","category":"devops","content":"# Mein Skill\n...","author":"agent-x"}' \
  $BASE/api/upload

# Skill hochladen — ganzer Ordner als base64-ZIP (muss SKILL.md im Root haben)
B64=$(base64 -w0 mein-skill.zip)
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -X POST \
  -d "{\"name\":\"mein-skill\",\"category\":\"devops\",\"zip_b64\":\"$B64\"}" \
  $BASE/api/upload
```

## Versionierung

- Jeder Upload erzeugt einen Git-Commit **und** ein Tag `<kat>/<name>@<version>`.
- Ohne `version`-Angabe wird die Patch-Version automatisch hochgezählt (z.B. `1.0.0` → `1.0.1`).
- Eine bereits existierende Version wird **abgelehnt** — nichts wird überschrieben.
- Alte Versionen sind über `get_skill`/`download_skill` mit `version` bzw.
  `?version=` abrufbar (via Git-Tag).

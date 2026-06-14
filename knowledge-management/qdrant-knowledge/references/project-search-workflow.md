# Multi-Source Project/Person Search Workflow 🔍

When the user asks to find information about a project, person, or topic — systematically search across ALL available sources before concluding "nothing found."

## Search Order

### For PERSON searches (name, phone, email)

1. **Qdrant** `goetschi_labs_contacts` — semantic search (fastest, most accurate)
2. **Google Drive** — `name contains 'Person'` for documents/zeugnisse
3. **Notion** — `Kontakte / Adressbuch` database
4. **Obsidian** — `grep -ril 'Name' /vault/2-Kontakte/`
5. **Gmail** — `from:person@email.com` for recent communication
6. **Confluence** — search by name (personal space)
7. **Jira** — text search in tickets

### For PROJECT searches (name, description, tickets)

1. **Confluence** — project pages, architecture docs (primary project docs hub)
2. **Jira** — dedicated project (GL/BESORG) or text search `text ~ keyword`
3. **Notion** — project pages, task databases
4. **Qdrant** `goetschi_labs_memory` — AI agent notes about the project
5. **Obsidian** — `grep -ril 'project' /vault/`
6. **Google Drive** — project folders, documents

## If Found

- **Always read the full content** — don't just note the title. Extract key info: URLs, credentials, architecture, blockers, related tickets.
- **Return structured summary** — table of sources found with brief description per source.

## If NOT Found Anywhere

1. Ask the user for more context
2. Offer to search the Internet via `web_search`
3. If urgent: create a ticket to investigate

## Example: Besorgs Dir (30.05.2026)

Found in: Notion (3 project pages + email credentials), Confluence (project overview with architecture), Jira (BESORG-1 ticket "Container-Setup & Deployment", High, Nova created).
Not found in: Qdrant, Obsidian.

→ User got a complete picture from 3 sources and could proceed without asking again.

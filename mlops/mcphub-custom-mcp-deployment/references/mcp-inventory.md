# Goetschi Labs MCP Inventory  
*Stand: 15.06.2026*

| Server | Status | Auth | Notes |
|--------|--------|------|-------|
| `goetschi-github` | Neu, noch nicht deployed | Hardcoded PAT | 7 Tools: repos, PRs, issues |
| `goetschi-google-workspace` | ✅ Live | OAuth (token.json) | 12 Tools (Gmail, Calendar, Drive, Sheets, Docs) |
| `goetschi-home-assistant` | ✅ Live | Hardcoded HA-Token | Home Assistant Control |
| `goetschi-jira-confluence` | ✅ Live | API Token | Jira + Confluence |
| `goetschi-qdrant` | ✅ Live | API Key | Vector DB |
| `goetschi-proxmox` | ✅ Live | SSH/Pass | Proxmox VE |
| `goetschi-paperless` | ✅ Live | API Token | Document Management |
| `goetschi-asterisk-ari` | ✅ Live | Hardcoded | Asterisk Telephony |
| `goetschi-postgres-pgvector` | ✅ Live | DB Creds | PostgreSQL + PGVector |
| `goetschi-unifi` | ✅ Live | Hardcoded | UniFi Controller |
| `goetschi-minio` | ✅ Live | Hardcoded | S3 Storage |
| `notion` | ✅ Live | npx (No API) | Notion via npx |
| `atlassian-proxy` | ⚠️ Disconnected | OAuth needed | Atlassian MCP remote |
| `vaultwarden-mcp` | Standalone (docker-compose) | API Key | NOT in MCPHub, separate service für Credential-Abfrage |

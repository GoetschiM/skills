# Qdrant & MinIO LXC Migration (23.05.2026)

## Summary
Beide Services wurden von Docker-Containern auf Apollo (10.0.60.121) auf eigene LXC-Container auf pve01 (10.0.60.10) migriert.

## Neue Adressen

| Dienst | LXC | IP | Ports | Credentials |
|--------|-----|-----|-------|-------------|
| **MinIO** | 505 | 10.0.60.106 | 9000 (S3 API), 9001 (Console) | admin / Louis_one_13 |
| **Qdrant** | 506 | 10.0.60.179 | 6333 (REST), 6334 (gRPC) | Kein API-Key (lokal) |

## Qdrant Collections (Stand 23.05.)
- goetschi_labs_memory: 589 points
- goetschi_labs_contacts: 215 points
- tgs_knowledge: 267 points
- Test-RAG: 0 points
- goetschi_labs_pipeline: neu (Asterisk Pipeline)

## MinIO Buckets (Stand 23.05.)
11 Buckets total. Wichtigsti: asterisk-backups, documents, hermes-backups, nova-backups, qdrant-snapshots, sd-api, swarm-skills

## Sources to Update When IPs Change
Wenn Infrastruktur-Änderige (IPs, Credentials, Ports):
1. **Confluence** → Seite "MinIO & Qdrant LXCs" (ID 34570281)
2. **Jira** → Ticket GL-75 (Infrastructure-Entlastung)
3. **Skills** → qdrant-knowledge/SKILL.md + scripts/ + paperless/SKILL.md + minio-backup/SKILL.md
4. **Memory** → replace old Qdrant/MinIO entry
5. **Qdrant** → store migration fact in goetschi_labs_memory

## Verification Commands
```bash
# Qdrant health
curl -s http://10.0.60.179:6333/  # → JSON mit version

# Qdrant collections
curl -s http://10.0.60.179:6333/collections

# MinIO health (S3 API)
curl -s http://10.0.60.106:9000/minio/health/live  # → HTTP 200

# MinIO Console Login
curl -s -X POST http://10.0.60.106:9001/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"accessKey":"admin","secretKey":"Louis_one_13"}'  # → HTTP 204
```

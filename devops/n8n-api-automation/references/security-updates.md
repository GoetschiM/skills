# n8n Version Checking & Security Update Handling

## Version prüefe

Uf em Dokploy-Host (10.0.60.121) lauft n8n als Docker-Container. De Containername isch nid immer glich:

```bash
# 1. Container-Name usefinde
docker ps --filter name=n8n --format '{{.Image}} {{.Names}}'
# Output z.B.: n8nio/n8n:latest homelab-n8nwithpostgres-pzbt9a-n8n-1

# 2. Version us em Container useläse
docker exec <CONTAINER_NAME> node -e 'const p=require("/usr/local/lib/node_modules/n8n/package.json");console.log(p.version)'
```

**Via SSH vom Apollo us:**
```bash
sshpass -p "Louis_one_13" ssh -o StrictHostKeyChecking=no root@10.0.60.121 \
  "docker ps --filter name=n8n --format '{{.Image}} {{.Names}}'"
CONTAINER=$(sshpass -p "Louis_one_13" ssh -o StrictHostKeyChecking=no root@10.0.60.121 \
  "docker ps --filter name=n8n --format '{{.Names}}' | head -1")
sshpass -p "Louis_one_13" ssh -o StrictHostKeyChecking=no root@10.0.60.121 \
  "docker exec $CONTAINER node -e 'const p=require(\"/usr/local/lib/node_modules/n8n/package.json\");console.log(p.version)'"
```

## Security Update Handling

Wenn n8n Security Advisories per E-Mail chömed (security@info.n8n.io):

1. **Version-Prüefig**: Installierti Version mit patched Version vergliche
2. **Betroffen?** Wenn installiert < patched → betrifft uns!
   - Aktuell (Stand Mai 2026): `2.21.7` (patched `2.21.8`)
3. **Ticket erstelle** (GL, Problem) mit:
   - Verlinkte Advisories (GitHub Security Advisories)
   - Installierti vs. patched Version
   - Empfehlig: Upgrade über Dokploy (Image-Update)

## Known Security Advisory Timeline

| Datum | Advisory | Severity | Patched in | Unser Version | Betroffen? |
|-------|----------|----------|------------|---------------|------------|
| 27.05.2026 | Python Sandbox Escape (GHSA-9pq8-m8gp-4p53) | 🔴 HIGH | v2.21.8 | v2.21.7 | ✅ Ja |
| 27.05.2026 | Git Node Sandbox Bypass (GHSA-5xp3-2w67-427v) | 🟡 MEDIUM | v2.21.8 | v2.21.7 | ✅ Ja |

## Upgrade via Dokploy

1. I de Dokploy-Weboberfläch (http://10.0.60.121:3000) deploye
2. Nöis n8n-Image (latest) loose
3. Nach Upgrade: Version nömals prüefe
4. Ticket schliesse

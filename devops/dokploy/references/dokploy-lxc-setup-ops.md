# Dokploy LXC Operations

## Listing Dokploy Apps

```bash
# Production (Swarm — container has task suffix):
pct exec <LXC> -- bash -c '
CID=$(docker ps -q -f name=dokploy-postgres | head -1)
docker exec $CID psql -U dokploy -d dokploy \
  -c "SELECT \"appName\", name FROM application;"
docker exec $CID psql -U dokploy -d dokploy \
  -c "SELECT \"appName\", name FROM compose;"
'
```

## Stopping a Service (SAFE — reversible)
Scale to 0 instead of deleting:
```bash
pct exec <LXC> -- docker service scale <service-name>=0
```

## Copying an App Image Between LXCs

```bash
pct exec <SRC> -- docker save <image>:latest -o /tmp/<name>.tar
pct pull <SRC> /tmp/<name>.tar /tmp/<name>.tar
pct push <TGT> /tmp/<name>.tar /tmp/<name>.tar
pct exec <TGT> -- docker load -i /tmp/<name>.tar
```

## Production vs Sandbox Differences

| Aspect | Production (LXC 100) | Sandbox (LXC 110) |
|--------|---------------------|-------------------|
| IP | 10.0.60.121 | 10.0.60.136 |
| Docker mode | Swarm | Compose |
| Dokploy | v0.29.2 | v0.29.5 |

## Post-Migration Verification

Check these after moving a service to a new LXC:
1. Correct port mapping (Next.js: port 3000 inside, not 80!)
2. App startup time (Next.js: ~11s compile)
3. LXC firewall (ufw/iptables)
4. Image name (Dokploy Swarm renames images)

```bash
docker run -d --restart unless-stopped --name <name> -p <ext>:<int> <image>:latest
sleep 10
docker logs <name> --tail 10
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://<LXC-IP>:<port>
```

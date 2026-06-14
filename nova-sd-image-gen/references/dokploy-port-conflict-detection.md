# Dokploy Port Conflict Detection

## Problem
Beim Deployment von Services auf dem Dokploy-Host (10.0.60.121) kann Port 3023 bereits belegt sein — **nicht durch SD 1.5, sondern durch den Dokploy-MCP Service**.

## Erkennung
```bash
# Check: läuft da schon was auf meinem Zielport?
sshpass -p 'Louis_one_13' ssh root@10.0.60.121 "ss -tlnp | grep <PORT>"

# Oder: docker ps -a — zeigt alle Container mit Port-Mappings
sshpass -p 'Louis_one_13' ssh root@10.0.60.121 "docker ps -a --filter publish=<PORT>"
```

## Symptom
```
docker: Error response from daemon: driver failed programming external connectivity
  on endpoint <name>: Bind for 0.0.0.0:<PORT> failed: port is already allocated
```

## Lösung
1. **Port im sd_app.py ändern** (PORT = <neuer_port>)
2. **Docker Image neu bauen** (nur letzter Layer, ~0.7s)
3. **Container mit neuem Port starten**: `-p <neuer_port>:<neuer_port>`

## Bekannte Konflikte
| Port | Service | Host |
|------|---------|------|
| 3023 | Dokploy-MCP (Service Mesh) | Dokploy |
| 3000 | Dokploy-MCP (intern) | Dokploy |

Im Zweifelsfall Port 3024 oder höher verwenden.

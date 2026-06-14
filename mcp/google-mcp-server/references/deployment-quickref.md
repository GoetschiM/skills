# Quick Reference — Build & Deploy

## Vollsändigä Rebuild (im Fall vo Source-Änderige)

```bash
cd /tmp/google-mcp-server
# Source isch ide server.py
docker stop google-mcp-server && docker rm google-mcp-server
docker build --no-cache -t google-mcp-server:latest .
docker run -d --name google-mcp-server \
  --restart unless-stopped \
  -p 8002:8002 \
  -v /opt/data/google-mcp-server/data:/data \
  google-mcp-server:latest
sleep 3 && docker logs google-mcp-server --tail 5
```

## Token prüfe

```bash
curl -s http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"google_health","arguments":{}}}'
```

## Tools-Liste

```bash
curl -s http://10.0.60.121:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | python3 -c "import sys,json; [print(t['name']) for t in json.load(sys.stdin)['result']['tools']]"
```

## Container-Troubleshooting

```bash
# Logs
docker logs google-mcp-server --tail 20

# Volume-Check
docker exec google-mcp-server ls -la /data/

# Server-Test von innen
docker exec google-mcp-server python3 -c "
import urllib.request,json
req=urllib.request.Request('http://localhost:8002/mcp',
  data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/list','params':{}}).encode(),
  headers={'Content-Type':'application/json','Accept':'application/json'})
resp=urllib.request.urlopen(req)
tools=json.loads(resp.read())['result']['tools']
print(f'{len(tools)} tools')
"
```

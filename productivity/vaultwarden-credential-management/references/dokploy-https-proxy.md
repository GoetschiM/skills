# Dokploy-Host HTTPS Proxy Pattern (Goetschi Labs CT121)

When deploying HTTPS services on Dokploy host (10.0.60.121), use a standalone nginx container because Dokploy's embedded Traefik does NOT expose ports 80/443.

## Architecture

```
Client → Port 443 → <service>-ssl (nginx:alpine) → <service> (:80)
               ↓
      /etc/ssl/<service>/ (self-signed cert)
```

## Commands Template

### 1. Generate Cert
```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
  -keyout /etc/ssl/<service>/<service>.key \
  -out /etc/ssl/<service>/<service>.crt \
  -subj "/C=CH/ST=TG/L=Amriswil/O=Goetschi Labs/CN=<domain>" \
  -addext "subjectAltName=DNS:<domain>,DNS:localhost,IP:10.0.60.121"
```

### 2. Start Service
```bash
docker run -d --name <service> \
  --restart unless-stopped \
  --network dokploy-network \
  -e ... \
  <image>
```

### 3. Start SSL Proxy
```bash
docker run -d --name <service>-ssl \
  --restart unless-stopped \
  -p 443:443 -p 80:80 \
  -v /etc/ssl/<service>:/etc/ssl/<service>:ro \
  --network dokploy-network \
  nginx:alpine
```

### 4. Nginx Config
```nginx
upstream backend {
    server <service>:80;
}

server {
    listen 80;
    server_name <domain> 10.0.60.121;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name <domain> 10.0.60.121;

    ssl_certificate /etc/ssl/<service>/<service>.crt;
    ssl_certificate_key /etc/ssl/<service>/<service>.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Port Management

| Service | Port Mapping | Purpose |
|---------|-------------|---------|
| Vaultwarden | 8100:80 | Direct HTTP (internal only) |
| vaultwarden-ssl | 443:443, 80:80 | HTTPS + HTTP→HTTPS redirect |

When adding new HTTPS services alongside existing ones, use different HOST ports mapped to different proxy containers, each listening on its own host port and forwarding to its service.

## DNS

Services use Docker DNS (`dokploy-network` is a Swarm overlay network, Subnet `10.0.1.0/24`).
- Container hostname = container name (e.g., `vaultwarden` resolves to `10.0.1.x`)
- `--network dokploy-network` enables DNS resolution between containers
- After restarting a service container, run `docker exec <proxy> nginx -s reload` to flush stale connections

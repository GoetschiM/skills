---
name: docker-ssl-proxy
description: Add HTTPS to any internal Docker container via a self-signed nginx reverse proxy. Covers cert generation, nginx config, network linking, and HTTP→HTTPS redirects.
tags:
  - ssl
  - https
  - nginx
  - reverse-proxy
  - tls
  - docker
  - self-signed
triggers:
  - "I need HTTPS for a Docker container"
  - "Could you make this run on HTTPS?"
  - "We need a certificate for [service]"
  - "enable HTTPS on port [N]"
  - "self-signed certificate"
---

# Docker SSL Proxy — Self-Signed HTTPS for Internal Services

Add HTTPS to any Docker container when:
- **Let's Encrypt is not available** (no public DNS, no port 80, internal-only service)
- **You need encryption** for passwords, tokens, admin panels
- **The container itself doesn't support TLS** (runs plain HTTP on port 80)

## Workflow

### 1. Generate the self-signed certificate

```bash
# Create cert directory
mkdir -p /etc/ssl/<service-name>

# Generate cert + key (10 year validity)
openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
  -keyout /etc/ssl/<service-name>/<service-name>.key \
  -out /etc/ssl/<service-name>/<service-name>.crt \
  -subj "/C=CH/ST=TG/L=Amriswil/O=Goetschi Labs/CN=<domain>" \
  -addext "subjectAltName=DNS:<domain>,DNS:localhost,IP:<host-ip>"
```

Parameters:
- `-days 3650` → valid for 10 years (reduces renewal burden for internal services)
- `CN=<domain>` → the domain name users will see (e.g., `vault.rebelone.ch`)
- `subjectAltName` → MUST include `DNS:localhost` and `IP:<host-ip>` so curl and browser tests work from localhost and LAN

### 2. Start the nginx SSL proxy container

```bash
docker run -d --name <service-name>-ssl \
  --restart unless-stopped \
  -p 443:443 \
  -p 80:80 \
  -v /etc/ssl/<service-name>:/etc/ssl/<service-name>:ro \
  --network <shared-network> \
  --link <upstream-container>:<upstream-hostname> \
  nginx:alpine
```

Key points:
- **Port 443** → HTTPS (primary)
- **Port 80** → HTTP→HTTPS redirect
- **Volume** mounts cert files read-only
- **--link** or **--network** so nginx can resolve the upstream container by hostname
- Use `nginx:alpine` for smallest image

### 3. Write nginx config

Create nginx config, then copy into container:

```bash
cat > /tmp/<service-name>-nginx.conf << 'CONF'
upstream backend {
    server <upstream-hostname>:80;
}

server {
    listen 80;
    server_name <domain> <host-ip>;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name <domain> <host-ip>;

    ssl_certificate /etc/ssl/<service-name>/<service-name>.crt;
    ssl_certificate_key /etc/ssl/<service-name>/<service-name>.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # WebSocket support (for Bitwarden, Jupyter, etc.)
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
CONF

docker cp /tmp/<service-name>-nginx.conf <container-name>:/etc/nginx/conf.d/default.conf
docker exec <container-name> nginx -s reload
```

**nginx directive note (nginx:alpine 1.27+)**: `listen 443 ssl` + `http2 on;` (separate line). The old `listen 443 ssl http2;` syntax is deprecated in newer nginx versions.

### 4. Verify

```bash
# Internal check
curl -sk https://localhost/ | grep "<title"

# LAN check
curl -sk https://<host-ip>/ | grep "<title"

# HTTP→HTTPS redirect
curl -sI http://<host-ip>/ | grep -E "HTTP|Location"

# Admin endpoint
curl -sk https://<host-ip>/admin
```

## Pitfalls

- **Dokploy embedded Traefik**: Dokploy v0.29.2 has Traefik built into the Dokploy container, but does NOT expose port 80/443 externally. Don't rely on Dokploy's Traefik for external HTTPS — use a standalone nginx container instead.
- **Container DNS resolution**: After restarting an upstream container, nginx may need `nginx -s reload` to pick up the new container IP. Docker DNS via `--network` or `--link` usually resolves the name, but a reload helps flush stale connections. This is especially important on Docker Swarm overlay networks like `dokploy-network` where container IPs can change after restart.
- **Vaultwarden health check**: Vaultwarden takes ~30s to become healthy. During that window nginx returns 502. Wait for the container health status before testing externally.
- **Browser warnings**: Self-signed certs show a security warning. Users must click "Accept risk" or "Proceed anyway". This is expected — the traffic IS encrypted despite the warning.

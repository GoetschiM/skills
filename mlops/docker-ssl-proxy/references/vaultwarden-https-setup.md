# Vaultwarden HTTPS Setup on Dokploy Host (CT121)

Deployed 2026-06-14.

## Architecture

```
Internet/LAN → Port 443 → vaultwarden-ssl (nginx:alpine) → vaultwarden (vaultwarden/server:latest)
                                      ↓
                            /etc/ssl/vaultwarden/ (self-signed cert)
```

## Commands Used

### Cert generation
```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
  -keyout /etc/ssl/vaultwarden/vaultwarden.key \
  -out /etc/ssl/vaultwarden/vaultwarden.crt \
  -subj "/C=CH/ST=TG/L=Amriswil/O=Goetschi Labs/CN=vault.rebelone.ch" \
  -addext "subjectAltName=DNS:vault.rebelone.ch,DNS:localhost,IP:10.0.60.121"
```

### Nginx proxy container
```bash
docker run -d --name vaultwarden-ssl \
  --restart unless-stopped \
  -p 443:443 \
  -p 80:80 \
  -v /etc/ssl/vaultwarden:/etc/ssl/vaultwarden:ro \
  --network dokploy-network \
  nginx:alpine
```

### Vaultwarden container
```bash
docker run -d --name vaultwarden \
  --restart unless-stopped \
  --network dokploy-network \
  -e SIGNUPS_ALLOWED=true \
  -e DOMAIN=https://vault.rebelone.ch \
  -e ADMIN_TOKEN=<stored-on-host> \
  -v vaultwarden-data:/data \
  vaultwarden/server:latest
```

### Nginx config
Written to `/etc/nginx/conf.d/default.conf` inside the container.
Config has `upstream backend { server vaultwarden:80; }` — note the service name matches the Docker container name.

## Verification
- HTTPS: `curl -sk https://10.0.60.121/` → Vaultwarden Web
- HTTP→HTTPS: `curl -sI http://10.0.60.121/` → 301 Moved Permanently
- Admin: `curl -sk https://10.0.60.121/admin` → Vaultwarden Admin Panel
- Cert subject: vau l t . r e b e l o n e . c h (self-signed)
- Admin token saved to `/root/vaultwarden-admin-token.txt` on CT121

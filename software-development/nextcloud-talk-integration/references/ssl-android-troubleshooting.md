# SSL/TLS Troubleshooting for Nextcloud Talk Android App

## Symptom

Android Nextcloud Talk app shows: **"400 Bad Request — The plain HTTP request was sent to HTTPS port"**

**Root cause:** The app's login/v2 WebView flow follows an HTTP (not HTTPS) redirection URL at some point. This happens when:
1. The self-signed certificate isn't trusted by Android system trust store
2. The app falls back to HTTP after the HTTPS handshake fails
3. HTTP sent to SSL port (8443) → nginx returns 400

## Resolution: Install self-signed cert on Android

### Step 1: Serve cert for download

```bash
# Run a plain HTTP nginx container that serves the cert
docker run -d --name nc-cert-server --restart unless-stopped \
  -v /opt/nginx-ssl/nextcloud.crt:/usr/share/nginx/html/nextcloud.crt:ro \
  -p 8081:80 nginx:alpine

# Cert is now downloadable at:
# http://10.0.60.121:8081/nextcloud.crt
```

### Step 2: Install on Android

1. Open Chrome on Android
2. Navigate to `http://10.0.60.121:8081/nextcloud.crt` (over Tailscale)
3. The cert file downloads
4. Go to Settings → Security → Encryption & credentials → Install a certificate
5. Select "CA certificate" → choose the downloaded `nextcloud.crt`
6. Accept the system warning (it's your own CA)

### Step 3: Configure Talk App

- Server URL: `https://10.0.60.121:8443`
- Username: `michel`
- Password: `NextCloud123!`

## Alternative: Accept in Chrome first (does NOT fix app)

Visiting `https://10.0.60.121:8443` in Chrome and tapping "Proceed" only works for that browser session — **the Talk app uses its own TLS stack and won't inherit the acceptance**. System-wide CA installation is required.

## Edge Cases

### Nextcloud Config Not Applied (occ fails silently)

`occ config:system:set` for `overwriteprotocol`/`overwrite.cli.url` can report success but NOT actually save changes. Always **verify** by reading back:

```bash
# Verify
grep 'overwriteprotocol\|overwrite.cli.url' /var/www/html/config/config.php

# If wrong — edit config.php directly via base64:
CONFIG=$(docker exec code-nextcloud-1 base64 /var/www/html/config/config.php | tr -d '\n')
# decode, sed, encode, write back
docker exec -u 0 code-nextcloud-1 sh -c "echo '$NEW_B64' | base64 -d > /var/www/html/config/config.php"
```

### Required Nextcloud Config for HTTPS Proxy

```php
'overwriteprotocol' => 'https',
'overwrite.cli.url' => 'https://10.0.60.121:8443',
'overwritehost' => '10.0.60.121:8443',
'trusted_proxies' => [
    0 => '172.18.0.0/16',   # docker_gwbridge
    1 => '172.23.0.0/16',   # nextcloud-network
    2 => '10.0.60.0/24',    # LAN
],
'forwarded_for_headers' => [
    0 => 'HTTP_X_FORWARDED_FOR',
    1 => 'HTTP_X_REAL_IP',
],
```

### Caddy Self-Signed Fails

Caddy with `tls /path/to/cert.crt /path/to/key.key` or `tls internal` produces:
```
OpenSSL/3.0.19: error:0A000438:SSL routines::tlsv1 alert internal error
```
**Use nginx:alpine instead** — it serves self-signed certs without TLS errors.

### nginx: HTTP→HTTPS redirect on the same port is impossible

You CANNOT add `listen 443; return 301 https://$host$request_uri;` alongside an SSL server block on the same port. nginx rejects plain HTTP before the server block is evaluated. Solution: serve the cert for Android download on a separate plain-HTTP port (e.g., 8081).

## Verification Commands

```bash
# Check HTTPS works
curl -sk https://10.0.60.121:8443/status.php

# Check Talk API via HTTPS
curl -sk -u 'michel:NextCloud123!' -H 'OCS-APIRequest: true' \
  'https://10.0.60.121:8443/ocs/v2.php/apps/spreed/api/v1/chat/iytt2n7g?lookIntoFuture=0&limit=1'

# Check cert
openssl x509 -in /opt/nginx-ssl/nextcloud.crt -text -noout | grep -E "Subject:|Not Before|Not After"

# Verify config.php
grep 'overwrite\|trusted_proxies\|forwarded_for' /var/www/html/config/config.php
```

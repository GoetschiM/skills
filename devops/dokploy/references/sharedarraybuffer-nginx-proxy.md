# SharedArrayBuffer / COOP-COEP Nginx Proxy Fix

## Problem

Webbasierten Apps, die **SharedArrayBuffer** benötigen (Actual Budget, Figma, collaborative Tools, WASM-Apps), laufen nicht im Browser wenn die Seite nicht **cross-origin isolated** ist.

**Symptom:** Die App lädt, zeigt aber einen Fehler wie:
- `Cannot use SharedArrayBuffer because the page is not cross-origin isolated`
- `Actual benötigt Zugriff auf SharedArrayBuffer, um richtig zu funktionieren`
- Leerer Bildschirm / hängende UI bei Actual Budget
- `Error: [object Object]` mit Stacktrace auf FatalError-Komponente

## Ursache (drei Bedingungen)

SharedArrayBuffer benötigt **alle** diese Voraussetzungen:

| Bedingung | Erklärung | Check |
|-----------|-----------|-------|
| **Secure Context** | HTTPS (oder localhost/127.0.0.1) — HTTP reicht NICHT | `isSecureContext` im Browser |
| **COOP: same-origin** | Cross-Origin-Opener-Policy Header | `crossOriginIsolated` im Browser |
| **COEP: require-corp** (oder credentialless) | Cross-Origin-Embedder-Policy Header | `crossOriginIsolated` im Browser |

**Wichtig:** Auch mit korrekten COOP/COEP-Headern wird SharedArrayBuffer auf **HTTP** (ohne HTTPS) niemals aktiviert, da `isSecureContext = false`.

## 🔴 Kritisches Pitfall: Duplizierte Header vom Upstream

### Symptom
- `curl -sI` zeigt korrekte COOP/COEP Header ✅
- Browser zeigt trotzdem `crossOriginIsolated: false` ❌
- `curl` zeigt: `cross-origin-embedder-policy: require-corp, require-corp`
  (Header erscheint ZWEIMAL, durch Komma getrennt)

### Ursache
**Der Upstream-Container (actual-server) sendet bereits COOP/COEP-Header!** Nginx fügt via `add_header` nochmal welche hinzu → Ergebnis: `require-corp, require-corp`. Chrome kann keinen gültigen Wert aus diesem Duplikat parsen.

### Fix
**NICHT** `add_header` im nginx verwenden, wenn der Upstream schon COOP/COEP sendet:

```nginx
# ❌ FALSCH — erzeugt Duplikate wenn Upstream bereits Header sendet
add_header Cross-Origin-Opener-Policy 'same-origin' always;

# ✅ RICHTIG — Header vom Upstream durchlassen, nix hinzufügen
# (kein add_header — Upstream sendet bereits korrekte Header)
```

### Prüfung: Sendet der Upstream bereits COOP/COEP?
```bash
# Vom nginx-Container aus den Upstream direkt abfragen
docker exec <proxy-container> sh -c 'curl -sI http://<upstream>:<port>/ | grep -i cross-origin'

# Beispiel (Actual Budget):
docker exec actual-budget-proxy curl -sI http://actual-server:5006/ | grep -i cross-origin
# Wenn das ausgibt → Upstream sendet bereits Header → KEIN add_header im nginx!
```

### Nginx `add_header` Verhalten verstehen
- `add_header` in einem `location`-Block **überschreibt NICHT** vorhandene Header — es **fügt hinzu**
- Die Upstream-Header werden standardmässig **durchgelassen**
- Ergebnis: Upstream-Header + nginx-Header = **Duplikat**
- Lösung: `proxy_hide_header Cross-Origin-Opener-Policy` (um Upstream-Header zu unterdrücken) ODER einfach kein `add_header` (wenn Upstream korrekt ist)

## Lösung A: Nur HTTP — Upstream sendet keine COOP/COEP (selten)

### 1. Compose File erweitern

```yaml
services:
  actual-server:
    image: actualbudget/actual-server:latest
    expose:
      - "5006"
    volumes:
      - actual-data:/data
    restart: unless-stopped

  actual-proxy:
    image: nginx:alpine
    ports:
      - "5006:80"
    volumes:
      - /etc/dokploy/compose/<project>/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - actual-server
    restart: unless-stopped
```

### 2. nginx.conf (mit `add_header`)

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://actual-budget:5006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;

        # 🔴 WICHTIG: Upstream-Header verstecke!
        # actual-server sendet selber COOP/COEP → Duplikat vermeide
        proxy_hide_header Cross-Origin-Opener-Policy;
        proxy_hide_header Cross-Origin-Embedder-Policy;

        # Required for SharedArrayBuffer
        add_header Cross-Origin-Opener-Policy "same-origin" always;
        add_header Cross-Origin-Embedder-Policy "credentialless" always;
    }
}
```

## Lösung B: HTTPS + mkcert (empfohlen) für Secure Context

**Notwendig:** SharedArrayBuffer benötigt HTTPS (secure context). HTTP allein reicht nicht.

**mkcert vs Self-Signed:** Self-Signed Certs funktionieren auf Desktop-Browsern (mit "Proceed anyway"), scheitern aber auf **iOS/iPadOS** (kein Umgehen möglich). mkcert ist der zuverlässige Weg.

### 1. mkcert Setup (auf dem Host)

```bash
# mkcert installieren
apt-get install -y mkcert libnss3-tools

# Lokale Root-CA erstellen
mkcert -install

# Cert für IPs generieren
mkcert -cert-file /etc/ssl/<service>/fullchain.pem \
       -key-file /etc/ssl/<service>/privkey.pem \
       <IP> localhost 127.0.0.1
```

### 2. nginx.conf (HTTPS mit proxy_hide_header + credentialless)

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://actual-server:5006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        proxy_hide_header Cross-Origin-Opener-Policy;
        proxy_hide_header Cross-Origin-Embedder-Policy;
        add_header Cross-Origin-Opener-Policy "same-origin" always;
        add_header Cross-Origin-Embedder-Policy "credentialless" always;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name _;

    ssl_certificate /etc/ssl/<service>/fullchain.pem;
    ssl_certificate_key /etc/ssl/<service>/privkey.pem;

    location / {
        proxy_pass http://actual-server:5006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_cache_bypass $http_upgrade;

        proxy_hide_header Cross-Origin-Opener-Policy;
        proxy_hide_header Cross-Origin-Embedder-Policy;
        add_header Cross-Origin-Opener-Policy "same-origin" always;
        add_header Cross-Origin-Embedder-Policy "credentialless" always;
    }
}
```

### 3. Compose File (zusätzlicher Port + SSL-Volume)

```yaml
  actual-proxy:
    image: nginx:alpine
    container_name: actual-budget-proxy
    ports:
      - "5006:80"         # HTTP (fallback, kein SAB)
      - "5007:443"        # HTTPS (SharedArrayBuffer)
    volumes:
      - /etc/dokploy/compose/<project>/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/ssl/<service>:/etc/ssl/<service>:ro
    depends_on:
      - actual-server
```

## 🔴 Kritisches Pitfall: Selbst-Signed Certs auf iOS/mobilen Geräten

**Problem:** Chrome auf iOS/iPadOS erlaubt **kein** "Proceed anyway" bei Self-Signed Zertifikaten. Der User sieht die Seite nie — die Meldung "Your connection is not private" ist eine Sackgasse.

**Lösung: mkcert** — lokal vertrauenswürdige Zertifikate, die auf jedem Gerät funktionieren (einmalige Root-CA Installation).

### mkcert Setup (auf dem Host)

```bash
# 1. mkcert installieren
apt-get install -y mkcert libnss3-tools

# 2. Lokale Root-CA erstellen (einmalig pro Host)
mkcert -install

# 3. Cert für IP + localhost generieren
mkcert -cert-file /etc/ssl/<service>/fullchain.pem \
       -key-file /etc/ssl/<service>/privkey.pem \
       10.0.60.121 localhost 127.0.0.1

# 4. Root-CA exportieren (dem User geben)
cat /root/.local/share/mkcert/rootCA.pem
```

### User-Anleitung: Root-CA installieren (einmalig)

| Gerät | Schritte |
|-------|----------|
| **iPhone/iPad** | Datei `rootCA.pem` erhalten → Einstellungen → Allgemein → Info → Zertifikatsvertrauensstellung → Schieber für die CA aktivieren |
| **Mac** | Datei öffnen → Schlüsselbundverwaltung → Zertifikat auf "Immer vertrauen" stellen |
| **Windows** | Doppelklick → Zertifikat installieren → Vertrauenswürdige Stammzertifizierungsstellen |
| **Android** | Einstellungen → Sicherheit → CA-Zertifikat installieren |

Danach: Browser neustarten → `https://<ip>:<port>` → **keine Warnung** ✅

### Vollständige nginx.conf (mkcert + credentialless + proxy_hide_header)

```nginx
# HTTP — COOP/COEP für interne Nutzung
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://actual-server:5006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # Upstream-Header verstecken (actual-server sendet selber COOP/COEP)
        proxy_hide_header Cross-Origin-Opener-Policy;
        proxy_hide_header Cross-Origin-Embedder-Policy;
        add_header Cross-Origin-Opener-Policy "same-origin" always;
        add_header Cross-Origin-Embedder-Policy "credentialless" always;
    }
}

# HTTPS mit mkcert-Zertifikat
server {
    listen 443 ssl;
    http2 on;
    server_name _;

    ssl_certificate /etc/ssl/actual-budget/fullchain.pem;
    ssl_certificate_key /etc/ssl/actual-budget/privkey.pem;

    location / {
        proxy_pass http://actual-server:5006;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_cache_bypass $http_upgrade;

        proxy_hide_header Cross-Origin-Opener-Policy;
        proxy_hide_header Cross-Origin-Embedder-Policy;
        add_header Cross-Origin-Opener-Policy "same-origin" always;
        add_header Cross-Origin-Embedder-Policy "credentialless" always;
    }
}
```

## Diagnose-Toolkit

### Server-Seite prüfen
```bash
# Header anzeigen (auf Duplikate achten!)
curl -sI http://10.0.60.121:5006/ | grep -iA2 cross-origin

# HTTPS via Self-Signed Cert
curl -skI https://10.0.60.121:5007/ | grep -iA2 cross-origin

# Prüfen ob Upstream selbst Header sendet
docker exec <proxy> curl -sI http://<upstream>:<port>/ | grep -i cross-origin
```

### Browser-Seite prüfen (JS Console)
```javascript
JSON.stringify({
  crossOriginIsolated: crossOriginIsolated,
  sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
  secureContext: isSecureContext
})
// Erwartet: {"crossOriginIsolated":true,"sharedArrayBuffer":true,"secureContext":true}
```

## ⚠️ Weitere Pitfalls

### HTTPS Self-Signed Cert: Browser-Warnung
Beim ersten Aufruf von `https://<ip>:<port>` zeigt Chrome:
1. "Your connection is not private" / `NET::ERR_CERT_AUTHORITY_INVALID`
2. User klickt: **Advanced** → **Proceed to <ip> (unsafe)**
3. Danach wird die Exception gespeichert → kein Hinweis mehr

**`isSecureContext` wird `true`, sobald HTTPS (auch mit Self-Signed) verwendet wird** — SharedArrayBuffer funktioniert dann.

### Variable escaping bei Python/paramiko
Siehe [separater Pitfall im Dokploy Skill](../SKILL.md#variable-escaping-bei-pythonparamiko).

### COOP/COEP deaktiviert Third-Party Content
`Cross-Origin-Embedder-Policy: require-corp` blockiert alle Cross-Origin-Ressourcen (Bilder, Skripts, Fonts von CDNs). **Actual Budget** benötigt keine externen Ressourcen → COEP funktioniert problemlos.

### Keine COOP/COEP über Traefik
Traefik-Labels in Dokploy können KEINE COOP/COEP-Header setzen. Der Nginx-Proxy ist der einfachste Weg.

## Browser Cache / Service Worker — Das unterschätzte Problem

Selbst wenn Server-Header korrekt sind, sieht der User den Fehler wenn der Browser die **alte Seite gecached** hat.

### Lösung (dem User mitteilen)

| Option | Aktion |
|--------|--------|
| A — Hard Refresh | Chrome: `Strg + F5` oder `Cmd + Shift + R` |
| B — Cache komplett leeren | DevTools (F12) → Network → "Disable cache" anhaken → neu laden |
| C — Service Worker deaktivieren | DevTools (F12) → Application → Service Workers → "Unregister" |
| D — Anderen Browser/Incognito | Einfachster Test: Inkognito-Fenster öffnen |

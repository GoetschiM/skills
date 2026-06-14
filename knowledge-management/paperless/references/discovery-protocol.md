# Paperless Discovery Protocol (18.05.2026)

Verwendet zum Identifiziere und Verbinde vo Paperless-ngx Instanzen im Goetschi-Labs Netzwerk.

## Schritt 1: IP finde

Paperless-Instanste chönd i verschiedene Tickets dokumentiert si:

| Ticket | Host | Port | Notiz |
|--------|------|------|-------|
| GL-29 | LXC (10.0.40.30) | 8000 | Produktiv-Instanz |
| TEAM-19 | LXC (10.0.40.30) | 8015 | SSH klappt nid |
| Docker Compose (Dokploy) | 10.0.60.121 | 8015 | Fallback, `restart: unless-stopped` |

Suche i Ticket-Descriptions und -Kommentar nach IPs:
```bash
source /opt/data/home/.hermes/.env  # statt /opt/data/.atlassian.env
AUTH="$ATLASSIAN_EMAIL:$ATLASSIAN_TOKEN"
BASE="https://$ATLASSIAN_DOMAIN"

curl -s -X POST -u "$AUTH" "$BASE/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{"jql":"text ~ paperless","fields":["summary","description"]}'
```

## Schritt 2: Prüfe ob läuft

```bash
curl -s -o /dev/null -w "HTTP %{http_code}" http://<host>:<port>/api/
# Sött 200 oder 302 si (302 = Login-Redirect)
```

## Schritt 3: Credentials finde

### Docker Compose (bekannte Hosts)
```python
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.0.60.121", username="root", password="Louis_one_13", timeout=10)
stdin, stdout, stderr = c.exec_command("cat /opt/paperless/docker-compose.yml")
# PAPERLESS_ADMIN_USER + PAPERLESS_ADMIN_PASSWORD
```

### LXC (unbekannte Credentials)
SSH uf LXC (10.0.40.x) klappt oft nid mit Standard-Passwort. Probiere:
- `root/Louis_one_13`
- `root/Riotstar_MICHEL_13`

Lönd beidi nöd, muess Michel im Paperless-UI en API-Token generiere.

## Schritt 4: Login teste

```bash
curl -s -X POST http://<host>:<port>/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'
# 200 = {"token":"..."} | 400 = {"non_field_errors":[...]}
```

## Schritt 5: API verifiziere

```bash
TOKEN="<token>"
curl -s http://<host>:<port>/api/documents/ \
  -H "Authorization: Token $TOKEN"
# count = Anzahl Dokumente
```

---
name: litellm
description: "LiteLLM — LLM API Gateway: Setup, Provider-Konfiguration, Key-Management, Migration, Hermes-Integration"
version: 1.6.0
author: Apollo
tags: [litellm, llm-gateway, provider, openai, gemini, openrouter, deepseek, api-keys]
related_skills: [hermes-agent, serving-llms-vllm]
---

# LiteLLM — LLM API Gateway

LiteLLM isch en Open-Source LLM API Gateway (OpenAI-kompatibel) wo mehreri Provider hinter emene einzige Endpunkt vereint. Idee fürs Homelab: eimal konfigurierä, und alli Dienste (Hermes, n8n, Scripts) gönd über `http://<host>:4000/v1`.

**Im homelab (aktuell):**
- **10.0.60.121:4000** — Primäri LiteLLM-Instanz (Docker + PostgreSQL, via Dokploy) — Gateway
- **10.0.60.167:4000** — Nova-LiteLLM (venv + systemd, database_url: null) — Proxy zu 121 (`references/proxy-architecture.md`)

**Historisch (nümm aktiv):**
- ~~10.0.60.156:4000~~ — Nova (LXC 100), bare-metal/Venv, **gelöscht am 07.06.2026** (`references/bare-metal-on-host-156.md`)
- ~~10.0.60.156:4001~~ — Premium LiteLLM auf Apollo (Docker), **offline** (Docker-Service inactive) (`references/premium-litellm-history.md`)

Siehe `references/121-docker-setup.md` für 121 Details.

---

## Setup

### Option A: Docker (bewährt, einfacher — PostgreSQL zwingend)

**⚠️ Wichtig: `ghcr.io/berriai/litellm:main-latest` erzwingt PostgreSQL** — de Entrypoint `docker/prod_entrypoint.sh` brucht Prisma wo auf PostgreSQL fest verdrahtet isch. Es git **kei `--no-db` Flag**. Ohni `DATABASE_URL` stürzt de Container ab.

**Volume-Mount-Gotcha:** `/app` isch s'Container-Arbeitsverzeichnis und enthält Entrypoint, Prisma Engine und App-Code. **NID `-v /opt/litellm:/app` verwende!** Sust überschriebsch du alli Container-Inneralien. Stattdesse einzelni Dateie/Verzeichnis mounä:

```bash
# PostgreSQL Container (zwingend)
docker run -d --name litellm-db \
  -e POSTGRES_USER=litellm \
  -e POSTGRES_PASSWORD=litellm \
  -e POSTGRES_DB=litellm \
  -v litellm-db-data:/var/lib/postgresql/data \
  postgres:16-alpine

# LiteLLM Container (MIT PostgreSQL, ohni Volume-Gotcha)
docker run -d --name litellm \
  --network litellm-net \                 # Shared Docker Network
  -p 4000:4000 \
  -e DATABASE_URL="postgresql://litellm:litellm@litellm-db:5432/litellm" \
  -e OPENAI_API_KEY="sk-..." \
  -e GEMINI_API_KEY="AIza..." \
  -e OR_API_KEY="sk-or-..." \
  -e LITELLM_MASTER_KEY="sk-..." \
  -v /opt/litellm/config.yaml:/app/config.yaml:ro \   # ✅ Config file mount (read-only)
  ghcr.io/berriai/litellm:main-latest \
  --port 4000 --config /app/config.yaml
```

Ohni as Docker Network wirsch du `localhost` im Container nid erreiche — bruch `postgresql://litellm:litellm@litellm-db:5432/litellm` (max 31 Zeiche für PostgreSQL-Rolle).

**Ohni PostgreSQL (nur Config-File, kei DB-Dependent Features):** `DATABASE_URL` nid setze → litellm lauft im *config-file-only mode*. Das bedütet: **kei `/key/generate`**, **kei Usage-Tracking**, **kei UI-Dashboard**. Models und Keys müend alli im Config-File oder als Environment-Variable defniert si.

### Option B: Ohni Docker (puristisch, bevorzugt — Venv + Systemd)

**Installation in Venv (kein `--break-system-packages` nötig):**

```bash
# Venv erstelle (einmalig)
python3 -m venv /opt/litellm/venv
source /opt/litellm/venv/bin/activate
pip install litellm[proxy]

# Config + .env vorbereite
mkdir -p /opt/litellm
cat > /opt/litellm/config.yaml << 'EOF'
model_list:
  - model_name: deepseek-v4-flash
    litellm_params:
      model: openrouter/deepseek/deepseek-chat
      api_key: os.environ/OR_API_KEY
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
EOF

cat > /opt/litellm/.env << 'EOF'
LITELLM_MASTER_KEY=sk-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
OR_API_KEY=sk-or-...
EOF
```

**Manuell starte (test):**
```bash
cd /opt/litellm
source /opt/litellm/venv/bin/activate
litellm --port 4000 --config /opt/litellm/config.yaml
```

### Option C: Systemd Autostart (für Produktiv)

Nach erfolgreichem Test Systemd-Service erstelle für **Autostart + Restart**:

```
# /etc/systemd/system/litellm.service
[Unit]
Description=LiteLLM Proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/litellm
EnvironmentFile=/opt/litellm/.env
ExecStart=/opt/litellm/venv/bin/litellm --port 4000 --config /opt/litellm/config.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now litellm
systemctl status litellm  # check
```

> **Warum EnvironmentFile?** Söttigi `.env`-Datei easy vo Host zu Host kopiert werde ohni Systemd-Unit z'ändere. Bi Provider-/Key-Änderige nume `.env` aapasse + `systemctl restart litellm`.

---

## Provider-Konfiguration

### Über Umgebungsvariable (schnelle Setup, kei Config-File nötig)

| Variable | Service | Status 121 |
|----------|---------|-----------|
| `OPENAI_API_KEY` | OpenAI GPT-4o-mini u. a. | ✅ gsetzt |
| `GEMINI_API_KEY` | Gemini 2.5 Flash | ✅ gsetzt |
| `OR_API_KEY` | OpenRouter (DeepSeek, Claude) | ✅ gsetzt |
| `LITELLM_MASTER_KEY` | LiteLLM Admin (UI) | ✅ gsetzt |
| `ANTHROPIC_API_KEY` | Claude direkt | ❌ leer |
| `COHERE_API_KEY` | Cohere | ❌ leer |
| `DEEPSEEK_API_KEY` | DeepSeek direkt | ❌ über Dashboard i DB (`references/deepseek-routing.md`) |

## Quick Health-Check (von LXC ohni Docker)

Wenn du **nid** uf em Host bisch wo de LiteLLM-Container lauft (z. B. Hermes im LXC ohni Docker-Socket):

```bash
# 1. Ping — läuft de Host?
ping -c 1 -W 2 <host-ip>

# 2. Port offe? (curl)
curl -s --connect-timeout 3 http://<host>:<port>/health
curl -s --connect-timeout 3 http://<host>:<port>/v1/models

# 3. SSH uf Host und Docker prüefe (wänn PW bekannt)
sshpass -p '<pw>' ssh -o StrictHostKeyChecking=no root@<host> 'docker ps --filter name=litellm --format "{{.Names}} {{.Status}}"'
sshpass -p '<pw>' ssh -o StrictHostKeyChecking=no root@<host> 'systemctl is-active docker 2>/dev/null'

# 4. Lokal Ports im Container scanne (wennd direkt druf bisch)
for p in 4000 4001 4002 4010 11434; do
  timeout 1 bash -c "echo >/dev/tcp/127.0.0.1/$p" 2>/dev/null && echo "$p: open" || echo "$p: closed"
done
```

**Typisches Fehlerbild:**
- Host pingbar (✅) + Port geschlossen (❌) = Prozess/Container läuft nid
- SSH möglich aber Docker-Socket fählt = Host het Docker service inactive
- LXC Container without Docker = SSH zum Host für Docker-Befehli nötig

Ohni `DATABASE_URL` lauft LiteLLM **config-frei** — d'Models wärded automatisch detektiert über die gsetzte API-Keys.

### Über Config-File (mit DB, für Production)

```yaml
# /etc/litellm/config.yaml
model_list:
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
  - model_name: deepseek-v4-flash
    litellm_params:
      model: openrouter/deepseek/deepseek-chat
      api_key: os.environ/OR_API_KEY
  - model_name: gemini-2.5-flash
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GEMINI_API_KEY
```

Starte mit Config:
```bash
litellm --port 4000 --config /etc/litellm/config.yaml
```

---

## Keys extrahiere (laufendi Instanz → neue Instanz)

### Via docker exec (Standard — env-Vars)

```bash
docker exec <container> env | grep -iE 'KEY|TOKEN|OPENAI|DEEPSEEK|GEMINI|ANTHROPIC'
```

### Via docker inspect

```bash
docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -i key
```

### Via Dokploy compose-Verzeichnis

D'LiteLLM-Instanz uf 121 lauft via Dokploy. D'Compose-Files und s'.env' ligged amene spezifische Ort:

```bash
# Projekt azeige (Name + Status + Config-Pfad)
docker compose ls

# .env direkt läse (dete wo au d'API-Keys drin sind)
cat /etc/dokploy/compose/<project-name>/code/.env

# Docker-compose.yml (nume Referenz, kei Keys drin)
cat /etc/dokploy/compose/<project-name>/code/docker-compose.yml
```

### Via LiteLLM `/credentials` API (maskiert — für Verifikation)

LiteLLM het en API-Endpunkt wo alli gsetzte Credentials mit **maskierte Keys** zeigt:

```bash
curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://<litellm-host>:4000/credentials | python3 -m json.tool
```

Output z. B.: `"api_key": "sk****1f"`. Hilft zum verifiziere OB en Key korrekt hinterleit isch, git aber **keine vollständige Key**.

### Via DB (verschlüsselt — NUR für Debugging)

Wänn `STORE_MODEL_IN_DB=True` und Keys übers Dashboard gsetzt worde, ligeds verschlüsslet i de PostgreSQL-DB:

```bash
# Credentials-Tabelle (maskiert/encrypted)
docker exec <container-db> psql -U litellm -d litellm \
  -c "SELECT credential_name, credential_values FROM \"LiteLLM_CredentialsTable\""

# Model-Configs inkl. api_key (verschlüsslet)
docker exec <container-db> psql -U litellm -d litellm \
  -c "SELECT model_name, litellm_params FROM \"LiteLLM_ProxyModelTable\""
```

**⚠️ Wichtig: D'Credentials sind mit em `LITELLM_MASTER_KEY` verschlüsslet.**
Au mit Root-Zugriff uf de Host chasch de Plaintext-Key **nid** extrahiere. De Key muess vom Original-Quelle neu g'holt oder us Notion/Memory gfunde werde.

### Remot via paramiko (SSH, kei Docker-CLI lokali)

```python
import paramiko, time
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('10.0.60.x', username='root', password='...', timeout=15)

stdin, stdout, stderr = client.exec_command("docker exec <container> env | sort")
for line in stdout.read().decode().strip().split('\n'):
    if any(k in line.upper() for k in ['KEY', 'TOKEN', 'OPENAI']):
        print(line)
client.close()
```

### Zusätzlich: SSH ohne sshpass (wenn nid installierbar)

Wänn sshpass nid verfügbar isch (z. B. i Container ohni Root), paramiko-Python direkt nutze:

```python
# Vorher: pip3 install paramiko --break-system-packages (falls nöd vorhande)
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.0.60.x', username='root', password='Louis_one_13', timeout=15)
stdin, stdout, stderr = ssh.exec_command('docker exec <container> env | sort')
print(stdout.read().decode())
ssh.close()
```

---

## Migration Host A → Host B

### Schnell: NuKeys kopiere (empfohle, ohni DB-Dump)

Für en reini Gateway-Instanz ohni DB-Dump:

1. **Keys vo laufender Instanz extrahiere** (lokal oder via paramiko):

   ```bash
   # Lokal: Docker env auslese
   docker exec <container> env | sort | grep -iE 'KEY|TOKEN|OPENAI|DEEPSEEK|GEMINI|ANTHROPIC|LITELLM'

   # Alternativ via docker inspect
   docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -iE 'key|token|openai|gemini'
   ```

2. **`.env` uf Ziel-Host erstelle** (nume die aktive Keys, Rest leer loh)
3. **`config.yaml` erstelle/übernäh** — Models liste wo brucht werde
4. **Systemd-Service erstelle** → (Option C)
5. **Teste:** `curl http://neuer-host:4000/v1/models`
6. **Hermes Config update** → `~/.hermes/config.yaml` uf neui Adrässe aapasse

### Vollständig: Inkl. DB-Dump

Wenn d'LiteLLM-Instanz en PostgreSQL-DataStore bruucht (z. B. für UI-Configs, Usage-Tracking):

```bash
pg_dump -h <alt-host> -U litellm litellm > litellm_dump.sql
psql -h <neu-host> -U litellm litellm < litellm_dump.sql
```

**Achtung:** Drunterligendi Provider-Keys (OpenAI, Gemini etc.) sind i de DB **nöd** gspeicheret — die müend immer via `.env`/`EnvironmentFile` gsetzt werde.

### Spezialfall: Keys über Dashboard gsetzt (in DB encrypted)

Wenn `STORE_MODEL_IN_DB=True` + Keys über s'LiteLLM-UI-Dashboard (Credentials-Tab) hinterlegt worde, sind si **verschlüsslet** i de `LiteLLM_CredentialsTable`. E Migration vo 121 (Docker) → 156 (bare-metal) wird zum Problem:

1. **Keys us DB extrahiere:** Geit nid — sind mit `LITELLM_MASTER_KEY` encryptet.
2. **DB-Dump uf neu Host:** Bringt nüt — d'Keys sind immer no encrypted, au uf neuem Host.
3. **Lösig:** De Plaintext-Key **mues vo de Original-Quelle** g'holt werde (z. B. platform.deepseek.com, openai.com dashboard). D'Credentials auf 121 händ keine sichtbare Plaintext-Key meh — au mit Root-Zugriff uf de Host.

**Praktisches Vorgehe bi Migration von 121 → 156:**
- `.env` kopiere → ✅ möglich (sind identisch)
- Applikations-Config (Proxy-Model-Table) via API neu erstelle → nötig
- DeepSeek-Key: entweder neue API-Key generiere, oder via OpenRouter routen (wenn Credits vorhande)

**Aufdecken vo DB-Keys via API:**

```bash
# Maske aaluege (nume letschti 2 Zeiche)
curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://<host>:4000/credentials | python3 -m json.tool

# Model-Detail vo DB-Models aaluege (zeigt Provider + encrypted Keys)
curl -s -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://<host>:4000/model/info
```

---

## Proxy API Keys (Model-restricted, no DB)

Ohni PostgreSQL-DB (`DATABASE_URL` nid gsetzt) funktioniert `/key/generate` nid. Stattdesse chasch **`proxy_api_keys`** i de Config defniere — festi Keys wo nume uf bestimmti Models beschränkt sind.

```yaml
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  proxy_api_keys:
    - key: sk-hermes-156-deepseek          # Neuer, fixer API-Key
      models:
        - deepseek-v4-flash                # Nur das Modell erlaubt
    - key: sk-readonly-all
      models:
        - "*"                               # Alle Models (Wildcard)
```

**Eigeschafte:**
- Keys sind **statisch** — nid via API generierbar, nid revocable einzeln
- Funktioniert au ohni DB perfekt
- `"*"` als Wildcard erlaubt alli Models, süsch e Liste vo Model-Names
- Im Hermes-Config chasch de Key direkt als `api_key` oder via env var verwende
- **Pitfall:** `/v1/models` listet IMMER alli Models uf — d'Restriktion wird ERST bim Chat Completion erzwunge (HTTP 401/403)

### Hermes-Integration

Im `~/.hermes/config.yaml`:

```yaml
model:
  default: deepseek-v4-flash
  provider: custom:litellm-local
  base_url: http://<litellm-host>:4000/v1
  api_mode: chat_completions

providers:
  litellm-local:
    name: LiteLLM Local
    base_url: http://<litellm-host>:4000/v1
    key_env: LITELLM_API_KEY          # Key via .env oder direkt
    default_model: deepseek-v4-flash
    models:
      deepseek-v4-flash:
        context_length: 65536
      gpt-4o-mini:
        context_length: 128000
      gemini-2.5-flash:
        context_length: 1048576
```

> **Wichtig:** D'Models wo über LiteLLM verfügbar send, müend im Hermes config.yaml **explizit** ufgfüehrt werde — Hermes discovers se nid automatisch.

### DB-backed Virtual Keys (STORE_MODEL_IN_DB=True)

Wenn `STORE_MODEL_IN_DB=True` gsetzt isch (Docker + PostgreSQL), chasch du **nid** `proxy_api_keys` i de Config bruche. Stattdesse generiersch Virtual Keys via d'LiteLLM API:

```bash
# Mitem Master Key en neue Virtual Key generiere
curl -s -X POST "http://<litellm-host>:4000/key/generate" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["deepseek-v4-flash", "gpt-4o-mini"],
    "metadata": {"user": "hermes-gateway"},
    "max_budget": 0.0
  }'
```

Response enthaltet e `"key": "sk-..."` wo i `LITELLM_API_KEY` i de Hermes `.env` gsetzt wird.

**Wichtig:**
- De Key isch i de DB gspicheret — er existiert **nid** i de Config-File
- Jeddi Verbindig zu LiteLLM brucht en registrierte Virtual Key (kei Random-`sk-`)
- `/key/generate` ohni `Authorization: Bearer $LITELLM_MASTER_KEY` git 401
- Ohni DB (`DATABASE_URL` nid gsetzt) funktioniert `/key/generate` nid — denn `proxy_api_keys` i de Config verwende (siehe obe)

## Verifikation

```bash
# Läuft?
curl http://localhost:4000/health

# Models?
curl http://localhost:4000/v1/models

# Chat Completion
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Sag Hallo"}]}'
```

---

## Pitfalls

### Docker vs Bare-Metal — Unterschiede

- **121 (Docker + PostgreSQL):** `/key/generate` funktioniert, Dashboard UI verfügbar, Usage-Tracking.
- **156 (Bare-Metal, kei DB):** `/key/generate` schlät fähl → `proxy_api_keys` in config.yaml verwende. Kei Dashboard.
- **Binary-Location:** Docker → Image-intern. Bare-Metal → `pip install` → `/usr/local/bin/litellm`.
- **.env Location:** Docker → Compose `environment:` oder Volume. Bare-Metal → `/etc/litellm/litellm.env` oder `~/.hermes/.env`.
- **Autostart:** Docker → Restart Policy. Bare-Metal → Systemd-Service nötig.
- **Server restart:** Docker → `docker restart litellm`. Bare-Metal → Prozess kill + neu starte.
- **Config-Edit:** Docker → Config am Volume mounte. Bare-Metal → `/etc/litellm/config.yaml` direkt editiere.

Siehe `references/bare-metal-on-host-156.md` für Vollständigi Doku vo de gelöschte Instanz.

- **Ohni DB = flüchtig** — Config-Änderungen über's UI sind wege nach Neustart. Für Produktiv: Postgres-DB oder Config-File.

- **Proxy-Architektur (Nova → LXC 100):** Wänn e LiteLLM-Instanz als reine Proxy zu ere andere Instanz fungiert (z. B. Nova:4000 → LXC 100:4000), chasch `database_url: null` setze — de Proxy brucht kei eigeti DB. D'Virtual Keys für de Upstream müend uf de Ziel-Instanz registriert si (i DB oder via Config). Lueg `references/proxy-architecture.md` für s'volle Architektur-Diagramm.

- **Virtual-Key Recovery via Direct DB Insert:** Wänn Virtual Keys nach eme Restart verlore gönd (`401 token_not_found_in_db`), chasch si über en direkte SHA256-Hash-Insert i d'Postgres-DB widerherstelle. **Ablauf:**
  1. Hash vom Key berechne: `echo -n "sk-zB0...-ONA" | sha256sum`
  2. Prüfe ob de Hash i de DB fählt: `SELECT token FROM "LiteLLM_VerificationToken" WHERE token = '<hash>';`
  3. Key i d'DB iiträge:
     ```sql
     INSERT INTO "LiteLLM_VerificationToken" (token, key_alias, models, metadata, spend, blocked)
     VALUES ('<sha256-hash>', 'key-name', '{}', '{"user": "description"}', 0, false);
     ```
  4. **Kei Neustart nötig** — d'Keys wärded sofort akzeptiert (DB-basierti Verifikation)
  5. **Master Key gliich behandle** — au de Master Key (`LITELLM_MASTER_KEY`) muess als Token i de DB existiere. Wänn er bi Migration/Neustart fählt, au per Direct Insert ergänze.
- **DeepSeek über OpenRouter** — brucht `OR_API_KEY`, nöd `DEEPSEEK_API_KEY`. Model-Prefix: `openrouter/`
- **DeepSeek direkt (deepseek/deepseek-v4-flash) benötigt DEEPSEEK_API_KEY** — De Key in `OPENAI_API_KEY` (sk-proj-...) funktioniert NID für DeepSeek. Git en "Authentication Fails (governor)" 401.
- **OpenRouter Credits leer → HTTP 402** — Fehler "This request requires more credits" bedütet: de OpenRouter-Account het s'Free-Tier ufbruucht. Lösig: Credits chaufe oder en anderi Route näh (direkte DeepSeek-Key).
- **/key/generate funktioniert NID ohni DB** — Wenn kei `DATABASE_URL` gsetzt isch, müend Keys über `proxy_api_keys` i de Config defniert werde.
- **Gemini SDK** brucht `pip install google-generativeai`, susch ImportError
- **User-Preference:** LiteLLM ohni Docker betriebe wenn möglich (Ressource-schoner, weniger Overhead)
- **`STORE_MODEL_IN_DB=True`** — mit dem Env-Var wärded Models i d'DB gschribe (nume mit PostgreSQL sinnvoll)
- **SFTP/paramiko: sftp.close() killt d'Connection** — Wenn mehreri Dateie via SFTP gschribe werde, muess alles vor em erschte `sftp.close()` fertig si. Alternativ: pro File en frische SSH-Client/SFTP-Session ufmache.
- **`/health/ready` git 404** — LiteLLM 1.84+ het `/health` under em OpenAI-Pfad. Verwend `curl http://localhost:4000/v1/models` für Health-Check, oder `/health/liveliness`.
- **Config-File-Recovery nach sed-Fehler:** Wänn `sed -i 's|database_url: null|...|'` d'Config zerstört (z. B. YAML-Struktur zerschosse), **nöd in Panik verfalle** — lueg öb es `.bak`-File git. Falls ned: d'Original-Config us em Skill (`references/proxy-architecture.md` oder Git-Repo) widerherstelle.
- **Credentials via Dashboard gsetzt sind unwiderbringlich encrypted** — Sobald en API-Key übers LiteLLM-Dashboard i d'DB gschribe wird, chasch ihn **nüme im Plaintext uslese**. D'API zeigt nume maskierti Keys (`sk****1f`). Für Migration: Plaintext-Key original vom Provider-Quelle neu hole oder über OpenRouter routen.
- **DeepSeek geit au ohni DEEPSEEK_API_KEY** — uf 121 funktioniert DeepSeek über `custom_llm_provider: "deepseek"` ohni expliziti `DEEPSEEK_API_KEY` i de `.env`. De Key isch über s'Dashboard i d'DB gschribe worde. E nöii Instanz brucht entweder de Key neu oder e alternativi Route (OpenRouter).
- **LiteLLM 1.84+ bare-metal brucht Prisma Engine Binary** — Sobald e `DATABASE_URL` gsetzt isch (au SQLite), initialisiert LiteLLM de Prisma Client. Dä brucht e Prisma Engine Binary (Go-Daemon) wo bim `prisma generate` normalerwies automisch us em Internet glade wird. Uf 156 isch de Download fählgschlage (kei Netz-/Platform-Match). **Symptom:** `httpx.ConnectError: All connection attempts failed` bim Startup. **Lösige:** (1) Ohni `DATABASE_URL` starte (nume Config-File-Mode), (2) Docker verwende (de Binary isch im Image), oder (3) Binary manuell us em Prisma CDN `https://binaries.prisma.sh/` installiere. (See `references/156-setup.md` für Details.)
- **Docker Container startet nid: PostgreSQL Connection Failed, aber PostgreSQL lauft** — `docker_prod_entrypoint.sh` erwartet `DATABASE_URL` im Format `postgresql://user:pass@host:5432/db`. **Wichtig:** `host` isch de Container-Name im Docker Network (z. B. `litellm-db`), nid `localhost`. Ohni Docker Network (`--network`) erreicht de LiteLLM-Container de PostgreSQL-Container nid. Lösig: Beidi Container im gliiche Network starte (`--network litellm-net` oder `docker network create litellm-net`).
- **Docker Volume `-v /opt/litellm:/app` zerstört de Container** — `/app` isch s'WorkingDir vom LiteLLM-Container mit Entrypoint, Prisma Engine und App-Code. Wänn du `/opt/litellm` (en leeres/anders Verzeichnis) uf `/app` mountsch, überschriebsch du alles. **Nur einzelni Files mounte:** `-v /opt/litellm/config.yaml:/app/config.yaml:ro`
- **Docker on Apollo (10.0.60.156) isch inactive** — `docker.service` isch disabled und nid am laufe. Wänn en LiteLLM-Container uf Apollo starte söll, muess zersch `systemctl start docker`. Hermes (LXC "Hermes-old") het kei direkte Docker-Socket — SSH zu root@10.0.60.156 (PW `Louis_one_13`) isch nötig für Docker-Befehli uf Apollo.

## Vollständigi Löschig (Backup + Wipe)

Wenn LiteLLM vo eme Host entfernt werde söll (z. B. usser Betrieb näh, migriere uf andere Host):

### Schritt 1: Backup erstelle

```bash
mkdir -p /tmp/litellm-backup

# Configs kopiere
cp /etc/litellm/config.yaml /tmp/litellm-backup/ 2>/dev/null
cp /etc/litellm/litellm.env /tmp/litellm-backup/ 2>/dev/null
cp /opt/litellm/config.yaml /tmp/litellm-backup/docker-config.yaml 2>/dev/null
cp /opt/litellm/docker-compose.yml /tmp/litellm-backup/ 2>/dev/null
cp -r /opt/litellm/data /tmp/litellm-backup/ 2>/dev/null

# Keys us .env extrahiere (nur LiteLLM-relevanti)
grep -E '^(LITELLM|DEEPSEEK|GEMINI|OPENAI|OPENROUTER)' /root/.hermes/.env > /tmp/litellm-backup/hermes-keys.env 2>/dev/null

# Versionsinfo
pip3 show litellm 2>/dev/null | grep -E '^(Name|Version|Location)' > /tmp/litellm-backup/litellm-package.txt 2>/dev/null
litellm --version > /tmp/litellm-backup/version.txt 2>/dev/null || echo "unknown" > /tmp/litellm-backup/version.txt
echo "docs.litellm.ai" > /tmp/litellm-backup/source.txt

# Tarball
DATE_TAG=$(date +%Y-%m-%d_%H%M%S)
tar czf /tmp/Litellm-backup_${DATE_TAG}.tar.gz -C /tmp/litellm-backup .
rm -rf /tmp/litellm-backup
echo "Backup: /tmp/Litellm-backup_${DATE_TAG}.tar.gz"
```

### Schritt 2: Upload zu MinIO + GitHub (oder alternativ)

**MinIO:** `mc cp /tmp/Litellm-backup_*.tar.gz homelab/hermes-backups/`

**⚠️ MinIO erreichbar?** Falls MinIO (10.0.60.106) vo 156 us nid erreichbar isch (Network-Isolation), alternativ via 121 uploade oder curl direkt.

**GitHub Release:**
```bash
curl -s -X POST \
  -H "Authorization: Bearer ***" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/GoetschiM/hermes-private-backups/releases" \
  -d '{"tag_name":"litellm-backup_$DATE_TAG","name":"LiteLLM Backup $DATE_TAG","body":"LiteLLM vo Host"}'
# Then upload asset
```

**⚠️ GitHub Token 401:** Falls Token abgloffe isch, lokal sichere: `cp /tmp/Litellm-backup_*.tar.gz /root/Litellm-hermes-108_backup.tar.gz`

### Schritt 3: Löschig

```bash
# 1. Prozess killä
KILLPID=$(ps aux | grep litellm | grep -v grep | awk '{print $2}')
[ -n "$KILLPID" ] && kill "$KILLPID" 2>/dev/null
sleep 2

# 2. Config löschä
rm -rf /etc/litellm
rm -rf /opt/litellm

# 3. Binary + Python Package
rm -f /usr/local/bin/litellm
rm -f ~/.local/bin/litellm
pip3 uninstall -y litellm 2>/dev/null
pip3 uninstall -y litellm-proxy 2>/dev/null

# 4. Env Keys use (nur die lokale Keys)
grep -vE '^(LITELLM_BASE_URL|LITELLM_API_KEY)' /root/.hermes/.env > /tmp/.env_clean
mv /tmp/.env_clean /root/.hermes/.env
```

**Pitfalls:**
- **MinIO unreachable vo 156 us** — `mc` hängt sich uf (timeout). Denn curl-Direktzugriff teste oder via SSH uf en andere Host.
- **Prozess in D (uninterruptible sleep)** — nach `kill` chas 3-5s bruuche bis de Prozess würkli verschwunde isch. `ps aux | grep litellm` no emal prüefe.
- **Env-Keys nur die lokale entferne** — NIE Keys löschä wo für en andere Host sind (z.B. `ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL`). Nur `LITELLM_BASE_URL` und `LITELLM_API_KEY` use.

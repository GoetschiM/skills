---
name: dograh-voice-platform
version: 3.0.0
description: "Dograh — Open Source Voice AI Platform uf CT117 (10.0.60.60). NEU SEIT 07.06.2026: Läuft nüm uf 10.0.60.167! Asterisk ARI 10.0.60.60:8088, AMI 10.0.60.60:5038. Vollständige Plattform-Capabilities: Asterisk ARI, Browser WebRTC, Embed Widget, MCP Server, Knowledge Base, Campaigns, Custom Tools, Recordings, SDKs. 120+ API Endpoints."
tags: [dograh, voice, ai, asterisk, ari, telephony, nova, docker, voice-ai, pipecat, webrtc, mcp, embed, knowledge-base, campaigns, tools, sdk]
category: telephony
---

# Dograh Voice AI Platform 🎙️

## Overview

Dograh is an **open source voice AI platform** — a self-hosted alternative to Vapi/Retell. Es isch uf **Nova (10.0.60.167)** deployt, direkt bim lokale Asterisk.

| Funktion | Beschrieb |
|-----------|-----------|
| 🎤 **Speech-to-Speech** | STT → LLM → TTS Voice Pipeline |
| 🧩 **Visual Workflow Builder** | Drag & Drop (kei Code) |
| 📞 **Telefonie** | Asterisk ARI (lokal!), Twilio, Vonage, Telnyx |
| 🌐 **Browser WebRTC Call** | Ohni Telefon! Direkt im Browser rede |
| 🔌 **MCP Server** | AI-Assistente (Claude Code, Cursor) verbinde |
| 🌍 **Embed Widget** | Voice-Bot i Website iibette |
| 🧠 **Knowledge Base / RAG** | Dokument-Upload + semantischi Suche |
| 🎯 **Campaigns** | Automatisierte Outbound-Calls mit CSV |
| 🛠️ **Custom Tools** | HTTP/MCP Tools für API-Integration |
| 🗂️ **Recordings** | Automatischi Transkripte + Aufnahme |
| 💬 **Text Chat** | Non-Voice Chat Sessions pro Workflow |
| 📦 **SDKs** | Python + Node.js |

## Trigger Conditions

- User frogt nach theoretische Use Cases: Smart Home, ESP32, Website-Embed, Nextcloud-Talk
- User frogt nach Dograh-Setup, Login, Konfiguration
- User will Voice AI Platform / Asterisk Voice Bot
- User will Browser-WebRTC-Call (ohni Telefon)
- User will Knowledge Base / RAG für Dokument
- User will Kampagne / Bulk-Outbound
- User will Custom Tools / Tool-Integration (Smart Home, API)
- User will Hermes-API-Integration für Voice Workflows
- User frogt nach Embed-Widget für Website / Nextcloud
- User frogt nach MCP-Server-Integration
- User frogt nach Asterisk ARI Provider

## Deployment — Nova (10.0.60.167)

### Info

| | |
|---|---|
| **Host** | Nova (10.0.60.167) |
| **SSH** | `ssh root@10.0.60.167` (Passwort: `Louis_one_13`) |
| **Typ** | Docker Compose |
| **Pfad** | `/opt/dograh/configs/dograh/` |
| **UI** | `http://10.0.60.167:3010` |
| **API** | `http://10.0.60.167:8000` |
| **Version** | 1.32.0 |

### Voraussetzige

- Docker + Docker Compose (Docker 29.1.3+, Docker Compose 2.40.3+)
- Asterisk mit ARI (lauft scho uf Nova!)

### Deployment-Schritt

```bash
# 1. Docker installiere (falls nöd vorhande)
apt-get install docker.io docker-compose-v2 -y

# 2. Clone / Download compose
mkdir -p /opt/dograh && cd /opt/dograh
curl -sL "https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml" -o docker-compose.yaml

# 3. .env erstelle
echo "OSS_JWT_SECRET=$(openssl rand -hex 32)" > .env
echo "ENVIRONMENT=local" >> .env
echo "ENABLE_TELEMETRY=false" >> .env

# 4. Starte
docker compose pull && docker compose up -d
```

### 🔴 CRITICAL PITFALL — UI BACKEND_URL

**MUSS** uf Host-IP zeige, nöd uf `api:8000` (Docker-intern). Sonst cha de Browser sich nöd aabinde.

```bash
cd /opt/dograh
docker stop dograh-ui-1 && docker rm dograh-ui-1
BACKEND_URL=http://10.0.60.167:8000 docker compose up -d ui
```

### Account

| | |
|---|---|
| **Email** | `michel@besorgsdir.ch` |
| **Passwort** | `Dograh2026!` |
| **Organisation** | 1 (OSS) |

## Container

```bash
$ docker ps --format 'table {{.Names}}\t{{.Status}}'
dograh-ui-1          Up (unhealthy — gesundheitstest z'churz, UI lauft trotzdem)
dograh-api-1         Up (healthy)
dograh-postgres-1    Up (healthy)
dograh-redis-1       Up (healthy)
minio                Up (healthy)
cloudflared-tunnel   Up
```

## Asterisk ARI Integration

**Dograh HET en komplette Asterisk ARI Provider** — code in `api/services/telephony/providers/ari/`.

### Konfiguration

| Setting | Wert | Beschrieb |
|---------|------|-----------|
| `ari_endpoint` | `http://10.0.60.167:8088` | ARI-REST-API uf Nova lokal |
| `app_name` | `callbot` | Stasis-App im Dialplan |
| `app_password` | `HermesVB2026` | ARI-User-Passwort |
| `ws_client_name` | `dograh` | websocket_client.conf |
| `from_numbers` | `["0796459743"]` | Outbound-Caller-ID |

### ARI User (Asterisk Config)

ARI-User `callbot` isch i `/etc/asterisk/ari.conf`:
```
[callbot]
type = user
read_only = no
password = HermesVB2026
```

### Dialplan (extensions.conf)

```
[hermes-ari]
exten => callbot,1,Stasis(callbot)
```

### ARI Manager

Dograh bruucht en separate **ARI Manager** Process wo d'WebSocket-Verbindig zu Asterisk haltet.

```bash
# Starte
cd /opt/dograh && docker compose exec -d api python3 /app/api/services/telephony/ari_manager.py

# Check Logs
docker compose logs api | grep -i ari | tail -10
```

## ARI Manager — Operations

See `references/ari-manager-operations.md` for:
- Start/restart commands
- Status verification
- ARI user creation on Asterisk
- Known limitations (no auto-restart on Docker compose restart)

### 🔴 Wichtig: Network

Asterisk lauft uf de **Docker-Host-Maschine (CT117 = 10.0.60.60 seit 07.06.2026)**, nöd i Docker. D'API-Container muess über d'Host-IP `10.0.60.60:8088` zügriefe, nöd über `localhost:8088` (localhost im Container isch de Container selber!).

## Nützlichi Befähl

```bash
# UI test
curl -s -o /dev/null -w '%{http_code}' http://localhost:3010/auth/login

# API health
curl -s http://localhost:8000/api/v1/health | grep -o '"version":"[^"]*"'

# ARI Manager status
docker compose logs api | grep 'WebSocket connected'

# ARI config i DB
docker compose exec -T postgres psql -U postgres \
  -c 'SELECT id, name, provider, credentials::text FROM telephony_configurations;'

# User account erstelle
curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@domain.ch","password":"Pass123!","name":"Name"}'
```

## Dograh — Vollständige API-Capabilities (120+ Endpoints)

Dograh isch **viel meh als nume Telefonie**. Es isch e kompletti Voice-AI-Plattform mit dene Domain':

| Domain | Endpoints | Purpose |
|--------|-----------|---------|
| 📞 **Telephony** | ~20 | Asterisk ARI, Twilio, Vonage, Telnyx, Vobiz, Cloudonix — Inbound/Outbound/Transfer |
| 🧩 **Workflows** | ~25 | Visual Builder: Create, Draft, Publish, Validate, Duplicate, Versions |
| 🎯 **Campaigns** | ~10 | CSV-Import, Start/Pause/Resume, Redial, Report, Progress |
| 🧠 **Knowledge Base** | 6 | Documents upload, RAG Search, Processing (PDF/TXT/CSV) |
| 🛠️ **Tools** | 8 | Custom HTTP-Tools, MCP Tools, Archive/Unarchive |
| 🔑 **Auth & Users** | ~8 | Login, Signup, API Keys, Service Keys, Configs |
| 🏢 **Organizations** | ~20 | Telephony Configs, Phone Numbers, Langfuse, Usage/Billing |
| 🎤 **Recordings** | 6 | Upload, List, Transcribe, Delete |
| 💬 **Text Chat** | 4 | Non-voice Chat Sessions per Workflow |
| 🌐 **Embed** | 4 | Public Embed Widget for Websites |
| 🌍 **Public APIs** | ~6 | Initiate Call by UUID, Download Artifacts |
| 🔌 **MCP Server** | 1 | Model Context Protocol — AI Assistants connect directly |
| 📊 **Reports** | 3 | Daily Runs, Workflow Options, Report Download |
| 🗄️ **S3 Storage** | 3 | Presigned Upload, File Metadata |

**Full API endpoint list:** See `references/api-endpoints.md`

### 🎮 Browser WebRTC / Web Call (ohni Telefon!)

Dograh het **WebRTC built-in**. Du chasch en Voice-Bot **direkt im Browser** teste — kei SIP, kei Asterisk, kei Telefon nötig.

```bash
# Öffne im Browser:
http://10.0.60.167:3010/workflow/{workflow_id} → "Web Call"
```

➡️ **Use Case:** Michel im Auto → Browser ufmache → Dograh aarüefe → plaudere. Bruucht nur WLAN/5G.

### 🌐 Embed Widget — I Website iibette

Dograh stellt öffentlichi Embed-Endpoints z'verfüegig (`/api/v1/public/embed/*`). Du chasch e **Voice-Bot direkt uf e Website setze**:

- GET `/api/v1/public/embed/config/{token}` — Widget-Config abruefe
- POST `/api/v1/public/embed/init` — Embed Session starte
- GET `/api/v1/public/embed/turn-credentials/{session_token}` — WebRTC TURN Credentials

➡️ **Nextcloud Talk:** Chöntsch en Embed-Widget i Nextcloud-Dashboard oder en iframe i d'Wiki iibette.

### 🔌 MCP Server — AI-Assistenten verbinde

Dograh het en **MCP (Model Context Protocol) Server**: `/api/v1/mcp/`. AI-Assistente (Claude Code, Claude Desktop, Cursor) chönd sich verbinde und d'Dograh-Workspace stüre.

```bash
claude mcp add --transport http dograh http://10.0.60.167:8000/api/v1/mcp/ \
  --header "X-API-Key: YOUR_API_KEY"
```

➡️ **Hermes + Dograh:** Hermes (oder Claude Code) voit Dograh direkt stüre — Workflows erstelle, Calls starte, Knowledge Base durchsueche.

### 🧠 Knowledge Base / RAG

Dograh cha **Dokument hochlade, verarbeite und semantisch durchsueche**:

- POST `/api/v1/knowledge-base/upload-url` — Presigned URL für PDF/TXT/CSV-Upload
- POST `/api/v1/knowledge-base/process-document` — Processing starte
- POST `/api/v1/knowledge-base/search` — Similar Chunks finde (RAG)

➡️ **Use Case:** Alli Goetschi-Doku (Confluence, Obsidian, Qdrant) als PDF i Dograh ladde → Bot het Kontext über alles.

### 🛠️ Custom Tools — Smart Home, API-Integration, Alles

Dograh het es vollständigs Tools-System:

| Tool-Feature | Beschrieb |
|-------------|-----------|
| HTTP Tool | `POST/GET` zu beliebigem Endpoint |
| MCP Tool | Automatischi Synchro vo externe MCP Servern |
| Archive/Unarchive | Tools deaktiviere/reaktiviere |
| Refresh MCP | Neu-Synchro vo MCP-Server-Tools |

➡️ **Smart Home:** Tool `http://10.0.60.156:8123/api/services/light/turn_off` + Workflow → "Dograh, Licht us" → HTTP-Call → Home Assistant → Feedback per TTS.

### 🎯 Campaigns — Automatisierte Outbound-Aaruaf

Dograh cha **Kampagne mit hunderte vo Aaruaf** starte:

| Feature | Endpoint |
|---------|----------|
| CSV import | POST `/api/v1/campaign/create` |
| Start/Pause/Resume | `/api/v1/campaign/{id}/start`, `/pause`, `/resume` |
| Redial | `/api/v1/campaign/{id}/redial` |
| Report | `/api/v1/campaign/{id}/report` (CSV Download) |

➡️ **Use Case:** Statt jedem Martin-Nerd-Call einzle → Kampagne wo automatischi Tages-Überprüfige macht.

### 💬 Text Chat (ohni Voice)

Dograh unterstützt au **Text-Chat-Sessions** pro Workflow — kei Audio nötig:

- POST `/api/v1/workflow/{id}/text-chat/sessions` — Session starte
- POST `/api/v1/workflow/{id}/text-chat/sessions/{run_id}/messages` — Nachricht sende
- POST `/api/v1/workflow/{id}/text-chat/sessions/{run_id}/rewind` — History zurücksetze

### 📦 SDKs

Dograh bietet offizielli SDK:

- **Python:** `pip install dograh-sdk`
- **Node.js:** `npm install @dograh/sdk`

➡️ **ESP32/Mikrocontroller:** Python SDK ermöglicht Embedded-Integration via REST API.

## Theoretischi Use Cases — Was alles mögli wär

| Use Case | Technisch | Wie? |
|----------|-----------|------|
| 🚗 **Im Auto plaudere** | Smartphone Browser → Dograh WebRTC Call | Browser ufmache -> "Web Call" -> rede |
| 🛋️ **"Hey Hermes" dehei** | Raspberry Pi + Mic + Wake-Word → Browser automatischi starte | ESPHome / Porcupine -> WebRTC -> Dograh |
| 🏭 **Smart Home Sprachsteuerig** | Custom Tool → Home Assistant API | "Dograh, Licht us" -> HTTP POST -> HA |
| 📲 **App-ähnlich** | PWA auf Home Screen | QR-Code -> Link -> Browser-Call |
| 🏪 **Website Widget** | Embed Widget in iframe | GET /embed/config/{token} -> HTML-Seite |
| 🧠 **Info-Bot (Doku)** | RAG über Goetschi-Doku | PDF in Knowledge Base -> Fragen stelle |
| 🌍 **Handy global** | Telegram/WhatsApp -> Dograh WebRTC-Link | Link teile -> Browser-Call |

## Nextcloud Talk — Integration

Dograh het **KEI** direkte Nextcloud Talk Integration. Mögliche Wege:

1. **Embed Widget** — Dograh Widget (iframe) i Nextcloud-Dashboard, Tab oder Talk-Nachricht
2. **Custom Tool → Talk API** — Dograh ruft Nextcloud Talk API uf (`/ocs/v2.php/apps/spreed/api/v1/chat/{token}`) für Nachrichte
3. **Umkeert via Webhook** — Nextcloud ruft Dograh's `/api/v1/telephony/initiate-call` uf
4. **Hermes als Brücke** — Hermes hockt i Talk, triggert Dograh via MCP/API

## Hardware — ESP32 / Raspberry Pi Wake-Word

**Mikrofon + Lautsprecher + WLAN** (ESP32-S3-Box, M5Stack Atom Echo, Raspberry Pi):

```text
[ESP32] → Wake-Word "Hey Hermes" → Audio captured → HTTP POST → [Dograh API]
                                                                    ↓
[ESP32] ← Audio playback ← TTS ← Dograh Workflow ← LLM ← STT ← 
```

Dograh's WebRTC und REST API mached das möglich. Python SDK cha uf em Middleman laufe, oder direkt via REST API.

## Architektur — Dograh + Hermes API Layer (geplant)

```
Nova (10.0.60.167)
┌──────────────────────────────────────────┐
│                                          │
│  ┌──────────────────┐                    │
│  │ Asterisk (18.10) │──ARI (localhost)───│─┐
│  │                  │                    │ │
│  └──────────────────┘                    │ │
│                                          │ │
│  ┌──────────────────────────────────┐    │ │
│  │  Dograh (Docker)                │    │ │
│  │  ┌──────────┐  ┌───────────┐    │    │ │
│  │  │ UI:3010  │  │ API:8000  │◄───┼────┘ │
│  │  └──────────┘  └─────┬─────┘    │      │
│  │                      │          │      │
│  └──────────────────────┼──────────┘      │
│                         │                 │
│  ┌──────────────────────┴──────────┐      │
│  │  Hermes API Layer (geplant)     │      │
│  │  → Agent Loop + Tools + Memory  │      │
│  └─────────────────────────────────┘      │
│                                            │
│  🐳 Docker läuft im Hintergrund            │
└────────────────────────────────────────────┘
```

**Dograh = Voice Layer** (Asterisk ARI, STT/TTS, Workflows)
**Hermes = Brain** (Agent Logic, Tools, Memory, Skills, Qdrant)

Dograh ruft Hermes über en API-Endpoint auf — nöd eifach en LLM, sondern de volli Agent.

## Hermes-Integration (geplant)

Statt Dograh eifach mit LiteLLM z'verbinde, wird Dograh en **Custom HTTP Tool** ha wo uf en Hermes-API-Endpoint zeigt:

1. Call kommt i → Dograh verarbeitet Voice (STT) → Text
2. Text wird a Hermes gschickt (HTTP POST)
3. Hermes macht Agent-Logik + Tool-Calls + Memory-Retrieval
4. Antwort chunnt zrugg zu Dograh → TTS + Voice Output
5. User gseht en natürliche Dialog mit vollem Kontext

## Related Skills

### asterisk-voice-agent — Low-Level Live Dialog Pipeline

For the **low-level Asterisk ARI voice pipeline** (VAD → STT → LLM → TTS via ExternalMedia RTP livestream), see the `asterisk-voice-agent` skill (`telephony/asterisk-voice-agent`). It provides:

- Real-time bidirectional voice dialog on phone calls
- ExternalMedia RTP input (receives caller's audio as μ-law RTP)
- Bridge playback output (sends TTS via Asterisk sound files)
- VAD turn-taking with barge-in support
- gTTS TTS proxy server
- Full state machine pattern for open-mic dialog

**Relationship:** `asterisk-voice-agent` = the low-level ARI pipeline building block. Dograh = the full platform that can orchestrate multiple such pipelines with UI, campaigns, Knowledge Base, and 120+ API endpoints.

## References

- `references/api-endpoints.md` — Full Dograh API endpoint list (120+ endpoints, grouped by domain)
- `references/ari-manager-operations.md` — ARI Manager start/restart/check/known issues
- `references/nova-deployment-log.md` — Full deployment log from 30.05.2026 (step-by-step with exact commands)
- `references/asterisk-ari-integration.md` — Asterisk ARI config detail
- `references/use-cases-and-security.md` — Platform capabilities research, use-case matrix with priorities (GL-126 to GL-131), security architecture, and hardware integration options

## Pitfalls

- **🔴 BACKEND_URL** — Mues Host-IP sii, nöd `api:8000`
- **🔴 ARI endpoint** — Mues `10.0.60.167:8088` sii, nöd `localhost:8088`
- **🔴 ARI Manager** — Startet nöd automatisch. Mues nach jedem Docker-Neustart neu gstartet werde via `docker compose exec -d`
- **🔴 ARI Username = Stasis-App-Name** — Dograh bruucht `app_name` au als ARI-Username. ARI-User `callbot` muess i ari.conf existiere
- **🔴 Dograh's `ari` Provider isch nöd i de UI-Metadaten** — nöd is Dropdown voreingstellt. ARI-Config muess direkt i DB gschribe werde
- **🔴 Node Types endpoint (GET /api/v1/node-types) lieferet leers / parse-fail** — De Endpoint existiert im Code, aber die Rückgab isch nöd konsistent. Workflow-Builder funktioniert trotzdem via UI
- **🔴 Tools list (GET /api/v1/tools/) lieferet oft 0 Einträg** — Custom Tools müend über s'UI aagleit werde, erst dänn sind si per API sichtbar
- **🔴 UI Health-Check isch z'churz (3s)** — Container zeigt "unhealthy" aber UI lauft trotzdem. Das isch en bekannte Dograh-Bug
- **🔴 OpenAPI Schema isch under `/api/v1/openapi.json`** — Nöd under `/openapi.json` (FastAPI default!). Swagger UI isch under `/docs`
- **🔴 JSON-Escaping i SSH-Heredocs** — Schriib JSON immer i Datei und verwand `-d @file.json`
- **🔴 WebRTC brucht TURN-Server** — Dograh het en TURN-Container im Stack, aber TURN isch standardmässig deaktiviert. Mues i de Organization-Config aktiviert werde für Browser-Calls von usserhalb

# Dograh Use Cases — Research Results (31.05.2026)

> **Source** Dograh API v1.32.0 (120 endpoints), GitHub README, docs.dograh.com
> **Doku:** Obsidian `Dograh Use Cases Research.md`, Notion Goetschi Labs, Qdrant goetschi_labs_memory

## Dograh's Platform Capabilities

| # | Domain | What it does | Endpoints |
|---|--------|-------------|-----------|
| 1 | **Browser WebRTC Web Call** | Voice call directly in browser — no phone/SIP needed | WebRTC built into UI |
| 2 | **Embed Widget** | Voice bot as JavaScript widget in any website | `/api/v1/public/embed/*` (4) |
| 3 | **MCP Server** | AI assistants connect to Dograh (Claude Code, Cursor) | `/api/v1/mcp/` endpoint |
| 4 | **Knowledge Base / RAG** | Upload PDF/TXT/CSV, semantic search | `/api/v1/knowledge-base/*` (6) |
| 5 | **Custom Tools** | HTTP + MCP tools for API integration | `/api/v1/tools/*` (8) |
| 6 | **Campaigns** | Automated outbound campaigns with CSV import | `/api/v1/campaign/*` (10) |
| 7 | **Text Chat** | Non-voice chat sessions per workflow | `/api/v1/workflow/*/text-chat/*` (4) |
| 8 | **Recordings + Transcribe** | Auto-record + transcribe calls | `/api/v1/workflow-recordings/*` (6) |
| 9 | **SDKs** | Python (`dograh-sdk`) + Node.js (`@dograh/sdk`) | Package registries |
| 10 | **API Keys / Service Keys** | Secure programmatic access | `/api/v1/user/api-keys/*` |

## Concrete Use Cases (priorisiert)

### 🔴 Prio 1: Hermes API Layer — Dograh als Voice, Hermes als Brain
- Dograh ruft Hermes via HTTP-Webhook statt nur LLM
- Hermes macht: Tools, Memory, Skills, Qdrant, Google, Smart Home
- Dograh macht: STT, TTS, WebRTC, Asterisk ARI, Workflow-Logik
- **GL-129** | Architektur: HTTP-Tool in Dograh → POST zu Hermes-API-Endpoint

### 🟡 Prio 2: Smartphone Browser Web Call
- NIX entwickeln! Dograh UI hat "Web Call" integriert
- Smartphone im Auto: Browser → `http://10.0.60.167:3010` → Web Call → rede
- QR-Code generieren / Lesezeichen auf Homescreen
- **GL-126** | Security: LAN = direkt; WAN = nur Tailscale/VPN

### 🟡 Prio 3: Smart Home Sprachsteuerung
- Dograh Custom Tool: HTTP-POST to Home Assistant
- "Dograh, Licht us" -> Workflow -> Tool-Node -> HA API -> TTS-Feedback
- Works for: Lights (Hue), Temp (Ecoflow), Switches (Shelly)
- **GL-127**

### ⚪ Prio 4: M5Stack / ESP32 "Hey Hermes" Device
- M5Stack Core2 / Atom Echo with mic + speaker + WiFi
- **LAN mode:** permanent connected at home, wake-word triggers WebRTC
- **WAN mode:** Tailscale VPN (ESP32-Tailscale exists), M5Stack in same tailnet as Nova
- **GL-128** | Security: MUST be "brutal safe" — no open ports

### ⚪ Prio 5: Nextcloud Talk Integration
- **Embed Widget:** Dograh as iframe/JS widget in Nextcloud Dashboard
- **API:** Dograh calls Nextcloud Talk API to send messages
- **Reverse:** Talk room triggers Dograh call via `/api/v1/telephony/initiate-call`
- **GL-130**

### ⚪ Prio 6: WhatsApp/Telegram Voice
- No direct Dograh integration for WhatsApp/Telegram
- Workaround: Hermes sends audio notes via Telegram -> Dograh processes
- **GL-131**

## Security Architecture

```
LAN (heimisches WLAN):
  [Browser/M5Stack] --HTTP/WebRTC--> [Nova:3010/8000]  (direct, no encryption)

WAN (unterwegs):
  [M5Stack/Handy] --Tailscale (Wireguard)--> [Nova Tailscale IP]  (encrypted, auth)
  
NIE:
  [Browser] --offenes Internet--> [Nova:3010]  (VERBOTEN — kein Port forward!)
```

### Prinzipien
1. **LAN:** Direct HTTP access — no TLS needed on internal network
2. **WAN:** Only via Tailscale (Wireguard VPN) — encrypted + authenticated
3. **Dograh ports (3010, 8000):** NEVER exposed to public internet
4. **Cloudflare Tunnel:** Only for Nextcloud, never for Dograh
5. **TURN:** Coturn in Dograh stack secures WebRTC NAT-traversal
6. **Tailscale:** M5Stack, Nova, and Hermes agent in same tailnet

## Hardware Integration Options

| Device | Mic | Speaker | WiFi | Animal | Best for |
|--------|-----|---------|------|--------|----------|
| **M5Stack Core2** | ✅ Built-in | ✅ Built-in | ✅ | M5Stack | Voice assistant, tabletop |
| **M5Stack Atom Echo** | ✅ PDM | ✅ Speaker | ✅ ESP32-PICO | Tiny | "Hey Hermes" wake-word |
| **ESP32-S3-Box** | ✅ | ✅ | ✅ | ESP32-S3 | All-in-one smart speaker |
| **Raspberry Pi** | ✅ (USB) | ✅ (3.5mm) | ✅ | | Flexible, middleware |

### Linux SBC Basic Recipe (see GL-128)
```
hardware setup:
  1. Flash firmware with WiFi + Tailscale support
  2. Install wake-word engine (Porcupine / Snowboy — offline)
  3. Register Dograh API key for auth

on wake-word "Hey Hermes":
  1. Capture audio from mic
  2. Open WebRTC connection to Dograh (browser call equivalent)
  3. Stream audio bidirectionally
  4. On idle timeout → close connection

security:
  - Tailscale mesh for WAN access (no open ports)
  - API key rotated monthly
  - Audio stream encrypted via WebRTC (DTLS-SRTP)
```

## Jira Tickets Created

| Key | Summary | Prio |
|-----|---------|------|
| GL-126 | Browser Web Call — Smartphone unterwegs | Highest |
| GL-127 | Smart Home Integration via Custom Tools | High |
| GL-128 | M5Stack/ESP32 'Hey Hermes' Device | High |
| GL-129 | Hermes API Layer — Dograh Voice, Hermes Brain | High |
| GL-130 | Nextcloud Talk Integration | Medium |
| GL-131 | WhatsApp/Telegram Voice | Low |

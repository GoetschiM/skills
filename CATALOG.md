# 🧠 Skills-Katalog - Goetschi Labs

_Total: 136 Skills_


##  (2)

- **dogfood** — Exploratory QA of web apps: find bugs, evidence, reports.
- **yuanbao** — Yuanbao (元宝) groups: @mention users, query info/members.

## autonomous-ai-agents (4)

- **claude-code** — Delegate coding to Claude Code CLI (features, PRs).
- **codex** — Delegate coding to OpenAI Codex CLI (features, PRs).
- **hermes-agent** — Configure, extend, or contribute to Hermes Agent.
- **opencode** — Delegate coding to OpenCode CLI (features, PR review).

## creative (20)

- **architecture-diagram** — Dark-themed SVG architecture/cloud/infra diagrams as HTML.
- **ascii-art** — ASCII art: pyfiglet, cowsay, boxes, image-to-ascii.
- **ascii-video** — ASCII video: convert video/audio to colored ASCII MP4/GIF.
- **baoyu-comic** — Knowledge comics (知识漫画): educational, biography, tutorial.
- **baoyu-infographic** — Infographics: 21 layouts x 21 styles (信息图, 可视化).
- **claude-design** — Design one-off HTML artifacts (landing, deck, prototype).
- **comfyui** — Generate images, video, and audio with ComfyUI — install, launch, manage nodes/models, run workflows with parameter injection. Uses the official comfy-cli for lifecycle and direct REST/WebSocket API for execution.
- **ideation** — Generate project ideas via creative constraints.
- **design-md** — Author/validate/export Google's DESIGN.md token spec files.
- **excalidraw** — Hand-drawn Excalidraw JSON diagrams (arch, flow, seq).
- **humanizer** — Humanize text: strip AI-isms and add real voice.
- **manim-video** — Manim CE animations: 3Blue1Brown math/algo videos.
- **p5js** — p5.js sketches: gen art, shaders, interactive, 3D.
- **pixel-art** — Pixel art w/ era palettes (NES, Game Boy, PICO-8).
- **popular-web-designs** — 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS.
- **pretext** — Use when building creative browser demos with @chenglou/pretext — DOM-free text layout for ASCII art, typographic flow around obstacles, text-as-geometry games, kinetic typography, and text-powered generative art. Produces single-file HTML demos by default.
- **sketch** — Throwaway HTML mockups: 2-3 design variants to compare.
- **songwriting-and-ai-music** — Songwriting craft and Suno AI music prompts.
- **threejs-agent-visualization** — Build 3D agent visualization worlds using React Three Fiber — isometric office spaces, voxel-style agent avatars, status animations, speech bubbles, and autonomous agent behavior loops. Inspired by OpenClaw Office.
- **touchdesigner-mcp** — Control a running TouchDesigner instance via twozero MCP — create operators, set parameters, wire connections, execute Python, build real-time visuals. 36 native tools.

## data-science (2)

- **jupyter-live-kernel** — Iterative Python via live Jupyter kernel (hamelnb).
- **qdrant** — Qdrant Vector Database — Goetschi Labs Instanz auf 10.0.60.121:6333. Collections: goetschi_labs_contacts (214 Kontakte), goetschi_labs_memory (51pts), Test-RAG. Import, Query, Backup & Telegram-Integration.

## devops (19)

- **all-inkl** — All-Inkl.com Webhosting MCP — Verwaltet Domains, DNS, E-Mail, DBs via KAS-SOAP-API. Nutzt entweder direkt CLI (Skill-Modus) oder MCPHub (Server-Modus). Zwei Modi: Skill (für Hermes) und MCP-Server (für ALLI Agents via Gateway).
- **browserless-chromium** — Browserless (headless Chromium) Docker-Container auf dem Dokploy-Host — Port 3005, Token, API-Endpoints, Nutzung im Hermes-Container.
- **deploy-mcp-server** — Deploy MCP servers that ANY agent can use. Covers mcp-proxy (Python) for wrapping stdio MCPs as HTTP/SSE servers, Docker-based deployment, MCPHub integration, systemd services, and SDK incompatibility fixes. NOT about the Hermes Native MCP client itself.
- **dokploy** — Manage Dokploy-deployed Docker services — SSH host access, compose file editing, port publishing, service redeploy, health verification.
- **goetschi-labs-site-mcp** — Goetschi Labs Website — React/Vite SPA analysieren, Portfolio-Seiten deploye, Team-Daten aus minified JS extrahiere — alles ohnni direkte SSH-Zugriff uf 121.
- **ha-shelly-bridge** — Sync a Home Assistant switch/input_boolean state to a physical Shelly relay, with tirith security workarounds for private-network access.
- **hermes-backup** — Backup Hermes configuration to MinIO S3 + GitHub Releases. Covers scheduling, verification, selective restore, dual-backup scripts, and identity-safe operations.
- **kali-container** — Kali Linux als LXC-Container (Proxmox 02) — Vollständigi Pentest-, OSINT- + Network-Tool-Suite
- **kanban-orchestrator** — Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
- **kanban-worker** — Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itself is auto-injected into every worker's system prompt as KANBAN_GUIDANCE (from agent/prompt_builder.py); this skill is what you load when you want deeper detail on specific scenarios.
- **media-automation** — Deploy and configure the ArrStack — qBittorrent, Prowlarr, Sonarr, Radarr, and Plex — for automated media downloads with German content prioritization. Covers Docker Compose setup, indexer configuration, quality profiles, and integration patterns.
- **mt5-trading-bot** — Manage MT5 trading bots via their FastAPI web backends — authenticate, query status/performance/history, diagnose offline issues, interact with dashboard.
- **n8n-api-automation** — Programmatically create, activate, and manage n8n workflows and credentials via the REST API. Covers workflow JSON structure, credential types, webhook setup, and the specific quirks discovered on Goetschi Labs' n8n instance (10.0.60.121:5678).
- **nextcloud-admin** — Nextcloud administration via direct database & occ access — password recovery, app management, user creation, Talk setup — when the web UI is slow or unreachable.
- **proxmox-lxc** — Proxmox LXC container management — create, start, quorum fix, Docker-in-LXC setup on single-node clusters.
- **proxmox-password-reset** — Passwörter i Docker-DB-Containere zrugsetze via Proxmox-Host — für Dokploy, Coolify, Nextcloud und anderi Docker-DB-Dienst.
- **system-monitoring** — Periodic system health checks via no_agent cronjobs — check TCP, HTTP, DNS services; alert-on-failure via Telegram; auto-log to Qdrant.
- **unifi-network** — UniFi Network Controller API (UDM Pro) — Clients verwalten, VLANs ändern, DNS konfigurieren, mDNS Gateway, Netzwerke abfragen, Security-Incident-Triage.
- **webhook-subscriptions** — Webhook subscriptions: event-driven agent runs.

## dogfood (1)

- **hermes-agent-profiles** — Hermes Agent Profile-Management — Erstelle, konfiguriere, verwalte und verbinde Profili für verschideni Agent-Persönlichkeite.

## email (2)

- **hermes-email-client** — Sende und lese E-Mails via hermes@goetschi-labs.ch (All-Inkl IMAP/SMTP). Python-Script als Wrapper, kein Gateway-Neustart. Direct IMAP/SMTP via Python imaplib+smtplib. Migriert von hermes@radislione.net am 08.06.2026.
- **himalaya** — Himalaya CLI: IMAP/SMTP email from terminal.

## evaluation (2)

- **evaluating-llms-harness** — lm-eval-harness: benchmark LLMs (MMLU, GSM8K, etc.).
- **weights-and-biases** — W&B: log ML experiments, sweeps, model registry, dashboards.

## gaming (2)

- **minecraft-modpack-server** — Host modded Minecraft servers (CurseForge, Modrinth).
- **pokemon-player** — Play Pokemon via headless emulator + RAM reads.

## github (6)

- **codebase-inspection** — Inspect codebases w/ pygount: LOC, languages, ratios.
- **github-auth** — GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login.
- **github-code-review** — Review PRs: diffs, inline comments via gh or REST.
- **github-issues** — Create, triage, label, assign GitHub issues via gh or REST.
- **github-pr-workflow** — GitHub PR lifecycle: branch, commit, open, CI, merge.
- **github-repo-management** — Clone/create/fork repos; manage remotes, releases.

## inference (3)

- **llama-cpp** — llama.cpp local GGUF inference + HF Hub model discovery.
- **obliteratus** — OBLITERATUS: abliterate LLM refusals (diff-in-means).
- **serving-llms-vllm** — vLLM: high-throughput LLM serving, OpenAI API, quantization.

## knowledge-management (4)

- **auto-link** — Automatisch Personen in Text/Kalender referenzieren und mit Qdrant-Kontakten verknüpfen
- **market** — Finanz-Marktdaten abrufen via Finhub.io (Quotes, Profile, News, Search, Candles)
- **paperless** — Paperless-ngx API-Integration — Dokumente hochladen, suchen, herunterladen, Tags verwalten. Zentrale Doku-Ablage via MinIO + Qdrant-RAG.
- **qdrant-knowledge** — Qdrant Knowledge Manager v2.0 — Semantische Kontakt- & Wissenssuche + Document-RAG (PDF → Qdrant + Minio)

## mcp (3)

- **google-mcp-server** — Zentraler Google MCP Server — alle Bots (Hermes, Nova, Henry) nutzen eine OAuth-Session für Gmail, Calendar, Drive, Sheets, Docs.
- **mcphub-gateway** — MCPHub — zentrale MCP Gateway Server uf LXC 107 (10.0.60.170:3000). Orchestriert multi MCP Backends (Subprozesse + URL-MCPs) für Hermes, Nova und anderi Agents. Dual-Auth: Session Token (UI/API) + API Key (MCP Endpoint). Health unter /health.
- **native-mcp** — MCP client: connect servers, register tools (stdio/HTTP) + build custom MCP servers.

## media (5)

- **gif-search** — Search/download GIFs from Tenor via curl + jq.
- **heartmula** — HeartMuLa: Suno-like song generation from lyrics + tags.
- **songsee** — Audio spectrograms/features (mel, chroma, MFCC) via CLI.
- **spotify** — Spotify: play, search, queue, manage playlists and devices.
- **youtube-content** — YouTube transcripts to summaries, threads, blogs.

## mlops (5)

- **huggingface-hub** — HuggingFace hf CLI: search/download/upload models, datasets.
- **litellm** — LiteLLM — LLM API Gateway: Setup, Provider-Konfiguration, Key-Management, Migration, Hermes-Integration
- **lora-training** — Train LoRA adapters for SD 1.5 on CPU — image prep, tagging, PEFT training, test generation. Supports iterative train→test→retrain workflow.
- **mt5-trading-docker** — All-in-One Docker-Container mit Wine + MT5 Terminal + FastAPI Backend für Trading-Bots. Single-Container-Ansatz — MT5, API, Frontend/minimal, spöter Hermes. Nöd übers Netz verteilt.
- **nova-sd-image-gen** — Image generation via Stable Diffusion — tiny-sd (LCM) on NOVA CPU or SD 1.5 via Docker on Dokploy. User preference: min 20-25 steps for quality.

## models (2)

- **audiocraft-audio-generation** — AudioCraft: MusicGen text-to-music, AudioGen text-to-sound.
- **segment-anything-model** — SAM: zero-shot image segmentation via points, boxes, masks.

## note-taking (2)

- **obsidian** — Read, search, create, and edit notes in the Obsidian vault.
- **syncthing** — Deploy and configure Syncthing as a Docker container for file synchronization — Obsidian vault sync, cross-device file sharing, and multi-agent note synchronization

## productivity (14)

- **airtable** — Airtable REST API via curl. Records CRUD, filters, upserts.
- **confluence** — Confluence Cloud REST API — Spaces, Seiten lesen/erstellen/bearbeiten, Knowledge-Base strukturieren. Goetschi Labs persönlicher Space + Support Onboarding.
- **email-classifier** — E-Mail-Dispatch V2: Hermes scannt ALLI unglesene Mails, auto-delete mit etablierte Regle (ungeniert!), zeigt nöii einzeln.
- **github-awesome-reporter** — Trigger-Wort "!ga" / "!github-awesome": Holt das neueste Video von GitHub Awesome (@GithubAwesome), extrahiert Transkript, identifiziert das vorgestellte GitHub-Repository, fasst es zusammen, und liefert parallel per Telegram (Text + Audio) + Telefonanruf aus.

- **google-workspace** — Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
- **jira** — Goetschi Labs (GL) + BESORG (Besorgsdir) — aktivi Jira-Projekte. TEAM/SUP sind seit 05/2026 deprecated.
- **linear** — Linear: manage issues, projects, teams via GraphQL + curl.
- **maps** — Geocode, POIs, routes, timezones via OpenStreetMap/OSRM.
- **nano-pdf** — Edit PDF text/typos/titles via nano-pdf CLI (NL prompts).
- **notion** — Notion API + ntn CLI: pages, databases, markdown, Workers.
- **ocr-and-documents** — Extract text from PDFs/scans (pymupdf, marker-pdf).
- **powerpoint** — Create, read, edit .pptx decks, slides, notes, templates.
- **teams-meeting-pipeline** — Operate the Teams meeting summary pipeline via Hermes CLI — summarize meetings, inspect pipeline status, replay jobs, manage Microsoft Graph subscriptions.
- **text-to-speech** — TTS-Audio-Generierung für Nachrichten — ElevenLabs (primär) / Piper (Fallback). User-Preferences: NUR männlich, 1.15x Speed, Hochdeutsch, SFX.

## red-teaming (3)

- **godmode** — Jailbreak LLMs: Parseltongue, GODMODE, ULTRAPLINIAN.
- **hacker-profile** — Erstelle en Hermes Hacker-Profil mit Security-Tools, Ethical-Hacker-Persona und OSINT/GODMODE-Skills. Deckt alles ab: Profil-Clone, SOUL.md, Tool-Installation, Skills-Sync, Config-Tuning.
- **osint-analysis-workflow** — Vollständige OSINT-Analyse uf en Person/Username — von de Rohdate zum fertige Report inkl. Cross-Referencing, Multi-Identity-Analyse und Telegram-Output

## research (6)

- **dspy** — DSPy: declarative LM programs, auto-optimize prompts, RAG.
- **arxiv** — Search arXiv papers by keyword, author, category, or ID.
- **blogwatcher** — Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool.
- **llm-wiki** — Karpathy's LLM Wiki: build/query interlinked markdown KB.
- **polymarket** — Query Polymarket: markets, prices, orderbooks, history.
- **research-paper-writing** — Write ML papers for NeurIPS/ICML/ICLR: design→submit.

## smart-home (3)

- **ecoflow-pv-load-management** — Ecoflow PowerStream + DeltaMax — Solar-Überschuss-Management für Lasten (Teichpumpe, Waschmaschine, etc.). HA-Automationen mit direkten Ecoflow-Daten statt evcc Grid-Surplus. SOC-basiertes Laden, Wetterprognose, Rush-Mode.
- **home-assistant** — Home Assistant API integration for smart home control — lights, motion sensors, power consumption, presence tracking. Michel's primary home interface.
- **openhue** — Control Philips Hue lights, scenes, rooms via OpenHue CLI.

## social-media (3)

- **telegram-telethon** — Use when the user asks you to access, read, send, or monitor their Telegram account. Provides Telethon-based client with full read/write access to Michel's DMs, groups, and channels.
- **whatsapp** — WhatsApp-Integration für Apollo — Zwei-Wege: Nachrichten lesen, senden, überwachen via Michels WhatsApp-Account. Primär whatsapp-web.js + Chromium, Fallback Baileys v7.
- **xurl** — X/Twitter via xurl CLI: post, search, DM, media, v2 API.

## software-development (14)

- **debugging-hermes-tui-commands** — Debug Hermes TUI slash commands: Python, gateway, Ink UI.
- **hermes-agent-skill-authoring** — Author in-repo SKILL.md: frontmatter, validator, structure.
- **nextcloud-talk-integration** — Nextcloud Talk als Kommunikationsplattform fuer Hermes/Nova/Apollo — Bot-User, Talk-Room, API-Integration
- **node-inspect-debugger** — Debug Node.js via --inspect + Chrome DevTools Protocol CLI.
- **plan** — Plan mode: write markdown plan to .hermes/plans/, no exec.
- **python-debugpy** — Debug Python: pdb REPL + debugpy remote (DAP).
- **react-three-js-vite** — React + Three.js (@react-three/fiber, @react-three/drei) i Vite-TypeScript-Projekt integriere, baue und uf Docker deploye — inkl. TypeScript-Strict-Linting-Fixes, Docker-Build-ohne-Internet, Und TTS-Call-Troubleshooting
- **requesting-code-review** — Pre-commit review: security scan, quality gates, auto-fix.
- **spike** — Throwaway experiments to validate an idea before build.
- **subagent-driven-development** — Execute plans via delegate_task subagents (2-stage review).
- **systematic-debugging** — 4-phase root cause debugging: understand bugs before fixing.
- **test-driven-development** — TDD: enforce RED-GREEN-REFACTOR, tests before code.
- **wordpress-growpro** — WordPress Site-Management für grow-pro.ch — REST API via Application Passwords. Posts lesen/erstellen/bearbeiten, Kommentare moderieren, Medien hochladen.
- **writing-plans** — Write implementation plans: bite-sized tasks, paths, code.

## telephony (7)

- **apollo-call** — Apollo/Hermes tätigt einen ausgehenden Benachrichtigungsanruf mit dynamischer TTS-Ansage — One-Way, kein Dialog. Nimm Text entgegen, generiere TTS, ruf Michel an, spiel ab, leg auf.

- **asterisk-voice-agent** — Real-time bidirectional voice conversation pipeline for Asterisk PBX — STT (faster-whisper) → LLM → TTS with ExternalMedia RTP livestream, VAD turn-taking, and barge-in. Build agents that can hear, understand, and speak in phone calls.
- **dograh-voice-platform** — Dograh — Open Source Voice AI Platform uf CT117 (10.0.60.60). NEU SEIT 07.06.2026: Läuft nüm uf 10.0.60.167! Asterisk ARI 10.0.60.60:8088, AMI 10.0.60.60:5038. Vollständige Plattform-Capabilities: Asterisk ARI, Browser WebRTC, Embed Widget, MCP Server, Knowledge Base, Campaigns, Custom Tools, Recordings, SDKs. 120+ API Endpoints.
- **guten-morgen-call** — Hermes' Guten-Morgen-Weckruf — sammelt Daten aus Kalender, Mail, Trading, Wetter und System, generiert ein Nerd-Briefing als TTS und ruft Michel per Asterisk an.
- **hermes-call-api** — REST API for outgoing calls — any agent can call Michel via TTS + Asterisk
- **martin-nerd-call** — Hermes ruft Martin Russell (0797507151) Mo–Fr 19:00 mit Trading-Briefing — frischi Date, nerdigi Sprüch, 1–2 Min, NUR DM (kei Gruppe). Läuft via LLM-Cron (kein no_agent).
- **status-call** — Umfassender Status Call Skill — sammelt Daten von MT5 Trading Bots, Home Assistant, Tesla, Jira, Wetter, News und Home Lab und ruft Michel per TTS mit Soundeffekten an (3-4 Min).

## workflow (2)

- **goetschi-labs-workflow** — Goetschi Labs Standardprozess — Implementieren > Doku > Qdrant > Skill > Ticket. Inkl. Agent-First Documentation Quality, Document Intake Workflow, Language Rule (Hochdeutsch), Cron-Management (Notion Cron DB), Identity Protection.
- **skill-marketplace** — Konzept und Architektur für en konsistente Skill-Marketplace — Source of Truth für alli Hermes-Skills (GitHub + MinIO + MCPHub).
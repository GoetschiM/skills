# NEI — Neuronales Entscheidungs-Intelligenz-System

## Overview
Trading AI system combining technical analysis, fundamental data, sentiment analysis, and neural memory (pgvector + Ollama) for trading decisions. Next.js frontend + Express backend in a single Docker container.

## Connection
- **Dokploy App:** `homelab-nei-pur7xq`
- **Host:** 10.0.60.121
- **Port:** 3011 (Frontend, extern)
- **Internal ports:** Backend 3001, Frontend 3000
- **GitHub:** https://github.com/GoetschiM/NEI
- **Code:** `/etc/dokploy/applications/homelab-nei-pur7xq/code/`

## Credentials
| Bereich | Zugang |
|---------|--------|
| Web Dashboard | http://10.0.60.121:3011 |
| Admin Login | michel / Louis_one_13 |
| Guest Login | guest / NEI |
| PostgreSQL | 10.0.60.141:5432 / nei / michel / Louis_one_13 |
| Ollama | 10.0.60.168:11434 (nomic-embed-text) |
| MQTT Broker | 10.0.60.104 (Bot04) |

## Architecture
Frontend (Next.js :3000) + Backend (Express :3001) in one container.
Services: PipelineEngine (7 phases), BrainEngine, MQTT Service, Ollama Service, Telegram Service, WebBrowse Agent, Ingestion Service.

## Database: PostgreSQL + pgvector
AssetMapping, CurrentAsset, Memory (embeddings), MarketSnapshot, BrainLog, Cycle, Knowledge (nomic-embed-text 768d), Strategy, Learning, AccountMetric, MarketBar.

## Key API Endpoints
- `POST /api/auth/login` — JWT login
- `GET /api/status` — System status
- `GET /api/thoughts` — AI decisions
- `GET /api/cycles` — Analysis cycles
- `POST /api/cycle/trigger` — Start analysis
- `GET|POST /api/knowledge` — Knowledge CRUD
- `POST /api/knowledge/search` — pgvector semantic search
- `GET /api/market-watcher/snapshot/:asset` — Market snapshot
- `POST /api/mt5/update` — MT5 EA data
- `GET|POST /api/settings` — Config

## 7-Phase Cycle: COLLECT → FIRST_IMPRESSION → HYPOTHESIS → STRATEGY_MATCH → ACTION_PLAN → RISK_ASSESSMENT → FINAL_DECISION

## Deployment
- `docker compose build nei && docker compose up -d` (Port 3011 ext → 3000 int)
- External PostgreSQL at 10.0.60.141

## Confluence Doku: ID 37126146 unter Integrationen (17170454)

## Pitfalls
- Build ~5-7 min (npm ci + Prisma generate + Next.js build)
- Docker Hub TLS timeouts — retry
- Backend+Frontend im selben Container

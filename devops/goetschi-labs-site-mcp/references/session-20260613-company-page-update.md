# Session: Company Page Missions-Update (13.06.2026)

## Goal
Missions-Seite auf http://10.0.60.121:1713/#missions von 4 Tech-Demos auf 6 Company-Leistungen umgestellt.

## Was geändert
- `missionData[]` in App.tsx (Zeile 139-169) — komplett ersetzt mit 6 neuen Einträgen
- `phrases[]` in TypingLog-Komponente (Zeile 235) — neue Company-Slogans statt "Building strange things with AI."

## Neue Missionen
1. 🌐 Web & Portal Entwicklung (Active, 95%)
2. 🤖 KI-Agenten & Automation (Live, 100%)
3. 📈 GridBot Trading — Automated Finance (Live, 100%)
4. 🏠 Smart Home & IoT Lösungen (Active, 95%)
5. 🔧 DevOps & Schweiz-Infrastruktur (Active, 90%)
6. 📦 Individuelle Software & Beratung (Active, 85%)

## Workflow
1. paramiko SSH zu 10.0.60.121 (root/Louis_one_13)
2. App.tsx editieren via SFTP
3. `docker compose build --no-cache` (~90s)
4. `docker compose up -d --remove-orphans`

## Gelernt
- Source liegt auf 10.0.60.121, nicht auf 156/201 (altes Wissen im Skill war falsch)
- Direktes SSH geht nicht — nur paramiko
- Build läuft via Docker (kein npm auf Host)
- `version:` in docker-compose.yml ist obsolet (warning)

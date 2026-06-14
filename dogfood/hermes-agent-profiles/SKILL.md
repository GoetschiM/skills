---
name: hermes-agent-profiles
version: 1.0.0
category: dogfood
description: Hermes Agent Profile-Management — Erstelle, konfiguriere, verwalte und verbinde Profili für verschideni Agent-Persönlichkeite.
tags:
  - profiles
  - hacker
  - workspace
  - agent-persona
  - hermes
triggers:
  - profile erstelle
  - hacker profil
  - agent profil
  - multiple profile
  - neus profil
  - hermes profil
related_skills:
  - hermes-agent
  - hacker-profile
---

# Hermes Agent Profile

## Übersicht

Hermes unterstützt **mehreri Profile** (default + benutzerdefinierti). Jed's Profil het eigeni Skills, Config, Micro-memoria, Terminal-Umgebig und Workspace.

**Perfekt für:**
- **Hacker-Profil** — Security-Tools, nmap, metasploit, OSINT
- **Workspace-Profil** — Projekt-spezifischi Config
- **Test-Profil** — Isolierti Umgebig zum usprobiere

## Profile verwalte

### Neus Profil erstelle

```bash
# Us em Default-Profil klone
hermes profile create <name>

# Mit CLI-Alias
echo 'alias <name>="hermes -p <name>"' >> ~/.bashrc
```

### Profile liste + wechsle

```bash
hermes profile list
hermes -p <name>            # Einmalig i dem Profil starte
hermes profile use <name>   # Als Default setze
```

### Profil-Struktur

Jedes Profil isch eigenständig under `~/.hermes/profiles/<name>/`:

```
profiles/<name>/
├── SOUL.md          # Agent-Persona/Personality
├── config.yaml      # Eigeni Config (from Default kopiert)
├── cron/            # Eigeni Cronjobs
├── home/            # HOME-Verzeichnis für Terminal
├── logs/            # Eigeni Logs
├── memories/        # Eigeni MEMORY.md + USER.md
├── plans/           # Eigeni Pläne
├── sessions/        # Eigeni Session-DB
├── skills/          # Eigeni Skills (nur relevanti)
├── skins/           # TUI-Skins
└── workspace/       # Eigeni Arbeitsdateie
```

### Hacker-Profil (spezial)

Für es Hacker-Profil empfiehlt sich:

```bash
# 1. Profil erstelle
hermes profile create hacker
echo 'alias hacker="hermes -p hacker"' >> ~/.bashrc

# 2. SOUL.md aapasse — kalt, sachlich, technisch
#    → Security-Engineer Mentalität, kei Smalltalk

# 3. Config aapasse
#    - approvals: smart (nid manual)
#    - max_turns: 150 (längeri Scans)
#    - terminal timeout: 300

# 4. Nume Security-relevanti Skills verlinke
cp -r /root/.hermes/skills/red-teaming/godmode       profiles/hacker/skills/
cp -r /root/.hermes/skills/red-teaming/osint-analysis-workflow profiles/hacker/skills/
cp -r /root/.hermes/skills/devops/hermes-agent        profiles/hacker/skills/
rm -rf profiles/hacker/skills/{knowledge-management,media,research,telephony,yuanbao}

# 5. Telegram-eigene Bot (optional)
#    → Eigeni TELEGRAM_BOT_TOKEN i .env vom Profil
#    → Gateway starte mit HERMES_HOME=/root/.hermes/profiles/hacker
```

## Telegram-Bot pro Profil

Jed's Profil chan en **eigene Telegram-Bot** übercho:

### 1. Token i .env
```bash
cat > profiles/<name>/.env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=<token_von_botfather>
ENVEOF
```

### 2. Whitelist i config.yaml
```yaml
telegram:
  allowed_chats: '<user_id>'
  allow_from: '<user_id>'
```

### 3. Gateway starte
```bash
HERMES_HOME=/root/.hermes/profiles/<name> hermes gateway run
```

**Wichtig:** De Gateway bruucht en **eigene Prozess** — als Background-Job oder Tmux-Session.

## So macht mer's (Best Practice)

1. **Nume relevanti Skills kopiere** — Sonscht wastes de Skill-Selector uf
2. **SOUL.md anpassen** — Jedes Profil bruucht en eigeni Persönlichkeit
3. **Config anpassen** — approvals, timeouts, toolsets pro Use-Case
4. **Eigeni Telegram-Bot** — Ersti Wahl für direkte Zugriff
5. **Memory isch isoliert** — Was im Hacker-Profil gspiicheret wird, gseht s'Default-Profil nöd

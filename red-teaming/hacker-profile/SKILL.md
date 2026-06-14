---
name: hacker-profile
description: "Erstelle en Hermes Hacker-Profil mit Security-Tools, Ethical-Hacker-Persona und OSINT/GODMODE-Skills. Deckt alles ab: Profil-Clone, SOUL.md, Tool-Installation, Skills-Sync, Config-Tuning."
version: 1.2.0
author: hermes
tags: [security, pentest, osint, profile, hacker, tools, ethical-hacking]
triggers:
  - hacker profile
  - pentest profile
  - security profile erstelle
  - hacker agent
  - ethical hacking profil
  - security tools install
  - kali profile
  - penetration testing profil
---

# Hacker-Profil für Hermes

## Trigger

- User seit "erstell en Hacker-Profile" / "mach en Hacker Agent"
- User will en spezielle Hermes-Profile nur für Security-Arbeit
- Du bruchsch en isolierte Bereich mit eigene Tools + Persönlichkeit

## Übersicht

Hermes unterstützt **multi-profile** (`hermes profile`). En **Hacker-Profil** isch e kopierte Hermes-Profile mit:

1. **SOUL.md** — Kalti, sachlichi Ethical-Hacker-Persona (kein Smalltalk, maximi Präzision)
2. **Security-Tools** — nmap, masscan, sqlmap, nikto, gobuster, ffuf, wfuzz, hydra, hashcat, john, impacket, pwntools, shodan, censys
3. **Skills** — Nur Security-relevanti: godmode, osint-analysis-workflow, hermes-agent
4. **Config** — approvals.smart, max_turns: 150, terminal timeout: 300s
5. **Eigene Telegram-Bot** — Separater Bot-Token für DM-Kommunikation

## Schritt-für-Schritt

### 1. Profil erstelle

```bash
hermes profile create hacker --clone default
hermes profile list  # Verifiziere: hacker sött auftauche
```

### 2. SOUL.md schriebe (Ethical Hacker Persona)

Schriib z' `/root/.hermes/profiles/hacker/SOUL.md`:

```markdown
# Hermes Agent Persona

Du bisch **Hermes im Hacker-Modus** — en präzise, analytische Security-Engineer.
Du redsch kurz, faktenbasiert, technisch. Kein Schnickschnack, kein Smalltalk.

**Persönlichkeit:**
- Kalt, sachlich, effizient — wie en CTF-Player
- Du sägsch "Nei" wenn öppis unmöglich isch
- Du dokumentiersch genau (Logs, Screenshots, Exploit-Versuche)
- Du respektiersch Systemgrenzen — **Ethical Hacker**
- Maximale Detailgrad bi Vulnerability-Descriptions

**Regeln:**
1. NIE Systemumgebige kaputt mache — lies statt z'schriebe
2. NIE ohni expliziti Erlaubnis i live Production-Container iigriffe
3. Immer Logs mitschriebe — was, wänn, Resultat
4. Immer Disclaimer wenn öppis rechtlich heikel isch
5. YOLO = OFF — kei Auto-Auth bi Security-Operatione
6. Backup vor Exploit — zersch Snapshot, denn manipuliere
7. OSINT = erlaubt (lesend)
8. Brute-Force / Exploit = IMMER expliziti Erlaubnis
```

### 3. Config tune

**YOLO-mode / approvals:** `smart` = LLM prüft Risiko vo kritische Befähl

```bash
hermes config set approvals.mode smart
hermes config set approvals.timeout 120
```

**Meh turns für langi Scan/Ufzüg:**

```bash
hermes config set agent.max_turns 150
hermes config set terminal.timeout 300
```

→ **Oder direkt i config.yaml patche** (git für bulk-Änderige):

`/root/.hermes/profiles/hacker/config.yaml`:
```yaml
approvals:
  mode: smart
  timeout: 120
agent:
  max_turns: 150
terminal:
  timeout: 300
```

### 4. Security-Tools installiere

Die Tools laufe im **selbe Container** wo Hermes (LXC) — kei separates Kali nötig:

```bash
# Apt-Installation
apt-get install -y nmap masscan sqlmap nikto gobuster ffuf wfuzz hydra john hashcat dirb

# Python-Tools
pip3 install --break-system-packages impacket pwntools shodan censys beautifulsoup4
```

**Tool-Tabelle:**

| Kategorie | Tools |
|-----------|-------|
| 🔍 Port-Scan | nmap, masscan, netcat |
| 🌐 Web-Scan | nikto, sqlmap, gobuster, ffuf, wfuzz |
| 🔐 Credential | hydra, john, hashcat |
| 📡 Python | impacket, pwntools, shodan, censys |
| 🧰 Basis | curl, git, python3 |

**Optionali Zusatz-Tools (nur bei Bedarf):**

| Tool | Installation | Grösse | Info |
|------|-------------|--------|------|
| Metasploit | `curl -sL https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb | bash` | ~700MB | Framework mit 2000+ Exploits |
| Responder | `cd /opt && git clone --depth 1 https://github.com/lgandx/Responder.git && ln -sf /opt/Responder/Responder.py /usr/local/bin/responder` | ~5MB | LLMNR/NBT-NS Poisoning |
| WPScan | `apt-get install -y ruby-dev && gem install wpscan && ln -sf /var/lib/gems/3.2.0/gems/wpscan-3.8.28/bin/wpscan /usr/local/bin/wpscan` | ~20MB | WordPress-Scanner |
| Burp Suite | → GUI-Tool, nöd uf Server sinnvoll | — | Web-App-Testing (lokal) |

**WPScan-Pitfall:** Es git en **fake WPScan auf PyPI** (`pip install wpscan` installiert en andere, minderwertige Scanner!). Immer via **Ruby gem** installiere, nie via pip! Erkennigsmerkmal: de fake zeigt "VimLxrd and Mr. Robot were here."

**dpkg-Problem:** Falls `dpkg was interrupted` chunnt, zersch:
```bash
dpkg --configure -a
```

### 5. Security-Skills ins Profil kopiere

Lösche alli unnötige Default-Skills us em Profil, kopier nume Security-relevanti:

```bash
# Skills kopiere woni bruch
cp -r /root/.hermes/skills/red-teaming/godmode /root/.hermes/profiles/hacker/skills/
cp -r /root/.hermes/skills/red-teaming/osint-analysis-workflow /root/.hermes/profiles/hacker/skills/
cp -r /root/.hermes/skills/autonomous-ai-agents/hermes-agent /root/.hermes/profiles/hacker/skills/

# Alti Default-Skills löschen
ls /root/.hermes/profiles/hacker/skills/  # vorher
rm -rf gaming knowledge-management media research social-media telephony yuanbao

# Resultat prüefe
ls /root/.hermes/profiles/hacker/skills/
# Söll zeige: godmode  hermes-agent  osint-analysis-workflow
```

### 6. Alias erstelle (optional)

```bash
hermes profile alias hacker --name hacker
# →
# ✓ Alias created: /root/.local/bin/hacker
# Jetzt goes: `hacker` = `hermes -p hacker`
```

### 7. Netzwerk-Scan mit /goal + tmux (Hintergrund-Session)

Für langlebigi Security-Scans (10.0.60.0/24 etc.) wo über Stunde laufe:

```bash
# 1. tmux installiere
apt-get install -y tmux

# 2. Hacker-Profil in tmux starte
tmux new-session -d -s hacker-scan -x 160 -y 50 'hermes -p hacker'
sleep 15  # warte bis Hermes ready isch

# 3. Goal setze (macht de Scan persistent, au nach Context-Window)
tmux send-keys -t hacker-scan '/goal READ-ONLY Scan 10.0.60.0/24: finde alle Hosts, offene Ports, Dienste + Versionen, Schwachstellen. Dokumentiere Ergebnisse in /root/hacker-scan-results.md. KEINE Änderungen, KEINE Exploits, KEIN DoS.' Enter

# 4. Fortschritt prüefe
tmux capture-pane -t hacker-scan -p | tail -20

# 5. Output logge (optional)
tmux pipe-pane -t hacker-scan -o "cat >> /root/hacker-scan.log"
```

**Goal-Tricks:**
- `/goal` macht de Scan **persistent** — au wenn Context-Kompression triggered wird, lauft de Scan wiiter
- `/goal status` — zeigt aktuelle Fortschritt
- `/goal pause` / `/goal clear` — stoppe / lösche
- **Wichtig:** Im Goal immer explizit **"READ-ONLY"** + **"KEINE Änderungen"** säge — sust chönnt de Hacker öppis manipuliere

### 8. Testlauf

```bash
hermes -p hacker chat -q "Liste alli installierte Security-Tools uf"
# oder:
hacker chat -q "Scan 10.0.60.156: Ports 1-1000"
```

## Benutzig

| Weg | Befehl |
|-----|--------|
| Terminal | `hermes -p hacker` oder `hacker` |
| Telegram | `/profile hacker` |
| Default ändere | `hermes profile use hacker` |

### 🔑 Eigen Telegram-Bot (optional)

Für DM-Kommunikation brucht de Hacker en **eigene Bot** via @BotFather:

#### 1. Bot erstelle + Token hole
- Gah zum [@BotFather](https://t.me/botfather) uf Telegram
- `/newbot` → Name (z.B. "HackBot") → Username (z.B. `@hackbot`)
- Token kopiere (z.B. `8710010958:AAEvxknQLU2inuOtagmh6yhWS4RAPQAtQ2M`)

#### 2. Token i .env vom Hacker-Profil setze

**⚠️ KRITISCH: D'GANZI .env erhalte, NUR de Token ersetze!**

```bash
# 1. Backup vom clone-default .env
cp /root/.hermes/profiles/hacker/.env /root/.hermes/profiles/hacker/.env.bak

# 2. Nume de TELEGRAM_BOT_TOKEN ersetze (d'andere Keys blibed!)
# Syntax: de Wert zwische TELEGRAM_BOT_TOKEN= und em nächste Zeileumuch
# 
# Im .env stöhn au no:
# - OPENAI_API_KEY, ANTHROPIC_API_KEY (vom Default-Profile kopiert)
# - LITELLM Configs (base_url, API key)
# - JIRA Credentials
# - HOMEASSISTANT_TOKEN
# - All-Inkl KAS Credentials
# - HERMES_EMAIL Credentials
# 
# Die alli MÜND im .env blibe, sust funktioniert de Gateway/Skills nöd!
```

→ **Empfohlen:** Eifach im Editor de Wert ersetze:
```bash
nano /root/.hermes/profiles/hacker/.env
# → Einzige Änderig: TELEGRAM_BOT_TOKEN=<neuer-hacker-token>
```

#### 3. Dini Telegram-ID i d'Whitelist

Dini ID findsch in Telegram via @userinfobot `/start` — zeigt dini numerischi ID.

```yaml
# In /root/.hermes/profiles/hacker/config.yaml — telegrams-Sektion aapasse:
telegram:
  reactions: false
  channel_prompts: {}
  allowed_chats: 'DEINE_TELEGRAM_ID'
  allow_from: 'DEINE_TELEGRAM_ID'   # <— WICHTIG: allow_from isch nöd automatis...
```

**Pitfall:** `allow_from` existiert nöd i de Default-Config. Du muesch es **manuell iifüege**. Ohni `allow_from` blockiert de Gateway alli iighende Nachrichten!

#### 4. Gateway starte (eigener Prozess)

```bash
cd /root/.hermes/profiles/hacker && HERMES_HOME=/root/.hermes/profiles/hacker nohup hermes gateway run > /dev/null 2>&1 &
sleep 5

# Prüefe obs lauft:
ps aux | grep "hermes.*hacker" | grep -v grep
# Söll zeige: /usr/bin/python3 /usr/local/bin/hermes gateway run

# Gateway-Logs prüefe:
tail -20 /root/.hermes/profiles/hacker/logs/gateway.log
# Söll zeige: ✓ telegram connected
```

**ODER via terminal(background=true) (empfohlen für CLI-Chat):**
```bash
terminal(command="cd /root/.hermes/profiles/hacker && HERMES_HOME=/root/.hermes/profiles/hacker hermes gateway run", background=true)
```
→ Gateway läuft im Hintergrund, chasch später mit `process(action='log', session_id='...')` de Output prüefe

#### 5. Verifizierig

```bash
tail -5 /root/.hermes/profiles/hacker/logs/gateway.log
# Sött bringe:
# [Telegram] set_my_commands OK for scope BotCommandScopeDefault (30 cmds)
# [Telegram] Connected to Telegram (polling mode)
# ✓ telegram connected
# Gateway running with 1 platform(s)
```

Jetzt chasch im Telegram dinerem @hackbot schriebe! 🎯

#### 6. Wartig

Wenn de Hacker-Gateway stirbt (Container-Reboot, Crash), starten mit:
```bash
# Prüefe obs no lauft
tail -5 /root/.hermes/profiles/hacker/logs/gateway.log

# Nöistarte
cd /root/.hermes/profiles/hacker && HERMES_HOME=/root/.hermes/profiles/hacker nohup hermes gateway run > /dev/null 2>&1 &
```

**Pitfalls Telegram-Gateway:**
- ❌ **Env überschriebe** — Nume de `TELEGRAM_BOT_TOKEN` wert ersetzte, nöd d'ganzi .env plattmache! Wennd d'ganzi .env überschriibsch, verlürsch API-Keys und de Gateway startet nöd
- ❌ **Gateway-Port-Konflikt** — De zweit Gateway brucht en andere Port (auto). Lueg `hermes gateway status` ob de Default no lauft
- ✅ **Hintergrund-Prozess** — `nohup` + `&` überlebet SSH-Logout i tmux
- ❌ **Bot antwortet nöd** → Check: `allowed_chats` + `allow_from` (beidi MÜEND!); Logs: `tail -20 /root/.hermes/profiles/hacker/logs/gateway.log`
- ✅ **Bot startet nöd** → Lueg `errors.log`: `tail -20 /root/.hermes/profiles/hacker/logs/errors.log`
- ❌ **"No token, authorization denied"** → De Token fehlt oder isch falsch im .env

## MCPHub-Zugriff für de Hacker

De Hacker chan alli MCPHub-Server nutze, aber **MUSS d'Dual-Auth verstande ha**:

### Auth-Übersicht

| Endpoint | Brucht | Status |
|----------|--------|--------|
| `/api/servers`, `/api/*` | **Session Token** (POST /api/auth/login) | ✅ Login: Hermes / Louis_one_13 |
| `/mcp` (Tool-Zugriff) | **API Key** (Settings→Keys) | ❌ Noch KEIN Key erstellt! |

**Session Token ≠ API Key.** De Token vom Login funktioniert NUR für Web-UI + REST API. Für MCP-Tool-Zugriff muess en API Key i de MCPHub-UI erstellt werde.

### Grundlegende Auth-Operatione

```bash
# 1. Login (Session Token hole)
curl -s -X POST http://10.0.60.170:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Hermes","password":"Louis_one_13"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['token'])"

# 2. Alli MCP-Server liste (via REST API)
curl -s http://10.0.60.170:3000/api/servers \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 3. Health-Check (kein Auth nötig)
curl -s http://10.0.60.170:3000/health
```

**Hinweis:** execute_code isch nöd verfügbar wenn de Hacker als Cron-Job oder im tmux-Hintergrund mit `approvals.cron_mode: deny` lauft. Verwende normali terminal() Calls.

## Dokploy-Zugriff (falls nötig)

Dokploy lauft uf **10.0.60.121:3000** (LXC 100). Admin-User: `michelgoetschi@gmail.com`. Passwort isch als **bcrypt-Hash** i de PostgreSQL-DB vom Postgres-Container gspeicheret.

Für DB-Zugriff (via Proxmox-Host):
```bash
sshpass -p 'Riotstar_PROXMOX_13' ssh root@10.0.60.10
pct exec 100 -- docker exec dokploy-postgres.1.<hash> \
  psql -U dokploy -d dokploy -c 'SELECT a.password, u.email FROM "account" a JOIN "user" u ON a.user_id = u.id;'
```

Pattern isch allgemein nützlich für alli Docker-Postgres-Services uf LXC 100.

## Referenzen

- `references/goetschi-labs-network-20260614.md` — Bekannti Hosts, IPs, Scan-Befehle für 10.0.60.0/24
- `references/goal-based-autonomous-scanning.md` — Goal-basierti Mehrphasen-Scans mit tmux (persistent, context-resilient)
- `references/hacker-scan-20260614.md` — Session-spezifische Scan-Details vom 14.06.2026

## Pitfalls

- ❌ **Naming:** Profil-Namen ohni Leerzeichen, Kleinbuchstabe (Bash-freundlich)
- ❌ **Config-Changes im geklonten Profil** — nach `hermes profile create` isch d'Config e 1:1-Kopie vom Default. Muess separat agpasst werde.
- ❌ **dpkg interrupted** — bi LXC-Containere wo Docker/Installatione vorhär abgstürzt sind: `dpkg --configure -a` zersch usführe
- ❌ **Docker vs apt:** `metasploit-framework` gits als apt-Package, `responder` nöd (GitHub)
- ❌ **Skills vom Default-Profil kopiert** — s'Hacker-Profil het initial ALLI Default-Skills kopiert. Die münd aktiv glöscht werde sust nutzed unnötig Speicher/Tokens.
- ✅ **Approvals.smart** statt manual = kei einzeln! "Bestätige Sie" bi jedem Befehl, aber nöd vollautomatisch wie YOLO
- ❌ **execute_code blockiert** — im Hintergrund (Cron/tmux) mit `cron_mode: deny` isch execute_code nöd verfügbar. Verwende terminal()
- ❌ **MCPHub /mcp blockiert** — ohni API Key (nume Session Token) chasch keni MCP-Tools ufrüefe

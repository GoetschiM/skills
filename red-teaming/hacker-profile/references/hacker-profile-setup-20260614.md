Hacker-Profil Setup vom 14. Juni 2026
======================================

Alles woni bi dere Session glehrt ha.

Umfang
-------
- Profil erstellt via `hermes profile create hacker --clone`
- Alias: `hacker` → `/root/.local/bin/hacker`
- bashrc-Alias: `alias hacker="hermes -p hacker"`
- Gateway mit eigenem Telegram-Bot-Token

Tool-Installation (alle installiert)
------------------------------------
Apt: nmap, masscan, sqlmap, nikto, gobuster, ffuf, wfuzz, hydra, hashcat, john
Python: impacket, pwntools, shodan, censys
Spezial: metasploit (curl|bash), responder (git clone), wpscan (gem)
Kei git-nötig: tmux (apt-install)

Config-Änderige (hacker-Profil)
-------------------------------
- approvals.mode: smart (statt manual)
- approvals.timeout: 120
- agent.max_turns: 150
- terminal.timeout: 300
- telegram.allowed_chats: '322663922'
- telegram.allow_from: '322663922'

Telegram-Bot
------------
- Token: via @BotFather
- Gateway: HERMES_HOME=/root/.hermes/profiles/hacker hermes gateway run
- Läuft als bg-Prozess (nohup)

Gateway-Logs: /root/.hermes/profiles/hacker/logs/gateway.log
Gateway-Errors: /root/.hermes/profiles/hacker/logs/errors.log

Hacker-Scan (10.0.60.0/24)
----------------------------
- Via tmux + /goal-Mechanismus
- 5 Phasen: Ping-Sweep → Service-Scan → Vuln-Scan → Analyse → Doku
- Phase 3/5 am 14.06.26 um 12:23 (no laufend)

Skript/Goal:
```bash
tmux new-session -d -s hacker-scan -x 160 -y 50 'hermes -p hacker'
sleep 15
tmux send-keys -t hacker-scan '/goal ... READ-ONLY Scan ...' Enter
```

Tools prüefe:
```bash
tmux capture-pane -t hacker-scan -p | tail -15
```

Aktive Sessions prüefe:
```bash
tmux list-sessions | grep hacker
```

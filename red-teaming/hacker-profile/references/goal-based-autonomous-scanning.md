# Goal-Based Autonomous Scanning

Pattern: Hermes-Profil (z.B. Hacker) in tmux starte, via `/goal` en langlebigi Scan-Mission gä, und autonom laufe lah.

## Use Case

S'Agent-Modell (z.B. deepseek-v4-flash) het e Context-Window (128k tokens). Bi grosse Netzwerk-Scans (10.0.60.0/24 = 254 Hosts) wird de Context nach 10-20 Tool-Calls voll. Ohne `/goal` wür de Agent vergässe, was er tuet oder wür eifach ufhöre.

## Ablauf

### 1. tmux-Session erstelle

```bash
apt-get install -y tmux
tmux new-session -d -s hacker-scan -x 160 -y 50 'hermes -p hacker'
```

- `-s hacker-scan` = Session-Name (referenzierbar)
- `-x 160 -y 50` = Term-Grössi (160 Spalte, 50 Zile)
- `'hermes -p hacker'` = Start-Befehl

### 2. Warte bis Hermes ready isch

```bash
sleep 15  # Hermes bruucht ~10s zum starte
```

### 3. Goal setze

```bash
tmux send-keys -t hacker-scan '/goal READ-ONLY Scan 10.0.60.0/24: finde Hosts via Ping-Sweep + Port-Scan. Dokumentiere alles i /root/hacker-scan-results.md.' Enter
```

**Goal-Structure (bewährt):**
```
/goal <READ-ONLY> <Was tuen>: <Details>. <Output-Format>. <Constraints>.
```

- **READ-ONLY** = Safety-Kennzeichnig (explizit säge: nüt ändere)
- **Was** = Art vom Scan (Ping-Sweep, Service-Scan, Vulnerability-Scan)
- **Details** = Subnetz, Ports, Targeted Hosts
- **Output** = Wo d'Resultat highöred (/path/to/report.md)
- **Constraints** = KEINE Änderungen, KEIN DoS, KEINE Exploits

### 4. Fortschritt prüefe

```bash
# Aktuelle Output (letzti 20 Zile)
tmux capture-pane -t hacker-scan -p | tail -20

# Logge (ganze Output in Datei)
tmux pipe-pane -t hacker-scan -o "cat >> /root/hacker-scan.log"

# Später: Output stoppe
tmux pipe-pane -t hacker-scan
```

### 5. Goal-Status / Steuerig

```bash
# In d'tmux-Session wechsle (live beobachte)
tmux attach -t hacker-scan
# Strg+B, D = detach (wieder in Hintergrund)

# Sende Goal-Status-Abfrag
tmux send-keys -t hacker-scan '/goal status' Enter

# Goal stoppe
tmux send-keys -t hacker-scan '/goal clear' Enter

# Ganzi Session beende
tmux send-keys -t hacker-scan 'exit' Enter
sleep 2
tmux kill-session -t hacker-scan
```

## Multi-Phase Scan Pattern (3 Phasen)

Vo de aktuelle Session bewährte Ablauf:

```bash
# Phase 1: Ping-Sweep (schnell, ~30s)
tmux send-keys -t hacker-scan '/goal READ-ONLY nmap -sn -T4 10.0.60.0/24. Erstelle Host-Liste. Output /root/hacker-scan-results.md' Enter

# → Prüefe: 19 Hosts gfunge

# Phase 2: Service-Scan (Top 1000 Ports, ~5min)
tmux send-keys -t hacker-scan '/goal READ-ONLY nmap -sV -T4 --top-ports 1000 10.0.60.0/24. Dienste + Versionen identifiziere. Output /root/hacker-scan-results.md' Enter

# → Prüefe: Open Ports, Versionen, OS-Detection

# Phase 3: Vulnerability-Scan (vorsichtig, ~10min)
tmux send-keys -t hacker-scan '/goal READ-ONLY nmap --script vuln --script-timeout=60s -T4 10.0.60.0/24. Dokumentiere Schwachstelle. KEINE Exploits. Output /root/hacker-scan-results.md' Enter

# → Prüefe: Kritschi Findings
```

## Pitfalls

- ❌ **Context-Verlust** — Ohni `/goal` vergisst de Agent nach ~20 Tool-Calls, was er tuet
- ✅ **Goal persistiert** — `/goal` isch gegen Context-Kompression immun (wird inmemory ghalte)
- ❌ **tmux stirbt** — Wenn de Container rebootet, isch d'tmux-Session weg. Plan für Neustart
- ✅ **/goal status checke** — Regelmässig prüefe obs no lauft (`tmux capture-pane` odr `/goal status`)
- ❌ **Robot-Verhalten** — De Hacker chönnt eigenständig in Phase 2 starte, au wenn du Phase 1 no nöd usgwertet hesch. Immer Schritt für Schritt goh
- ✅ **Logging** — `tmux pipe-pane` für persistence (Output sichert au bi tmux-Stopp)

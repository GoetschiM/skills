Hacker Scan - 14. Juni 2026
=============================

Goal: READ-ONLY Scan vom interne Netz 10.0.60.0/24
Agent: hacker-Profil (eigene Gateway, eigener Telegram-Bot)
Modell: deepseek-v4-flash (via LiteLLM 10.0.60.152:4000)

Durchgeführti Schritte
-----------------------
1. nmap -sn -T4 (Ping-Sweep) → 19 Hosts gfunde
2. nmap -sV -T4 --top-ports 1000 → Service-Versionen uf allne Hosts
3. nmap --script=vuln --script-timeout=60s → Schwachstelle-Scan
4. Auswertig/Analyse + Doku → in Arbeit (Phase 3/5)

Gfundeni Hosts (10.0.60.0/24)
------------------------------
- 10.0.60.1 (Gateway)
- 10.0.60.10
- 10.0.60.60
- 10.0.60.104
- 10.0.60.106
- 10.0.60.110
- 10.0.60.111
- 10.0.60.121 (Dokploy-Host)
- 10.0.60.135
- 10.0.60.139 (CT118 - Coolify)
- 10.0.60.140 (LXC109 - InfluxDB)
- 10.0.60.141
- 10.0.60.152
- 10.0.60.156 (Apollo - Hermes Host)
- 10.0.60.167 (Nova)
- 10.0.60.170 (CT107 - MCPHub)
- 10.0.60.179
- 10.0.60.186
- 10.0.60.201

Status: Auswertig lauft (Hacker analysiert grad d'Vuln-Scan-Resultat)
Output: /root/hacker-scan-results.md (wird gschriebe)

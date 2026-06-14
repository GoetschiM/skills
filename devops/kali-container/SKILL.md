---
name: kali-container
tags: []
related_skills:
  - hermes-agent-hacker-profile
  - mcphub-gateway
description: Kali Linux als LXC-Container (Proxmox 02) — Vollständigi Pentest-, OSINT- + Network-Tool-Suite
triggers:
  - kali
  - penetration testing
  - pentest
  - security
  - kalilinux
  - wireshark
  - tshark
  - nmap
  - nuclei
  - osint
  - wordpress
  - wpscan
  - wpprobe
  - icmp
  - network audit
  - netzwerk-audit
  - packet capture
  - pcap
  - mDNS
  - ARP
  - enumeration
  - vulnerability scan
---

# Kali Linux Container uf Proxmox 02 (10.0.60.11)

## Übersicht

Kali Linux lauft als **LXC-Container uf Proxmox 02 (10.0.60.11)**. Installiert vo Nova via Coolify. **NICHT uf Apollo** — Docker dert isch dead/disabled.

**MIGRATION HISTORY:** Ursprünglich als Docker-Container uf Apollo (10.0.60.156). Nova hät Kali uf Proxmox 02 neu installiert (LXC, nöd Docker). De alti Apollo-Host isch obsolet.

**35+ Security-Tools installiert**, ufteilt i 9 Kategorie.

## Container-Status prüefe

```bash
# Proxmox 02 (10.0.60.11) via Proxmox 01:
ssh root@10.0.60.10 "ssh root@10.0.60.11 'lxc-ls -f | grep kali'"

# Direkt uf Proxmox 02 (wenn Route verfügbar):
ssh root@10.0.60.11 "lxc-ls -f | grep kali"
```

## Zuegriff für anderi Agentä

Anderi Agentä (Nova, Apollo) chönd uf zwei Wäg uf de Kali-Container zuegriefe:

### 1. Via SSH direct (wenn Netzwerkroute existiert)
```bash
ssh root@10.0.60.11 "lxc-attach -n kali -- bash -c '<befehl>'"
```

### 2. Via Proxmox 01 (empfohlen, funktioniert immer)
```bash
ssh root@10.0.60.10 "ssh root@10.0.60.11 'lxc-attach -n kali -- bash -c \"<befehl>\"'"
```

### 3. Skill vo GitHub/ MinIO loade
```bash
# GitHub (Source of Truth)
git clone https://github.com/GoetschiM/hermes-agent-skills.git

# MinIO (Backup)
mc cp minio/swarm-skills/skills/devops/kali-container/SKILL.md .
```

## Ressource-Limits

| Limit | Wert |
|-------|------|
| RAM | 2 GB (`--memory=2g`) |
| CPU | 1 Core (`--cpus=1`) |
| Network | host |
| Persistenz | `/root/kali-home` → `/root` (im Container) |

## Tools installiert (30+)

Installationsbefähl:
```bash
# OSINT + Pentest (via apt)
apt install -y nmap nikto sqlmap dirb gobuster wfuzz hydra john whois \
  dnsutils netcat-openbsd curl wget git python3-pip wpscan theharvester \
  sherlock whatweb dnsrecon dnsenum masscan ffuf amass metagoofil unzip

# Python-Tools (via pip)
pip3 install --break-system-packages holehe shodan maigret socialscan

# ProjectDiscovery (Go-Binaries) — direkt von GitHub Releases
# Siehe /root/install_pdtools.py
# Tools: nuclei, subfinder, naabu, dnsx, katana, tlsx, interactsh-client
```

### 🕵️ OSINT (Open Source Intelligence)

| Tool | Version | Zweck | Beispiel |
|------|---------|-------|----------|
| theHarvester | 4.10.1 | Email/Subdomain-Enumeration | `theharvester -d example.com -b google` |
| sherlock | 0.15.0 | Username-Suche über 400+ Plattforme | `sherlock username` |
| holehe | 1.61 | Email-Registrierungs-Check | `holehe email@example.com` |
| maigret | neust | Alternative Username-Suche | `maigret username` |
| socialscan | neust | Email/User-Check auf Plattforme | `socialscan email@example.com` |
| metagoofil | neust | File-Metadaten-Extraktion | `metagoofil -d example.com -t doc,pdf` |
| whatweb | 0.6.3 | Website-Fingerprinting | `whatweb https://example.com` |
| shodan | aktuell | IoT/Network-Device-Suche | `shodan search apache` |
| whois | aktuell | Domain-Besitzer-Info | `whois example.com` |

### 🌐 DNS-Enumeration

| Tool | Version | Zweck | Beispiel |
|------|---------|-------|----------|
| dnsrecon | 1.3.1 | Advanced DNS-Enumeration | `dnsrecon -d example.com -t rvl` |
| dnsenum | 1.3.2 | DNS-Brute-Force + Enumeration | `dnsenum example.com` |
| dnsx | 1.2.3 | Schnelli DNS-Query-Tool (PD) | `echo example.com \| dnsx -a -aaaa` |
| amass | 5.0.1 | OWASP-DNS-Recon + Subdomain-Find | `amass enum -d example.com` |
| subfinder | 2.14.0 | Schnelli Subdomain-Discovery (PD) | `subfinder -d example.com` |
| dig/nslookup | aktuell | Basis-DNS-Abfragen | `dig ANY example.com` |
| gobuster | 3.8.2 | DNS-Subdomain-Busting | `gobuster dns -d example.com -w wordlist.txt` |

### 🔍 Netzwerk-Scanning

| Tool | Version | Zweck | Beispiel |
|------|---------|-------|----------|
| nmap | 7.98 | Netzwerk-Scanner (Port/Service/OS) | `nmap -sV -O 10.0.60.0/24` |
| masscan | 1.3.2 | Massen-Port-Scanner (sehr schnell) | `masscan 10.0.0.0/16 -p1-65535 --rate=1000` |
| naabu | 2.6.1 | Schneller Port-Scanner (PD) | `naabu -host 10.0.60.121` |
| tshark (Wireshark) | 4.6.4 | Packet-Capture + Analyse | `tshark -i eth0 -w capture.pcap` |
| tcpdump | 4.99.6 | CLI Packet-Capture | `tcpdump -i eth0 -w dump.pcap` |
| netcat | aktuell | TCP/UDP-Debugging | `nc -zv 10.0.60.121 22` |

### 🌍 Web-App-Testing

| Tool | Version | Zweck | Beispiel |
|------|---------|-------|----------|
| nuclei | 3.8.0 | Vulnerability-Scanner (8000+ Templates) | `nuclei -u https://example.com` |
| katana | 1.6.1 | Web-Crawler (PD) | `katana -u https://example.com -d 2` |
| nikto | 2.6.0 | Web-Server-Scanner | `nikto -h https://example.com` |
| sqlmap | 1.10.2 | SQL-Injection-Automation | `sqlmap -u "http://example.com?id=1"` |
| ffuf | 2.1.0 | Web-Fuzzer (schnell, modern) | `ffuf -u https://example.com/FUZZ -w wordlist.txt` |
| dirb | 2.22 | Directory-Brute-Force | `dirb http://example.com` |
| gobuster | 3.8.2 | Directory/File-Busting | `gobuster dir -u https://example.com -w wordlist.txt` |
| wfuzz | aktuell | Web-Fuzzer (parameterisiert) | `wfuzz -c -z file,wordlist.txt http://example.com/FUZZ` |
| httpx | aktuell | HTTP-Prober (PD) | `httpx -l urls.txt -status-code` |
| interactsh-client | 1.3.1 | OOB-Interaction-Detection (PD) | `interactsh-client -v` |
| tlsx | 1.2.2 | TLS-Grabber (PD) | `tlsx -u example.com` |

### 🔐 Credential-Testing

| Tool | Version | Zweck | Beispiel |
|------|---------|-------|----------|
| hydra | 9.6 | Login-Brute-Force (SSH, HTTP, RDP) | `hydra -l admin -P pass.txt ssh://10.0.60.x` |
| john | aktuell | Passwort-Cracker (Hash) | `john --wordlist=rockyou.txt hash.txt` |

### 🎯 WordPress

| Tool | Version | Zweck | Beispiel |
|------|---------|-------|----------|
| wpscan | 3.8.28 | WordPress-Scanner | `wpscan --url https://example.com` |
| wpprobe | 0.11.8 | WordPress Plugin Vulnerability Scanner | Siehe `references/wpprobe.md` |
| wpprobe | 0.11.8 | WP Plugin Enumeration (Go) | `wpprobe scan -u https://example.com` |

### ⚙️ Basis-Tools

| Tool | Version | Zweck |
|------|---------|-------|
| python3 | 3.13 | Scripting (kein GUI) |
| git | 2.51 | Versionskontrolle |
| curl | 8.18 | HTTP-Requests |
| unzip | 6.0 | ZIP-Archiv-Extraktion |

## 🎯 Use Cases

### 1. Netzwerk-Audit (Goetschi Labs)

**Vollständigi Methodik + Befund-Interpretation:** Siehe `references/network-audit-methodology.md`

Kurzer Quick-Start:

```bash
# 1. Capture uf Host erstelle (5-10 min)
tcpdump -i eth0 -s 0 -B 4096 -w /tmp/capture.pcap -f "not port 22" &
sleep 300; kill %1

# 2. In Kali kopiere
docker cp /tmp/capture.pcap kali:/root/capture.pcap

# 3. Protocol-Überblick
docker exec kali tshark -r /root/capture.pcap -q -z io,phs 2>/dev/null

# 4. Top Talkers
docker exec kali tshark -r /root/capture.pcap -q -z conv,ip 2>/dev/null | head -30

# 5. Externi IPs
docker exec kali tshark -r /root/capture.pcap \
  -Y "ip.dst != 10.0.0.0/8 and ip.dst != 224.0.0.0/4 and ip.dst != 255.255.255.255" \
  -T fields -e ip.dst 2>/dev/null | sort | uniq -c | sort -rn | head -10

# 6. Service-Scan (aktiv)
docker exec kali nmap -sT -p 22,80,443,3000,8123,1883,6333,9000,9090,9443,2377 <ip>
```

### 2. Person-OSINT (Passiv)
Multi-Phase-Workflow für vollständigi Persona-Analyse:
- Phase 1: Domain-Recon (whois, dig, dnsrecon, whatweb)
- Phase 2: Username-Suche (sherlock, maigret)
- Phase 3: Email-Check (holehe, socialscan)
- Phase 4: API Deep-Dives (GitHub, GitLab, Gravatar)
- Phase 5: Cross-Reference & Report

```bash
# Quick-Combo
theharvester -d example.com -b google,linkedin
sherlock username
holehe email@example.com
amass enum -d example.com
subfinder -d example.com
```

### 3. WordPress-Security
```bash
wpscan --url https://grow-pro.ch --api-token YOUR_TOKEN

# WPProbe (schneller, REST-API basiert, 5000+ Plugins)
wpprobe update-db                    # Vuln-Datenbank lade
wpprobe scan -u https://example.com  # Stealthy Mode (REST API)
wpprobe scan -u https://example.com --mode hybrid  # + Bruteforce
wpprobe search --plugin woocommerce  # vulns sueche
wpprobe search --cve CVE-2024-1234   # CVE sueche
wpprobe list                         # DB-Statistik
```

### 4. Vulnerability-Scanning (Nuclei)
```bash
# Einzelni Domain
nuclei -u https://example.com -severity critical,high

# Liste vo URLs
nuclei -l urls.txt -severity medium,high,critical

# Bestimmti Templates
nuclei -u https://example.com -t cves/ -t exposures/
```

### 5. OSINT-Scripting
```bash
# DNS → Subdomain → HTTP-Check Pipeline
subfinder -d example.com -silent | httpx -status-code -title
```

## ⚠️ Limitationen

| Nöd möglich | Grund | Alternative |
|-------------|-------|-------------|
| WiFi-Hacking (aircrack-ng) | Kei WLAN-Hardware im LXC | USB-WLAN-Stick a Proxmox 02 dureiche |
| GUI-Tools (Burp Suite, Zap) | LXC is CLI-only | Browser am Host nutze |
| Full WireShark | Kei GUI | `tcpdump` + `tshark` via CLI |
| Langi Scans > 1h | Begrenzti Ressource (RAM/CPU) | In Batches ufteile |
| Kernel-Level Exploits | LXC = isoliert | Host-Zuegriff via SSH |
| Grosse Download | Internet über Proxmox-Route | Uf Host vorlade + in Container kopiere |

## 🔴 Aktuelle Erreichbarkeit (14.06.2026)

**Proxmox 02 (10.0.60.11) isch nöd geroutet** ab 10.0.60.0/24:
- `ping 10.0.60.11`: 100% packet loss
- `ssh root@10.0.60.11`: No route to host
- Via Proxmox 01 (10.0.60.10): `ssh root@10.0.60.10 "ssh root@10.0.60.11 ..."` — au No Route

**Solang Proxmox 02 nöd erreichbar isch**, chömed d'Kali-Tools nöd brucht werde. **Alternative:** Alli gängige Security-Tools lokal installiere (lueg Hacker-Profil).

## Go Binary Installationshinweis

Vili Security-Tools (nuclei, wpprobe, subfinder, amass) sind Go-Binaries wo als Einzeldateie uf GitHub Releases usegäh wärde. **Neueri Releases (2025+) verzichte oft uf .tar.gz** und sended d'Binarys roh. Siehe `references/go-binary-install.md` für korrektes Download-Pattern.

## 🧪 Verifikation

```bash
# 1. Container läuft?
docker ps | grep kali

# 2. Netzwerk-Scanning?
nmap --version | head -1

# 3. Packet-Capture?
tshark --version | head -1

# 4. Vulnerability-Scan?
nuclei -version

# 5. OSINT-Tools?
theharvester -d example.com -b google 2>&1 | head -3

# 6. DNS-Recon?
subfinder -d example.com -silent | head -3
```

## Wichtigi Hiwis

- **Kein GUI** — nur CLI. Kali läuft ohni Desktop.
- **Host:** Proxmox 02 (10.0.60.11) — **NICHT** uf Apollo.
- **LXC via Proxmox** — kei Docker-Mehr. Zuegriff via `lxc-attach`.
- **wpprobe** isch installiert für WordPress Plugin-Enumeration. Vor erstem Gebrauch: `wpprobe update-db`.
- **Nuclei-Templates** und **wpprobe-Datenbank** regelmässig update: `nuclei -update-templates && wpprobe update-db`.
- **Nützlichi Reference:** `references/go-binary-install.md` — korrektes Download-Pattern für moderni Go-Binary-Release ohni tar.gz.

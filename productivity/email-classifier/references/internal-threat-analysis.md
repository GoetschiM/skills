# Internal-Source UniFi Threat Analysis

## Pattern: Apollo/Kali-Container → IoT-VM (26.05.2026 — GL-98)

Discovered in session 26.05.2026: 5 identische UniFi Threat-Detected-Alerts (innert 2 Sekunden) von **Apollo e3:c7 (10.0.60.156)** nach **10.0.40.30** (IoT-VLAN).

Das ist ein neues Pattern: Frühere Threats kamen von externen IPs (45.9.168.16 = CDN-Perf-Test). Dieses Mal ists **interne Quelle**.

## Analyse-Schritte für interne Source-IPs

### 1. Source identifizieren
- `ping -c 2 -W 2 <IP>` — isch Host erreichbar?
- `nmap -sT -P0 -p 22,80,443,5002,5678,8080 <IP> --open` — was lauft druff?
- `ip neigh show | grep <IP>` — MAC-Adresse (Quervergleich mit bekannten Hosts)
- Hostname/MAC in ARP-Tabelle suchen (bei Apollo war "e3:c7" MAC-Suffix)

### 2. Target identifizieren (10.0.40.30 in diesem Fall)
- Gleiche Checks (ping, nmap)
- Bereits bekannte Ports aus früheren Incidents (bei 10.0.40.30: Port 22 SSH + 80 Apache, Debian 12)
- Querverweis auf frühere Tickets (GL-94, GL-90 => gleiches Target)

### 3. Risikobewertung intern
| Szenario | Risiko | Begründung |
|----------|--------|------------|
| Bekannter Admin-Host (Apollo/Kali) → bekanntes Target | 🟢 NIEDRIG | Vermutlich geplanter Scan oder nmap-Script |
| Unbekannter interner Host → kritisches Target | 🟡 MITTEL | Abklärungsbedarf |
| Bekannter Host → unbekanntes Target | 🟡 MITTEL | Neues Verhalten abklären |
| Unbekannter Host → unbekanntes Target | 🔴 HOCH | Potenziell kompromittiertes Gerät |

### 4. Tool-Kompatibilität
| Tool | Ergebnis bei internen IPs |
|------|--------------------------|
| ipinfo.io | `"bogon": true` (keine externe Info, nur interne IP) |
| ping | ✅ funktioniert über VLAN-Grenzen |
| nmap | ✅ funktioniert (open ports je nach FW) |
| ip neigh | Nur hosts im gleichen Subnetz (10.0.60.x) |

### 5. Besonderheiten Apollo (10.0.60.156)
- **Kali Linux Docker-Container** — NMAP, Metasploit, OSINT-Tools installiert
- Ports: 22 (SSH), 5002 (Call API)
- Kann legitime Scans ausführen, die UDM als Threat flagged
- Bei 5+ identischen Alerts in <3s: typisch für NMAP-Scan-Welle, nicht Malware

## GL-98 Erkenntnisse
- 5 identische Mails in 2 Sekunden = 1 Incident, kein Flood
- Source "Apollo e3:c7" = MAC-Suffix, nicht Hostname in DNS
- Interner Traffic wird von UDM korrekt erfasst, aber False-Positive-Rate ist höher
- Empfehlung: Bei Apollo-Threats immer zuerst auf Apollo SSH und nachschauen ob ein Scan gelaufen ist

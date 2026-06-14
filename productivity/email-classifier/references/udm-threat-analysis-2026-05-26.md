# UDM Threat Analysis — Session 26.05.2026

## Incident GL-94: 45.9.168.16 → 10.0.40.30

### Externi IP Findings
```
IP: 45.9.168.16
Hostname: hu5.eu.node.cdn-perfprod.com
Location: Budapest, Hungary (47.4984,19.0404)
Org: AS211619 MAXKO d.o.o.
Typ: CDN Performance Testing Node
```

### Interni Target Findings
```
10.0.40.30 (IoT-VLAN 10.0.40.x):
  - Ping: ✅ (0.3ms, TTL 63 → 1 Hop via UDM)
  - Port 22: OpenSSH 9.2p1 Debian 2+deb12u7
  - Port 80: Apache 2.4.66 (Default Page)
  - Gerätetyp: Debian 12 Server/VM
```

### Identified Internal IPs
| IP | VLAN | Status | Notes |
|----|------|--------|-------|
| 10.0.40.30 | IoT (10.0.40.x) | Erreichbar | Debian 12, OpenSSH+Apache, unbekanntes Passwort |
| 10.0.20.45 | DMZ/Gast (10.0.20.x) | Ping filtered | Keine offenen Ports, taucht in GL-90+GL-71 als SOURCE auf |
| 10.0.10.135 | Privat (10.0.10.x) | Ping filtered | Keine offenen Ports |
| 10.0.10.142 | Privat (10.0.10.x) | Ping filtered | Hohe Latenz 2.6s |

### Verwandti Incidents
| Ticket | Datum | Source zu Target | Status |
|--------|-------|------------------|--------|
| GL-94 | 26.05. 01:43 UTC | 45.9.168.16 zu 10.0.40.30 | Erledigt |
| GL-90 | 25.05. 01:43 UTC | 45.9.168.16 zu 10.0.40.30 | Erledigt |
| GL-90 | 25.05. 02:11 UTC | 10.0.20.45 zu 10.0.10.135 | Erledigt |
| GL-71 | 22.05. 14:11 UTC | 10.0.20.45 zu 10.0.10.142 | Erledigt |

### Risikobewertig
- **45.9.168.16** = CDN-Perf-Test → FALSE POSITIVE
- **10.0.20.45** taucht in 2 Tickets als SOURCE auf -> beobachtungswuerdig
- UDM hat korrekt blockiert

### Tool-Compatibility
| Tool | Host | Ergebnis |
|------|------|----------|
| ipinfo.io | Hermes | Externi IP-Info |
| ping | Hermes | Zielabhaengig |
| nmap | Kali (10.0.60.156) | Port-Scan ueber VLANs |
| SSH uf 10.0.60.167 | Nova/Asterisk | ARP nur 10.0.60.x |
| SSH uf 10.0.60.121 | Dokploy | ARP nur 10.0.60.x |
| HA API | Home Assistant | Kein Unifi-Plugin |
| UDM Pro (10.0.60.1) | Ubiquiti | SSH gesperrt |

# Netzwerk-Audit Methodology — Goetschi Labs

Vollständige Analysereihenfolge für eine pcap-Datei (z.B. 5-min Capture via `tcpdump` oder `tshark`).

## 1. Container vorbereite

```bash
# Capture-Host kopieren
docker cp /tmp/capture_5min.pcap kali:/root/capture.pcap

# Container-Bash
docker exec -it kali bash
cd /root
```

## 2. Global Overview

```bash
# Protocol Hierarchy — zeigt Anteil pro Protokoll (%)
tshark -r capture.pcap -q -z io,phs

# IP Conversations — wer redet mit wem (Frames)
tshark -r capture.pcap -q -z conv,ip

# Top Talkers nach Bytes
tshark -r capture.pcap -T fields -e ip.src -e ip.dst -e frame.len | \
  awk '{a[$1"→"$2]+=$3; b[$2"→"$1]+=$3} END{for(k in a)printf("%s  %d bytes\n",k,a[k]+b[k])}' | \
  sort -rn -k2 | head -20
```

**Was luege:**
- Ungewöhnliche Protokolle (UDP-data? unbekannti Ports?)
- Dominanz vo mDNS/ARP/Broadcast → normal im Homelab, aber auffällig weni >50%
- Top Talker: externi IPs = expected? CloudFront? Telegram? Unbekannt?

## 3. DNS / mDNS Analyse

```bash
# Alle ausgehende DNS-Queries (nicht Antworten)
tshark -r capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name -e dns.qry.type | sort | uniq -c | sort -rn | head -30

# mDNS Service Types
tshark -r capture.pcap -Y "dns.qry.name contains _tcp or dns.qry.name contains _udp" \
  -T fields -e dns.qry.name | sort | uniq -c | sort -rn | head -30

# Alle externen DNS-Abfragen (kein .local, kein 10.x)
tshark -r capture.pcap -Y "dns.flags.response == 0 and dns.qry.name not contains .local and dns.qry.name not contains .arpa" \
  -T fields -e dns.qry.name | sort | uniq -c | sort -rn | head -20
```

**Was luege:**
- mDNS-Flut: sehri vili Gerät sendet alli 2-3s Discovery. Jedes Subnetz hat en Gateway wo mitmacht.
- External DNS: welche Dienste werdet kontaktiert? Eventuell Telemetrie/Phoning-Home?
- LLMNR (wenn vorhande): Windows-Gerät im Netz?

## 4. Externi Verbindige

```bash
# Alle externen IPs (nicht RFC1918, nicht Multicast, nicht Broadcast)
tshark -r capture.pcap \
  -Y "ip.dst != 10.0.0.0/8 and ip.dst != 192.168.0.0/16 and ip.dst != 172.16.0.0/12 and ip.dst != 224.0.0.0/4 and ip.dst != 255.255.255.255" \
  -T fields -e ip.dst | sort | uniq -c | sort -rn
```

**Was luege:**
- Liste isch normalerweis churz (< 10 IPs). Vili IPs = möglicher Data-Exfiltration oder Infektion.
- Bekannti IPs: CloudFront (AWS), Telegram, GitHub, Docker Hub, etc.
- Unbekannti IPs → whois/Reverse-Lookup prüefe

## 5. ICMP Traffic Analyse

```bash
# ICMP-Typen-Statistik
tshark -r capture.pcap -Y "icmp" -T fields -e icmp.type | sort | uniq -c | sort -rn

# ICMP Type 13 (Timestamp) — Quelle
tshark -r capture.pcap -Y "icmp.type == 13" -T fields -e ip.src | sort | uniq -c | sort -rn

# ICMP Type 8 (Echo Request) — Quelle
tshark -r capture.pcap -Y "icmp.type == 8" -T fields -e ip.src | sort | uniq -c | sort -rn

# ICMP Unreachable (Type 3) — Details
tshark -r capture.pcap -Y "icmp.type == 3" -T fields -e ip.src -e ip.dst -e icmp.code | \
  sort | uniq -c | sort -rn | head -15
```

**ICMP Type Reference:**
| Type | Name | Bedeutung |
|------|------|-----------|
| 0 | Echo Reply | Ping-Antwort |
| 3 | Dest Unreachable | Host/Port nöd erreichbar |
| 8 | Echo Request | Ping |
| 11 | Time Exceeded | TTL abgloffe (traceroute) |
| 13 | Timestamp Request | **Ungewöhnlich** — System-Zeitabfrage. Linux-Kernel-Feature oder Recon |

**Was luege:**
- Type 13 (Timestamp) isch **untypisch für Normalbetrieb**. Sött immer hinterfragt werde.
- Type 8 ohne Type 0 (Echo ohne Reply) → Ziel antwortet nöd (Firewall oder offline)
- Type 3 → welche IPs sind nöd erreichbar? Vielleicht Stale-Konfiguratione?

## 6. ARP Analyse

```bash
# ARP Requests (who-has) — pro Ziel + Quelle
tshark -r capture.pcap -Y "arp.opcode == 1" -T fields -e arp.src.proto_ipv4 -e arp.dst.proto_ipv4 | \
  awk '{print $1,"→",$2}' | sort | uniq -c | sort -rn | head -20

# Unbeantworteti ARP-Requests (stale entries)
# Wiederholti Anfrage über > 5 Min = Host vermutlich offline
```

**WICHTIG — Quelle identifiziere!**
D'ARP-Requests chömed **nid** zwingend vom analysierte Host. Im Homelab sinds oft:
- **Gateway (10.x.x.1)** — normal, UDM probiert alli IPs im Subnetz
- **HP-Box / Thin Client / Server** (`10:e7:c6:*` = Hewlett Packard) — het en alti Config wo uf decommissioned IPs zeigt
- **Docker-Container** — überlebendi Config nach Container-Löschig

**Schritt 1: Quelle live prüefe**
```bash
# Aktuelle ARP-State uf Apollo
ip neigh show | grep -E "10\.0\.60\.(182|200|201)"
# Output: STALE = mal online gsi, REACHABLE = aktuell da, INCOMPLETE/FAILED = offline

# Live prüefe obs d'IP nonig git
timeout 3 ping -c1 -W1 <ip> 2>/dev/null && echo "✅ LÄBT" || echo "❌ Offline"
```

**Schritt 2: Quelle identifiziere (MAC-Vendor-Lookup)**
```bash
# Wer isch d'Quelle vo de ARP-Requests?
nmap -sT -p 22,80,443 <quelle_ip> -O 2>/dev/null
# MAC-Check: https://macvendors.com/<mac>
# Bekannti Prefixes:
#   10:e7:c6:* → Hewlett Packard
#   d4:c9:ef:* → ?
#   bc:24:11:* → Quanta Computer (Dokploy-Node)
#   02:ad:67:* → lokali MAC (Docker/HAOS)
```

**Schritt 3: Quelle untersuche (falls möglich)**
```bash
# SSH teste
ssh -o ConnectTimeout=3 root@<quelle_ip> "hostname; uptime"
# Uf Quelle luege: cron, systemd, mount-config uf die verschollene IPs
```

**Was luege:**
- **NID d'Frag "welchi IPs sind offline" — sondern "WER sucht sie?"**
- Häufig: decommissioned VMs, umzognigi Gerät, Docker-Container die nüm existiere
- Lösig: Uf de QUELLE d'Konfiguration säuberen (nöd uf Apollo `arp -d`)
- Wenn kei SSH-Zuegriff → UDM-Konsole oder Gerät direkt aaluege

## 7. Service Detection (aktiv)

```bash
# Schnell-Scan uf bekannte Hosts
nmap -sT -p 22,80,443,8080,3000,5000,8123,9000,9090,1883,6333,9443,2377 <ip>

# Categorisierig:
# - 22/SSH: Server-Zuegriff
# - 80/443: Web-Interface
# - 3000: Grafana/Gitea/Prometheus
# - 8123: Home Assistant
# - 1883: MQTT
# - 6333: Qdrant
# - 9443: Portainer/Dokploy
# - 2377: Docker Swarm
```

## 8. HTTP-Traffic (unverschlüsselt)

```bash
tshark -r capture.pcap -Y "http.request" -T fields -e http.host -e http.request.uri | \
  sort | uniq -c | sort -rn | head -20
```

Wenig HTTP = guet (meiste isch TLS-verschlüsselt).
Viel HTTP = mögliche unverschlüsselti Credentials/Daten.

## 9. Zusammenfassung / Report

Pro 5-Min-Capture typische Befunde:

| Metrik | Normal | Warnung |
|--------|--------|---------|
| mDNS-Anteil | 10-30% | > 40% = viele IoT-Gerät im Netz, normale Homelab-Situation |
| ARP-Anteil | 5-15% | > 20% = viele Stale-Entries oder Subnetz-Grösseproblem |
| Externe IPs | < 10 | > 20 = ungewöhnlich, prüfe |
| ICMP Type 13 | 0 | Jede Type 13 = unerwartet, Quelle prüfe |
| ICMP Unreachable | < 5 ips | Vili versch. IPs = Host scannt Subnetz |
| HTTP (< TLS) | Minimal | Sött < 1% si — alles andere isch unverschlüsselt |

## ⚠️ Pitfalls

- **mDNS zählt in VLAN-Captures doppelt** — Vlan-Header verursacht separati Frame-Zählig. Im Zweifel raw Capture ohni VLAN-Filter.
- **ICMP Type 13 chunt vo Linux-Kernel** wenn `icmp_echo_ignore_broadcasts=0` oder en Monitoring-Tool es Timestamp-Request macht. Uf Source-Host prüefe: `sysctl net.ipv4.icmp_echo_ignore_broadcasts`
- **Docker container mit host networking** — Captures vom Host finge au Container-Traffic. Nur Filter über IP hilft zur Trännig.
- **tcpdump vs tshark Buffer** — Längeri Captures > 10 Min chönd Buffer-Overflow gäh (`tcpdump: dropped packets`). Immer `-s 0 -B 4096` für Produktiv-Captures.
- **Uplink vs intern** — Traffic zu CloudFront (3.x.x.x, 52.x.x.x) -> Hermes/TG-Bot. Traffic zu 149.154.x.x -> Telegram. Das isch normal für de Setup.

## 🔄 Live Verify — Findings nachprüefe

**Wichtig: PCAP isch en Snapshot.** En Fund us em Capture chan momentan gsi si. Immer live verifiziere:

```bash
# ICMP Type 13 — no vorhande?
timeout 5 tcpdump -i any -n "icmp[icmptype] == 13" -c 3 2>/dev/null
# Echo Requests — no vorhande?
timeout 5 tcpdump -i any -n "icmp[icmptype] == 8" -c 5 2>/dev/null

# Stale ARP — no aktuell?
ip neigh show | grep -E "10\.0\.60\.(182|200|201)"
# STALE = mal gsi, REACHABLE = jetzt da, INCOMPLETE/FAILED = immer no weg
```

**Wenn live nöd reproduzierbar:** Fund trotzdem dokumentiere (im Capture gsi). Aber "beobachte" statt "sofort handle".

## 🔧 Bonus: IRQ Affinity Check

**Wann?** Viel Netzwerk-Traffic uf eim Host (Homelab-Server) und eifachi CPU-Kern isch überlascht.

```bash
# Alle Interrupts prüefe
cat /proc/interrupts 2>/dev/null | grep -E "eth|eno|ens|enp|virtio"

# IRQ-Affinität prüefe
cat /proc/irq/*/smp_affinity 2>/dev/null

# Fix: verteile uf alli CPUs
echo f > /proc/irq/124/smp_affinity   # 'f' = 0b1111 = CPU0+1+2+3

# SoftIRQ-Last prüefe
cat /proc/softirqs 2>/dev/null | head -5
```

**Was luege:**
- Alli Interrupts uf **CPU0** (> 300M) und 0 uf andere? → IRQ-Pinning-Problem
- Normal: 4 CPUs söttet d'Last teile
- **Ursach:** Oft Proxmox/KVM virtio-Treiber wo SMP-Affinity ignoriert
- **Fix uf Host-Ebeni** (nöd im Container) via Proxmox-Konfiguration

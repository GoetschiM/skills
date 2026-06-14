# Bekannti Externi Threat-Pattern (UDM IDS/IPS)

## False Positives 🟢

| Quelle | Hostname | Typ | Risiko | Beschrieb |
|--------|----------|-----|--------|-----------|
| `45.9.168.16` | `hu5.eu.node.cdn-perfprod.com` | CDN Performance Test | 🟢 False Positive | MAXKO d.o.o. (AS211619, Budapest). CDN-Performance-Test-Nodes scannen regelmässig zufällige IP-Bereiche, um Latenzen und Erreichbarkeit zu messen. Normals Internet-Rausche. UDM blockiert korrekt. **Kei Handlungsbedarf.** |

## Zuefüege

Wenn en neue externi IP als False Positive identifiziert wird:
1. ipinfo.io-Check mache (`curl -s https://ipinfo.io/<IP>/json`)
2. Hostname + AS-Org analysiere
3. Bi CDN/Crawler-Typ: Als 🟢 False Positive i die Liste ufnäh
4. Ticket-Bemerkig schriibe: "FALSE POSITIVE — <Begründung>"
5. Ticket chan zuemacht werde

## Muster zum Wiedererkenne

Typischi False-Positive-Quelle:
- **cdn-perfprod.com / cdn-test.nodes** — CDN Performance Tests
- **Shodan/Censys-Scanner** — Internet-Sichtbarkeits-Scans
- **Known AS-Orgs wie MAXKO, Hetzner, DigitalOcean** — wenns nume en Portscan isch
- **Einzelni GET/Ping pro Ziel** (kein Exploit-Versuch)

Würkliche Threat-Zeiche:
- Mehrmaligi Login-Versüech (Brute Force)
- Bekannti Exploit-Payloads i de UDM-Logs
- Unübliche Traffic uf Admin-Ports (22, 3389, 8443)
- Mehreri Ports / Protocol-Versüech vom gliiche Source

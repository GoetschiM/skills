# False Positive: CDN Performance Test Nodes

Bekannti CDN-Performance-Test-Nodes, wo regelmässig zufälligi IP-Range scanne und UDM Threat Alerts uslöse. Das sind **FALSE POSITIVES** — kei bösartigi Quelle.

## Bekannti Hosts

| IP | Hostname | Standort | AS-Organisation |
|----|----------|----------|-----------------|
| 45.9.168.16 | hu5.eu.node.cdn-perfprod.com | Budapest, HU | AS211619 MAXKO d.o.o. |

## Erkennigsmerkmol

- Hostname enthält `.node.cdn-perfprod.com`
- AS: MAXKO d.o.o. (Kroatien)
- Scans zufälligi Ziel-IPs, meischtens einzelni Connection-Versuech
- Kei Exploit-Versuech, kei Brute-Force, kei Malware-Payload
- UDM IDS/IPS blockiert korrekt

## Verhalte

Wenn en Threat vo dene Quelle chunnt:
1. **FALSE POSITIVE 🟢** — kei Risiko
2. Ticket erstelle + im Kommentar "CDN-Performance-Test-Node, False Positive" notiere
3. Ticket chasch schliesse
4. Muess nid witer analysiert werde — Muster isch bekannt

Gsee au `udm-threat-analysis-2026-05-26.md` für es vollständigs Analyse-Beispiel.

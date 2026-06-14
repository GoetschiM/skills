# Apollo/Kali Self-Scan Threat Pattern

## Problem
Wenn Hermes via Kali-Container (10.0.60.156 = Apollo) internal Hosts scannt (nmap, curl), generiert das UDM IDS-Alarm mit Source "Apollo e3:c7" — das isch de Apollo-Host, wo de Kali-Container druff lauft.

## Erkennigs-Muster
- Sender: `no-reply@notifications.ui.com`
- Betreff: "UDM Pro: Threat Detected"
- Body enthält: `from Apollo e3:c7 to <target>`
- Identischi Mails innert <10 Sekunde (Burst)

## Behandlung
- Das sind **SELF-GENERATED False Positives** — Hermes/lucy het selber scannt
- **SOFORT DELETE** — nie es Ticket erstelle
- Within-Batch Auto-Apply: Alli identische innerhalb vo 10s gliich lösche

## Trigger
| Aktivität | Threat-Text | Ursach |
|-----------|-------------|--------|
| nmap scan vom Kali-Container | `Apollo e3:c7 → 10.0.40.30` | Portscan für Threat-Analyse |
| curl/wget zum Target | `Apollo e3:c7 → 10.0.40.30` | HTTP-Check für Geräte-Identifikation |
| ping über Kali | `Apollo e3:c7 → <IP>` | ICMP-Test für Erreichbarkeit |

## Prävention
Nach eigene Scans: UDM-Dashboard öffne und prüefe ob Alarm usglöst worde. Wänn ja: Batch-DELETE via Gmail-Suche (`is:unread "Apollo e3:c7"`).

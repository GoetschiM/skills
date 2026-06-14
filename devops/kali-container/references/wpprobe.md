# WPPrrobe: WordPress Plugin Vulnerability Scanner

**Tool:** https://github.com/Chocapikk/wpprobe
**Version:** v0.11.8 (Stand 09.06.2026)
**Typ:** Go-Binary (single file, no deps)

## Installation

```bash
# 1. Latest Release binary direkt downloaden
curl -sL -o /usr/local/bin/wpprobe \
  "https://github.com/Chocapikk/wpprobe/releases/download/v0.11.8/wpprobe_v0.11.8_linux_amd64"
chmod +x /usr/local/bin/wpprobe

# 2. Datenbank initialisieren (Wordfence vuln DB)
wpprobe update-db

# Wichtig: Release hat KEINE .tar.gz! Nur reine Binaries als GitHub Release Assets.
```

## Scan-Modi

| Modus | Beschrieb | Schreibzugriff |
|-------|-----------|----------------|
| `--mode stealthy` | Nur REST API + HTML (NICHT bei wP-Post-API) | ❌ Nei |
| `--mode hybrid` | Stealthy + Bruteforce (Plugin-Pfade) | ❌ Nei |
| Standard | Vollständig (alle Methode) | ⚠️ Ja |

**Default = `--mode hybrid`** — immer explizit `--mode stealthy` für READ-ONLY!

## Nutzung

```bash
# Scan (Stealthy = READ-ONLY)
wpprobe scan -u https://grow-pro.ch --mode stealthy -o /tmp/scan-result.json

# Plugin-Suche
wpprobe search --plugin woocommerce --severity critical

# Statistik
wpprobe list --stats
```

## Scan grow-pro.ch (09.06.2026) — GL-143

- **Resultat:** 1 Critical (CVE-2023-5360 — File Upload), 13 High, 175 Medium
- **JSON:** /tmp/wpprobe-growpro.json
- **Ticket:** https://goetschi.atlassian.net/browse/GL-143

## Pitfalls

- **Glob = NIGC tar.gz!** Releases sind rohe Binaries, `.tar.gz` git's nöd
- **`wpprobe update-db`** muess vorgängig — suscht keine vuln data
- **`wpprobe`-Befehl** isch case-sensitive (chlineggschriebe)
- **WPScan-Token** isch optional (Enterprise) — Wordfence-DB chunt ohni

# Infrastruktur-Scan: Workflow & Format

> Stand: 07.06.2026 | Letzter Scan: pve01 (10.0.60.10)

## Workflow — Parallele Subagenten

Bei grossflächigen Scans (15+ LXCs/VMs) **3 parallele Subagenten** via `delegate_task(tasks=[...])`:

### Task-Aufteilung

| Task | Inhalt | Beispiel-CTs |
|------|--------|-------------|
| **Task 1: Apps & Dienste** | CTs 100-118 — Docker, Web-Apps, Deployment-Plattformen | CT100 (Dokploy), CT103 (Paperless), CT107 (MCPHub), CT108 (Hermes), CT109 (InfluxDB), CT112 (Nova), CT116 (LiteLLM), CT117 (Voice), CT118 (Coolify) |
| **Task 2: Infrastruktur & VMs** | Datenbanken, Vektordbs, S3, Smart Home, NAS | CT105 (PGVector), CT301 (NAS-Video), CT505 (MinIO), CT506 (Qdrant), VM113 (HA-OS), VM201 (CasaOS/Nextcloud) |
| **Task 3: Spezial & Agents** | AI-Agents, Trading-Bots, Exoten | CT401 (Magos), CT402 (Orion), CT504 (MT5-Bot) |

### Jeder Subagent bekommt
- **Vollständigen SSH-Befehl** (inkl. Passwort) — fixfertig zum Einfügen
- **Klare Liste** der zu scannenden CTs/VMIDs
- **Zielformat** (siehe unten)
- **Keine voreiligen Zusammenfassungen** — jedes Detail einzeln per `pct exec` abfragen

### SSH-Muster für Subagent-Prompts

```python
# In jedem Subagent-Prompt:
HOST = "root@10.0.60.10"
PASS = "Riotstar_PROXMOX_13"

# Für LXC-Interaktion:
sshpass -p 'Riotstar_PROXMOX_13' ssh -o StrictHostKeyChecking=no root@10.0.60.10 "pct exec <VMID> -- <command>"

# ACHTUNG: ! im Passwort zerschießt Shell-Heredocs. Immer via Python subprocess.run mit array-args!
```

## Format für jeden Container/Eintrag

Michels gewünschtes Format — Key: Value pro Zeile, pro Container eine Sektion, Emoji-Status voran:

```
### CT100 — Dokploy ✅
| IP | 10.0.60.121 |
| Typ | LXC (Ubuntu) |
| Status | ✅ running (onboot=1) |
| Ports | 3000 (Dokploy UI), 5678 (n8n), 8002 (Google MCP), 3033 (Moto-Poschung) |
| Docker | 12 Container: Dokploy v0.29.2, Portainer, n8n, LiteLLM, Postgres:16, Redis:7 |
| Dienste | Docker, containerd, Postfix |
| URLs | http://moto-poschung.rebelone.ch, http://10.0.60.121:1713 |
| Beschreibung | Haupt-Dokploy-Instanz — Container-Orchestrierung |
```

### Pflichtfelder pro Container
1. **IP** — primäre IP (aus `ip addr` oder Proxmox API)
2. **Typ** — LXC / Qemu VM
3. **Status** — ✅ running / ⛔ stopped / ❌ problem (mit `onboot=` Status)
4. **Ports** — alle offenen Ports + Dienstname
5. **Docker** — Anzahl + Namen + Images (wenn vorhanden)
6. **Dienste** — systemd services, Hintergrundprozesse
7. **Datenbanken** — wenn relevant (PG-Version, Datenbank-Namen, Grössen)
8. **URLs** — externe und interne URLs
9. **Beschreibung** — 1-2 Sätze was der Container macht (mit Emoji)

### Kategorien-Struktur (7 Bereiche)

Michel hat die Infrastruktur in 7 Kategorien organisiert:

| Kategorie | Inhalt |
|-----------|--------|
| **🏗️ 1. Deployment & Hosting** | CT100 (Dokploy), CT118 (Coolify), CT301 (gestoppt) |
| **🤖 2. AI-Agents & Gateways** | CT108 (Hermes Gen1), CT112 (Nova), CT117 (Voice), CT401 (Magos), CT402 (Orion) |
| **📄 3. Dokumente & Daten** | CT103 (Paperless), CT109 (InfluxDB), CT105 (PGVector), CT506 (Qdrant), CT505 (MinIO) |
| **🏠 4. Smart Home & Media** | VM113 (HA-OS), VM201 (CasaOS) |
| **🧩 5. MCP-Infrastruktur** | CT107 (MCPHub) |
| **🖥️ 6. Spezial-Anwendungen** | CT504 (MT5-Bot), CT116 (LiteLLM) |
| **🌐 7. Externe Domains** | Alle öffentlichen URLs + Status |

### Proxmox Host-Block (ganz oben)

```
## 🖥️ Proxmox Host — pve01
| Feld | Wert |
| IP | 10.0.60.10 |
| URL | https://10.0.60.10:8006 |
| Root User | root |
| Root Passwort | Riotstar_PROXMOX_13 |
| Version | pve-manager 8.4.19 |
| Storage | Disk (LVM): 83% (161GB frei), HDD (ZFS): 55% (418GB frei) |
```

## Checkliste pro Container (was abfragen)

```bash
# 1. Läuft er?
pct list | grep <VMID>

# 2. IP?
pct exec <VMID> -- ip addr show eth0 | grep 'inet '

# 3. Docker-Container?
pct exec <VMID> -- docker ps --format "{{.Names}}|{{.Image}}|{{.Ports}}" 2>/dev/null || echo "Kein Docker"

# 4. Offene Ports?
pct exec <VMID> -- ss -tlnp 2>/dev/null || pct exec <VMID> -- netstat -tlnp

# 5. Systemd-Dienste?
pct exec <VMID> -- systemctl list-units --type=service --state=running 2>/dev/null | grep -E '\.service'

# 6. Datenbanken? (Postgres)
pct exec <VMID> -- timeout 10 su - postgres -c "psql -c 'SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datistemplate = false ORDER BY datname;'" 2>/dev/null || echo "Kein Postgres"
```

## Nach dem Scan

1. **Doku speichern**: als `/root/goetschi-labs-infrastruktur.md`
2. **Memory updaten**: Kurzreferenz für die wichtigsten IPs/Ports/Passwörter
3. **Confluence**: Upload zur Seite "🔧 Infrastruktur" — ACHTUNG: Confluence API-Token kann abgelaufen sein!

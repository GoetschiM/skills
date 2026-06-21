# Paperless ↔ Nextcloud Workflow (Goetschi Labs, Stand 07.06.2026)

## Architektur

```
Nextcloud (CT201, CasaOS Docker)         Paperless (CT103, LXC native)
┌────────────────────────────┐           ┌──────────────────────┐
│  User lädt PDF hoch        │           │  Consumer Daemon     │
│  → /Scanner/ oder /Paperless/         │  → /opt/paperless/   │
│                                      │    consume/           │
│  Samba Share                │           │                      │
│  → /media/NAS/Paperless-   │  rsync    │  Bind Mount von pve01│
│    Consume/                 │───(2min)──│  → /opt/paperless/   │
│                            │           │    consume/          │
└────────────────────────────┘           └──────────────────────┘
                                              │
                                              ▼
                                         Paperless verarbeitet
                                         → indexiert + archiviert
```

## Komponenten

| Komponente | Host | Details |
|-----------|------|---------|
| **Nextcloud** | CT201 (CasaOS VM) | Docker Container, Port 10081, DB: MariaDB |
| **Paperless** | CT103 (LXC) | Native, PostgreSQL, consume via Bind Mount |
| **6TB USB** | CT201 | `/media/NAS/` (exfat, 5.5TB frei) |
| **Sync-Host** | pve01 | rsync + SSH-Key zu CT201 + Bind Mount zu CT103 |

## Setup-Schritte

### 1. Samba Share auf CT201 (CasaOS)

```bash
# Auf CT201 via SSH (michel@10.0.60.201, pw: Louis_one_13)
mkdir -p /media/NAS/Paperless-Consume
chmod 777 /media/NAS/Paperless-Consume

# In /etc/samba/smb.conf hinzufügen:
# [Paperless-Consume]
#    path = /media/NAS/Paperless-Consume
#    browseable = yes
#    read only = no
#    guest ok = yes
#    create mask = 0777
#    directory mask = 0777

systemctl restart smbd
```

### 2. SSH-Key auf pve01 für passwortlosen Zugriff

```bash
# Auf pve01:
ssh-keygen -t ed25519 -N ""
cat ~/.ssh/id_ed25519.pub | sshpass -p "Louis_one_13" ssh michel@10.0.60.201 \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### 3. rsync Cron (alle 2 Min)

```bash
# Auf pve01 in /root/sync-paperless-consume.sh:
#!/bin/bash
rsync -avz --remove-source-files --rsh="ssh -o StrictHostKeyChecking=no" \
  michel@10.0.60.201:/media/NAS/Paperless-Consume/ \
  /var/tmp/paperless-consume/

# Cron:
*/2 * * * * /root/sync-paperless-consume.sh >/dev/null 2>&1
```

### 4. Bind Mount zu CT103

```bash
# Auf pve01:
pct set 103 -mp0 /var/tmp/paperless-consume,mp=/opt/paperless/consume

# LXC mountpoint: /opt/paperless/consume zeigt auf /var/tmp/paperless-consume vom Host
# Paperless config:
# PAPERLESS_CONSUMPTION_DIR=/opt/paperless/consume
```

### 5. Nextcloud Scanner Ordner

Michel muss in Nextcloud-WebUI einen Ordner `/Scanner` oder `/Paperless` anlegen.
Dateien die dort landen → Samba-Share (wenn der Ordner per Symlink auf Paperless-Consume zeigt) → rsync → Paperless consume → automatisch verarbeitet.

## Wichtige Credentials

| Service | User | Passwort |
|---------|------|----------|
| **Nextcloud Admin** | michel | Michel_NC_Admin_2026! |
| **Nextcloud DB** | nextcloud | NextCl...lDB! |
| **CasaOS SSH** | michel | Louis_one_13 |
| **Paperless DB** | paperless | H9Yp4dz8bPT3v |
| **Paperless WebUI** | paperless-admin | E8UfVSsHtReHQUmwtKLlbk3y |

## Wichtige URL

| Service | URL |
|---------|-----|
| **Nextcloud** | http://10.0.60.201:10081 |
| **Nextcloud extern** | https://nextcloud.rebelone.ch |
| **Paperless** | http://10.0.60.121:8015 (via CT100 Dokploy) |
| **CasaOS** | http://10.0.60.201 |

## Pitfalls

1. **CT103 kann CT201 nicht direkt erreichen** — Firewall auf CT201 (Proxmox) blockt. Daher rsync über pve01 als Mittelsmann.
2. **pct set -mp0** überschreibt den consume-Ordner — frühere consume-Dateien landen im Backup unter `/var/tmp/paperless-consume-local/`
3. **paperless user** kann keine chown auf Bind-Mount — Provider `nobody:nogroup` mit 777 Permissions funktioniert trotzdem
4. **CasaOS SSH** — nur michel-User hat Zugang (root blockt), sudo mit echo password pipe nötig
5. **Nextcloud Scanner Ordner** — muss über Web-UI angelegt werden (occ files:mkdir existiert nicht)

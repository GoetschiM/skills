---
name: proxmox-lxc
description: "Proxmox LXC container management — create, start, quorum fix, Docker-in-LXC setup on single-node clusters."
category: devops
tags: [proxmox, lxc, container, quorum, pct, pvesh, virtualization]
---

# Proxmox LXC Management

Proxmox LXC Container (pct) management — der zentrale Workflow für Infrastructure-as-Code auf pve01 (10.0.60.10).

## Trigger

- User sagt "neue LXC erstelle", "Container ufsetze", "Sandbox-LXC"
- pct create/pct start schlägt fehl mit "cluster not ready - no quorum?"
- Docker soll in LXC laufen (braucht nesting=1)
- MinIO/S3 Backup für neuen Service konfigurieren
- **NEU:** User will LXC-Dienste via Tailscale erreichbar mache (Subnet Routing)(

## Zugriff

| Host | IP | Auth |
|------|----|------|
| pve01 | 10.0.60.10 | root + Passwort (via sshpass) |

Proxmox Version: 8.4.19, Kernel 6.8.12-18-pve

## LVM Thin Disk: fstrim nach Dateilöschung

**Problem:** LXC zeigt 100% Disk voll (`df -h`) obwohl grosse Dateien gelöscht wurden. Das passiert weil LVM Thin-Provisioning Blöcke erst nach `fstrim` freigibt.

**Symptome:**
```bash
pct exec <VMID> -- df -h /                    # 100% full
pct exec <VMID> -- du -sh /                    # sagt nur 38G
lvs | grep vm-<VMID>                           # data_percent 96-99%
```

**Ursache:** Gelöschte Dateien von Docker-Containern (Torrents, Logs) bleiben im LVM Thin-Pool allokiert, weil der `DISCARD`-Befehl nie ans Block-Device gesendet wurde. Unprivilegierte LXCs dürfen `fstrim` nicht selbst ausführen ("Operation not permitted").

**Lösung — fstrim vom Proxmox Host:**

```bash
# 1. Prozesse stoppen die gelöschte Files noch offe hebet
pct exec <VMID> -- lsof +L1 | grep deleted  # Check which processes
pct exec <VMID> -- docker stop <container>  # Stop container holding files

# 2. lsof nochmal check — falls kei offene Handles meh
pct exec <VMID> -- lsof +L1 | grep deleted  # Should be empty

# 3. Vom Proxmox Host: Thin Pool trimmen
pct fstrim <VMID>

# 4. Verifizieren
pct exec <VMID> -- df -h /                   # Soll freien Platz zeigen
lvs | grep vm-<VMID>                         # Soll niedrigere data_percent zeigen
```

**Wichtig:** Files die von Docker-Containern via Volume geschriebe worde, sind über den Container-Prozess offe. `pct fstrim` allein bringt nüt — zersch Container stoppe, denn trimme.

## LXC erstellen (pct create)

```bash
sshpass -p '<PASSWORT>' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  'pct create <VMID> local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
    --hostname <NAME> \
    --cores 2 \
    --memory 8192 \
    --rootfs Disk:<DISK_SIZE_GB> \
    --net0 name=eth0,bridge=vmbr0,firewall=1,ip=dhcp,ip6=dhcp,type=veth \
    --features nesting=1 \
    --unprivileged 1 \
    --ostype ubuntu \
    --password "<ROOT_PASSWORD>"'
```

**Disk size:** Use 30G for minimal services, 110G for media stacks (REMUX 4K movies fill 30G instantly — see `media-automation` skill for sizing). Available storage pools: `Disk` (LVM-Thin, ~139G free) and `HDD` (ZFS, ~406G free), referenced as `--rootfs HDD:<SIZE>` or `--rootfs Disk:<SIZE>`.

**Vergibeni LXC IDs (pve01, Stand Mai 2026):**
- `100` — Dokploy (Production) — 10.0.60.121
- `103` — Paperless-NGX
- `105` — Postgresql-PGVector
- `107` — Moto-Poschung
- `108` — Hermes-LiteLLM (Apollo) — 10.0.60.156
- `109` — InfluxDB
- `110` — Sandbox-Dokploy — 10.0.60.136
- `112` — Nova-Sipcall
- `122` — QDevice
- `301` — NAS-Video
- `504` — mt5-bot04
- `505` — MinIO — 10.0.60.106
- `506` — Qdrant

**Freii LXC IDs:** vor 100: 101, 102, 104, 106, 110 (jetzt belegt), 111, 113-119, 123-299

## 🔴 Proxmox Quorum Issue — Der Klassiker

**Problem:** `pct create` / `pct start` / `pct list` schlägt fehl mit `cluster not ready - no quorum?`.

**Ursache:** Proxmox ist als Cluster konfiguriert (2+ Nodes + optional QDevice), aber der zweite Node (z.B. pve02 10.0.60.11) ist **offline**. Quote: `Expected votes: N` > `Total votes: 1`.

**Lösung — drei Wege:**

### Weg A: pmxcfs local mode (quick & dirty)

Am schnellsten, wenn nur ein LXC erstellt oder gestartet werden muss:

```bash
systemctl stop pve-cluster
systemctl stop corosync
# pmxcfs im local mode starten — ignoriert quorum vollständig
pmxcfs -l -f &
sleep 2
# Jetzt pct create/start ausführen
pct create 110 ...
pct start 110
# Danach Cluster restart
killall pmxcfs
systemctl start corosync && sleep 2
systemctl start pve-cluster
```

### Weg B: SQLite DB direkt editieren (permanent fix)

Modifiziere die korosync.conf direkt in der pmxcfs SQLite-Datenbank. Damit der Cluster auch mit nur 1 Node quorate wird:

```bash
# 1. Cluster stoppen
systemctl stop pve-cluster
systemctl stop corosync
killall pmxcfs 2>/dev/null
sleep 2

# 2. SQLite DB modifizieren
python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect("/var/lib/pve-cluster/config.db")
cur = conn.cursor()
cur.execute("SELECT inode, data FROM tree WHERE name = 'corosync.conf'")
inode, data = cur.fetchone()
content = data.decode("utf-8")

# Offline-Node entfernen
# expected_votes: 1 setzen
# qdevice votes auf 0 setzen wenn nötig
new_content = """logging {
  debug: off
  to_syslog: yes
}
nodelist {
  node {
    name: pve01
    nodeid: 1
    quorum_votes: 1
    ring0_addr: 10.0.60.10
  }
}
quorum {
  device {
    model: net
    net {
      algorithm: ffsplit
      host: 10.0.60.182
      tls: on
    }
    votes: 0
  }
  provider: corosync_votequorum
}
totem {
  cluster_name: Homelab
  config_version: <N+1>
  interface {
    linknumber: 0
  }
  ip_version: ipv4-6
  link_mode: passive
  secauth: on
  version: 2
  expected_votes: 1
}
"""
cur.execute("UPDATE tree SET data = ? WHERE inode = ?", (new_content.encode("utf-8"), inode))
conn.commit()
conn.close()
PYEOF

# 3. Cluster restarten
systemctl start corosync && sleep 2
systemctl start pve-cluster

# 4. Verifizieren
pvecm status | grep "Expected"
# Sollte "Expected votes: 1" zeigen
```

### Weg C: pvecm expected (temporär, oft wirkungslos)

`pvecm expected 1` kann helfen, wird aber oft sofort vom QDevice-Daemon
zurückgesetzt. Au hiift `corosync-cmapctl -s votequorum.expected_votes u32 1`
nöd — das wird au vom QDevice überschribe.

**Grund:** QDevice het sin eigete Vote (votequorum.device_votes=1) und zählt zum
expected. Au wenn de QDevice selber offline isch (Status=NA/NV), wird sin Vote
immer no zum expected_Votes dezuegrechnet.

**Verlässlichi Lösig:** SQLite-DB direkt editieren (Weg B oben).
Dert de QDevice votes uf 0 setze oder ganz us em nodelist entferne.

## LXC starten + verwalten

Nachdem Quorum gelöst ist:

```bash
pct start 110
pct exec 110 -- ip addr show eth0 | grep "inet "
pct list
pct stop 110
pct destroy 110
```

## 🔴 LXC-Zugriff: `lxc-attach` vs `pct exec`

**`lxc-attach` ist zuverlässiger als `pct exec`** für komplexe/nested commands — speziell wenn `docker exec` mit heredoc stdin oder Hintergrundprozesse im Spiel sind.

| Pattern | Empfehlung |
|---------|-----------|
| `pct exec <LXC> -- <short-command>` | OK für einfache einzeilige Kommandos |
| `pct exec <LXC> -- docker exec <container> <cmd>` | ⚠️ Timeout-Risiko bei komplexen Commands |
| `lxc-attach -n <LXC> -- docker exec <container> <cmd>` | ✅ Zuverlässig, auch mit heredocs |
| `lxc-attach -n <LXC> -- timeout 180 docker exec ...` | ✅ Sollte bei langsamen Befehlen (PHP occ) immer timeout setzen |

**Bevorzugter Zugriff auf Docker-Container in LXC:**

```bash
# Von Proxmox host aus
sshpass -p '<PASSWORT>' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  'lxc-attach -n <LXC_ID> -- docker exec <container> <command>'

# Mit heredoc stdin (z.B. für psql):
sshpass -p '<PASSWORT>' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "lxc-attach -n <LXC> -- docker exec -i <container> psql -U <user> -d <db>" << 'SQL'
SELECT * FROM table;
SQL

# Mit lxc-attach + timeout (für Nextcloud occ):
sshpass -p '<PASSWORT>' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  'lxc-attach -n <LXC> -- timeout 180 docker exec -w /var/www/html <container> php occ <command>'
```

**🔴 LXC-Dateisystem bei Timeout lesen: `pct mount` / `pct unmount`**

Wenn `pct exec` oder `lxc-attach` hartnäckig timed out (typisch bei Docker-in-LXC mit langer Befehlsausführung), kann das LXC-Dateisystem direkt vom Proxmox Host gemountet werden:

```bash
# 1. LXC-Filesystem mounten (VMID = LXC-ID)
pct mount <VMID>
# Ausgabe: "copied /var/lib/lxc/<VMID>/delta . . ." oder "Copied /var/lib/vz/images/<VMID>..."
# Der Pfad variert — pct mount output zeigt wohin

# 2. In das gemountete Root-Filesystem wechseln
# Bei LXC-Thin-Provisioning: /var/lib/lxc/<VMID>/rootfs/
# Bei ZFS/Dir: /var/lib/vz/images/<VMID>/rootfs/
# Bei mount-Output mit "rootfs at /var/lib/lxc/<VMID>/delta": dort /rootfs/ verwenden
# Bei mount-Output mit "mounted at /tmp/pct-mount-<VMID>-XXXX": dorthin gehen

# 3. Dateien lesen/schreiben
cat /var/lib/lxc/107/rootfs/opt/mcphub/mcp_settings.json

# 4. Wichtig: Container während des Mounts läuft nicht — mount danach unmounten!
pct unmount <VMID>
```

**Pitfalls:**
- Während `pct mount` läuft, ist der Container **gestoppt** (das Dateisystem wird exklusiv gemountet). Planbare Ausfallzeit einrechnen.
- Nach dem Lesen/Schreiben **immer** `pct unmount <VMID>` aufrufen — sonst bleibt der Container dauerhaft offline.
- Der gemountete Pfad variert je nach Storage-Typ (LVM-Thin vs ZFS vs Dir). `pct mount` Output zeigt den exakten Pfad.
- `pct unmount` schlägt fehl wenn das Verzeichnis noch in use ist (`device or resource busy`). In dem Fall:
  ```bash
  # Offene Handles finden
  lsof /var/lib/lxc/<VMID>/rootfs
  # PID killen oder cd aus dem Verzeichnis
  cd / && pct unmount <VMID>
  ```

**Hinweis:** `lxc-attach` vo usserhalb vom Proxmox host (via SSH-Session) funktioniert stabiler als `pct exec` welches quoted strings falsch parse cha.

**Zugriff via SSH (Alternative, LXC hat eigenes root-Passwort):**
```bash
sshpass -p '<LXC_PASSWORD>' ssh -o StrictHostKeyChecking=no root@<LXC_IP> '<command>'
```

LXC-Config liegt unter `/etc/pve/lxc/<VMID>.conf` (via pmxcfs).

## Docker in LXC — Anforderungen

Docker funktioniert in Proxmox LXC, aber braucht:

1. **LXC-Config: `features: nesting=1`** — zwingend für Docker-Container-in-Container
2. **Unprivilegiert: `unprivileged: 1`** — Standard für pct create
3. **Docker Compose statt Docker Swarm** — Swarm host-mode Ports schlagen in LXC fehl

**🔴 Docker Daemon startet nicht nach LXC Neustart**

**Symptom:** LXC läuft (`pct list: running`), aber Docker-Daemon ist inaktiv → Container starten nicht, `docker ps` schlägt fehl.

**Ursache:** Docker wird zwar installiert + enabled (`systemctl enable docker`), aber bei LXC-Neustart bootet Docker nicht zuverlässig — speziell bei unprivilegierten LXCs mit `nesting=1`.

**Lösung:**
```bash
# Vom Proxmox Host aus
pct exec <VMID> -- systemctl start docker
# Oder via lxc-attach (zuverlässiger)
lxc-attach -n <VMID> -- systemctl start docker

# Verifizieren
pct exec <VMID> -- docker ps
```

**Prävention:** Nach dem ersten LXC-Neustart immer Docker starten und den Container prüfen. Docker Compose-Projekte starten danach normal via `docker compose up -d`.

**Docker installieren:**
```bash
pct exec <VMID> -- bash -c '
apt-get update -qq
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker; systemctl start docker
'
```

**🔴 Perl-Base DPKG-Fix:** Falls `dpkg --configure -a` mit Perl-Paketen scheitert, hilft:
```bash
cd /tmp && apt-get download perl-base
dpkg -i --force-overwrite perl-base_*.deb
apt-get install --fix-broken -y
```

## Templates auf pve01

```
local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst  (135 MB, empfohlen)
local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst      (118 MB)
local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst       (124 MB)
```

Neue Templates downloaden: `pveam update && pveam download local ubuntu-24.04-standard_24.04-2_amd64.tar.zst`

## Tailscale Zugriff: Subnet Routing (Proxmox Host statt LXC-Install)

**Pattern:** LXC-Dienste (z.B. Nextcloud) über Tailscale erreichbar mache, OHNE Tailscale in jedem LXC zu installieren.

**Problem:** Unprivilegierte LXCs hei kei `/dev/net/tun` und chönd Tailscale nöd direkt installiere (`mknod /dev/net/tun` isch nöd permitted). Alternativ: `features: tun=1` in der LXC Config erlaubt TUN, aber Subnet-Routing vom Proxmox Host us isch eleganter.

**Lösung — Tailscale Subnet Routing vom Proxmox Host:**

```bash
# 1. Tailscale auf Proxmox Host installiert + authentifiziert (läuft scho)
tailscale up --accept-routes --advertise-routes=10.0.60.0/24 --accept-dns=false

# 2. In der Tailscale Admin Console (login.tailscale.com):
#    - pve01 &rarr; Edit Route Settings &rarr; "10.0.60.0/24" &rarr; Save

# 3. Auf dem Client (Android/iOS):
#    Verbinde mit Tailscale &rarr; direkt https://10.0.60.121:8443
```

**Wi funktionierts:**
```
Android (Tailscale) -- WireGuard --> pve01 (10.0.60.10, Tailscale)
                                      |
                                leitet Traffic wiiter
                                (Subnet Routing)
                                      |
                              LXC 100 (10.0.60.121:8443)
```

**Vorteil:** Nur ei Tailscale-Node im ganze Subnetz. Kei TUN-Device nötig, kei Client-Installation in jedem LXC. De ganz 10.0.60.x-Bereich isch vo jedem Tailscale-Client aus erreichbar.

**Tailscale Status checke:**
```bash
tailscale status
# 100.90.250.116  pve01     michelgoetschi@  linux    -
# 100.88.139.116  android    michelgoetschi@  android  idle
```

## MinIO S3 Backup für LXC-Dienste

MinIO läuft auf LXC 505 (10.0.60.106:9000). Für neue LXC-Dienste empfohlen:

```bash
mc alias set homelab http://10.0.60.106:9000 <ACCESS_KEY> <SECRET_KEY>
mc mb homelab/<service>-backup
```

Dokploy-interne Backup-Konfiguration: siehe `dokploy` Skill → "MinIO S3 Backup vorkonfigurieren".

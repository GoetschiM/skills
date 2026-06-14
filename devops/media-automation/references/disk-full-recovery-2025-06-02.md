# Disk Full Recovery — LXC 110 (Sandbox) · 2026-06-02

**Context:** Radarr grabbed 4K REMUX torrents (30-80GB each). 6 torrents started downloading concurrently on a 110G LVM-thin volume. Disk hit 100% before anyone noticed.

## Timeline

1. qBittorrent downloaded for ~2h
2. Only Inception (5.1GB AV1) completed and was imported to Radarr `/movies`
3. 3 other torrents partially downloaded (33G, 29G, 67G) in `/downloads/` 
4. Disk hit 104G/109G = 100% — all docker exec commands fail with "no space left on device"

## Discovery Commands

```bash
# From Proxmox host:
pct exec 110 -- df -h /
#   /dev/mapper/Disk-vm--110--disk--0  109G  104G     0 100% /

pct exec 110 -- du -sh /
#   38G   /   (only 38G from userspace perspective!)
```

**Discrepancy:** 38G used per `du`, but 104G per `df`. The difference is Docker overlay2 layers and LVM thin provisioning.

## Finding Hidden Space

```bash
# Check actual directory sizes
pct exec 110 -- du -sh /opt/media-stack/downloads/*/
#   33G downloads/Blade.Runner...
#   29G downloads/Dune...
#   rm did not work because path had subfolder structure
```

## The qBittorrent Open File Handle Problem

```bash
# After deleting files, check what's still open
pct exec 110 -- lsof +L1 2>/dev/null | grep deleted
#   qbittorre 3017 1000  21u  REG 252,22 77098924052 ... (deleted)
#   qbittorre 3017 1000  23u  REG 252,22 43957238106 ... (deleted)
#   qbittorre 3017 1000  64r  REG 252,22  9563173563 ... (deleted)
#   qbittorre 3017 1000 128u  REG 252,22 67761893115 ... (deleted)
```

**4 files held open by qBittorrent PID 3017, totaling ~198GB** (but real on-disk was ~104GB due to partial downloads). Files showed "(deleted)" meaning the directory entry was unlinked but the inode data persists until the process closes the file descriptor.

## fstrim Recovery

```bash
# 1. Stop qBittorrent to release file handles
pct exec 110 -- docker stop qbittorrent

# 2. Delete remaining download data
pct exec 110 -- rm -rf /opt/media-stack/downloads/*

# 3. Verify no open handles remain
pct exec 110 -- lsof +L1 | grep deleted   # Should be empty

# 4. Trim LVM thin pool from host (NOT from inside LXC!)
pct fstrim 110
#   /var/lib/lxc/110/rootfs/: 3.4 GiB (3666886656 bytes) trimmed
#   First run freed 3.4G only (most files were still held open)

# 5. After stopping qBittorrent, run again:
pct fstrim 110
#   Result: data_percent dropped from 96.98% to 51.04% to 28.35%
#   LXC df: 29G used, 75G free
```

**Key insight:** `pct fstrim` must be run AFTER the process holding the file handles (qBittorrent) is stopped. Otherwise, only truly-deleted (unlinked AND closed) files get trimmed.

## LVM Progression

| Step | LVM data_percent | LXC df Used | Free |
|------|------------------|-------------|------|
| Before cleanup | 99.49% | 104G | 0 |
| After file deletion (still open) | 96.98% | 104G | 22M |
| After qBittorrent stop + fstrim | 51.04% | 29G | 75G |
| Second fstrim pass | 28.35% | 29G | 75G |

## Lessons

1. **4K REMUX is too large for 110G disk** — each movie is 30-80GB. Use x265 or AV1 4K (5-15GB).
2. **qBittorrent keeps deleted files open** — `lsof +L1` detects these. Must stop qB before fstrim.
3. **Unprivileged LXC can't run `fstrim`** — always run `pct fstrim <ID>` from Proxmox host.
4. **`df` vs `du` discrepancy** flags thin-provisioning block allocation that needs trim.

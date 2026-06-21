# Bind-Mounts for LXC Containers

LXC containers lack `CAP_SYS_ADMIN` by default in Proxmox — they **cannot** mount NFS, CIFS, FUSE, or any filesystem internally.

**Workaround**: bind-mount a host directory into the container.

## Creating a Bind Mount

```bash
pct set <CT_ID> -mp0 /path/on/host,mp=/path/in/container
```

- `mp0`, `mp1`, `mp2`... for multiple mounts
- Path on host must exist before setting
- The mount is persistent across container restarts
- **Not preserved** after `pct restore` — re-attach if container is recreated

## Example: Paperless Consume Directory

```bash
# 1. Create directory on host
mkdir -p /var/tmp/paperless-consume
chmod 777 /var/tmp/paperless-consume

# 2. Bind mount to LXC
pct set 103 -mp0 /var/tmp/paperless-consume,mp=/opt/paperless/consume

# 3. Verify in container
pct exec 103 -- ls -la /opt/paperless/consume
```

## File Permissions

Bind-mounts preserve the original permissions from the host filesystem. If the files are owned by UID 1000 (or `nobody`/`nogroup`) on the host, the container sees them with those same UIDs. The container user must have read access — can't `chmod` from inside the container because the mount is read-only from the container's perspective.

**Workaround**: Set ownership/permissions on the host:
```bash
chown -R 1000:1000 /var/tmp/paperless-consume
chmod -R 777 /var/tmp/paperless-consume
```

## Use With Samba/NFS

Common pattern: host mounts CIFS from a NAS, then bind-mounts into LXC:

```bash
# 1. Mount CIFS on host
mount -t cifs //10.0.60.201/Share /mnt/share -o guest,vers=3.0

# 2. Bind mount into LXC
pct set 103 -mp0 /mnt/share,mp=/opt/service/input

# 3. Sync via cron on host
cp -n /mnt/share/*.pdf /var/tmp/paperless-consume/
```

## Removing a Bind Mount

```bash
pct set <CT_ID> -mp0 /path/on/host,mp=/path/in/container
# Or remove all: pct set <CT_ID> -delete mp0
```

## Pitfalls

- **Not restored after `pct restore`** — must be re-applied
- **Read-only from container** — permissions must be set on host
- **No symlink resolution** — `-mp0` path must be a real directory, not a symlink target
- **`pct set` with -mp0 fails silently** if the host path doesn't exist yet — create it first

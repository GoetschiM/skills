# Network Scanner → Document Ingestion Pipeline

When to use this reference: user has a networked MFP (Brother, HP, Epson, Kyocera, Canon) and wants automatic document ingestion into Paperless-ngx.

## Step 0: Reconnaissance

```bash
ping -c 2 <scanner-ip>
for port in 21 22 23 80 139 443 445 515 631 9100; do
  timeout 2 bash -c "echo >/dev/tcp/<scanner-ip>/$port" 2>/dev/null && echo "Port $port OPEN" || true
done
```

Port meanings: 21=FTP, 80/443=Web, 139/445=SMB/CIFS, 515=LPD, 631=IPP, 9100=JetDirect

## Step 1: Access Web Interface (Brother)

Most Brother MFPs expose a web interface on port 80/443. Login field name varies:
- MFC-J5955DW: `Bc0c` → POST `/general/status.html`
- MFC-L3750CDW: `Bc0c` → POST `/general/status.html`
- DCP-L5500DN: `Bc0c` → POST `/general/status.html`

**⚠️ CRITICAL**: "Pwd" sticker on the device is often the WPS/WiFi key, NOT the admin password. Always try `initpass` first (Brother factory default). Secondary: blank, "admin", "access", "0000".

## Method A: Direct SMB/CIFS to Consume Folder (BEST)

```bash
# On Paperless server — add Samba share
cat >> /etc/samba/smb.conf << 'SMBEOF'
[Paperless-Consume]
   path = /opt/paperless/consume
   browseable = yes
   read only = no
   guest ok = yes
   create mask = 0644
   force user = paperless
SMBEOF
systemctl restart smbd
```

Configure scanner: Protocol SMB/CIFS, Host <Paperless-IP>, Share `Paperless-Consume`, file type PDF.

## Method B: SANE/brscan4 (server-side)

```bash
wget https://download.brother.com/welcome/dlf105200/brscan4-0.4.11-1.amd64.deb
dpkg -i brscan4-0.4.11-1.amd64.deb
apt install -y sane-utils
brsaneconfig4 -a name=<model> model=<model> ip=<scanner-ip>
scanimage -d "brother4:net1;dev0" --mode Color --resolution 300 --format=tiff --batch=/tmp/scan_%d.tiff
convert /tmp/scan_*.tiff /opt/paperless/consume/scan_$(date +%s).pdf
```

**Prefer eSCL/AirScan** devices (`airscan:e1:...`) over `brother4:...` — faster, smaller files, no registration needed.

## Method C: NAS Share + rsync

When scanner and Paperless server are on different subnets:
```bash
*/2 * * * * rsync -av --remove-source-files /mnt/nas/Paperless-Consume/ /var/tmp/paperless-consume/
```
Bind mount `/var/tmp/paperless-consume` to Paperless consume dir.

## Verification

```bash
smbclient //<server>/Paperless-Consume -N -c "ls"
curl -s http://<paperless-ip>:<port>/api/documents/ | python3 -c "import sys,json;[print(f'{d[\"id\"]}: {d[\"title\"]}') for d in json.load(sys.stdin).get('results',[])[:5]]"
```

See also: `scripts/scan-to-paperless.sh` (in this skill) for the full-featured end-to-end script.

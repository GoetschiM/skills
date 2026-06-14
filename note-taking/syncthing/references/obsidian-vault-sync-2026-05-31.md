# Goetschi Labs — Obsidian Vault Sync (Apollo)

**Deployed:** 2026-05-31  
**Host:** Apollo (10.0.60.156)  
**Container:** `syncthing`  
**Vault path:** `/opt/syncthing/vault/`  
**Device ID:** AGDPLWD-MC3U2UK-5CE4FQB-DGBKDVI-IU3ITAU-LXLXNQZ-Q2BN6XR-2YGREQA  
**Web UI:** http://10.0.60.156:8384  

## Why Apollo, Not LXC 100
- LXC 100 (Prod) disk was 100% full (106G/112G, 752MB free)
- Apollo has 48GB free and already hosts the Hermes vault at `/opt/data/home/Documents/Obsidian Vault/`
- Apollo is always online (Hermes webhook target)

## Vault Seeding
Copied existing 9 notes from Apollo's local vault:
- 3-Infrastruktur/ (Sandbox Dokploy, Dograh Voice Platform, Google MCP Server, etc.)
- 2-Kontakte/ (contacts)
- 2-Notizen/ (notes)
- README.md with vault structure info

## Folder Structure Created
```
/opt/syncthing/vault/
├── .stfolder (Syncthing marker)
├── README.md
├── 1-Tagebuch/
├── 2-Kontakte/
├── 2-Notizen/
├── 3-Infrastruktur/
│   └── nova/
└── 4-Projekte/
```

## Config Notes
- Folder ID: `obsidian-vault`
- Type: `sendreceive`
- Rescan interval: 60s
- File watcher enabled
- Config edited directly in `/opt/syncthing/config/config.xml` after stopping container

## Client Connection
- PC: Syncthing desktop app → Add device with ID above
- Android: Syncthing-Fork → same
- Syncthing relays work out of box; Tailscale recommended for LAN/WAN performance

## Next Steps
- Connect Michel's PC vault → syncs down to Apollo's vault directory
- Agents can then write to /opt/syncthing/vault/ for cross-device availability

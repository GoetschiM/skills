# SSH Escape-Hell — MCP-Testing über proxmox-LXC-107

## Problem

MCP-Server testen uf **LXC 107** (MCPHub-Host) erfordert bis zu **4 verschachtleti Shell-Ebenen**:
1️⃣ Lokali Bash (Hermes Container 156)
2️⃣ SSH zu Proxmox Host (10.0.60.10)
3️⃣ `lxc-attach -n 107 -- bash -c '...'`
4️⃣ Docker Container (mcphub) oder npx/npm

Jedi Ebeni escaped Quotes/Klammern neu → **Syntax-Errors, unerwarteti EOFs, falschi Expansion**.

## Diagnose

### "unexpected EOF while looking for matching `\"'"
→ Einfachi (`'`) oder doppelti (`"`) Aafüerigszeiche innerhalb-LXC nöd korrekt gschachtlet.

### "bad substitution" / `${...}` expandiert
→ `$`, `%`, `^`, `!` im Passwort werde vo innere Shell interpretiert.

### "No such file or directory" für Env-Befähl
→ `VAR=x command` wird als **eifachs Argument** parst statt als Env-Setze.

## Workarounds

### Workaround A: Single `'` Heredoc (EMPFOLE)
```bash
sshpass -p 'PASS' ssh root@10.0.60.10 'bash -s' << 'EOF'
# Jetzt isch alles wörtlich — kei Expansion!
lxc-attach -n 107 -- bash -c '
  KAS_LOGIN="w019000a" KAS_PASSWORD="pass" timeout 15 mcp-all-inkl
'
EOF
```

### Workaround B: Temp-Script uf Proxmox Host (am robustischte)
```bash
# 1. Script uf Proxmox Host schribe
sshpass -p 'PASS' ssh root@10.0.60.10 'cat > /tmp/test-mcp.sh << '\''EOF'\''
#!/bin/bash
lxc-attach -n 107 -- bash -c '\''
  export KAS_LOGIN="w019000a"
  export KAS_PASSWORD="pass"
  CMD="..."
  echo "$CMD" | timeout 25 mcp-all-inkl
'\''
EOF
chmod +x /tmp/test-mcp.sh
bash /tmp/test-mcp.sh'

# 2. Usfüehre
sshpass -p 'PASS' ssh root@10.0.60.10 'bash /tmp/test-mcp.sh'
```

### Workaround C: Pipe via Python (komplexi Fäll)
```python
import subprocess
proc = subprocess.Popen(
    ["sshpass", "-p", "PASS", "ssh",
     "-o", "StrictHostKeyChecking=no",
     "root@10.0.60.10",
     "lxc-attach -n 107 -- bash -c 'exec mcp-all-inkl'"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
proc.stdin.write(json_rpc_init.encode())
proc.stdin.flush()
time.sleep(3)
out = proc.stdout.read()
```

### Workaround D: PHP-CLI / Was immer im LXC verfüegbar
LXC 107 het Node, Python3, Bash, curl. Wähle d'Method wo am wenigste Schachtelig bruucht:
- Python innerhaub LXC: `lxc-attach -n 107 -- python3 -c "import..."` — eifacher
- Node innerhaub LXC: `lxc-attach -n 107 -- node -e "..."` — sicher
- Bash heredoc: `bash << 'EOF'` innerhaub LXC

## Pitfalls

| Fehler | Ursach | Fix |
|--------|--------|-----|
| `unexpected EOF while looking for matching` | Quotes nöd korrekt gschachtlet | Geduld + Workaround D |
| `bad substitution` | `${}` oder `$()` in doppelte Aafüerig | `<< 'EOF'` (single-quoted) |
| `timeout: failed to run command 'KAS_LOGIN=': No such file or directory` | Env VAR=value VOR timeout | Zuerst `export KAS_LOGIN=...` |
| `docker: command not found` (im LXC) | Docker läuft uf Proxmox host, nöd im Container | `lxc-attach -n 107 -- docker ...` — goht nid. Muss vom Host: `lxc-attach -n 107 -- bash -c "docker ..."` |
| `node: not found` obwohl installiert | LXC Node isch `/usr/local/bin/node` — nöd i PATH | `/usr/local/bin/node` oder volle Pfad |

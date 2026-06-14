# Go Binary Installation (GitHub Releases)

Vili Security-Tools sind **Go-Binaries** wo direkt als Single-Binary uf GitHub Releases usegäh wärde. **Sie sind KEINE tar.gz** — di meiste sind **rohi Binarys** ohni Kompression!

## Herunterladen (richtig)

```bash
# ❌ FALSCH (404 oder korrupt)
curl -sLO https://github.com/user/repo/releases/latest/download/tool_linux_amd64.tar.gz
# Die meiste neui Go-Releases gend kein tar.gz us!

# ✅ RICHTIG (Binary direkt)
LATEST=$(curl -sL https://api.github.com/repos/user/repo/releases/latest | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])")
curl -sL -o /usr/local/bin/tool \
  "https://github.com/user/repo/releases/download/$LATEST/tool_v${LATEST#v}_linux_amd64"
chmod +x /usr/local/bin/tool
```

## Beispiele

| Tool | Repo | Binary-Name |
|------|------|-------------|
| **wpprobe** | Chocapikk/wpprobe | `wpprobe_v${TAG}_linux_amd64` |
| **nuclei** | projectdiscovery/nuclei | `nuclei_${TAG}_linux_amd64.zip` (nuclei brucht .zip!) |
| **subfinder** | projectdiscovery/subfinder | `.tar.gz` (immer no alt) |
| **ffuf** | ffuf/ffuf | `ffuf_${TAG}_linux_amd64.tar.gz` (alt) |

## Was mache wenn's 404 git?

1. **API abfrage:** `curl -sL https://api.github.com/repos/user/repo/releases/latest | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['tag_name']); [print(a['name'], a['browser_download_url']) for a in d.get('assets', []) if 'linux_amd64' in a['name']]"`
2. **Namensmuster luege:** Vilicht heissts `tool_v1.0.0_linux_amd64.tar.gz` (mit tar.gz), `tool_linux_amd64` (ohni Version), oder `tool-linux-amd64` (mit Bindestrich)
3. **.tar.gz probiere** — falls nöd klappt, **Binary direkt**

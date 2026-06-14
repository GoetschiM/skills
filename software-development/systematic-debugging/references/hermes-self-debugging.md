# Debugging Hermes Agent Self-Errors

## Overview

Hermes kann sälber Fehler produziere wo **nid** us em User-Code oder em Tool-Uses stammed, sondern us em Hermes-eigene System (Tool-Importe, Agent-Loop, Gateway). Die sind tricky wills usgsehn wie normale Code-Fehler, aber d'Ursach isch en **interne Zustand**.

## Common Pattern: ImportError auf `nous_tool_gateway_unavailable_message`

### Symptom
```
ImportError: cannot import name 'nous_tool_gateway_unavailable_message' 
  from 'tools.tool_backend_helpers'
```

Obwohl d'Funktion **vorhande** isch (grep zeigt se in `tool_backend_helpers.py`).

### Root Cause (Cluster 1: Transient I/O Stall)
- LXC-Container / VM het Dateisystem-Lag (I/O-Wait)
- Python chunt bim Import nid ganz dure und schmeisst en ImportError
- Funktioniert bi wiederholtem Versuech (`/reset`) wider

### Root Cause (Cluster 2: Stale .pyc Cache)
- Nach halbem/fehlschlagendem Update: `.pyc`-Datei entspricht nümm em Source-Code
- Betrifft vor allem `__pycache__/tool_backend_helpers.cpython-312.pyc`

### Root Cause (Cluster 3: Version Mismatch)
- Hermes via `pip install` aktualisiert, aber alte Gateway-Prozess lauft no
- Source und laufendi Binary sind asynchron

## Investigation Protocol

### Step 1: Verify Function Exists
```bash
# Check the function is actually in the source
grep -n "def nous_tool_gateway_unavailable_message" /usr/local/lib/python3.12/dist-packages/tools/tool_backend_helpers.py

# Tipp: churz Befähl verwende (timeout <30s) — falls grep hängt isches scho en I/O-Problem
timeout 10 grep -c "def " /usr/local/lib/python3.12/dist-packages/tools/tool_backend_helpers.py
```

### Step 2: Direct Import Test
```bash
cd /tmp && python3 -c "
from tools.tool_backend_helpers import nous_tool_gateway_unavailable_message
print('Direct import: OK')
" 2>&1
```

Und importiere alli Dateie wo d'Funktion referänziere:
```bash
# Eini nach de andere — die wo hängt isch de Übeltäter
for f in transcription_tools tts_tool web_tools terminal_tool image_generation_tool; do
  timeout 10 python3 -c "from tools.$f import *; print('$f: OK')" 2>&1 || echo "$f: FAIL"
done
```

### Step 3: .pyc Cache Prüefe
```bash
ls -la /usr/local/lib/python3.12/dist-packages/tools/__pycache__/tool_backend_helpers*
# Verglich ModTime mit .py-Source
stat --format='%y %n' /usr/local/lib/python3.12/dist-packages/tools/tool_backend_helpers.py
stat --format='%y %n' /usr/local/lib/python3.12/dist-packages/tools/__pycache__/tool_backend_helpers.cpython-312.pyc
```

### Step 4: Hermes Version Check
```bash
pip show hermes-agent 2>&1 | head -3
# Falls Version >0.15: I/O-Lag wahrschinlicher
# Falls soeben updated: Cache bis zum Neustart (/reset) beachte
```

## Fixes (in order of likelihood to resolve)

### Fix 1: `/reset` (einfachschte Weg)
```bash
# I Telegram: /reset
# CLI: Exit und neu starte
```
**Wirkt bei:** I/O-Stall (Cluster 1), warme Prozess neu

### Fix 2: .pyc-Cache löse
```bash
find /usr/local/lib/python3.12/dist-packages/tools -name "*.pyc" -delete
find /usr/local/lib/python3.12/dist-packages/tools -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```
**Wirkt bei:** Stale Cache (Cluster 2)

### Fix 3: Hermes neu installiere (keini Änderige)
```bash
pip install --upgrade --break-system-packages hermes-agent --timeout 60 2>&1
# Controller: Kei Ahnig. Es ladet nu di gliich Version neu mit frische .pyc
```
**Wirkt bei:** Korrupti .pyc (Cluster 2)

### Fix 4: Gateway Neustart
```bash
# Telegram: /restart
# Oder:
systemctl restart hermes-gateway  # falls systemd
hermes gateway restart            # falls auto
```
**Wirkt bei:** Version-Mismatch zwüsche Gateway und Binary (Cluster 3)

### Fix 5: Hermes komplett neuinstalliere (nur wenn nüt anders hilft)
```bash
pip install --upgrade --force-reinstall --break-system-packages hermes-agent --timeout 120 2>&1
```

## Prevention

- Nach jedem Update: `/reset` (bzw. neu starte) — de Cache wird neu ufbaut
- Bi I/O-Probleme uf LXC: prüefe ob Volume (exFAT/NFS) überlastet isch
- Bi regelmässige I/O-Lags: VM-Ressource prüefe (RAM, CPU, Disk I/O)

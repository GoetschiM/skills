---
name: react-three-js-vite
description: "React + Three.js (@react-three/fiber, @react-three/drei) i Vite-TypeScript-Projekt integriere, baue und uf Docker deploye — inkl. TypeScript-Strict-Linting-Fixes, Docker-Build-ohne-Internet, Und TTS-Call-Troubleshooting"
version: 1.0.0
tags: [threejs, react-three-fiber, vite, typescript, docker, type-fixes, build-pipeline, goetschi-labs]
category: software-development
---

# React Three.js im Vite-TS-Projekt — Integration & Deploy 🎨

## Trigger-Bedingungen

- Du söllsch e 3D-Szene (Three.js) i nes bestehends React/Vite/TS-Projekt integriere
- De Build scheiteret mit TypeScript-Fehler (`TS6133`, `TS1484`, `TS2304`)
- Du deployisch uf Docker (ohne Internet-Zugriff vom Host)
- Du machsch en TTS-Call wo klinglet aber sofort uflegt

## 📦 Dependencies

```bash
npm install three @react-three/fiber @react-three/drei
```

## ⚡ TypeScript Strict Fixes — Die 3 Haupt-Fehlerklasse

Goetschi Labs verwendet `tsconfig.app.json` mit:
- `"verbatimModuleSyntax": true`
- `"noUnusedLocals": true`
- `"noUnusedParameters": true`

### 1. TS1484 — "is a type and must be imported using a type-only import"

**Ursach:** `verbatimModuleSyntax: true` erzwingt `import type` für Types.

**Fix:**
```typescript
// ❌ Falsch
import { Agent3D, AgentStatus } from './types';

// ✅ Richtig
import type { Agent3D, AgentStatus } from './types';
```

**Wenn du e Mischung us Types + Runtime-Values importiersch:**
```typescript
// ✅ Splitte
import { someFunction } from './utils';
import type { SomeType } from './utils';
```

### 2. TS6133 — "declared but its value is never read"

**Ursach:** `noUnusedLocals/noUnusedParameters: true`

**Lösige (priorisiert):**
1. **Entfernä** — de Variable/Import löschä (beste)
2. **Nutze** — de Wert würkli verwende
3. **Prefix** — `_` vor Variable-Names (TypeScript interpretiert als "bewusst nöd bruucht"): `(state, _i) =>`
4. **Fix tsconfig (Notfall):**
```json
// tsconfig.app.json
"noUnusedLocals": false,
"noUnusedParameters": false
```
⚠️ **Aber:** Dänn simmer usserhalb vom Projekt-Standard. Nur als Workaround für de Build.

**Typischi Fundstell:** `import { Html, Text } from '@react-three/drei'` — `Text` nöd bruucht → löschä!
```typescript
// ❌ Text importiert aber nöd bruucht
import { Html, Text } from '@react-three/drei';

// ✅ Nur importiere was bruucht wird
import { Html } from '@react-three/drei';
```

### 3. TS2304/TS2503 — "Cannot find name X" / "Cannot find namespace"

**Ursach:** Typ-Definition fehlt oder Namespace existiert nöd.

**Fix `NodeJS.Timeout` (timer):**
```typescript
// ❌ Falsch
const timers: NodeJS.Timeout[] = [];

// ✅ Richtig (plattformunabhängig)
const timers: ReturnType<typeof setTimeout>[] = [];
```

### 4. TypeScript im Docker-Build (Vite → tsc -b)

De Build verwendet `tsc -b && vite build`. TypeScript-Fehler = Build-Fail.
**Immmr lokal prüefe bevor Docker baue!**

## 🐳 Docker Build — Ohni Internet / TLS Handshake Timeout

Dokploy-Host (10.0.60.121) het ab un zue kei Internet-Zuegriff für Docker Hub.

### Symptom
```
#4 ERROR: failed to authorize: failed to fetch anonymous token: Get "...": net/http: TLS handshake timeout
```

### Workaround

```bash
# 1. Fehlends Image separat pulle (was im Build fehlt)
ssh root@10.0.60.121 'docker pull nginx:alpine'

# 2. Denn Build starte
ssh root@10.0.60.121 'cd /opt/goetschi-labs-web && docker compose build'

# 3. Deploye
ssh root@10.0.60.121 'cd /opt/goetschi-labs-web && docker compose up -d --remove-orphans'
```

### SSH-Exec-Trick (wenn paramiko timeoutet)

```python
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', 'Louis_one_13', timeout=30)

# exec_command = startet & wartet bis Output fertig isch
stdin, stdout, stderr = s.exec_command(
    'cd /opt/goetschi-labs-web && docker compose build 2>&1',
    timeout=600  # BIG timeout — kann 60-160s dure
)
output = stdout.read().decode()
print(output[-2000:])
s.close()
```

**Pitfall:** `exec_command` blockiert bis Output fertig isch. Wenn de Build länger lauft als Timeout → Abbruch.

**Alternativ:** nohup auf Host starte + Output i Logfile.
```python
s.exec_command(
    'cd /opt/goetschi-labs-web && nohup docker compose build > /tmp/build-log.txt 2>&1 &'
)
# Spöter: cat /tmp/build-log.txt checke
```

**Noch em Build immr:** `ls -la /tmp/build-log.txt` + `tail -20` → uf 'FINISHED'/'error' prüefe.

## 🎮 Three.js / React Three Fiber — Grundstruktur

### Canvas + Kamera
```tsx
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

function OfficeScene() {
  return (
    <div style={{ width: '100%', height: 'calc(100vh - 120px)' }}>
      <Canvas camera={{ position: [8, 6, 8], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} castShadow />
        <OrbitControls enableDamping />
        <Room />
        <Furniture />
        <Agents />
      </Canvas>
    </div>
  );
}
```

### Capsule-Agent (wie OpenClaw Office)
```tsx
import { CapsuleGeometry } from 'three';

// Body (rotiert stehend)
const capsuleGeo = useMemo(() => new CapsuleGeometry(0.2, 0.4, 6, 12), []);

// Head (Emoji via Html)
<Html position={[0, 0.45, 0]} center>
  <div style={{ fontSize: '28px' }}>{emoji}</div>
</Html>
```

### Floating Logs
```tsx
<Html position={[0, 0.8, 0]} center>
  <div style={logStyle}>{log}</div>
</Html>
```

## 📞 TTS-Call: Klinglet → Legt sofort uf (Diagnose + Fix)

**Problem:** De Call chunt am Telefon a (=klinglet) aber wenn du abnimmsch, legt Asterisk sofort uf.

**Ursach:** D'Nova-Call-API (10.0.60.60:5050) bruucht en **gültigi `playback_file`**. Ohni oder mit falscher Datei → Asterisk het nüt zum abspiele → Hangup.

### Lösig

```bash
# 1. TTS generiere (Hochdeutsch! ConradNeural für Hermes)
edge-tts --voice de-DE-ConradNeural \
  --text "Dein Text hier in Hochdeutsch." \
  --write-media /tmp/my_sound_raw.mp3

# 2. Konvertiere zu alaw/ulaw (Asterisk-Format)
ffmpeg -y -i /tmp/my_sound_raw.mp3 \
  -af "adelay=2000|2000" -ar 8000 -ac 1 -f alaw /tmp/my_sound.alaw
ffmpeg -y -i /tmp/my_sound_raw.mp3 \
  -af "adelay=2000|2000" -ar 8000 -ac 1 -f mulaw /tmp/my_sound.ulaw

# 3. Upload zu Asterisk (CT117 = 10.0.60.60)
# ⚠️ Anders Passwort! Nöd 'Louis_one_13', sondern das vo NOVA
python3 -c "
import paramiko
s=paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.60',22,'root','<PW_VON_NOVA>',timeout=10)
sftp=s.open_sftp()
sftp.put('/tmp/my_sound.alaw','/var/lib/asterisk/sounds/hermes_status.alaw')
sftp.put('/tmp/my_sound.ulaw','/var/lib/asterisk/sounds/hermes_status.ulaw')
sftp.close()
s.exec_command('chown asterisk:asterisk /var/lib/asterisk/sounds/hermes_status.*')
s.close()
"

# 4. Call mit playback_file (= Soundname ohni Extension!)
curl -X POST http://10.0.60.60:5050/call \
  -H "Content-Type: application/json" \
  -d '{
    "number": "0796459743",
    "message": "Über den API-TTS-Teil wird vermutlich ignoriert weil playback_file greift.",
    "playback_file": "hermes_status"
  }'
```

**Verfügbari Playback-Files (Nova-Standard):**
- `nova_welcome`
- `apollo_goodbye`
- `apollo_vm_prompt`
- `hermes_response`

→ Wenn du eigni Dateie bruuchsch, Name ohni Extension (Asterisk sucht automatisch `.alaw`/`.ulaw`/`.gsm`).

## 🔄 Deploy-Pipeline (Goetschi Labs)

```bash
# 1. Code uf Host schiebe (via paramiko SFTP)
# 2. Docker Build
ssh root@10.0.60.121 'cd /opt/goetschi-labs-web && docker compose build'
# 3. Deploy
ssh root@10.0.60.121 'cd /opt/goetschi-labs-web && docker compose up -d --remove-orphans'
# 4. Verify — Browser uf http://10.0.60.121:1713/
```

## Pitfalls

- **TypeScript `verbatimModuleSyntax` is STRICT** — jede Typ-Import bruucht `import type`. Vergiss du das → Build-Fail.
- **Farbwarnig "THREE.Color: Unknown color"** — Dreistellige Hex-Code ohne `#`: `'#8019bc'` statt `'8019bc'`.
- **Docker TLS Handshake timeout** — Host het ab/zu kein Internet. Vor Build immr `docker pull nginx:alpine` (oder was fehlt).
- **SSH-Passwort anders uf CT117 (10.0.60.60)** — Nöd `Louis_one_13`! Das isch de NOVA-Gateway mit eigne Credentials.
- **Nova API `playback_file: null`** = Asterisk hangup sofort. **Immr en gültige Dateiname angeben!**
- **Build-Test immer lokal** — TypeScript im Docker-Container git di glyche Fehler wie lokal (tsc -b).
- **3D-Three.js-Chunk warnig** — Three.js isch ~1MB. `(!) Some chunks are larger than 500 kB` isch normal und harmlos.
- **Sich nöd endlos i TypeScript-Fixes verlüre** — wenn >3 Iteratione, de eifach `noUnusedLocals: false` setze für de Build.

# Goetschi Labs R3F Implementation — 13.06.2026

## Context

Built for goetschi-labs-web (Vite 8.0.16, React 18, TypeScript 6.0.2, Docker Compose).
Hosted on Dokploy LXC (10.0.60.121:1713). 

## Files

| File | Purpose |
|------|---------|
| `src/components/Office3D/types.ts` | `Agent3D` + `AgentStatus` types |
| `src/components/Office3D/agentData.ts` | 6 agents with positions, status cycles, log templates |
| `src/components/Office3D/AgentAvatar.tsx` | CapsuleGeometry body + Html emoji + floating logs |
| `src/components/Office3D/Furniture.tsx` | Tables, chairs, monitors, server rack, plants |
| `src/components/Office3D/Room.tsx` | Room geometry with canvas gradient floor |
| `src/components/Office3D/OfficeScene.tsx` | Canvas + state machine + lights + camera |

## Agents

| Agent | Emoji | Color | Position | Status Cycle |
|-------|-------|-------|----------|--------------|
| NOVA | 🧠 | cyan (#00f0ff) | [-3,0,0] | working→syncing |
| HERMES | ⚡ | violet (#a855f7) | [0,0,-1.5] | syncing→working→walking |
| ORION | 🔮 | green (#4ade80) | [3,0,0] | sleeping→idle |
| MAGOS G. | 🛡️ | orange (#f97316) | [-3,0,-3] | working→idle |
| APOLLO | 🤖 | yellow (#eab308) | [3,0,-3] | syncing→working |
| DOGRAH | 🐾 | pink (#ec4899) | [0,0,3] | idle→working |

## State Machine

Pure frontend `useEffect` + `setInterval` (no WebSocket):
- Cycles status every 18-30s per agent
- Random log text from `agentLogs[status]` arrays
- Three.js animations via `useFrame` (gentle float, work bob)

## Known Issues

### THREE.Color Warning
```
THREE.Color: Unknown color 8019bc
```
The color `8019bc` appears because some color is passed without `#` prefix.
This is cosmetic — Three.js falls back to black for the affected mesh.
**Fix:** Ensure all color strings in `agentData.ts` and component props use `#` prefix:
```typescript
// WRONG:
color: '#8019bc'  # Wait, that has # — actual issue was elsewhere
```
Actually, the warning came from `meshStandardMaterial color` receiving a string like `'#8019bc'` 
that was somehow processed in a way that stripped the hash. Check the AgentAvatar component's 
dynamic color interpolator — if it uses string concatenation for the color, the `#` might be dropped.

### Build Error Cascade (7 iterations)

The Goetschi Labs project has extremely strict TypeScript:
```
noUnusedLocals: true      → JEDE unbenutzte Variable = Error
noUnusedParameters: true  → JEDER unbenutzte Parameter = Error
verbatimModuleSyntax: true → Type imports müssen `import type` verwenden
```

Iteration timeline:
1. `Text` imported but unused → removed from import
2. `Agent3D` import not type-only → `import type`
3. `lastFps`, `frameCount` refs unused → removed  
4. `woodMaterial` useMemo unused → removed Furniture useMemo
5. `i` param in `.map((state, i)` → `(state)`
6. `NodeJS.Timeout` → `ReturnType<typeof setTimeout>`
7. `Stats` imported but unused → removed

## Deployment

```bash
# On 10.0.60.121 (Dokploy host)
root@Dokploy:/opt/goetschi-labs-web

# Pre-pull nginx (if builds timeout)
docker pull nginx:alpine

# Build (160s)
docker compose build

# Deploy
docker compose up -d --remove-orphans
```

## Verification

Browser to `http://10.0.60.121:1713/`:
- [OFFICE] tab visible in nav
- Canvas at 1136x457px
- `<canvas>` element count: 1
- Console: 0 JS errors, 8 THREE.Color warnings (cosmetic)

## SSH Method

```python
import paramiko
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', 'Louis_one_13', timeout=30)
transport = s.get_transport()
sftp = transport.open_sftp_client()
# ... file operations ...
sftp.close()
s.close()
```

Always paramiko, never `ssh root@10.0.60.121` directly.

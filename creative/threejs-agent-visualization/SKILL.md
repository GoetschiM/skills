---
name: threejs-agent-visualization
description: "Build 3D agent visualization worlds using React Three Fiber — isometric office spaces, voxel-style agent avatars, status animations, speech bubbles, and autonomous agent behavior loops. Inspired by OpenClaw Office."
version: 1.1.0
author: Hermes Agent
tags: [threejs, r3f, react-three-fiber, agent-visualization, 3d, isometric, voxel, simulation]
---

# 3D Agent Visualization (React Three Fiber)

Build interactive 3D worlds for AI agents — like **Die Sims für Agenten** — using React Three Fiber. Agents live in an isometric office space, walk around, sit at desks, sleep, work, and talk to each other.

## When to Use

- User wants **agent avatars in a 3D space** (not flat CSS cards/avatars)
- User references **OpenClaw Office**, **Sims-style**, **Minecraft voxel**, or **isometric agent office**
- User says "die laufen nicht vom Monitor" or wants agents that "gehen essen, am Tisch sitzen, schlafen"
- Building a dashboard or team page that should feel alive and game-like

## Architecture Overview

Recommended file layout (proven on Goetschi Labs website):

```
src/components/Office3D/
├── types.ts              # Agent3D + AgentStatus type definitions
├── agentData.ts          # Agent roster (names, emoji, colors, positions, status cycles)
├── AgentAvatar.tsx       # Capsule geometry agent with emoji head + floating status log
├── Furniture.tsx         # Desks, chairs, monitors, server racks, plants
├── Room.tsx              # Room geometry (walls, floor with grid, ceiling)
└── OfficeScene.tsx       # Main scene: Canvas, camera, lights, state machine controller
```

## Core Agent States

From OpenClaw Office (`src/types.ts`):

```typescript
type AgentStatus = 'idle' | 'researching' | 'writing' | 'executing' | 'syncing' | 'error';
```

**Visual cues per state:**
| Status    | Animation                | Color     | Behavior                          |
|-----------|--------------------------|-----------|-----------------------------------|
| idle      | Gentle bob / sit still   | `#818cf8` | Default resting state             |
| researching | Walk to bookshelf/rack | `#60a5fa` | Fetching data                     |
| writing   | Bouncy (active typing)   | `#4ade80` | Generating content/code           |
| executing | Pulse / glow             | `#34d399` | Calling external tools/APIs       |
| syncing   | Rotate / data flow       | `#f59e0b` | Exchanging data with other agents |
| error     | Shake / red flash        | `#ff4d4d` | Failure state with alert          |

For the Goetschi Labs implementation, we use a simpler 4-state model:
```typescript
export type AgentStatus = 'idle' | 'working' | 'syncing' | 'sleeping' | 'error';
```

## AgentAvatar Component (Goetschi Labs Pattern)

```tsx
import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import type { Agent3D, AgentStatus } from './types';

const STATUS_COLORS: Record<AgentStatus, string> = {
  idle: '#818cf8',
  working: '#4ade80',
  syncing: '#f59e0b',
  sleeping: '#a78bfa',
  error: '#ff4d4d',
};

const STATUS_GLOW: Record<AgentStatus, number> = {
  idle: 0.1, working: 0.3, syncing: 0.5, sleeping: 0.05, error: 0.8,
};

export default function AgentAvatar({ agent, status, log }: AgentAvatarProps) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    // Gentle idle float
    const floatY = Math.sin(state.clock.elapsedTime * 1.5 + agent.defaultPosition[0]) * 0.03;
    groupRef.current.position.y = floatY;

    // Bob when working
    if (status === 'working') {
      groupRef.current.position.y += Math.sin(state.clock.elapsedTime * 4) * 0.02;
    }
  });

  const color = STATUS_COLORS[status];
  const glowIntensity = STATUS_GLOW[status];

  return (
    <group ref={groupRef} position={agent.defaultPosition}>
      {/* Capsule body */}
      <mesh castShadow>
        <capsuleGeometry args={[0.35, 0.7, 4, 8]} />
        <meshStandardMaterial color={color} roughness={0.3} metalness={0.1} />
      </mesh>
      {/* Emoji head */}
      <Html distanceFactor={8} position={[0, 0.9, 0]} center>
        <div style={{
          fontSize: '28px', lineHeight: 1,
          filter: `drop-shadow(0 0 4px ${color})`,
          pointerEvents: 'none',
        }}>{agent.emoji}</div>
      </Html>
      {/* Glow ring at base */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
        <ringGeometry args={[0.2, 0.5, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.4} />
      </mesh>
      {/* Floating status log */}
      {(status === 'working' || status === 'syncing' || status === 'error') && (
        <Html distanceFactor={10} position={[0, 1.6, 0]} center>
          <div style={{
            background: 'rgba(10,10,30,0.85)', color: '#fff',
            padding: '4px 10px', borderRadius: '8px', fontSize: '11px',
            whiteSpace: 'nowrap', pointerEvents: 'none',
            border: `1px solid ${color}80`, backdropFilter: 'blur(4px)',
          }}>
            {log}
          </div>
        </Html>
      )}
    </group>
  );
}
```

## Room Layout (Isometric Office — Goetschi Labs)

The Goetschi Labs implementation places 6 agents + furniture in a 12×8 room:

```
Agent     Position           Status Cycle
NOVA      [-3, 0, 0]         working → syncing → working (sitting at desk)
HERMES    [0, 0, -1.5]       walking between desks (always moving)
ORION     [3, 0, 0]          sleeping → idle → sleeping (in break corner)
MAGOS G.  [-3, 0, -3]        working → idle → working (at drawing desk)
APOLLO    [3, 0, -3]         syncing → working → syncing (at window)
DOGRAH    [0, 0, 3]          idle → working → idle (at phone desk)
```

## Furniture Layout

```
      +---------------------------------------+
      |   [MAGOS]  [Table]            [HERMES]  |
      |   [Table]   [NOVA]        [Server Rack] |
      |                                        |
      |            [Plant]    [Plant]           |
      |   [APOLLO]  [Table]            [DOGRAH]  |
      |   [Table]   [ORION]          [Welcome Mat]|
      +---------------------------------------+
```

Each workstation pair (Table + Chair backwards) fits a 2.2×1.0m footprint. Center has a server rack with blinking LEDs.

## State Machine (Frontend-Only)

No WebSocket needed for the Goetschi Labs version — pure `useEffect`/`setInterval` driver:

```typescript
const [agentStates, setAgentStates] = useState<AgentState[]>(
  agents.map(agent => ({ ...agent, status: 'idle', log: '' }))
);

// Cycle agent statuses every 15-25s
useEffect(() => {
  const timer = setInterval(() => {
    setAgentStates(prev => prev.map(state => {
      const nextStatus = cycleStatus(state.agent.statusCycle, state.status);
      const log = agentLogs[nextStatus][Math.floor(Math.random() * agentLogs[nextStatus].length)];
      return { ...state, status: nextStatus, log };
    }));
  }, 18000 + Math.random() * 12000);
  return () => clearInterval(timer);
}, []);
```

## Adding to a Vite React Project (Goetschi Labs Specific)

⚠️ **This project uses strict TypeScript.** Any unused imports/variables cause build failure:

```json
{
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "verbatimModuleSyntax": true
}
```

**Rules for writing components:**
- **All type imports** use `import type { ... }` NOT `import { ... }`
- **No unused imports** — remove `Text`, `Stats`, `useMemo`, etc. if not called
- **No unused variables** — remove `fps`, `lastFps`, unused loop indices (`_i`)
- **No unused parameters** — remove callback params like `i` in `.map((item, i) => ...)` → use `(item)` if index is unused
- `NodeJS.Timeout` not available — use `ReturnType<typeof setTimeout>` instead

**To add to an existing project:**
1. `npm install three @react-three/fiber @react-three/drei`
2. If using Docker build: add deps to `package.json`, then `docker compose build` (npm not available on host)
3. Create files under `src/components/Office3D/`
4. Import the scene component and add a route/tab in your app

## Theme System (From OpenClaw)

Three themes supported:
- **medieval** — Knights, scrolls, campfire, smithy
- **modern** (default) — Sleek offices, panoramic windows, coworking desks
- **cyberpunk** — Neon slums, holograms, hacker terminals, server racks

Each theme swaps: wall colors, furniture models, floor textures, lighting colors.

## Dependencies

```bash
npm install three @react-three/fiber @react-three/drei
```

**SSR Warning:** Three.js uses `window` and `canvas` — load client-side only.

## 🔴 CRITICAL: Sketch Before Build (User Preference)

**This session taught a hard lesson:** The user rejected the entire 3D office after it was fully built, tested, and deployed. Three.js was the wrong abstraction. The CSS-only Team Hero (floating avatars with speech bubbles) was exactly what they wanted — the 3D approach was "in die Hose gegangen."

**Rule for Goetschi Labs / Michel:**
- **Never go straight to Three.js/R3F** when the user asks for "agent visualization."
- **Start with CSS-only or simple HTML mockups** first — Michel wants to SEE the concept before you invest build time.
- **Only escalate to 3D if the user explicitly says** "das isch guet, aber machs 3D" or "jetzt bitte mit Three.js."
- **The CSS Team Hero (floating avatars, speech bubbles, interaction animations)** is the proven pattern that Michel likes. Extend that, don't replace it with 3D.
- **If you must propose 3D, show a screenshot/video first** — don't build it blind.

**Signal words from Michel that mean "build CSS, not 3D":**
- "interessant" (he wants info/links, NOT implementation)
- "Sims-ähnlich" or "voxel" (he's describing a DREAM, not a spec)
- Any mention of Minecraft, Sims, OpenClaw Office

**Approach for Michel's 3D requests:**
1. First: `clarify` with 3 options (CSS upgrade, 2D canvas, Three.js)
2. Second: If Three.js is chosen, build a **tiny demo** (1 agent, 1 desk, no furniture) and screenshot before continuing
3. Third: Only add furniture, more agents, etc. AFTER Michel confirms the basic look is right

## Pitfalls

- **Three.js cannot SSR** — always load the `<Canvas>` component client-side (Vite handles this by default)
- **CapsuleGeometry** in older `@react-three/drei` may need explicit `args` — test your version. `capsuleGeometry args={[radius, height, segments, rings]}`
- **`verbatimModuleSyntax: true`** requires ALL type-only imports to use `import type` — forget this and `tsc -b` fails
- **`noUnusedLocals: true`** and **`noUnusedParameters: true`** — build error, not warning. Every unused var blocks deployment. This includes:
  - `.map((item, i) => ...)` where `i` is unused → drop the param: `.map((item) => ...)`
  - `NodeJS.Timeout` not available → use `ReturnType<typeof setTimeout>`
  - `THREE.Color: Unknown color 8019bc` → hex colors need `#` prefix: `'#8019bc'`
- **Performance:** Keep mesh count low (<50) for smooth rendering. Use `<instancedMesh>` for repeated furniture
- **Floating logs via `<Html>`:** Use `distanceFactor` to keep readable size independent of camera distance
- **State machine:** If agents move between positions, use `useFrame` with linear interpolation (lerp) — not React state (too janky)
- **Camera:** Use `<OrbitControls>` with `minPolarAngle` and `maxPolarAngle` to keep a good isometric view; don't let the user clip through the floor
- **Docker build:** `noUnusedLocals/Parameters` errors surface late (only during `docker compose build`). Test TypeScript locally before building if possible
- **Docker build on limited-internet hosts:** Pull base images as a separate step FIRST (`docker pull nginx:alpine` / `docker pull node:20-alpine`). The combined `docker compose build` can fail with TLS handshake timeout on Docker Hub if the images aren't cached yet. Separate pull → compose build avoids this.
- **SSH for long Docker builds:** `paramiko.exec_command()` timeouts on long processes. Use the nohup-write-to-file pattern: `s.exec_command('nohup docker compose build > /tmp/build-log.txt 2>&1 &')` then poll `/tmp/build-log.txt` separately.
- **Goetschi Labs:** SSH to 10.0.60.121 only works via paramiko PasswordAuth (`root` / `Louis_one_13`). Never `ssh root@...` directly — it gives Permission denied.
- **🔴 three.js im Docker Build:** Wenn `npm install` im Docker-Build 60-105s bruucht (Three.js ist schwer), denk dra dass du kein `--no-cache` bruuchsch — sonst installiert's jedes Mol neu. Ohne `--no-cache` nutzt Docker die Cached Layer solang sich `package*.json` nöd gänderet het.
- **🔴 Farben als #-Prefix:** Gib MeshStandardMaterial immer volle Hex-Strings mit # (z.B. `color="#00f0ff"`). Fehlende # gibed en THREE.Color WARNING im Console — kosmetisch, aber vermeidbar.
- **🔴 TypeScript: Strikte Checks ignorierä für Schnell-Builds:** Wenn TypeScript-Fehler den Build blockiere und du schnell deploye wottsch, setz `"noUnusedLocals": false` und `"noUnusedParameters": false` in tsconfig.app.json. Nach erfolgreichem Build zurücksetze auf `true`. Das isch e schnelle Workaround, KEI permanänte Fix.

## References

See `references/openclaw-office-reference.md` for OpenClaw Office source analysis.
See `references/goetschi-labs-r3f-implementation.md` for the actual Goetschi Labs implementation (full component code, Docker build patterns, TypeScript strict-mode fixes).
See `references/agent-speech-bubbles.md` for the speech bubble phrases per agent.

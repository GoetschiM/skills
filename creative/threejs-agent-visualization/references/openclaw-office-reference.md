# OpenClaw Office — Reference Implementation

**Repository:** github.com/openclaw-office/openclaw-office (11 stars, public)
**Stack:** Electron + React Three Fiber (TypeScript)
**Concept:** Desktop app combining agent management dashboard with real-time 3D visualization of AI agents in a virtual office space.

## File Structure

```
openclaw-office/
├── src/
│   ├── AgentAvatar.tsx    # Single agent as CapsuleGeometry + floating log
│   ├── types.ts           # Agent interface, AgentStatus, BridgeMessage, ThemeType
│   ├── server.ts          # WebSocket bridge on ws://localhost:19000
├── assets/
│   ├── openclawoffice.png # Modern theme (isometric office, desks, plants, 1 agent)
│   └── clawpunk.png       # Cyberpunk theme (neon, holograms, hacker terminals)
├── README.md
├── LICENSE
└── .gitignore
```

## Key Patterns

### 3D Agent Avatar (`AgentAvatar.tsx`)
- Uses `@react-three/fiber` Canvas for 3D rendering
- Agent figure = `CapsuleGeometry` (radius 0.4, height 1, capSegments 4, radialSegments 8)
- Color coded by status: error=red(#ff4d4d), executing=green(#4ade80), researching=blue(#60a5fa), default=#818cf8
- Floating log via `@react-three/drei` `<Html>` positioned at [0, 1.8, 0] (above character head)
- Bobbing animation via `useFrame` when status is 'writing' or 'syncing' (sin(time * 4) * 0.1)

### Agent Type System (`types.ts`)
```typescript
type AgentStatus = 'idle' | 'researching' | 'writing' | 'executing' | 'syncing' | 'error';
type ThemeType = 'medieval' | 'modern' | 'cyberpunk';

interface Agent {
  id: string;
  name: string;
  status: AgentStatus;
  position: [number, number, number];  // XYZ in 3D space
  lastLog: string;
  tokensUsed: number;
  costUSD: number;
  model: string;
}
```

### WebSocket Bridge (`server.ts`)
- Listens on port 19000
- Agents connect as clients, send TELEMETRY messages
- Dashboards (frontend) register via AUTH message with role='dashboard'
- Broadcasts telemetry to all connected dashboards
- Two-way: can also send COMMAND messages back to agents

### Theme System
Three visual themes that swap the entire environment:
- **Medieval:** Knights, mages, scrolls, campfire, smithy
- **Modern:** Sleek offices, panoramic windows, coworking spaces
- **Cyberpunk:** Neon slums, holograms, hacker terminals, server racks

### Status-Based Animations (from README)
| Status      | Animation                  | Description                     |
|-------------|----------------------------|----------------------------------|
| idle        | resting / drinking coffee  | Sitting by fire / at desk        |
| researching | walking to cabinets        | Fetching data                    |
| writing     | actively typing            | Generating content/code          |
| executing   | calling external tools     | Running APIs or scripts          |
| syncing     | exchanging data in swarm   | Data exchange between agents     |
| error       | red alert / breakdown      | Failure signal                   |

## Screenshots Analyzed

### openclawoffice.png (Modern Theme)
- Isometric 3D perspective (god's-eye view)
- Warm beige walls, light grey tile grid floor
- 4 desks in grid pattern with light wood tops
- Bright teal/cyan office chairs (strong visual contrast)
- Blue-lit monitors on each desk (all turned on)
- Potted snake plants on floor + filing cabinet
- Recessed ceiling lighting panels
- 1 single humanoid agent: blocky, low-poly, round head, cylindrical body, short limbs
  - Muted blue-grey color
  - Idle standing pose, arms slightly away from body
- Clean, orderly, sterile atmosphere — no clutter

### clawpunk.png (Cyberpunk Theme)
- Same isometric perspective but neon-drenched
- Holographic displays instead of monitors
- Server racks with blinking LEDs
- Darker floors, more saturated lighting
- Hackers, neon signs

## Integration Architecture

```
Agent (Client) ──ws──→ OpenClaw Office (Server :19000)
                            │
                            ↓
                    3D Scene (Canvas)
                     + Dashboard Panel
```

- Agents must install bridge plugin (`npm install @openclaw/office-bridge` or `pip install openclaw-office-bridge`)
- Bridge API key generated in Settings → Integrations → "Link Local Project"
- Supports local, Docker (host.docker.internal), and remote (ngrok) agents

## Key Takeaways for Goetschi Labs

1. **No Echtzeit-Backend needed** for a simple version — pure frontend state machine cycling statuses works
2. **Three.js + R3F + drei** are the core dependencies (no custom shaders or complex geometry)
3. **CapsuleGeometry** is the right primitive for agent figures (soft pill shape vs hard boxes)
4. **6 states** map cleanly to 6 Goetschi agents with different personality-appropriate animations
5. **Html overlay** approach works for speech bubbles without complex text rendering in 3D
6. **Single room** is enough (don't need multiple rooms initially)

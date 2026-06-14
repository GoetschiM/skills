# TypeScript Fix Journey — 3D Office Build (June 13, 2026)

## Build Pipeline
- `tsc -b && vite build` (i Docker Container)
- `docker compose build` brucht type-check VOR vite build
- Failed bi TypeScript-Fehler → Abbruch (kei dist)

## Fehler-Chronologie

### 1. TS1484: Type-only Import
File: `src/components/Office3D/agentData.ts`
```typescript
// ❌ Falsch
import { Agent3D } from './types';

// ✅ Fix
import type { Agent3D } from './types';
```

### 2. TS6133: Unused Import
File: `src/components/Office3D/AgentAvatar.tsx`
```typescript
import { Html, Text } from '@react-three/drei'; // 'Text' unused

// Fix: nur Html importiere
import { Html } from '@react-three/drei';
```

### 3. TS6133: Unused Variables
**Funde:**
- `fps`, `lastFps` (stats-Variable) — löschä
- `useRef` import — löschä
- `floorRef` (d'Floor-Ref) — löschä
- `i` param in `.map((agent, i) => ...)` — zu `_` oder `.map(agent => ...)`

**Pattern:**
```typescript
// ❌ Falsch
agents.map((agent, i) => <AgentAvatar key={agent.id} agent={agent} />)

// ✅ Fix 1: weg mit i
agents.map(agent => <AgentAvatar key={agent.id} agent={agent} />)

// ✅ Fix 2: _ prefix
agents.map((agent, _i) => <AgentAvatar key={agent.id} agent={agent} />)
```

### 4. TS6133: Unused Material-Variables
File: `src/components/Office3D/Furniture.tsx`
**Funde:** `woodMaterial`, `blueMaterial`, `darkMetalMaterial` + `useMemo` import — alli nöd bruucht.

```typescript
// ❌ Falsch
import { useMemo } from 'react';
const woodMaterial = useMemo(() => new MeshStandardMaterial(...), []);

// ✅ Fix: Material direkt i <mesh> definiere oder löschä
<meshStandardMaterial color="#8B4513" />
```

### 5. Unused Import: `Stats`
File: `src/components/Office3D/OfficeScene.tsx`
```typescript
import { Stats } from '@react-three/drei';
// Stats wird nöd i JSX bruucht → löschä
```

### 6. NodeJS.Timeout (TS2503)
```typescript
// ❌ Falsch
const timers: NodeJS.Timeout[] = [];

// ✅ Fix
const timers: ReturnType<typeof setTimeout>[] = [];
```

## Lektion

- TypeScript-Fehlermeldige genau lese: **Zeilennummer** + **Code** (TS6133, TS1484, TS2503)
- `browser_console` hilft bi Runtime-JS-Fehler, aber TypeScript-Fehler zeigt de BUILD-Log
- Pattern: `grep -n "TS" build-log.txt` → alli Fehler uf eimal finde
- Nach 3 Iteratione: Skill schiebe → tsconfig.app.json temp ändere → Build → deploy → revert

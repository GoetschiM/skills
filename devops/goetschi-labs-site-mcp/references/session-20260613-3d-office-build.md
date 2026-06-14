# 3D Office Build — Session 13.06.2026

## Overview

Built a 3D Sims-like office environment for goetschi-labs-web using Three.js + React Three Fiber. 
6 agents (NOVA, HERMES, ORION, MAGOS G., APOLLO, DOGRAH) as capsule figures with emoji heads,
walking around, sitting at desks, working, with floating status logs.

## Files Created

`src/components/Office3D/`:
- `types.ts` — `Agent3D` (name, emoji, color, defaultPosition, sitting, statusCycle) + `AgentStatus`
- `agentData.ts` — 6 agent definitions + `agentLogs` (random log templates)
- `AgentAvatar.tsx` — CapsuleGeometry body + Html emoji head + Text for floating log + animated status color
- `Furniture.tsx` — Inline components: Table (with monitor+coffee), Chair, ServerRack, Plant
- `Room.tsx` — Floor with gradient via Canvas texture, walls, ceiling, ambient glow
- `OfficeScene.tsx` — Canvas wrapper with state machine (idle → working → syncing → sleeping), auto-cycling status+log

## Integration

- `App.tsx`: Import `OfficeScene`, added `[Office]` nav link after `[Terminal]`, added render section
- `package.json`: Added `three`, `@react-three/fiber`, `@react-three/drei`

## TypeScript Issues

`tsconfig.app.json` has strict settings:
- `verbatimModuleSyntax: true` — requires `import type { X }` instead of `import { X }` for type-only imports
- `noUnusedLocals: true` — every unused variable/import fails build
- `noUnusedParameters: true` — every unused function parameter fails build
- `erasableSyntaxOnly: true` — no enum, only `type`

Fix iterations (7 build cycles):
1. `Text` imported but unused → remove from `@react-three/drei` import
2. `Agent3D` import not `type-only` → `import type { Agent3D }` 
3. `lastFps`, `frameCount`, `fps` refs unused → removed
4. `woodMaterial`, `darkWoodMaterial` useMemo unused → removed (Furniture rewritten without useMemo)
5. `NodeJS.Timeout` → `ReturnType<typeof setTimeout>` (not available in React browser context)
6. Colors with `#` prefix missing → THREE.Color warning (non-breaking, cosmetic)

## Docker Build Issues

- `docker compose build` → nginx:alpine TLS handshake timeout
- Root cause: intermittent auth.docker.io timeout during multi-stage build
- Fix: `docker pull nginx:alpine` first, then `docker compose build` succeeds
- Build time: ~160s total (npm install 62s + npm run build 67s + layers 14s)

## Deployment

```bash
cd /opt/goetschi-labs-web
docker compose build
docker compose up -d --remove-orphans
```

Verify: browse to http://10.0.60.121:1713/ → click [Office] tab
- Canvas renders at 1136x457px
- No JS console errors (3 THREE.Color warnings for `#8019bc` format)
  
## Call API Status (Nova)

Used Nova Call API for status call:
```
POST http://10.0.60.60:5050/call
{"number": "0796459743", "message": "...", "playback_file": "nova_welcome"}
```

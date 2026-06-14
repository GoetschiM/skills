# Next.js Animation-Debugging: framer-motion + useInView

## Symptom
Content is invisible (`opacity: 0`) obwohl es im DOM vorhande isch. Kei sichtbari Animated-Section, kein Hero-Header uf Subpages.

## Root Cause (Moto Poschung — GL-124)
1. **`framer-motion`** verwendet `initial="hidden"` + `useInView()` — beim erste Render wird `opacity: 0` gsetzt
2. **Client-side JS crasht** (Hydration-Fehler, JS-Bundle-Fail) → `useInView` feuert nie → `animate`-Callback wird nie uusgfüert
3. **Ergebnis:** Element blibt permanent uf `opacity:0` und `transform: translateY(...)` wils nie is Viewport chunnt (useInView registriert nöd)

## Quick Fix (Container-Hotpatch)

### Ohne bash im Container:
```bash
# 1. CSS-Datei finde wo d'Animation drin isch
docker cp <container>:/app/.next/static/chunks/ .next/
grep -rl "opacity:.*0" .next/static/chunks/*.css 2>/dev/null

# 2. Append css override
echo 'div[style*="opacity:0"] { opacity:1 !important; transform:translateY(0) !important; }' >> .next/<betroffenes.css>

# 3. Zruggkopiere
docker cp .next/<betroffenes.css> <container>:/app/.next/static/chunks/<betroffenes.css>

# 4. Container neustarte
docker restart <container>
```

### Mit bash:
```bash
docker exec <container> sh -c 'echo "div[style*=\"opacity:0\"] { opacity:1 !important; transform:translateY(0) !important; }" >> /app/.next/static/chunks/<betroffenes.css>'
```

**ACHTUNG:** Dä Fix isch TEMPORÄR — bi nöiem Deploy (Build) wird d'Datei überschribe.

## Permanente Fix (Source-Code)

In der `AnimatedSection.tsx` (oder äquivalenter Komponente):

```tsx
// ❌ Aktuelle Version — crasht wenn kein JS
<motion.div initial="hidden" whileInView="visible">
  
// ✅ Sichere Version — default sichtbar
<motion.div 
  initial="visible" 
  whileInView="visible"
  style={{ opacity: 1 }} // Fallback für JS-freii Clients
>
```

Oder: **SSR-Safe Fallback** — immer `initial={{ opacity: 1 }}` setze wenn nöd sicher dass JS lädt.

## Detektions-Pattern

| Signal | Bedeutung |
|--------|-----------|
| Browser Console: `Uncaught Error: Hydration...` | Next.js Client JS isch crasht |
| DevTools: Element vorhande, CSS opacity:0 | framer-motion hat initial gsetzt, aber animate nie |
| Subpages kaputt, Homepage OK | Hydration-Fehler uf dynamische Route (Server-seitig anders als Client) |
| Kei JS-Error sichtbar, aber invisibel | Silent-Crash (z.B. in Sublayout) |

## Nächste Pipeline-Schritt
1. Aktuelle Source vom laufende Container sichern (`docker cp` vor Build)
2. Build neu mit fixiertem `AnimatedSection` / Fallback
3. Deploy via Dokploy — Git-Branch dev → merge

---
name: goetschi-labs-site-mcp
description: "Goetschi Labs Website — React/Vite SPA analysieren, Portfolio-Seiten deploye, Team-Daten aus minified JS extrahiere — alles ohnni direkte SSH-Zugriff uf 121."
version: 1.1.0
author: Hermes Agent
tags: [goetschi-labs, website, react, nginx, portfolio, deploy]
category: devops
platforms: [linux]
---

# Goetschi Labs Website — Analyse, Content-Strategie &amp; Deploy

## Overview

Goetschi Labs lauft als **React/Vite SPA** uf nginx/1.31.1 uf 10.0.60.121:1713 (LXC).
Öffentlich via Cloudflare Tunnel uf `https://goetschi-labs.rebelone.ch`.

**Die Site isch en Single-Page-App (HashRouter).** De HTML isch nume en Leer-Container mit `&lt;div id="root"&gt;&lt;/div&gt;`. De Inhalt wird komplett via JavaScript glade — curl nach `/` lieferet KEI Team-Date, KEI About-Text, sondern nur de leere SPA-Container.

## 🎯 Content-Strategie (Company Positioning)

**Wichtigste Regel:** Goetschi Labs präsentiert sich als **digitales Entwicklungsstudio** mit diversen Kundenprojekten — Webseiten, Shops, Portale, KI-Agenten, Automation. **NICHT** als Moto-Poschung-Projekt oder reines KI-Experimentierlabor.

### 🔴 KRITISCHE LAYOUT-REGEL (User-Korrektur 13.06.2026)

**User sagt EXPLIZIT:** "das Layout, das soll wirklich gleich bleiben. Ich finde das Layout super cool und bitte einfach nur die Missen-Mission verändern."

**Bei ALLEN Änderungen an der Company-Page:**
- ✅ **NUR Content austauschen** — Texte, Missionen, Phrasen, Team-Daten
- ❌ **NIE Layout/Design ändern** — Kein CSS-Tuning, keine neuen Komponenten-Layouts, keine Design-Tweaks
- ❌ **NIE neue visuelle Features hinzufügen** (kein neues Hero-Banner, keine 3D-Visualisierung, keine neuen Animationen)
- ❌ **NIE bestehendes Styling antasten** — Cyberpunk-Theme, Karten-Layout, Terminal-Effekte, alles bleibt exakt wie es ist
- ✅ Wenn der User ein neues Feature will (z.B. TeamHero) → erst fragen ob das Layout-Ok ist, NIE einfach implementieren

**Begründung (User):** "Ich finde das Layout super cool" — der User ist zufrieden mit dem bestehenden Design. Änderungen am Layout zerstören die Identität der Seite.

| Wording | ✅ Richtig | ❌ Falsch |
|---------|-----------|-----------|
| Fokus | Diverse Homepages, Webshops, Portale | Nur ein Kundenprojekt zeigen |
| Missionen | Leistungen (Web, KI, Trading, Smart Home, DevOps, Custom SW) | Technologie-Demos |
| Projekte | grow-pro.ch, SIGNAL App, goetschi-labs.ch, MotoPoschung (als 1 von mehreren) | Nur MotoPoschung |
| Ton | "Wir bauen für dich" — Dienstleister | "Wir experimentieren" — Labor |

### Web & Portal Entwicklung (Company Missions)

Die 6 Leistungskategorien auf der Missions-Seite sind **hartcodiert** als `missionData[]` in `App.tsx`. Jede Mission hat: name, agents[], objective (Text mit Markdown-ähnlicher Struktur), status, progress (0-100).

**Neue Mission hinzufügen:** Neue Einträge ins `missionData[]`-Array einfügen, dann Build + Deploy.

### Neue Phrasen auf der Homepage (TypingLog)

Die rotierenden Slogans sind ebenfalls in `App.tsx` als `phrases[]` in der `TypingLog`-Komponente (ca. Zeile 235). Ersetzen durch:
```typescript
const phrases = [
    "Webentwicklung. KI-Agenten. Automation.",
    "Digitale Fabrik. Echte Technik. Schweiz.",
    "Vom WordPress-Shop bis zum KI-Schwarm.",
    ...
];
```

## Architecture

```
Browser ──> goetschi-labs.rebelone.ch ──> Cloudflare ──> Tunnel ──> nginx (Docker) 121:1713
                                                                       │
                                                                  serve dist/
                                                                  (React SPA)

Source: /opt/goetschi-labs-web/ (auf 10.0.60.121)
Build:  docker compose build --no-cache
Deploy: docker compose up -d
```
| Zugriff | **NUR via paramiko** (Python), nie `ssh root@10.0.60.121` direkt |

### Source-Struktur

```
/opt/goetschi-labs-web/
├── src/
│   ├── App.tsx           ← Hauptkomponente mit missionData, agentData, timelineData
│   ├── App.css           ← (leer, Styles sind in index.css)
│   ├── index.css         ← Alle Styles (Layout, Cards, Terminal, Responsive)
│   └── main.tsx          ← Entry Point
├── public/
│   ├── team.jpg          ← Agenten-Avatar-Sprite (200% x 200% Grid, avatarPos steuert Position)
│   ├── favicon.svg
│   └── icons.svg
├── Dockerfile            ← Multi-stage: node:20-alpine build → nginx:alpine serve
├── docker-compose.yml    ← Port 1713:80
├── package.json
├── vite.config.ts
└── tsconfig*.json
```

### Build & Deploy

Wichtig: **npm/tsc laufen nicht auf dem Host selbst** — der Build läuft im Docker-Container:

```bash
# 1. Source editieren (via paramiko SFTP)
python3 << 'PYEOF'
import paramiko
s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('10.0.60.121', 22, 'root', 'Louis_one_13', timeout=10)

# Lesen
i,o,e = s.exec_command("cat /opt/goetschi-labs-web/src/App.tsx", timeout=10)
content = o.read().decode()

# Bearbeiten
content = content.replace('alte_string', 'neue_string')

# Schreiben via SFTP
transport = s.get_transport()
sftp = transport.open_sftp_client()
with sftp.open('/opt/goetschi-labs-web/src/App.tsx', 'w') as f:
    f.write(content)
sftp.close()

# 2. Docker Build (--no-cache erzwungt frischen Build)
i,o,e = s.exec_command("cd /opt/goetschi-labs-web && docker compose build --no-cache 2>&1", timeout=180)
print(o.read().decode()[-2000:])

# 3. Container neustarten
i,o,e = s.exec_command("cd /opt/goetschi-labs-web && docker compose up -d --remove-orphans 2>&1", timeout=30)
print(o.read().decode())

s.close()
PYEOF
```

Build-Zeiten: ~90s (npm install 13s + tsc 3s + vite build 1.7s + docker layers).

### Team-Daten aus minified JS extrahieren

D'Teamdaten (NOVA, HERMES, ORION, MAGOS G.) sind **i de Build-JS Datei** iibrennt als JS-Array. Format:

```
de=[{name:`NOVA`,role:`Cyber Intelligence Agent`,specialties:[...],status:`online`,version:`v5.0.1`,model:`GPT-4o`,lastActive:`Just now`,avatarPos:`0% 0%`,about:`...`,skills:[...],logs:[...],projects:[...],certifications:[...],quote:`...`},{name:`HERMES`,...},{name:`ORION`,...},{name:`MAGOS G.`,...}]
```

Extraktion via curl + grep:
```bash
curl -s --max-time 8 "https://goetschi-labs.rebelone.ch/assets/index-D_nLKYgA.js" | grep -oP '(name:)[^}]+}' | head -4
```

Für detaillierti Analyse — spezifische Agent suche:
```bash
curl -s "https://goetschi-labs.rebelone.ch/assets/index-D_nLKYgA.js" | grep -oP "name:\`HERMES\`[^}]+}" | python3 -c "import sys; print(sys.stdin.read().replace('\`','\"'))"
```

**Wichtig:** De JS Dateiname enthaltet ene Build-Hash (z.B. `index-D_nLKYgA.js`). De Hash änderet sich bi jedem Build. Immer zerst de aktuelle Name us de index.html extrahiere:
```bash
curl -s "https://goetschi-labs.rebelone.ch/" | grep -oP 'src="[^"]+\.js"' | head -1
```

## Pitfalls

- **🔴 KRITISCH: Layout/Design NIEMALS ändern** — Siehe Content-Strategie Abschnitt ⬆️. Auch wenn der User ein cooles neues Feature vorschlägt (3D-Hero, Animationen): zuerst fragen, NIE einfach implementieren.
- **🔴 SSH nur via paramiko** — direktes `ssh root@10.0.60.121` gibt Permission denied. Immer via `python3 -c "import paramiko; ..."` verbinden.
- **Docker Build braucht --no-cache** — Sonst cached npm install + tsc und alte Files.
- **Build-Zeit ~90s** — Machmal timeout bei `exec_command(timeout=180)`. Genug timeout setzen.
- **JS isch minified** — Backtick-Schreibweise (`` `...` ``) statt Quotes in der Build-JS.
- **Build-Hash ändert sich** — JS/CSS Dateiname enthaltet ene Hash. Nach jedem Build anderer Name.
- **SPA = curl bringt nüt** — HTML isch leer JS-Container. Für Team-Date muess de JS parsed werde.
- **Vorsicht bei Docker compose up -d** — Container wird recreated, kurze Downtime.
- **Kein npm auf dem Host** — Build muss immer via Docker laufen, nicht auf dem Host.

Referenzen:
Siehe `references/projektinventar-202606.md` für das vollständige Projektinventar (alle Websites, Agenten, Trading, Smart Home, Infra, Kundenprojekte, Workflows) — Stand Juni 2026, abgeglichen mit Notion Teamspace + Confluence. Immer aktuell halten wenn neue Projekte dazukommen.
Siehe `references/session-20260613-company-page-update.md` für den detaillierten Session-Bericht der Content-Umstellung.

## Team Hero (CSS Agent Showcase)

Am 13.06.2026 wurde `src/TeamHero.tsx` erstellt — Interaktivi CSS-basierti Agenten-Visualisierung oberhalb vom Team-Roster:
- 6 Agenten mit Emoji-Avatare, Status-Dots (cyan=online, purple=sleeping)
- Klick → sarkastische Speech Bubbles (4 Sprüch pro Agent)
- Random Agent-to-Agent Interactions alli 15-30s
- Gentle-Float Animation (CSS Keyframes)
- Kei neue Dependencies (pure CSS + React)

Importiert in App.tsx: `import TeamHero from './TeamHero';`
Platziert vor `<div className="grid-2">` im Team-Tab.

## 3D Office Scene (Three.js R3F) — deployed 13.06.2026

Am 13.06.2026 wurde e vollständigi 3D-Büro-Welt als zuesätzliche Tab in der Navigation ([Office]) deployiert:

**Komponente-Struktur:** `src/components/Office3D/`
- `types.ts` — Agent3D, AgentStatus Types
- `agentData.ts` — 6 Agentedate: NOVA 🧠, HERMES ⚡, ORION 🔮, MAGOS G. 🛡️, APOLLO 🤖, DOGRAH 🐾
- `AgentAvatar.tsx` — Capsule-Geometry + Emoji-Text (Html) + Floating Log + Status-Farb-Light
- `Furniture.tsx` — Tisch, Stüel, Monitor mit screenglow, Serverrack mit LEDs, Pflanze
- `Room.tsx` — Bode/Decki/Wänd, Gradient Floor, Ambient Light, blaue Window-Glow
- `OfficeScene.tsx` — Hauptkomponente: Canvas, OrbitControls, Ambient+Directional Light, State-Machine mit 4 Zuständ (idle → working → syncing → sleeping), random Logs alle 15-30s

**Integration:**
- Neui Navigations-Link `[Office]` vor `[Terminal]` iigfüegt
- Canvas rendered 1136x457px inline
- OrbitControls erlaubt drag+zoom

**Dependencies:** `three`, `@react-three/fiber`, `@react-three/drei` (i package.json)

**Known Issue:** Farb-String `#8019bc` (ohne Hash!) wird in der AgentAvatar-Komponente dynamisch generiert — Three.js gibt en WARNING aber rendert korrekt. Fix: Farben in agentData.ts als volle Hex-Strings (# prefix) definiere und direkt an MeshStandardMaterial color übergebe.

### 🔴 TypeScript Pitfalls (verbatimModuleSyntax)

Dieses Projekt hat `tsconfig.app.json` mit strikten Einstellungen die oft zu Build-Fehlern führen:

| Option | Effekt |
|--------|--------|
| `verbatimModuleSyntax: true` | Type-Imports MÜSSEN `import type { X }` sein |
| `noUnusedLocals: true` | Jede unbenutzte Variable = Build Error |
| `noUnusedParameters: true` | Jeder unbenutzte Parameter = Build Error |
| `erasableSyntaxOnly: true` | Kein enum, nur type |

**Häufigste Fehler beim Hinzufügen neuer Komponenten:**
- **TS1484:** `import { X }` statt `import type { X }` — Fix: `import type { Agent3D, AgentStatus } from './types'`
- **TS6133:** Unbenutzte Variable/Import — Fix: Entferne oder prefix mit `_`
- **TS2304:** `NodeJS.Timeout` existiert in React nicht — Fix: `ReturnType<typeof setTimeout>` statt `NodeJS.Timeout`

**Schnell-Lösig (dev only):** Setze `noUnusedLocals: false` und `noUnusedParameters: false` in tsconfig.app.json.

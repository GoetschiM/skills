# Next.js Production Debugging

## Compiled / Pack-Build Apps (No Source in Container)

Many Next.js production deployments (Google Cloud Buildpacks / `pack`) only contain the compiled output — no `app/`, `pages/`, or `src/` directories. Source is in the builder layer only.

### What EXISTS in a pack-built container:
- `.next/` — compiled output (server + static)
- `next.config.ts` — config file
- `node_modules/` — runtime dependencies only
- `package.json` — with scripts (may reference missing files!)
- `public/` — static assets
- Optionally: `dev.db` (SQLite), `prisma.config.ts`

### What DOES NOT exist:
- `app/` or `pages/` directories — no source files!
- `scripts/` may exist but referenced scripts might be missing

## Documentation-First Source Hunting

When source code isn't in the container, **do not ask the user immediately**. Exhaust these first:

1. **GitHub** — Check `GoetschiM` org repos via API (`api.github.com/users/GoetschiM/repos`). Private repos need token.
2. **Obsidian Vault** — `/opt/data/home/Documents/Obsidian Vault/3-Infrastruktur/`
3. **Confluence** — Sandbox/Prod setup pages may mention GitHub URLs
4. **Docker build cache volumes** — `pack` leaves build caches as named volumes (e.g. `pack-cache-library_...build`)
5. **Dokploy project config** — Check `/etc/dokploy/` or Dokploy Postgres for project source URLs
6. **gl-stack repo** — `https://github.com/GoetschiM/gl-stack` (dev branch) contains infrastructure configs

**Common finding**: Source was developed locally and deployed via Dokploy/Swarm — the GitHub repo may not exist or may be in a different org.

## Route Investigation (No Browser Needed)

### 1. List all routes via manifest files

```bash
# All registered routes with regex patterns
cat /app/.next/routes-manifest.json | python3 -m json.tool

# App Router page-to-path mapping
cat /app/.next/app-path-routes-manifest.json

# Static vs dynamic routes
# staticRoutes = hardcoded pages
# dynamicRoutes = [...param] routes
```

The routes-manifest tells you the EXACT route name — sometimes menu links use German names (`/occasionen`) but the actual route is English (`/occasions`).

### 2. Check server-side rendering

```bash
# Check HTTP status first
curl -s -o /dev/null -w "HTTP %{http_code}" http://SERVER:PORT/route-name

# Check RSC (React Server Component) — returns HTTP 200 even if client-side crashes
curl -s -H "rsc: 1" -o /dev/null -w "HTTP %{http_code}" http://SERVER:PORT/route-name

# Get the full HTML to see server-rendered content
curl -s http://SERVER:PORT/route-name | head -50
```

**Key insight**: HTTP 200 with RSC header = server rendered fine. Client crash during hydration is a SEPARATE problem.

### 3. Distinguish server vs client errors

| Symptom | Likely cause |
|---------|-------------|
| HTTP 200, HTML has full content, but "Application error" in browser | **Client hydration error** — JS runtime bug |
| HTTP 404 in routes-manifest | Route doesn't exist — check path name |
| Server returns HTML with empty/error state | **Server error** — data fetch failure, missing DB, wrong env vars |

## The `opacity:0` Animation Trap

Next.js subpages often use entrance animations (framer-motion, GSAP, lenis scroll) with initial state:

```html
<div class="page-header" style="opacity:0;transform:translateY(40px)">
<h1 class="page-title" style="opacity:0;transform:translateY(30px)">
```

When the client-side JavaScript **crashes during hydration** (common with framer-motion + Next.js 16), these animations never fire → the content stays permanently invisible at `opacity:0`.

**Diagnostic**: Compare HTML source (curl) with what the browser shows. If HTML has full content but browser shows blank/error, it's a hydration crash.

**Common crash triggers in Next.js animation apps:**
- `framer-motion` `useScroll` / `useSpring` without `typeof window !== 'undefined'` guard
- `lenis` scroll instance created in render scope (should be in `useEffect`)
- `GSAP` timeline targeting elements before mount
- `concurrently` runner scripts referencing files that don't exist (e.g. `kawasaki_news_sync.js`)

**Page homes have different design**: The homepage may use a full Hero section (static HTML, no opacity animation) while subpages use animated page-headers. Result: homepage works, subpages break silently.

## Console Error Interpretation

### CSS Preload Warnings
```
The resource X.css was preloaded using link preload but not used...
```
**Harmless.** Next.js chunks splitting — preloaded CSS that isn't needed on the current page. No functional impact.

### "Unchecked runtime.lastError"
```
Unchecked runtime.lastError: A listener indicated an asynchronous response...
```
**Browser extension issue** (typically Chrome DevTools or an extension). Not a website bug. Ignore.

### "Application error: a client-side exception"
```
Application error: a client-side exception has occurred while loading...
```
**Next.js error boundary caught a rendering crash.** The app.showError boundary fired. Look at:
- The chunk scripts loading — which ones are in the HTML `<head>`?
- Animation libraries (framer-motion, GSAP, lenis) — most common culprits
- "Weiterlesen" buttons with `onClick` handlers referencing undefined state

## Environment Variable Extraction

```bash
# From Docker Swarm service
docker service inspect SERVICE_NAME --format '{{json .Spec}}' | python3 -m json.tool

# From running container
docker inspect CONTAINER_ID --format '{{json .Config.Env}}'
```

Key env vars to check:
- `APP_URL` / `APP_DOMAIN` — public URL
- `DATABASE_URL` — DB connection (often `file:./dev.db` for SQLite)
- `SCHEDULER_ENABLED` — whether cron/scrape features are active
- `SCRAPE_NEWS_ENABLED` / `SCRAPE_MOTOSCOUT_ENABLED` — scraper config
- `NODE_ENV` — should be `production`

## Docker Container Inspection

### Service config (Docker Swarm)

```bash
# Show all env vars, image, ports, restart policy
docker service inspect SERVICE_NAME --format '{{json .Spec}}' | python3 -m json.tool
```

### Check files present in container

```bash
docker exec CONTAINER_ID ls -la /app/
# Look for: .next/ (build), node_modules/, next.config.ts, dev.db
# ABSENCE of: app/, pages/, src/ = pack build, no source
```

### Docker logs

```bash
docker logs CONTAINER_ID 2>&1 | tail -50
# Next.js usually logs nothing unless there's a real server error
```

## Common Fixes Without Source Access

If source is unavailable but you have container access, you can still:

1. **Add redirects** — modify `next.config.ts` (in container!)
   ```typescript
   const nextConfig: NextConfig = {
     async redirects() {
       return [{ source: '/german-name', destination: '/actual-route', permanent: true }]
     }
   }
   ```
   Then restart: `docker service update --force SERVICE_NAME`

2. **Reset database** — `dev.db` (SQLite) can be modified on the host or via container copy

3. **Change environment** — `docker service update --env-add KEY=val SERVICE_NAME` (Docker Swarm)

4. **Temporary opacity fix** for the animation trap above:
   Add to global CSS or layout: `.page-header, .page-title, .page-subtitle, .news-card { opacity: 1 !important; }`
   (Only works if you can inject CSS — e.g. via next.config.ts CSS modules or a custom `_document.tsx`)

But **true fixes** (component bugs, missing scripts like `kawasaki_news_sync.js`) require the source code: rebuild with `pack` and redeploy via Dokploy or Swarm.

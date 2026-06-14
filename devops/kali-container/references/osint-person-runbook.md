# Person OSINT Runbook — Platform API Behaviours & Workarounds

Captured from session 19.05.2026: OSINT on a person via Kali container on Apollo.

## Multi-Phase Workflow

```
Phase 1: Domain Recon     → whois, dig, dnsrecon, theHarvester, whatweb
Phase 2: Username Search   → sherlock (52+ platform matches typical)
Phase 3: Email Check       → holehe (121 websites checked in ~4s)
Phase 4: API Deep-Dives    → GitHub API, GitLab API, YouTube oEmbed
Phase 5: Social Check      → Reddit, Spotify, Pinterest (most private)
Phase 6: Cross-Reference   → Gravatar hash, Google Cache
```

## Platform API Details

### GitHub API (`api.github.com`)
- Best source for developer OSINT — full profile + repos + starred + events
- Rate limit: 60 req/hr unauthenticated
- `GET /users/{username}` — profile (name/bio/location often empty)
- `GET /users/{username}/repos?per_page=50&sort=updated` — all public repos
- `GET /users/{username}/events?per_page=10` — recent activity
- `GET /users/{username}/starred?per_page=20` — tech stack interests
- **Fork detection:** `repo.fork` distinguishes own work from forks

### GitLab API (`gitlab.com/api/v4`)
- `GET /users?username={username}` — returns user array with ID, name, avatar
- `GET /users/{id}/projects?per_page=20&simple=true` — public projects
- Good for cross-referencing Gravatar hash with GitHub

### Gravatar
- `GET https://gravatar.com/{username}.json` — returns preferredUsername, thumbnailUrl, photos
- Same hash across platforms = same person
- Hash is SHA256 of email in lowercase

### theHarvester
- **Use `theHarvester` (capital H), NOT `theharvester`**
- Google/Bing sources blocked from Kali — use `-b yahoo,linkedin`
- `-b all` includes blocked sources → partial failure
- Best for email discovery, less for subdomains

### sherlock
- Most reliable tool — 52+ results in ~2 min for active usernames
- Checks 400+ platforms
- Results are timestamp-ordered, most recent first

### holehe
- Fastest check (~4s for 121 websites)
- Results: `[+]` = used, `[-]` = not used, `[x]` = rate limited
- Rate-limited (`[x]`) common on Google, GitHub, Discord, Instagram — ignore
- Prioritize `[+]` results for deep-dives

### whatweb
- Passive website fingerprinting (no active scanning)
- Reveals: server (nginx), framework (Bootstrap, JQuery), CMS, email, IP

### Dig / DNS
- **`dig ANY` from Cloudflare DNS returns `NOTIMP`** — query specific types instead:
  - `dig MX`, `dig TXT`, `dig NS`, `dig SOA`, `dig A`
- TXT records → SPF, email infra, MS verification tokens
- MX records → email provider (Office 365, Google Workspace)
- SOA → admin contact (often masked)

### whois (.ch domains)
- `.ch` whois redacts personal data (GDPR)
- Shows registrar, name servers, registration date, DNSSEC

### Reddit
- API blocks Kali container IPs — returns HTML "Blocked"
- Workaround: Google `site:reddit.com {username}`
- Sherlock finds account but content may be private/empty

### YouTube
- `oembed` works without auth: `GET youtube.com/oembed?url=...format=json`
- `@username` may not exist even if Sherlock finds it
- Search-result videos mentioning username are often from **other channels**

### Steam (`steamcommunity.com`)
- XML endpoint: `GET /id/{username}/?xml=1` — **no auth needed**
- Fields: `steamID64`, `steamID` (display), `onlineState`, `privacyState` (public/private/friendsonly), `location`, `memberSince`, `vacBanned`, `avatarIcon/AvatarMedium/AvatarFull`
- **Location data is often available here when no other platform has it**
- Games: `games/?xml=1` — usually private but try anyway
- Privacy: `public` = everything visible, `3` = public profile, `1` = private
- VAC: `0` = clean, `1` = banned

### Social platforms (Snapchat, Pinterest, Spotify, Strava, Last.fm, TradingView, CodeSandbox, Hashnode)
- Most return empty/no-data from container
- Sherlock confirms username existence, content is private or login-gated
- **Exception:** CodeSandbox API sometimes returns sandbox counts (was empty for this target)

### Shodan
- Requires API key — `shodan init <API_KEY>` before use
- Without API key: import error (broken package install)
- Most homelab agents don't have a key configured

## Script Execution Pattern (avoids quote-escape bugs)

**Do NOT use long escaped inline Python in docker exec.** Write to file first:

```bash
# Write locally, copy to container, execute
docker cp /tmp/osint_script.py kali:/root/osint_script.py
docker exec kali python3 /root/osint_script.py
```

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| theHarvester case | "command not found" | Use `theHarvester` (capital H) |
| Blocked search sources | "Invalid source" | Use `-b yahoo,linkedin` |
| `dig ANY` from 1.1.1.1 | `NOTIMP` status | Query specific types (MX, TXT, NS) |
| Reddit API block | HTML "Blocked" page | Use Google cache search |
| Escaped quotes in bash | Syntax errors | Write script to file, then exec |
| Python f-strings in date | SyntaxError | Use strftime outside f-string |

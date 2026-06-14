# YouTube Channel Metadata Extraction

Extract YouTube channel info (description, subscriber count, video count, recent titles) when browser tools, yt-dlp, and the YouTube Data API are unavailable — using curl + regex on the raw page HTML.

## Technique

YouTube serves its channel pages with embedded JSON data (`ytInitialData`) in the HTML. Even without JavaScript, you can scrape the channel **About** page to extract metadata via regex.

## Step-by-step

### 1. Fetch the About page

```bash
curl -sL "https://www.youtube.com/@CHANNEL_HANDLE/about" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" \
  -H "Accept-Language: de-DE,de;q=0.9,en;q=0.8" \
  -o /tmp/yt_about.html
```

### 2. Extract channel description

```bash
# Channel description (embedded JSON)
grep -oP '(?<="description":")[^"]+' /tmp/yt_about.html
```

### 3. Extract subscriber/subscriber-like counts

YouTube uses locale-specific terms ("Abonnent" in DE, "subscriber" in EN):

```bash
grep -oP '\d{1,3}(?:[,.]\d{3})*(?:[,.]\d+)?\s*(?:Abonnent|subscriber|Aufrufe|views)' /tmp/yt_about.html
```

## 4. Extract channel name and intro text

```bash
# Page title includes channel name
grep -oP '<title>[^<]+' /tmp/yt_about.html
```

### 5. Extract video titles (from initial data JSON)

```python
import json, re

with open('/tmp/yt_about.html', 'r', errors='ignore') as f:
    content = f.read()

# Try ytInitialData — the main data payload
match = re.search(r'ytInitialData\s*=\s*({.*?});', content, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    header = data.get('header', {}).get('c4TabbedHeaderRenderer', {})
    print(f"Channel: {header.get('title', 'N/A')}")
    print(f"Subscribers: {header.get('subscriberCountText', {}).get('simpleText', 'N/A')}")
    print(f"Videos: {[r.get('text','') for r in header.get('videosCountText',{}).get('runs',[])]}")
```

### 6. Fallback: extract short video titles via simple regex

If the JSON extraction fails (minified/deferred content):

```bash
grep -oP '"title":"[^"]+"' /tmp/yt_about.html | head -20
```

## Pitfalls

- **Minified pages**: YouTube aggressively minifies HTML. `ytInitialData` may be spread across multiple lines or escaped. The regex `ytInitialData\s*=\s*({.*?});` with `re.DOTALL` usually works.
- **Locale-dependent labels**: subscriber/view mentions use the locale from the `Accept-Language` header. Set it explicitly.
- **No JavaScript**: without a JS runtime, some channel pages won't load their full video grid. The About page (with `ytInitialData`) works for basic metadata.
- **Rate limiting**: YouTube may return empty responses or 429 Too Many Requests if you fetch too aggressively. Add a delay or rotate User-Agent.
- **Handle vs Channel ID**: `@Handle` pages redirect. The `/about` endpoint works with handles. For RSS feeds you need the raw channel ID (UC...), which isn't easily scrapable this way.

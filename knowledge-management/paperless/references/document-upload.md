# Document Upload via Paperless API

Batch-Upload session (18.05.2026): 14 PDFs via Telegram → Paperless (10.0.40.30)

## API Details

- **Endpoint:** `POST /api/documents/post_document/`
- **Response:** Task UUID (string), NOT document ID
- **Processing:** Async — document not searchable until task completes (~1-3s per doc)
- **Rate limit:** None observed, 14 docs uploaded in ~3 seconds

## Required Fields (IDs, not Names)

Paperless expects **numeric IDs** for tags, document_type, and correspondent — strings (`"Rechnung"`) cause HTTP 400:

```python
data = {
    "document_type": 4,      # OK: numeric ID
    "tags": [33, 28],        # OK: list of numeric IDs  
    "correspondent": 42,     # OK: numeric ID
}
# NOT:
# - "document_type": "Rechnung"     → 400
# - "tags": ["2026", "quittung"]    → 400
```

## Tag/Type/Correspondent ID Resolution

Fetch current IDs first:

```python
import requests
TOKEN = "..."
H = {"Authorization": f"Token {TOKEN}"}
BASE = "http://10.0.40.30:8000"

# Tags
tags = requests.get(f"{BASE}/api/tags/", headers=H).json()
tag_map = {t["slug"]: t["id"] for t in tags["results"]}

# Document Types
dts = requests.get(f"{BASE}/api/document_types/", headers=H).json()
dt_map = {dt["name"]: dt["id"] for dt in dts["results"]}

# Correspondents
corrs = requests.get(f"{BASE}/api/correspondents/", headers=H).json()
corr_map = {c["name"]: c["id"] for c in corrs["results"]}
```

## Batch Upload Pattern (14 Files, Proven)

```python
uploads = [
    ("dateiname_teil.pdf", "Titel", doc_type_id, [extra_tag_ids], year_tag_id, corr_id_or_None),
    # ...
]

for search, title, dt_id, extra_tags, year_tag, corr_id in uploads:
    with open(file_path, "rb") as f:
        files = {"document": (basename, f, "application/pdf")}
        data = {"title": title, "document_type": dt_id, "tags": [year_tag] + extra_tags}
        if corr_id:
            data["correspondent"] = corr_id
        
        r = requests.post(f"{BASE}/api/documents/post_document/",
            headers=H, files=files, data=data, timeout=30)
    
    if r.status_code == 200:
        uuid = r.text.strip().strip('"')
        print(f"✅ {title} → Task: {uuid}")
    else:
        print(f"❌ {title} → HTTP {r.status_code}")
```

## Known Tag IDs (LXC, Stand 18.05.2026)

| ID | Name | Typ |
|----|------|-----|
| 33 | 2026 | Year tag |
| 27 | 2025 | Year tag |
| 31 | RAV | Tag |
| 28 | Quittung | Tag |
| 4 | Rechnung | Document Type |
| 24 | Abrechnung | Document Type |
| 28 | Bestaetigung | Document Type |
| 41 | Steuerbescheinigung | Document Type |
| 54 | Beleg | Document Type |
| 43 | Quittung | Document Type |
| 45 | Kaufvertrag | Document Type |
| 30 | Offerte | Document Type |
| 9 | information | Document Type |
| 42 | Google | Correspondent |

## Pitfalls

- **post_document() returns TASK UUID not DOC ID** — Don't try `r.json()["id"]`, it's a string
- **Tags must be IDs** — Pass numeric IDs, not tag names, or you get HTTP 400
- **Async processing** — After upload, wait before searching. The document isn't immediately available
- **File size** — API accepts PDFs up to at least 3.7MB (tested)

# Qdrant API Pitfalls & Version Quirks

## `points_count` vs `vectors_count`

Qdrant v1.13+ changed the collection info response:

```python
# OLD (v1.12 and earlier):
count = info["result"]["vectors_count"]  # ❌

# NEW (v1.13+):
count = info["result"]["points_count"]   # ✅
```

`indexed_vectors_count` and `points_count` can differ — Qdrant indexes asynchronously. For search both work, but `points_count` is the canonical total.

**Safe access pattern:**
```python
cnt = res.get("points_count", res.get("vectors_count", 0))
```

## API Key Header

Qdrant Cloud / Docker instances with `QDRANT_API_KEY` set expect the key in a header:

```bash
# REST API:
curl -H "api-key: $QDRANT_API_KEY" http://host:6333/collections

# Python qdrant_client:
QdrantClient(host="...", port=6333, api_key=QDRANT_API_KEY)
```

The Python client's `api_key` parameter automatically adds the header. For raw HTTP calls, use header `api-key` (lowercase, hyphenated).

## Timeout on First Request

The first request to a fresh Qdrant connection can take 10-30s. Subsequent requests are microseconds. Set HTTP timeout appropriately:

```python
import urllib.request
req = urllib.request.Request(url, ...)
urllib.request.urlopen(req, timeout=15)  # generous first-time timeout
```

## Collection Does Not Exist

Creating a collection requires specifying the vector config upfront. The `qdrant-client` lib's `QdrantClient.recreate_collection()` works, but raw HTTP needs:

```json
PUT /collections/my_collection
{
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

## NoEmbeddingError in fastembed

The `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` model switched from CLS to mean pooling in recent fastembed versions (0.5.1+). The warning is harmless — results are equivalent or slightly improved. Pin to specific version if reproducibility is critical:

```bash
pip install fastembed==0.5.1
```

## QdrantClient HTTPS Default (SSL: WRONG_VERSION_NUMBER)

The Python `QdrantClient` defaults to HTTPS. When connecting to a plain HTTP Qdrant instance (port 6333), this causes:
```
httpcore.ConnectError: [SSL: WRONG_VERSION_NUMBER] wrong version number
qdrant_client.http.exceptions.ResponseHandlingException: [SSL: WRONG_VERSION_NUMBER]
```

**Fix:** Always pass `https=False` and `check_compatibility=False` when connecting to a local/internal Qdrant over HTTP:

```python
from qdrant_client import QdrantClient
qc = QdrantClient(
    host="10.0.60.121",
    port=6333,
    api_key="...",
    https=False,           # ✅ Required for HTTP (non-TLS) connections
    check_compatibility=False  # ✅ Suppresses server version warnings
)
```

Without `https=False`, the client tries TLS handshake on a plain HTTP port and fails with `WRONG_VERSION_NUMBER`. The `check_compatibility=False` suppresses benign version skew warnings when the client lib version differs from the server.

## Minio S3 AccessDenied

On Docker-hosted Minio, external S3 API calls may return 403 on PUT/POST even with root credentials. Workaround: write files directly into the Minio container's `/data/<bucket>/<path>` via `docker exec` or `tee` — Minio watches the filesystem and makes objects immediately available via S3 GET. See `references/minio-docker-upload.md` in the same skill directory.

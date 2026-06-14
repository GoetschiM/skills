---
name: qdrant
description: "Qdrant Vector Database — Goetschi Labs Instanz auf 10.0.60.121:6333. Collections: goetschi_labs_contacts (214 Kontakte), goetschi_labs_memory (51pts), Test-RAG. Import, Query, Backup & Telegram-Integration."
category: data-science
version: 1.0.0
status: aktiv
---

# Qdrant — Vector Database 🧠

Qdrant ist die Vektor-Datenbank für semantische Suche, Hermes Memory und RAG-Pipelines.
Läuft als Docker-Container auf dem Dokploy-Host (`10.0.60.121`).

## Übersicht

| Eigenschaft | Wert |
|-------------|------|
| Host | `10.0.60.121` |
| Port | `6333` (gRPC + HTTP) |
| Container | `homelab-qdrant-qlmtvm-qdrant-1` |
| API-Key | Über SSH abrufbar (siehe Credentials) |
| Auth | `api-key` Header (nicht Bearer) |

## Collections

| Name | Points | Vector Size | Distance | Zweck |
|------|--------|-------------|----------|-------|
| `goetschi_labs_contacts` | 214 | 384d | Cosine | Kontakt-Datenbank (Personen, Services, Hotlines) |
| `goetschi_labs_memory` | 51 | 384d | Cosine | Hermes Memory (semantische Erinnerungen) |
| `Test-RAG` | 0 | — | — | Test-Collection (leer) |

Embedding-Modell: `sentence-transformers/multilingual-MiniLM-L12-v2` (384d)

## API-Key abrufen

```python
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.0.60.121", username="root", password="Louis_one_13", timeout=10)

stdin, stdout, stderr = c.exec_command(
    "docker exec homelab-qdrant-qlmtvm-qdrant-1 env | grep QDRANT__SERVICE__API_KEY | cut -d= -f2"
)
api_key = stdout.read().decode().strip()
c.close()
```

Der Key ist ein 32-Zeichen-String. Einmal abgerufen, in `~/.hermes/.env` als `QDRANT_API_KEY` speichern.

## API-Operationen

### Collections auflisten

```python
import requests, os

key = os.environ["QDRANT_API_KEY"]  # oder aus /tmp/qdrant_api_key.txt
r = requests.get("http://10.0.60.121:6333/collections",
    headers={"api-key": key}, timeout=10)
cols = r.json()["result"]["collections"]
for c in cols:
    print(f'  {c["name"]}')
```

### Collection-Info

```python
r = requests.get("http://10.0.60.121:6333/collections/goetschi_labs_contacts",
    headers={"api-key": key}, timeout=10)
info = r.json()["result"]
# info["vectors_count"], info["points_count"], info["status"], info["config"]["params"]
```

### Kontakte suchen (Semantisch)

→ **Empfohlen:** Siehe `scripts/semantic_search.py` oder die vollständige
Code-Sequenz im Abschnitt "Vollständige semantische Suche (End-to-End)" oben.

```python
import requests, json

key = "..."  # QDRANT_API_KEY
vector = [...]  # 384d Embedding via fastembed generieren

r = requests.post("http://10.0.60.121:6333/collections/goetschi_labs_contacts/points/search",
    headers={"api-key": key, "Content-Type": "application/json"},
    json={"vector": vector, "limit": 5, "with_payload": True}, timeout=10)

for h in r.json()["result"]:
    print(f'  {h["payload"]["display_name"]}: {", ".join(p["value"] for p in h["payload"].get("phones",[]))}')
```

## Voraussetzungen

```bash
# Python-Client für API-Zugriff
pip install --break-system-packages requests

# Lokales Embedding (für semantische Suche OHNE externen API-Aufruf)
# LEICHT — fastembed ist <100MB, ONNX-basiert, installiert in Sekunden
# (NICHT sentence-transformers verwenden — das ist 2GB+ und dauert ewig)
pip install --break-system-packages fastembed

# SSH-Zugriff zu Dokploy-Host
pip install --break-system-packages paramiko
```

## Embedding-Modell

Wird beim Import / Backup verwendet:

```python
from fastembed import TextEmbedding
# multilingual-MiniLM-L12-v2 — 384d, Cosine, Deutsch-kompatibel
model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vector = list(model.embed("Suchtext"))[0].tolist()  # → [384 floats]
```

**Wichtig:** Das Modell muss mit dem identisch sein, das beim Import verwendet wurde, sonst sind die Vektoren nicht vergleichbar.

## Vollständige semantische Suche (End-to-End)

```python
from fastembed import TextEmbedding
import requests, json

QDRANT_HOST = "http://10.0.60.121:6333"

# API-Key holen
with open('/tmp/qdrant_api_key.txt') as f:
    key = f.read().strip()
# Oder: key = os.environ["QDRANT_API_KEY"]

# Embedding generieren
model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vector = list(model.embed("Suchtext hier"))[0].tolist()

# In Qdrant suchen
r = requests.post(f"{QDRANT_HOST}/collections/goetschi_labs_contacts/points/search",
    headers={"api-key": key, "Content-Type": "application/json"},
    json={"vector": vector, "limit": 5, "with_payload": True},
    timeout=15)

for hit in r.json()["result"]:
    pl = hit["payload"]
    print(f'  [{hit["score"]:.4f}] {pl["display_name"]}')
    print(f'         📍 {pl.get("city","")} | 👤 {pl.get("relationship","")}')
    print(f'         📞 {", ".join([p["value"] for p in pl.get("phones",[])])}')
```

Siehe auch `scripts/semantic_search.py` für eine wiederverwendbare Version.

## In goetschi_labs_memory schreiben (Wissen speichern)

```python
import requests, json

key = "..."  # QDRANT_API_KEY
vector = [...]  # 384d Embedding wie oben

point = {
    "id": str(uuid.uuid4()),
    "vector": vector,
    "payload": {
        "text": "Der Inhalt deiner Wissens-Notiz",
        "type": "infrastructure",  # infrastructure, skills, known-issue, architecture_decision, identity, notion, atlassian, etc.
        "source": "apollo-conversation",  # oder system, sysadmin, user
        "created_at": "2026-05-17T12:00:00"
    }
}

r = requests.put(f"{QDRANT_HOST}/collections/goetschi_labs_memory/points",
    headers={"api-key": key, "Content-Type": "application/json"},
    json={"points": [point]},
    timeout=10)
```

## Minio Backup & Schwarmwissen

Qdrant wird automatisch via Qdrant-Snapshot in Minio gesichert:

| Komponente | Minio Bucket | Pfad |
|------------|-------------|------|
| Qdrant-Snapshots | `swarm-skills/qdrant-snapshots/` | Tägliche Snapshot-Dateien |
| Skills (alle) | `swarm-skills/` | Nach Kategorien sortiert |
| Hermes Full-Backup | `hermes-backups/` | tar.gz Archive |
| Nova Backups | `nova-backups/` | tar.gz Archive |
| Hermes-156 Backup | `hermes-156-backups/` | Dedizierter Bucket |

Qdrant-Snapshots prüfen über SSH auf 10.0.60.121:
```bash
docker exec homelab-minio-0sa7uj-minio-1 ls /data/swarm-skills/qdrant-snapshots/
```

## Schwarmwissen-Architektur (GL-36, Erledigt)

```
┌─────────────────────────────────────────────────┐
│  Hermes 156 (Apollo)     Nova     Zukünftige     │
│       │                     │          │          │
│       ▼                     ▼          ▼          │
│  ┌──────────────── Qdrant ────────────────┐      │
│  │ goetschi_labs_contacts (214 Kontakte)  │      │
│  │ goetschi_labs_memory  (52 Wissensp.)   │      │
│  └────────────────────────────────────────┘      │
│       │                                           │
│       ▼                                           │
│  ┌────────── Minio ──────────┐                    │
│  │ swarm-skills/ (Skills)    │                    │
│  │ qdrant-snapshots/ (DB)    │                    │
│  │ hermes-backups/ (Config)  │                    │
│  │ nova-backups/             │                    │
│  └───────────────────────────┘                    │
│                                                  │
│  3-fach Backup: Qdrant ↔ Minio ↔ Notion/Confluence│
└─────────────────────────────────────────────────┘
```

## Verknüpfte Dateien (im Skill-Verzeichnis)

| Datei | Beschreibung |
|-------|-------------|
| `scripts/semantic_search.py` | Wiederverwendbares CLI-Script für semantische Suche |
| `references/schwarmwissen-architecture.md` | Architektur-Doku: Agenten ↔ Qdrant ↔ Minio |

## Pitfalls

- ⚠️ **Auth via `api-key` Header**, nicht `Authorization: Bearer`
- ⚠️ Embedding muss mit demselben Modell erstellt sein, das beim Import verwendet wurde (multilingual-MiniLM-L12-v2, 384d)
- ⚠️ Collection-Name ist case-sensitiv: `goetschi_labs_contacts` (nicht `Goetschi_Labs_Contacts`)
- ⚠️ SSH zu 10.0.60.121 (Dokploy) nur nötig, wenn der API-Key nicht lokal gespeichert ist
- ⚠️ `requests.post` — bei `/collections` Endpoint ist GET korrekt, bei `/points/search` POST

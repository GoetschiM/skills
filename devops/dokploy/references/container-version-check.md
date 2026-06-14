# Container Version Check — Security Audit Technique

## Problem
Du musst prüfen ob e deployedi Container-App aktuell isch (Security Patch, Advisory-Check) — aber d'App het kei öffentlichi Version-Endpoint oder du hesch kei UI-Zugriff.

## Solution: Docker Image Labels

Docker Images trage oft Metadate i ihre Labels — inklusive Versions-Nummer:

```bash
docker image inspect <image>:<tag> --format '{{json .Config.Labels}}' | python3 -m json.tool
```

### n8n Beispiel (us GL-110 vom 28.05.2026)

```bash
# Version vom deployte Image uslese
docker image inspect n8nio/n8n:latest --format '{{json .Config.Labels}}' | \
  python3 -c 'import json,sys; d=json.load(sys.stdin); \
    [print(f"{k}: {v}") for k,v in d.items() if "version" in k.lower()]'

# Output:
# com.docker.dhi.version: 24.15.0-alpine3.22-dev
# org.opencontainers.image.version: 2.21.7
```

### Prüefe ob e neuer Version uf Docker Hub isch

```bash
# Latest Tag — Datum prüefe
curl -s "https://hub.docker.com/v2/repositories/n8nio/n8n/tags/latest" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
    print(f'Latest: {d.get(\"name\",\"?\")} pushed {d.get(\"last_updated\",\"?\")[:10]}')"

# Output:
# Latest: latest pushed 2026-05-28  ← Heit updated!
```

## Typischi Label Keys für Version

| Label Key | Typisch bi |
|---|---|
| `org.opencontainers.image.version` | Standard OCI Label — n8n, viele Open-Source-Images |
| `com.docker.dhi.version` | Docker Official Images |
| `org.label-schema.version` | Älterer Standard (vor OCI) |

## Workflow

1. Security Advisory checkt → betroffeni Version erfahre (z.B. n8n 2.21.7 ist vulnerable, 2.21.8 fixed)
2. Docker Image Label vom deployte Container uslese
3. Docker Hub latest tag timestamp prüefe (falls `:latest` verwendet wird)
4. Wenn veraltet → `docker pull <image>:latest` + Container-Neustart
5. Verifizierig: Image Label nomol prüefe → sött jetz fixi Version zeige

## Fallback: Docker Inspect Config

Falls Labels lehr sind, zeigts `docker inspect <container>` au s'Image an:

```bash
docker inspect <container-name> --format '{{.Config.Image}}'
```

Git dich de Image-Name, wo bim Start verwendet worde isch — zum googlen ob das d'patchedi Version isch.

## Scope

Das isch nid es vollständigs Vulnerability-Scanning — das isch en schnelle **Version-Check** fürd Security-Patch-Verifizierig. Für vollständigs Scanning bruuchsch Tools wie Trivy oder Grype.

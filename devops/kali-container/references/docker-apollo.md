# Docker uf Apollo (10.0.60.156)

## Daemon-Status

Docker uf Apollo isch disabled (systemctl is-active docker → inactive).
Nach eme Host-Neustart startet Docker nöd automatisch — Container sind verlore.

## Daemon aktiviere (optional)

```bash
systemctl enable docker --now    # Aktiv + sofort starte
systemctl is-active docker       # Kontrolle: active
```

## Container-Persistenz

Wenn Container au uf Host-Neustart überlebe söll:
```bash
docker run -d --restart unless-stopped --name mein-container ... 
```

**Ohne `--restart`:** Container existiert nume solang Docker läuft. Wenn Docker stoppt (Crash, Reboot), isch de Container weg — au wenn de `sleep infinity` Prozess drin isch.

## Erkannti Problem

| Datum | Problem | Fix |
|-------|---------|-----|
| 18.05.2026 | Docker war gestoppt (inactive) am Abig. Container `kali` existiert nüm. | Docker starte (`systemctl start docker`), Container neu erstelle |

## Hinweis für Agentä

Wenn en Docker-Container uf Apollo nöd existiert oder nöd lauft:
1. `systemctl start docker` (Daemon starte)
2. `docker ps -a` (Container prüefe)
3. Falls verlore → nei erstelle (Config isch im Skill oder im Memory)

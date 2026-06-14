# Multi-Instance Deployment & Config Path Resolution

## How Hermes Finds Its Config

When Hermes starts, it resolves `config.yaml` and `.env` paths based on the
`HERMES_HOME` environment variable — **not** `~/.hermes/`:

| Variable | Effect |
|----------|--------|
| `HERMES_HOME` | Root dir: `$HERMES_HOME/config.yaml` + `$HERMES_HOME/.env` |
| `HOME` / `~` | Only matters for `~/.hermes/` fallback data (telegram sessions, call recordings, skills). **Not** used for config. |
| Neither set | Defaults to `~/.hermes/config.yaml` + `~/.hermes/.env` |

### Verification

```bash
hermes config show  # → ◆ Paths section shows actual config + secrets paths
```

### Systemd Deployment Pattern

```ini
[Service]
Type=simple
WorkingDirectory=/opt/hermes/app
ExecStart=/opt/hermes/start-gateway.sh
```

```bash
#!/bin/sh
cd /opt/hermes/app || exit 1
exec env HOME=/opt/hermes/data/home \
         HERMES_HOME=/opt/hermes/data \
         /opt/hermes/venv/bin/hermes gateway run
```

With this:
- **Config:** `/opt/hermes/data/config.yaml`
- **Secrets:** `/opt/hermes/data/.env`
- **Skills:** `/opt/hermes/data/skills/`
- **Sessions:** `/opt/hermes/data/home/.hermes/sessions/`
- **Telegram session:** `/opt/hermes/data/home/.hermes/telegram_config.json`
- **Call recordings:** `/opt/hermes/data/home/.hermes/call_recordings/`

### Concrete Example: Nova Instance (Goetschi Labs)

The actual Nova deployment (`10.0.60.167`):

```ini
# /etc/systemd/system/hermes167.service
[Service]
Type=simple
WorkingDirectory=/opt/hermes167/app
ExecStart=/opt/hermes167/start-gateway.sh
Restart=always
RestartSec=5
```

```bash
#!/bin/sh
# /opt/hermes167/start-gateway.sh
cd /opt/hermes167/app || exit 1
exec env HOME=/opt/hermes167/data/home \
         HERMES_HOME=/opt/hermes167/data \
         HERMES_BUNDLED_SKILLS=/opt/hermes167/app/skills \
         /opt/hermes167/venv/bin/hermes gateway run
```

With this:
- **Config:** `/opt/hermes167/data/config.yaml`
- **Secrets:** `/opt/hermes167/data/.env`
- **Skills:** `/opt/hermes167/data/skills/`
- **Home data:** `/opt/hermes167/data/home/.hermes/` (telegram session, call recordings)

### Pitfalls

- **Writing config to the wrong path.** If you SSH into a secondary instance and
  write to `/root/.hermes/config.yaml` or `~/.hermes/config.yaml`, it will
  NOT be read — Hermes looks at `$HERMES_HOME/config.yaml` instead.
- **After updating config, the service must be restarted.** `hermes gateway restart`
  won't work via SSH if the gateway runs as a systemd service — use
  `systemctl restart hermes-gateway` or the service name directly.
- **`hermes config edit` writes to the correct path** because it reads
  `$HERMES_HOME` from the running process — prefer it over manual writes.
- **SSH session vs systemd service:** When you SSH in and run `hermes config show`,
  if `HERMES_HOME` isn't set in your SSH env, it shows `~/.hermes/config.yaml`.
  The actual service may use a different path. Always check the service's
  `ExecStart` script or `systemctl show <service>` for the real env vars.

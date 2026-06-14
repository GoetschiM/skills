# Dograh ARI Manager — Operations Reference

## Start / Restart

The ARI Manager does NOT auto-start with `docker compose up`. It must be started manually:

```bash
cd /opt/dograh/
# Kill old process if running (inside api container)
docker compose exec -T api pkill -f ari_manager 2>/dev/null || true

# Start new one in detached mode
docker compose exec -d api python3 /app/api/services/telephony/ari_manager.py

# Verify connection
sleep 5
docker compose logs api | grep -i 'WebSocket connected'
# Expected: "WebSocket connected to http://<asterisk-host>:8088"
```

## Check Status

```bash
# Check if ari_manager process is running
docker compose exec -T api ps aux | grep ari_manager

# Check for WebSocket connection errors
docker compose logs api | grep -i 'ari\|WebSocket\|401\|error\|connect' | tail -15
```

## Network: Host IP, NOT localhost

Critical: ARI endpoint in the telephony config MUST use the host machine's IP (e.g. `10.0.60.167`), NOT `localhost`. Inside the Docker container, `localhost` refers to the container itself, not the host.

If Docker can't reach Asterisk via host IP, check:
1. Asterisk ARI port 8088 is not firewalled
2. Docker network mode allows host access (default bridge works)

## ARI User on Asterisk

Dograh's ARI provider uses `app_name` as BOTH the Stasis application name AND the ARI username in WebSocket auth (`api_key={app_name}:{app_password}`). Ensure both match in Asterisk config.

```bash
# On the Asterisk host, add the ARI user matching the Stasis app name:
echo -e '\n[callbot]\ntype = user\nread_only = no\npassword = HermesVB2026\n' >> /etc/asterisk/ari.conf

# Reload ARI module without restarting Asterisk:
asterisk -rx 'module reload res_ari'
```

## Known Limitations

- No auto-restart on Docker compose restart — must be manually started
- Single instance only (one WebSocket per ARI manager)
- If connection drops, the manager retries automatically (config refresh interval)

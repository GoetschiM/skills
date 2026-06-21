# Loki Configuration for Goetschi Labs

Copy to `/opt/monitoring/loki/loki-config.yaml` on CT110 (10.0.60.110).

## Minimal Production Config

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  ring:
    kvstore:
      store: inmemory
  replication_factor: 1
  path_prefix: /loki

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v12
      index:
        prefix: index_
        period: 24h

storage_config:
  tsdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
  filesystem:
    directory: /loki/chunks

compactor:
  working_directory: /loki/compactor
```

## Docker Compose Service Entry

```yaml
  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - /opt/monitoring/loki/loki-config.yaml:/etc/loki/config.yaml:ro
      - /data/loki-data:/loki
    command: -config.file=/etc/loki/config.yaml
    networks:
      - monitoring-net
```

## Verification

```bash
# Check loki is healthy
curl -s http://10.0.60.110:3100/ready

# Check if logs arrived
curl -s -G http://10.0.60.110:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="systemd-journal"}' \
  --data-urlencode 'limit=5'
```

## Pitfalls

- Without the `/data/loki-data:/loki` volume bind, logs are lost on container restart
- The TSDB schema (v12) is required for Loki >= 3.0 — older schema (v11) will fail
- `auth_enabled: false` means any LXC can push logs — enable auth in production

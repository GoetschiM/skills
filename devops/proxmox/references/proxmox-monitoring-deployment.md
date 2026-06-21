---
name: proxmox-monitoring
description: "Deploy and manage Prometheus + Grafana + Loki monitoring stack on Proxmox LXC infrastructure (Goetschi Labs). Covers node_exporter deployment (Docker + native), promtail log shipping, Prometheus config, Grafana datasource provisioning, and dashboard setup."
version: 1.0.0
author: Magos
license: MIT
metadata:
  hermes:
    tags: [proxmox, monitoring, prometheus, grafana, loki, goetschi-labs]
    related_skills: [proxmox]
---

# Proxmox Monitoring Stack (Prometheus + Grafana + Loki)

## When to use

- User asks about setting up monitoring, metrics collection, or dashboards
- User wants to see CPU/RAM/Disk usage across all LXCs
- User reports Grafana shows no data
- User wants log aggregation across containers and services
- Any task involving Prometheus, Loki, Grafana, node_exporter, promtail on Proxmox

## Overview

Goetschi Labs monitoring stack runs on CT110 (10.0.60.110):
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Visualization (port 3000)
- **Loki**: Log aggregation (port 3100)
- **OpenObserve**: Optional log/metrics tool (port 5080 — unstable)
- **node_exporter**: System metrics agent on each LXC (port 9100)
- **promtail**: Log shipper on each Docker-enabled LXC

## Quick Reference: LXC IPs

| LXC | Name | IP | Has Docker |
|-----|------|----|------------|
| 100 | Dokploy | 10.0.60.121 | ✅ |
| 103 | Paperless | 10.0.60.30 | ❌ |
| 105 | PGVector | 10.0.60.141 | ❌ |
| 107 | MCPHub | 10.0.60.170 | ✅ |
| 108 | Hermes | 10.0.60.156 | ✅ |
| 109 | InfluxDB | 10.0.60.140 | ❌ |
| 110 | Monitoring | 10.0.60.110 | ✅ (self-host) |
| 112 | Nova | 10.0.60.167 | ✅ |
| 116 | LiteLLM | 10.0.60.176 | ❌ |
| 117 | Voice-Gateway | 10.0.60.60 | ✅ |
| 118 | Coolify | 10.0.60.139 | ✅ |
| 401 | Magos | — | ❌ |
| 402 | Orion | — | ❌ |
| 504 | MT5-Bot04 | 10.0.60.104 | ❌ |
| 505 | MinIO | 10.0.60.106 | ❌ |
| 506 | Qdrant | 10.0.60.179 | ❌ |
| pve01 | Proxmox Host | 10.0.60.10 | ❌ |

## Deployment

All commands run via `sshpass` to pve01 (10.0.60.60) then `pct exec` into the target LXC.

### Prerequisites

```bash
NODE_EXPORTER_VERSION="1.8.2"
```

### 1. Deploy node_exporter to Docker-enabled LXCs

Create a batch script `deploy_node_exporters.sh` on pve01:

```bash
# Pipe to pve01: cat /tmp/script.sh | sshpass -p 'pass' ssh root@pve01 "cat > /tmp/script.sh"
# Then: sshpass ... "chmod +x /tmp/script.sh && bash /tmp/script.sh"

for VMID in 100 107 108 112 117 118; do
  pct exec $VMID -- docker rm -f node-exporter 2>/dev/null || true
  pct exec $VMID -- bash -c 'docker run -d --name node-exporter \
    --restart unless-stopped \
    --network host \
    --pid host \
    -v /proc:/host/proc:ro \
    -v /sys:/host/sys:ro \
    -v /:/rootfs:ro \
    quay.io/prometheus/node-exporter:latest \
    --path.procfs=/host/proc \
    --path.sysfs=/host/sys \
    --path.rootfs=/rootfs'
done
```

### 2. Deploy node_exporter to non-Docker LXCs (native install)

```bash
for VMID in 103 105 108 109 401 402 504 505 506; do
  pct exec $VMID -- bash -c "
    cd /tmp
    curl -sLO https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    tar xzf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    cp node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
    rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64*
    chmod +x /usr/local/bin/node_exporter
  "
  
  # Service file — Omit --path.procfs flags for native installs!
  pct exec $VMID -- bash -c '
    cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/local/bin/node_exporter \
  --collector.filesystem.mount-points-exclude="^/(sys|proc|dev|host|etc)($|/)"

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable node_exporter
    systemctl start node_exporter
  '
done
```

### 3. Deploy promtail to Docker-enabled LXCs

```bash
LOKI_IP="10.0.60.110"  # CT110

for VMID in 100 107 108 112 117 118; do
  pct exec $VMID -- docker rm -f promtail 2>/dev/null || true
  pct exec $VMID -- mkdir -p /etc/promtail
  HOSTNAME=$(pct exec $VMID -- hostname | tr -d '\n\r')
  
  # Write promtail config
  pct exec $VMID -- bash -c "cat > /etc/promtail/config.yml << 'CONFEND'
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://${LOKI_IP}:3100/loki/api/v1/push
scrape_configs:
  - job_name: journal
    journal:
      max_age: 12h
      labels:
        job: systemd-journal
        host: ${HOSTNAME}
    relabel_configs:
      - source_labels: ['__journal__hostname']
        target_label: 'hostname'
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
CONFEND"

  pct exec $VMID -- docker run -d --name promtail \
    --restart unless-stopped \
    --network host \
    -v /etc/promtail/config.yml:/etc/promtail/config.yml \
    -v /var/log:/var/log:ro \
    -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
    -v /run/log/journal:/run/log/journal:ro \
    grafana/promtail:latest \
    -config.file=/etc/promtail/config.yml
done
```

### 4. Update Prometheus Configuration

**See reference: `references/loki-config.md` for the full Loki config and verification steps.**

Write to `/opt/monitoring/prometheus/prometheus.yml` (on CT110):

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: pve01
    static_configs:
      - targets: ["10.0.60.10:9100"]

  - job_name: docker-lxcs
    static_configs:
      - targets:
        - "10.0.60.121:9100"
        - "10.0.60.170:9100"
        - "10.0.60.167:9100"
        - "10.0.60.60:9100"
        - "10.0.60.139:9100"

  - job_name: no-docker-lxcs
    static_configs:
      - targets:
        - "10.0.60.30:9100"
        - "10.0.60.141:9100"
        - "10.0.60.140:9100"
        - "10.0.60.104:9100"
        - "10.0.60.106:9100"
        - "10.0.60.179:9100"
```

⚠️ **PITFALL**: `labels` is NOT a valid key at the `scrape_config` level in Prometheus. Labels must go inside `static_configs`. Writing `labels: {group: docker}` at the job level will cause a YAML parse failure.

**Reload Prometheus:**
```bash
pct exec 110 -- docker exec prometheus promtool check config /etc/prometheus/prometheus.yml  # Validate first!
pct exec 110 -- docker kill -s HUP prometheus  # SIGHUP reload
```

**Check targets:**
```bash
pct exec 110 -- curl -s 'http://localhost:9090/api/v1/targets' | python3 -c 'import sys,json; d=json.load(sys.stdin); active=d.get("data",{}).get("activeTargets",[]); [print(f"{t[\"labels\"][\"instance\"]:25} {t[\"health\"]:6}") for t in active]'
```

### 5. Configure Grafana Datasources

Write to `/opt/monitoring/grafana/datasources.yaml` (on CT110):

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

```bash
pct exec 110 -- docker restart grafana
```

### 6. Verify Everything

```bash
# Prometheus targets
pct exec 110 -- curl -s 'http://localhost:9090/api/v1/targets' | python3 -c 'import sys,json; d=json.load(sys.stdin); active=d.get("data",{}).get("activeTargets",[]); up=sum(1 for t in active if t["health"]=="up"); print(f"{len(active)} targets, {up} up")'

# Grafana datasources
pct exec 110 -- curl -s http://localhost:3000/api/datasources -u admin:admin

# Check node_exporter on specific LXC
pct exec 100 -- curl -sf http://localhost:9100/metrics | head -2
```

## Pitfalls

1. **`labels` at scrape_config level is invalid**: In Prometheus config, `labels` must go inside `static_configs`, not at the job level. Promtool will fail with: `field labels not found in type config.ScrapeConfig`.

2. **node_exporter native vs Docker flags**: For Docker deployments, use `--path.procfs=/host/proc --path.sysfs=/host/sys --path.rootfs=/rootfs`. For native installs, **OMIT these flags** — they point to /host/* paths that don't exist on a native install.

3. **pct exec + bash heredoc escaping**: Nested bash -c with heredocs for pct exec is fragile. Use Python inline (`pct exec VMID -- python3 -c '...'`) for complex config writing, or write to a temp file on pve01 and pipe it.

4. **pct push not available**: `pct push` doesn't exist on all Proxmox versions. Use `cat > /tmp/file` pipe instead: `cat /tmp/script.sh | sshpass ... pve01 "cat > /tmp/script.sh"`.

5. **OpenObserve restart loop**: OpenObserve tends to crash on startup. Not critical — the stack works without it.

6. **Docker-only LXCs may not have curl**: For `curl -sf` health checks, some minimal LXCs (MinIO, Qdrant) lack curl. Use `wget -qO-` or install curl.

7. **Grafana initial password**: After first restart, Grafana defaults may reset. Check `/opt/monitoring/docker-compose.yml` for `GF_SECURITY_ADMIN_PASSWORD`. If the compose file masks it with `***`, the password was set during initial deployment and may need resetting via Grafana CLI.

8. **Prometheus port already in use**: If CT110 already has something on 9090 (e.g., OpenObserve), Prometheus may conflict. Use a different port in the compose file.

9. **pct exec + curl output disappears**: When running `pct exec VMID -- bash -c 'curl -s http://localhost:9090/api/v1/targets | python3 ...'` from inside an SSH session, the response may be empty because `pct exec` doesn't cleanly return stdout of piped commands targeted at internal localhost services. Prefer:
   - Running the check **inside the container** via `docker exec` directly
   - Or running `curl` from the PVE host against the container IP: `curl -s http://10.0.60.110:9090/api/v1/targets`
   - Or just checking once with `pct exec` then verifying via curl from outside

If `GF_SECURITY_ADMIN_PASSWORD` is a placeholder (`***`) or the password is unknown:

1. Stop grafana: `docker compose -f /opt/monitoring/docker-compose.yml stop grafana`
2. Run a temporary grafana container with the same volume to reset:
   ```bash
   docker run --rm -v monitoring_grafana-data:/var/lib/grafana --entrypoint grafana \
     grafana/grafana:latest server admin reset-admin-password Me...    --homepath=/usr/share/grafana
   ```
   Wait for the log output to show "All modules healthy" then the container exits.
3. **IMPORTANT**: Remove `GF_SECURITY_ADMIN_PASSWORD` from the compose file's environment section
4. Start grafana: `docker compose -f /opt/monitoring/docker-compose.yml up -d grafana`
5. Login with the password you set

**PITFALL**: If `GF_SECURITY_ADMIN_PASSWORD` is still in the compose file, it overrides the DB password on every start — your reset will be overwritten. Either remove it entirely or set it to match your chosen password.

**PITFALL**: The `docker run --rm ... reset-admin-password` command will attempt to start a full Grafana server on port 3000. If the old container is still running (port conflict), the reset fails. Stop grafana first.

8. **Prometheus port already in use**: If CT110 already has something on 9090 (e.g., OpenObserve), Prometheus may conflict. Use a different port in the compose file.

## Verification Checklist

- [ ] `curl -s http://10.0.60.110:9090/api/v1/targets` shows expected targets
- [ ] `curl -s http://10.0.60.110:3000/api/datasources` shows Prometheus + Loki
- [ ] All LXC node_exporters show "up" in Prometheus after 30s
- [ ] Grafana can query Prometheus data
- [ ] Loki receives logs (check Loki's `/ready` endpoint)

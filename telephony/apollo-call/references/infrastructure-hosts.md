# Infrastructure Host Access

SSH access pattern for Goetschi Labs infrastructure hosts.
All hosts use the same credential scheme.

## Hosts

| Host | IP | Role | Services |
|------|-----|------|----------|
| Dokploy | `10.0.60.121` | Docker Swarm orchestration host | Qdrant, Minio, LiteLLM, Paperless, Postgres, Redis, worldmonitor |
| Asterisk | `10.0.60.167` | PBX / Telephony | Asterisk, ARI (8088), AMI (5038) |
| Hermes | `10.0.60.156` | Hermes Agent LXC | Hermes Agent, Skills, Memory |

## Credentials

| Host | User | Password | Auth Method |
|------|------|----------|-------------|
| 10.0.60.121 | root | `Louis_one_13` | SSH password |
| 10.0.60.167 | root | `Louis_one_13` | SSH password |

## SSH via Paramiko (Python, recommended for Hermes)

```python
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.0.60.121", username="root", password="Louis_one_13", timeout=10)

# Run a command
stdin, stdout, stderr = c.exec_command("docker ps --format '{{.Names}} {{.Image}}'")
print(stdout.read().decode())

# SFTP file transfer
sftp = c.open_sftp()
sftp.put("/tmp/local_file.txt", "/remote/path/file.txt")
sftp.close()

c.close()
```

## Paramiko Installation

```bash
pip install --break-system-packages paramiko
```

Verify:
```bash
python3 -c "import paramiko; print(paramiko.__version__)"
```

## Notes

- Password auth only — no SSH keys deployed on these hosts
- `AutoAddPolicy()` is safe for internal lab network
- Connection timeout should be 10s max for lab hosts
- Dokploy host runs Docker Swarm; containers are managed via `docker` CLI
- Asterisk host is a dedicated LXC; services are managed by systemd or directly via `asterisk -rx`

## Typical Use Cases

1. **Apollo Call**: SSH to Asterisk → SFTP sound files → originate call
2. **Guten Morgen Call**: Same pattern + data collection before call
3. **Qdrant Access**: SSH to Dokploy → `docker exec` to get Qdrant API key → REST API calls
4. **Docker Inspection**: SSH to Dokploy → `docker inspect` containers for env/config

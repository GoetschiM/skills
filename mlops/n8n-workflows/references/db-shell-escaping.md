# DB Shell Escaping for Multi-Layer SSH + Docker + PostgreSQL

When modifying n8n workflow data via PostgreSQL, the command chain is:
```
local bash → sshpass + ssh → remote bash → pct exec → docker exec → psql
```

Each layer strips or mangles quotes, backticks, `$` symbols, and escaping. This file documents proven strategies.

## Strategy 1: Write Python script to LXC, then run it (MOST RELIABLE)

```bash
# Step 1: Create the Python script on the LXC
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no root@10.0.60.10 bash << 'SSHEOF'
pct exec 100 -- bash -c 'cat > /tmp/fix_workflow.py << '\''PYEOF'\''
import json, subprocess

WORKFLOW_ID = "some-uuid"

# Read nodes from DB
sql = "SELECT nodes::text FROM workflow_entity WHERE id = '\''" + WORKFLOW_ID + "'\'';"
r = subprocess.run([
    '\''docker'\'', '\''exec'\'', '\''homelab-n8nwithpostgres-pzbt9a-postgres-1'\'',
    '\''psql'\'', '\''-U'\'', '\''michel'\'', '\''-d'\'', '\''n8n'\'', '\''-t'\'', '\''-A'\'', '\''-c'\'', sql
], capture_output=True, text=True, timeout=10)

nodes = json.loads(r.stdout.strip())

# Modify nodes...

# Update DB
nodes_json = json.dumps(nodes)
sql_update = "UPDATE workflow_entity SET nodes = '\''" + nodes_json.replace("'\''", "'\'''\''") + "'\''::jsonb WHERE id = '\''" + WORKFLOW_ID + "'\'';"
subprocess.run([
    '\''docker'\'', '\''exec'\'', '\''homelab-n8nwithpostgres-pzbt9a-postgres-1'\'',
    '\''psql'\'', '\''-U'\'', '\''michel'\'', '\''-d'\'', '\''n8n'\'', '\''-c'\'', sql_update
])
PYEOF'

# Step 2: Run it
pct exec 100 -- python3 /tmp/fix_workflow.py
SSHEOF
```

**Key escaping rules for this pattern:**
- The outer `<< 'SSHEOF'` uses single-quoted delimiter to prevent local shell expansion
- Inside that, `<< '\''PYEOF'\''` uses escaped single quotes to pass a literal `'PYEOF'` to the remote bash
- Inside the Python script, single quotes for Python strings use `'\''` (break out of single-quote, add escaped quote, resume)
- Inside the `messages` value in node parameters, use `\"` for JSON-in-Python-in-bash

## Strategy 2: Write SQL to a file, then pipe it (for simple SQL updates)

```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no root@10.0.60.10 bash << 'SSHEOF'
# Write the SQL to a temp file
pct exec 100 -- bash -c 'cat > /tmp/update.sql << '\''SQLEOF'\''
UPDATE workflow_entity 
SET nodes = '\''[{"type": "n8n-nodes-base.httpRequest", ...}]'\''::jsonb
WHERE id = '\''some-uuid'\'';
SQLEOF'

# Pipe the file to psql
pct exec 100 -- docker exec -i homelab-n8nwithpostgres-pzbt9a-postgres-1 \
  psql -U michel -d n8n < /tmp/update.sql
SSHEOF
```

## Strategy 3: Multiple small `psql -c` calls (for simple SELECT/UPDATE)

Works for trivial queries but breaks with complex JSON containing quotes:

```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no root@10.0.60.10 \
  "pct exec 100 -- docker exec homelab-n8nwithpostgres-pzbt9a-postgres-1 \
    psql -U michel -d n8n -c \"SELECT id, name, active FROM workflow_entity WHERE id = 'some-uuid';\"" 2>&1
```

**Limitation:** Double quotes (`"`) inside the SQL query need `\"` at EACH layer, and single quotes (`'`) must be preserved through ssh → pct exec → docker exec. This breaks for multi-line or complex JSON.

## Strategy 4: `pct push` (for uploading files)

```bash
pct push 100 /local/path/file.py /remote/path/file.py
```

**Note:** The source path must exist on the **Proxmox host** filesystem, not on the originating machine. `pct push` uploads FROM the Proxmox host TO the LXC. To use this: first scp the file to the Proxmox host, then `pct push`.

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `unterminated quoted string` in psql | Single quote inside JSON not escaped | Use `.replace("'", "''")` on JSON before building SQL |
| `syntax error at or near "("` | Newline in jsCode field broke JSON string | Avoid jsCode in inline SQL; use Python to build JSON |
| Script exits with code 1, no output | Python subprocess timeout or sshpass stderr hidden | Add `2>&1` and check exit code explicitly |
| `failed to open ... for reading` on pct push | Source file not on Proxmox host | Copy to Proxmox host first: `scp file root@10.0.60.10:/tmp/` |

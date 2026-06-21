#!/usr/bin/env python3
"""
Deploy an n8n workflow JSON directly into the PostgreSQL database,
bypassing the REST API.

Usage:
  python3 pg-deploy-workflow.py /path/to/workflow.json

Requires:
  - sshpass (for SSH to Proxmox host)
  - pct exec access to CT100 (Dokploy LXC)
  - Docker access to n8n's postgres container
"""

import subprocess, json, uuid, sys

def deploy_workflow(json_path: str, name: str = None) -> str:
    """Inject a n8n workflow JSON into PostgreSQL and return the workflow ID."""
    
    with open(json_path) as f:
        workflow = json.load(f)
    
    workflow_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    
    # Extract connections (must match exactly what's inside the nodes JSON)
    connections = workflow['connections']
    
    # CRITICAL: Escape single quotes for PostgreSQL string literals
    workflow_json = json.dumps(workflow, ensure_ascii=False).replace("'", "''")
    connections_json = json.dumps(connections, ensure_ascii=False).replace("'", "''")
    
    if name:
        workflow_name = name
    else:
        workflow_name = workflow.get('name', 'Unnamed Workflow')
    
    # SSH args for Goetschi Labs Proxmox + CT100 + Docker
    ssh_cmd = [
        'sshpass', '-p', 'Riotstar_PROXMOX_13',
        'ssh', '-o', 'StrictHostKeyChecking=no',
        'root@10.0.60.10',
        'pct exec 100 -- bash -c \'docker exec -i homelab-n8nwithpostgres-pzbt9a-postgres-1 psql -U michel -d n8n\''
    ]
    
    sql = f"""
    INSERT INTO public.workflow_entity (id, name, active, nodes, connections, "versionId", settings, "staticData", "pinData", "triggerCount", meta, "isArchived", "versionCounter")
    VALUES (
      '{workflow_id}',
      '{workflow_name.replace("'", "''")}',
      false,
      '{workflow_json}'::json,
      '{connections_json}'::json,
      '{version_id}',
      '{{}}'::json,
      NULL,
      '{{}}'::json,
      0,
      NULL,
      false,
      1
    );

    INSERT INTO public.shared_workflow ("workflowId", "projectId", role)
    VALUES (
      '{workflow_id}',
      (SELECT id FROM public.project LIMIT 1),
      'workflowOwner'
    );
    """
    
    result = subprocess.run(ssh_cmd, input=sql, capture_output=True, text=True, timeout=30)
    
    if result.returncode != 0:
        raise RuntimeError(f"SSH/DB error: {result.stderr}")
    
    if 'ERROR' in result.stderr:
        raise RuntimeError(f"SQL error: {result.stderr}")
    
    return workflow_id


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 pg-deploy-workflow.py <workflow.json> [workflow-name]")
        sys.exit(1)
    
    name = sys.argv[2] if len(sys.argv) > 2 else None
    wid = deploy_workflow(sys.argv[1], name)
    print(f"✅ Workflow deployed! ID: {wid}")
    print(f"   URL: http://10.0.60.121:5678/workflow/{wid}")
    print("   ⚠️  Credentials (Gmail, OpenAI, Telegram) must be connected via N8N UI!")

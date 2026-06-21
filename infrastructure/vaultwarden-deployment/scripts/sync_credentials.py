#!/usr/bin/env python3
"""
Vaultwarden Bulk Credential Sync — Goetschi Labs
Run inside the vaultwarden container: python3 /tmp/sync.py <client_id> <client_secret>

Uses OAuth2 Client Credentials flow.
PACE with time.sleep(0.3) between creates to avoid rate limits.
"""
import json, sys, os, urllib.request, urllib.parse, urllib.error, time

VAULTWARDEN_URL = os.environ.get("VAULTWARDEN_URL", "http://127.0.0.1:80")

CREDENTIALS=***    {"name": "Example Service", "uri": "https://example.com", "username": "user", "password": "pass", "notes": "Context"},
]

def get_token(client_id, client_secret):
    """Get OAuth2 access token. device_identifier is REQUIRED by Vaultwarden."""
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "api",
        "device_identifier": "goetschi-sync-001",
        "device_name": "Goetschi Labs Credential Sync",
        "device_type": "2",
    }).encode()
    req = urllib.request.Request(f"{VAULTWARDEN_URL}/identity/connect/token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["access_token"]

def sync(client_id, client_secret):
    token = get_token(client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    results = {"created": 0, "skipped": 0, "failed": 0}
    
    for cred in CREDENTIALS:
        payload = {
            "type": 1, "name": cred["name"],
            "login": {
                "uris": [{"uri": cred["uri"], "match": None}],
                "username": cred["username"],
                "password": cred["password"],
            },
            "notes": cred.get("notes", ""),
            "favorite": False,
        }
        try:
            req = urllib.request.Request(f"{VAULTWARDEN_URL}/api/ciphers", data=json.dumps(payload).encode(), headers=headers, method="POST")
            resp = urllib.request.urlopen(req)
            results["created"] += 1
            print(f"+ {cred['name']}", flush=True)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if "already exists" in body.lower() or e.code == 409:
                print(f"= {cred['name']} (exists)", flush=True)
                results["skipped"] += 1
            else:
                print(f"- {cred['name']}: {e.code} {body[:80]}", flush=True)
                results["failed"] += 1
        except Exception as e:
            print(f"! {cred['name']}: {e}", flush=True)
            results["failed"] += 1
        time.sleep(0.3)
    
    print(f"\n📊 {results['created']} created, {results['skipped']} skipped, {results['failed']} failed", flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 sync.py <client_id> <client_secret>")
        sys.exit(1)
    sync(sys.argv[1], sys.argv[2])

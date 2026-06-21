#!/usr/bin/env python3
"""
Vaultwarden MCP Server — provides credential lookup via Hermes MCP stdio protocol.
Register on MCPHub at /app/mcp_settings.json as a stdio transport.
Uses HTTPS external URL (not Docker internal DNS) because it runs on MCPHub CT, not Vaultwarden host.
"""
import json, urllib.request, urllib.parse, sys, os

# Use external HTTPS URL (env overridable)
VAULTWARDEN_URL = os.environ.get("VAULTWARDEN_URL", "https://10.0.60.121")
CLIENT_ID = os.environ.get("VAULTWARDEN_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("VAULTWARDEN_CLIENT_SECRET", "")

def get_token():
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "api",
        "device_identifier": "hermes-mcp-001",
        "device_name": "Goetschi Labs MCP",
        "device_type": "2",
    }).encode()
    req = urllib.request.Request(f"{VAULTWARDEN_URL}/identity/connect/token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    ctx = urllib.request.HTTPSHandler(context=ssl._create_unverified_context() if "INSECURE" in os.environ else None)
    opener = urllib.request.build_opener(ctx) if "INSECURE" in os.environ else urllib.request.urlopen
    resp = (opener if "INSECURE" in os.environ else urllib.request).urlopen(req)
    return json.loads(resp.read())["access_token"]

def list_ciphers():
    token = get_token()
    req = urllib.request.Request(f"{VAULTWARDEN_URL}/api/ciphers")
    req.add_header("Authorization", f"Bearer {token}")
    ctx = urllib.request.HTTPSHandler(context=ssl._create_unverified_context()) if "INSECURE" in os.environ else None
    opener = urllib.request.build_opener(ctx) if "INSECURE" in os.environ else urllib.request
    resp = opener.urlopen(req)
    data = json.loads(resp.read())
    return [{"id": c["id"], "name": c["name"], "username": c.get("login",{}).get("username",""), "uri": c.get("login",{}).get("uris",[{}])[0].get("uri","")} for c in data.get("data",[])]

def get_credential(name):
    ciphers = list_ciphers()
    for c in ciphers:
        if name.lower() in c["name"].lower():
            return c
    return None

def handle(req):
    method, params = req.get("method",""), req.get("params",{})
    if method == "tools/list":
        return {"tools": [
            {"name": "vaultwarden_list_ciphers", "description": "List all credentials", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "vaultwarden_get_credential", "description": "Get credential by name", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
        ]}
    elif method == "tools/call":
        name, args = params.get("name",""), params.get("arguments",{})
        if name == "vaultwarden_list_ciphers":
            return {"content": [{"type": "text", "text": json.dumps(list_ciphers(), indent=2)}]}
        elif name == "vaultwarden_get_credential":
            c = get_credential(args.get("name",""))
            return {"content": [{"type": "text", "text": json.dumps(c, indent=2) if c else "Not found"}]}
        return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}
    elif method == "initialize":
        return {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "vaultwarden-mcp", "version": "1.0.0"}}
    elif method == "notifications/initialized":
        return None
    return {"isError": True, "content": [{"type": "text", "text": f"Unknown method: {method}"}]}

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            msg = json.loads(line)
            result = handle(msg)
            if result is not None:
                resp = json.dumps({"jsonrpc": "2.0", "id": msg.get("id"), "result": result})
                sys.stdout.write(f"Content-Length: {len(resp)}\r\n\r\n{resp}")
                sys.stdout.flush()
        except: pass

if __name__ == "__main__":
    main()

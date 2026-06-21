#!/usr/bin/env python3
"""MCP Server Template — REST API (urllib, ssl verify=false)

Replace: SERVICE_NAME, TOOL_DESCRIPTION, TOOL_PARAMS, API_ENDPOINT, API_AUTH
"""
import sys, json, urllib.request, urllib.error, ssl, os

# Config from ENV
SERVICE_URL = os.environ.get("SERVICE_URL", "http://default:8080")
SERVICE_TOKEN = os.environ.get("SERVICE_TOKEN", "default-token")

# SSL context (verify=False for self-signed certs)
ssl_ctx = ssl._create_unverified_context()

def send_message(msg):
    data = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()

def handle_call_tool(req_id, params):
    name = params.get("name", "")
    args = params.get("arguments", {})
    
    if name == "list_items":
        req = urllib.request.Request(f"{SERVICE_URL}/api/items")
        req.add_header("Authorization", f"Bearer {SERVICE_TOKEN}")
        resp = urllib.request.urlopen(req, context=ssl_ctx)
        items = json.load(resp)
        send_message({"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":json.dumps(items,indent=2)}]}})
    
    elif name == "get_item":
        item_id = args.get("id")
        req = urllib.request.Request(f"{SERVICE_URL}/api/items/{item_id}")
        req.add_header("Authorization", f"Bearer {SERVICE_TOKEN}")
        resp = urllib.request.urlopen(req, context=ssl_ctx)
        item = json.load(resp)
        send_message({"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":json.dumps(item,indent=2)}]}})
    
    else:
        send_message({"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Tool not found: {name}"}})

def main():
    buffer = ""
    for line in sys.stdin:
        buffer += line
        while "\r\n\r\n" in buffer:
            # Extract Content-Length
            header_end = buffer.index("\r\n\r\n") + 4
            headers = buffer[:header_end]
            body = buffer[header_end:]
            
            # Parse Content-Length
            content_length = 0
            for h in headers.split("\r\n"):
                if h.lower().startswith("content-length:"):
                    content_length = int(h.split(":")[1].strip())
            
            if len(body) < content_length:
                break  # Wait for more data
            
            msg = json.loads(body[:content_length])
            buffer = buffer[header_end + content_length:]
            
            req_id = msg.get("id", 0)
            method = msg.get("method", "")
            params = msg.get("params", {})
            
            if method == "initialize":
                send_message({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",  # EXACT string
                        "serverInfo": {"name": "goetschi-SERVICE_NAME", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                })
            elif method == "tools/list":
                send_message({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "list_items",
                                "description": "List all items from SERVICE_NAME",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "get_item",
                                "description": "Get a specific item by ID",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "description": "Item ID"}
                                    },
                                    "required": ["id"]
                                }
                            }
                        ]
                    }
                })
            elif method == "tools/call":
                handle_call_tool(req_id, params)

if __name__ == "__main__":
    main()

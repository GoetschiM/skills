#!/usr/bin/env python3
"""MCP Server Template — subprocess/CLI based (mc, psql, sshpass)

Use this when the service has no REST API but a CLI tool.
"""
import sys, json, subprocess, os

SSH_USER = os.environ.get("SSH_USER", "root")
SSH_PASS = os.environ.get("SSH_PASS", "")
SSH_GAT...os.environ.get("SSH_GATEWAY", "")
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]

def send_message(msg):
    data = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()

def run_ssh(cmd):
    """Run command on remote host via sshpass + ssh"""
    full_cmd = ["sshpass", "-p", SSH_PASS, "ssh"] + SSH_OPTS + [f"{SSH_USER}@{SSH_GATEWAY}", cmd]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=15)
    return result.stdout, result.stderr, result.returncode

def handle_call_tool(req_id, params):
    name = params.get("name", "")
    args = params.get("arguments", {})
    
    if name == "run_query":
        query = args.get("query", "SELECT 1")
        out, err, rc = run_ssh(f"psql -h localhost -U postgres -d db -c \"{query}\"")
        if rc == 0:
            send_message({"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":out}]}})
        else:
            send_message({"jsonrpc":"2.0","id":req_id,"error":{"code":-32000,"message":err}})
    else:
        send_message({"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Tool not found: {name}"}})

def main():
    buffer = ""
    for line in sys.stdin:
        buffer += line
        while "\r\n\r\n" in buffer:
            header_end = buffer.index("\r\n\r\n") + 4
            headers = buffer[:header_end]
            body = buffer[header_end:]
            
            content_length = 0
            for h in headers.split("\r\n"):
                if h.lower().startswith("content-length:"):
                    content_length = int(h.split(":")[1].strip())
            
            if len(body) < content_length:
                break
            
            msg = json.loads(body[:content_length])
            buffer = buffer[header_end + content_length:]
            
            req_id = msg.get("id", 0)
            method = msg.get("method", "")
            params = msg.get("params", {})
            
            if method == "initialize":
                send_message({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",  # EXACT string!
                        "serverInfo": {"name": "goetschi-SERVICE", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                })
            elif method == "tools/list":
                send_message({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"tools": [...]}
                })
            elif method == "tools/call":
                handle_call_tool(req_id, params)

if __name__ == "__main__":
    main()

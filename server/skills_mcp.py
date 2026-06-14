#!/usr/bin/env python3
"""
Goetschi Labs Skill-Marketplace MCP Server
===========================================
Bietet Tools für Skill-Suche, Installation und Publishing.
Lauft als MCP-Server (STDIO) für MCPHub oder standalone HTTP.

ENV:
- SKILLS_REPO_PATH: Pfad zum geklonten skills-Repo (default: /app/skills)
- MCP_TOKEN: Optionaler Auth-Token für HTTP-Mode
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Any

# ── Config ────────────────────────────────────────────────────────────
REPO_PATH = Path(os.environ.get("SKILLS_REPO_PATH", "/app/skills"))
MCP_TOKEN = os.environ.get("MCP_TOKEN", "")


# ── Helpers ────────────────────────────────────────────────────────────
def parse_skill(path: Path) -> dict[str, Any]:
    skill_dir = path.parent
    skill_md = path.read_text(encoding="utf-8")
    
    # YAML-Frontmatter parse
    meta = {}
    if skill_md.startswith("---"):
        parts = skill_md.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
    
    return {
        "name": meta.get("name", skill_dir.name),
        "category": (skill_dir.parent.name if skill_dir.parent.name != "skills" else "uncategorized"),
        "description": meta.get("description", ""),
        "version": meta.get("version", "0.0.1"),
        "tags": meta.get("triggers", meta.get("tags", [])),
        "path": str(skill_dir.relative_to(REPO_PATH)),
        "author": meta.get("author", ""),
        "license": meta.get("license", ""),
        "skill_md_size": len(skill_md),
    }


def find_all_skills() -> list[dict[str, Any]]:
    skills = []
    for skill_md in sorted(REPO_PATH.rglob("SKILL.md")):
        # Überspring archive/ .venv
        parts = skill_md.relative_to(REPO_PATH).parts
        if any(p.startswith(".") or p.startswith(".venv") for p in parts):
            continue
        if "node_modules" in parts:
            continue
        try:
            skills.append(parse_skill(skill_md))
        except Exception as e:
            print(f"⚠️  Skipping {skill_md}: {e}", file=sys.stderr)
    return skills


# ── MCP Tool Implementations ──────────────────────────────────────────
def handle_list_skills(args: dict) -> list:
    """Liste alli verfügbare Skills"""
    skills = find_all_skills()
    query = (args or {}).get("query", "").lower()
    category = (args or {}).get("category", "").lower()
    
    if query:
        skills = [s for s in skills if query in s["name"].lower() or query in s["description"].lower()]
    if category:
        skills = [s for s in skills if s["category"].lower() == category]
    
    return skills


def handle_get_skill(args: dict) -> dict | None:
    """Holt en einzelne Skill mit vollständigem SKILL.md-Content"""
    name = args.get("name", "")
    skills = find_all_skills()
    
    for s in skills:
        if s["name"] == name:
            skill_path = REPO_PATH / s["path"] / "SKILL.md"
            s["content"] = skill_path.read_text(encoding="utf-8")
            return s
    
    return {"error": f"Skill '{name}' nöd gfunde"}


def handle_get_categories(args: dict) -> list:
    """Liste alli Kategorie mit Skill-Count"""
    skills = find_all_skills()
    cats = {}
    for s in skills:
        cat = s["category"]
        cats.setdefault(cat, {"category": cat, "count": 0, "skills": []})
        cats[cat]["count"] += 1
        cats[cat]["skills"].append(s["name"])
    return sorted(cats.values(), key=lambda x: -x["count"])


def handle_pull_from_github(args: dict) -> dict:
    """Pull latest changes from GitHub"""
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_PATH), "pull", "--ff-only"],
            capture_output=True, text=True, timeout=30
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── MCP Router ────────────────────────────────────────────────────────
HANDLERS = {
    "list_skills": handle_list_skills,
    "get_skill": handle_get_skill,
    "get_categories": handle_get_categories,
    "pull_from_github": handle_pull_from_github,
}


def handle_mcp_request(req: dict) -> dict:
    """Verarbeitet en MCP-JSON-RPC Request"""
    method = req.get("method", "")
    args = req.get("params", {})
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "list_skills",
                    "description": "Liste alli verfügbare Skills. Optional: query (Suchbegriff), category (Filter)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Suchbegriff für Name/Description"},
                            "category": {"type": "string", "description": "Kategorie-Filter"}
                        }
                    }
                },
                {
                    "name": "get_skill",
                    "description": "Holt en einzelne Skill mit vollständigem SKILL.md-Content",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string", "description": "Skill-Name (exakt)"}
                        }
                    }
                },
                {
                    "name": "get_categories",
                    "description": "Liste alli Kategorie mit Skill-Count",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "pull_from_github",
                    "description": "Pull latest changes from GitHub (sync MinIO/Coolify)",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        }
    
    if method == "tools/call":
        tool_name = args.get("name", "")
        tool_args = args.get("arguments", {})
        
        if tool_name in HANDLERS:
            try:
                result = HANDLERS[tool_name](tool_args)
                return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            except Exception as e:
                return {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "isError": True }
    
    return {"content": [{"type": "text", "text": json.dumps({"error": f"Unknown method: {method}"})}], "isError": True}


# ── Server Loop ───────────────────────────────────────────────────────
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # HTTP-Mode für standalone
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class MCPHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    req = json.loads(body)
                    resp = handle_mcp_request(req)
                except Exception as e:
                    resp = {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "isError": True}
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode())
            
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "service": "goetschi-labs/skills-mcp",
                    "version": "1.0.0",
                    "status": "ok",
                    "skills_count": len(find_all_skills())
                }).encode())
        
        port = int(os.environ.get("PORT", 8000))
        server = HTTPServer(("0.0.0.0", port), MCPHandler)
        print(f"✅ Skills-MCP Server HTTP mode on :{port}", flush=True)
        server.serve_forever()
    else:
        # STDIO-Mode für MCPHub
        print("✅ Skills-MCP Server STDIO mode", flush=True)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = handle_mcp_request(req)
                print(json.dumps(resp), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), file=sys.stderr)


if __name__ == "__main__":
    main()

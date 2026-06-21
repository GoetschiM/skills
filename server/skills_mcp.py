#!/usr/bin/env python3
"""
Goetschi Labs Skill-Marketplace MCP Server — v3
================================================
Bietet Tools für Skill-Suche, Download, Versionierung und Publishing.
Läuft als MCP-Server (STDIO) für MCPHub oder standalone HTTP.

ENV (via /etc/skills-hub.env):
  SKILLS_REPO_PATH  — Pfad zum geklonten skills-Repo (default: /opt/skills)
  SKILLS_USER       — Login-Benutzername (default: michel)
  SKILLS_PASS       — Login-Passwort
  SKILLS_API_KEY    — Statischer Bearer-Key für Agenten (überlebt Neustarts)
  GITHUB_TOKEN      — GitHub PAT für git push
  PORT              — HTTP-Port (default: 8010)
  SKILLS_AUTOPUSH   — '0' deaktiviert git push bei Upload (default: an)
"""

import os, sys, json, yaml, subprocess, secrets, threading, re, base64, io, zipfile
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs, unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Config ────────────────────────────────────────────────────────────
REPO_PATH    = Path(os.environ.get('SKILLS_REPO_PATH', '/opt/skills'))
SKILLS_USER  = os.environ.get('SKILLS_USER', 'michel')
SKILLS_PASS  = os.environ.get('SKILLS_PASS', 'Louis_one_13')
SKILLS_API_KEY = os.environ.get('SKILLS_API_KEY', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
AUTO_PUSH    = os.environ.get('SKILLS_AUTOPUSH', '1') != '0'
SERVER_VERSION = '3.0.0'

# Session store: token → username  (in-memory, resets on restart)
_sessions: dict[str, str] = {}
_sessions_lock = threading.Lock()

# ── Helpers ────────────────────────────────────────────────────────────
def parse_skill(path: Path) -> dict[str, Any]:
    skill_dir = path.parent
    skill_md  = path.read_text(encoding='utf-8')
    meta: dict = {}
    if skill_md.startswith('---'):
        parts = skill_md.split('---', 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
    rel = str(skill_dir.relative_to(REPO_PATH)).replace('\\', '/')
    files = sorted(
        str(p.relative_to(skill_dir)).replace('\\', '/')
        for p in skill_dir.rglob('*')
        if p.is_file() and '.git' not in p.parts
    )
    return {
        'name':          meta.get('name', skill_dir.name),
        'category':      skill_dir.parent.name if skill_dir.parent.name != 'skills' else 'uncategorized',
        'description':   meta.get('description', ''),
        'version':       str(meta.get('version', '0.0.1')),
        'tags':          meta.get('triggers', meta.get('tags', [])),
        'path':          rel,
        'author':        meta.get('author', ''),
        'license':       meta.get('license', ''),
        'files':         files,
        'file_count':    len(files),
        'download_url':  f'/api/download/{rel}',
        'skill_md_size': len(skill_md),
    }


def find_all_skills() -> list[dict[str, Any]]:
    skills = []
    for skill_md in sorted(REPO_PATH.rglob('SKILL.md')):
        parts = skill_md.relative_to(REPO_PATH).parts
        if any(p.startswith('.') for p in parts):
            continue
        if 'node_modules' in parts:
            continue
        try:
            skills.append(parse_skill(skill_md))
        except Exception as e:
            print(f'WARN Skipping {skill_md}: {e}', file=sys.stderr)
    return skills


def find_skill_by_name(name: str) -> Optional[dict]:
    for s in find_all_skills():
        if s['name'] == name:
            return s
    return None


def _semver(v: str) -> tuple:
    nums = [int(x) for x in re.findall(r'\d+', v or '')[:3]] + [0, 0, 0]
    return tuple(nums[:3])


def _bump_patch(v: str) -> str:
    a, b, c = _semver(v)
    return f'{a}.{b}.{c + 1}'


def _git(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', str(REPO_PATH)] + args,
                          capture_output=True, text=True, timeout=timeout)


def _git_with_token(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a git command, injecting GITHUB_TOKEN into the remote URL if needed."""
    if GITHUB_TOKEN:
        current_url = _git(['remote', 'get-url', 'origin'], timeout=5).stdout.strip()
        if current_url.startswith('https://') and '@' not in current_url:
            token_url = current_url.replace('https://', f'https://{GITHUB_TOKEN}@')
            _git(['remote', 'set-url', 'origin', token_url], timeout=5)
    return _git(args, timeout=timeout)


def _tag_exists(tag: str) -> bool:
    return _git(['tag', '-l', tag]).stdout.strip() == tag


def _set_frontmatter_version(skill_md: Path, version: str) -> None:
    text = skill_md.read_text(encoding='utf-8')
    if text.startswith('---'):
        parts = text.split('---', 2)
        meta = yaml.safe_load(parts[1]) or {}
        meta['version'] = version
        fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
        skill_md.write_text('---\n' + fm + '---' + parts[2], encoding='utf-8')
    else:
        fm = yaml.dump({'version': version}, default_flow_style=False, allow_unicode=True)
        skill_md.write_text('---\n' + fm + '---\n\n' + text, encoding='utf-8')


def _safe_names(name: str, cat: str) -> tuple[str, str]:
    safe_name = ''.join(c for c in name.lower().replace(' ', '-').replace('_', '-')
                        if c.isalnum() or c == '-')
    safe_cat = ''.join(c for c in cat.lower().replace(' ', '-')
                       if c.isalnum() or c in '-_')
    return safe_name, safe_cat or 'uncategorized'


def _extract_zip_safely(zip_b64: str, target_dir: Path) -> None:
    zf = zipfile.ZipFile(io.BytesIO(base64.b64decode(zip_b64)))
    members = [m for m in zf.infolist() if not m.is_dir()]
    # Strip a single common top-level folder if present (e.g. "skillname/...")
    tops = {m.filename.split('/')[0] for m in members if '/' in m.filename}
    strip = (list(tops)[0] + '/') if (len(tops) == 1 and all('/' in m.filename for m in members)) else ''
    base = target_dir.resolve()
    for m in members:
        rel = m.filename[len(strip):] if strip and m.filename.startswith(strip) else m.filename
        if not rel:
            continue
        dest = (target_dir / rel).resolve()
        if dest != base and not str(dest).startswith(str(base) + os.sep):
            raise ValueError(f'Unsicherer Pfad im ZIP: {m.filename}')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(zf.read(m))


def _archive_zip(treeish: str) -> bytes:
    r = subprocess.run(['git', '-C', str(REPO_PATH), 'archive', '--format=zip', treeish],
                       capture_output=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode('utf-8', 'replace'))
    return r.stdout


# ── Tool Implementations ──────────────────────────────────────────────
def handle_list_skills(args: dict) -> list:
    skills   = find_all_skills()
    query    = (args or {}).get('query', '').lower()
    category = (args or {}).get('category', '').lower()
    if query:
        skills = [s for s in skills if query in s['name'].lower() or query in s['description'].lower()]
    if category:
        skills = [s for s in skills if s['category'].lower() == category]
    return skills


def handle_get_skill(args: dict) -> dict:
    name    = args.get('name', '')
    version = args.get('version', '')
    s = find_skill_by_name(name)
    if not s:
        return {'error': f"Skill '{name}' nöd gfunde"}
    if version:
        tag = f"{s['path']}@{version}"
        r = _git(['show', f"{tag}:{s['path']}/SKILL.md"])
        if r.returncode != 0:
            return {'error': f"Version '{version}' vo '{name}' nöd gfunde"}
        s['content'] = r.stdout
        s['version'] = version
    else:
        s['content'] = (REPO_PATH / s['path'] / 'SKILL.md').read_text(encoding='utf-8')
    return s


def handle_get_categories(args: dict) -> list:
    cats: dict = {}
    for s in find_all_skills():
        cat = s['category']
        cats.setdefault(cat, {'category': cat, 'count': 0, 'skills': []})
        cats[cat]['count'] += 1
        cats[cat]['skills'].append(s['name'])
    return sorted(cats.values(), key=lambda x: -x['count'])


def handle_list_versions(args: dict) -> dict:
    name = args.get('name', '')
    s = find_skill_by_name(name)
    if not s:
        return {'error': f"Skill '{name}' nöd gfunde"}
    p = s['path']
    tags = _git(['tag', '-l', f'{p}@*']).stdout.split()
    versions = sorted({t.split('@', 1)[1] for t in tags if '@' in t}, key=_semver)
    log = _git(['log', '--follow', '--format=%h|%ad|%s', '--date=short', '--', f'{p}/SKILL.md']).stdout
    history = []
    for line in log.splitlines():
        if line.count('|') >= 2:
            h, d, subj = line.split('|', 2)
            history.append({'hash': h, 'date': d, 'subject': subj})
    return {'name': s['name'], 'current': s['version'], 'versions': versions, 'history': history}


def handle_download_skill(args: dict) -> dict:
    name    = args.get('name', '')
    version = args.get('version', '')
    fmt     = args.get('format', 'md')
    s = find_skill_by_name(name)
    if not s:
        return {'error': f"Skill '{name}' nöd gfunde"}
    p = s['path']
    if fmt == 'zip':
        treeish = (f'{p}@{version}:{p}' if version else f'HEAD:{p}')
        try:
            data = _archive_zip(treeish)
        except Exception as e:
            return {'error': str(e)}
        url = s['download_url'] + '?format=zip' + (f'&version={version}' if version else '')
        return {'format': 'zip', 'filename': f"{p.split('/')[-1]}.zip",
                'base64': base64.b64encode(data).decode(), 'download_url': url}
    else:
        res = handle_get_skill({'name': name, 'version': version})
        if 'error' in res:
            return res
        return {'format': 'md', 'filename': 'SKILL.md', 'content': res['content'],
                'version': res.get('version', s['version'])}


def handle_pull_from_github(args: dict) -> dict:
    try:
        result = _git_with_token(['pull', '--ff-only'], timeout=30)
        return {'success': result.returncode == 0, 'output': result.stdout + result.stderr}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def handle_upload_skill(args: dict) -> dict:
    name     = args.get('name', '')
    cat      = args.get('category', 'uncategorized')
    content  = args.get('content', '')
    zip_b64  = args.get('zip_b64', '')
    author   = args.get('author', 'anonymous')
    req_ver  = args.get('version', '')

    if not name:
        return {'success': False, 'error': 'Name isch Pflicht'}
    if not content and not zip_b64:
        return {'success': False, 'error': 'content oder zip_b64 isch Pflicht'}

    safe_name, safe_cat = _safe_names(name, cat)
    target_dir  = REPO_PATH / safe_cat / safe_name
    target_file = target_dir / 'SKILL.md'
    rel_path    = f'{safe_cat}/{safe_name}'

    exists = target_file.exists()
    current_ver = None
    if exists:
        try:
            current_ver = parse_skill(target_file)['version']
        except Exception:
            current_ver = '0.0.0'

    # Version bestimmen
    if req_ver:
        if exists and _semver(req_ver) <= _semver(current_ver):
            return {'success': False,
                    'error': f'Version {req_ver} mues grösser sii als die aktuelli {current_ver}'}
        new_ver = req_ver
    else:
        new_ver = _bump_patch(current_ver) if exists else '1.0.0'

    tag = f'{rel_path}@{new_ver}'
    if _tag_exists(tag):
        return {'success': False, 'error': f'Version {new_ver} existiert scho (tag {tag})'}

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        if zip_b64:
            _extract_zip_safely(zip_b64, target_dir)
            if not target_file.exists():
                return {'success': False, 'error': 'ZIP enthaltet kei SKILL.md im Root'}
        else:
            if not content.strip().startswith('---'):
                fm = yaml.dump({'name': safe_name, 'category': safe_cat, 'author': author},
                               default_flow_style=False, allow_unicode=True, sort_keys=False)
                content = '---\n' + fm + '---\n\n' + content
            target_file.write_text(content, encoding='utf-8')

        _set_frontmatter_version(target_file, new_ver)

        _git(['add', str(target_dir)], timeout=15)
        _git(['commit', '-m', f'feat: {safe_name} v{new_ver} ({safe_cat})',
              '--author', f'{author} <{author}@skills.goetschi-labs.ch>'], timeout=15)
        _git(['tag', tag], timeout=10)

        push_ok = None
        push_out = 'autopush deaktiviert'
        if AUTO_PUSH:
            push = _git_with_token(['push'], timeout=40)
            _git_with_token(['push', 'origin', tag], timeout=40)
            push_ok = push.returncode == 0
            push_out = push.stdout + push.stderr

        return {
            'success':    True,
            'name':       safe_name,
            'category':   safe_cat,
            'version':    new_ver,
            'tag':        tag,
            'path':       f'{rel_path}/SKILL.md',
            'previous':   current_ver,
            'git_push':   push_ok,
            'git_output': push_out,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ── MCP Router ────────────────────────────────────────────────────────
HANDLERS = {
    'list_skills':      handle_list_skills,
    'get_skill':        handle_get_skill,
    'get_categories':   handle_get_categories,
    'list_versions':    handle_list_versions,
    'download_skill':   handle_download_skill,
    'pull_from_github': handle_pull_from_github,
    'upload_skill':     handle_upload_skill,
}

MCP_TOOLS = [
    {'name': 'list_skills',
     'description': 'Liste alli verfügbare Skills. Optional: query (Suchbegriff), category (Filter)',
     'inputSchema': {'type': 'object', 'properties': {
         'query':    {'type': 'string', 'description': 'Suchbegriff für Name/Description'},
         'category': {'type': 'string', 'description': 'Kategorie-Filter'}}}},
    {'name': 'get_skill',
     'description': 'Holt en einzelne Skill mit vollständigem SKILL.md-Content. Optional: version (alti Fassig)',
     'inputSchema': {'type': 'object', 'required': ['name'], 'properties': {
         'name':    {'type': 'string', 'description': 'Skill-Name (exakt)'},
         'version': {'type': 'string', 'description': 'Optional: bestimmti Version'}}}},
    {'name': 'get_categories',
     'description': 'Liste alli Kategorie mit Skill-Count',
     'inputSchema': {'type': 'object', 'properties': {}}},
    {'name': 'list_versions',
     'description': 'Zeigt alli Versione und d Historie vo eme Skill',
     'inputSchema': {'type': 'object', 'required': ['name'], 'properties': {
         'name': {'type': 'string'}}}},
    {'name': 'download_skill',
     'description': 'Lädt en Skill abe. format=md (SKILL.md) oder zip (ganze Ordner als base64). Optional: version',
     'inputSchema': {'type': 'object', 'required': ['name'], 'properties': {
         'name':    {'type': 'string'},
         'version': {'type': 'string'},
         'format':  {'type': 'string', 'enum': ['md', 'zip'], 'description': 'md (default) oder zip'}}}},
    {'name': 'pull_from_github',
     'description': 'Pull latest changes from GitHub',
     'inputSchema': {'type': 'object', 'properties': {}}},
    {'name': 'upload_skill',
     'description': 'Upload/Update en Skill (Einzeldatei via content ODER Ordner via zip_b64) → Git Commit + Tag + Push. Versioniert automatisch (semver).',
     'inputSchema': {'type': 'object', 'required': ['name'], 'properties': {
         'name':     {'type': 'string'},
         'category': {'type': 'string'},
         'content':  {'type': 'string', 'description': 'SKILL.md-Inhalt (Einzeldatei)'},
         'zip_b64':  {'type': 'string', 'description': 'base64-ZIP vom ganze Skill-Ordner'},
         'author':   {'type': 'string'},
         'version':  {'type': 'string', 'description': 'Optional: semver; sonst Patch-Bump'}}}},
]


def handle_mcp_request(req: dict) -> dict:
    method = req.get('method', '')
    args   = req.get('params', {})
    if method == 'tools/list':
        return {'tools': MCP_TOOLS}
    if method == 'tools/call':
        tool_name = args.get('name', '')
        tool_args = args.get('arguments', {})
        if tool_name in HANDLERS:
            try:
                result = HANDLERS[tool_name](tool_args)
                return {'content': [{'type': 'text', 'text': json.dumps(result, indent=2, ensure_ascii=False)}]}
            except Exception as e:
                return {'content': [{'type': 'text', 'text': json.dumps({'error': str(e)})}], 'isError': True}
    return {'content': [{'type': 'text', 'text': json.dumps({'error': f'Unknown method: {method}'})}], 'isError': True}


# ── HTTP Server ───────────────────────────────────────────────────────
class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(self.address_string() + ' - - [%s] ' % self.log_date_time_string() + fmt % args, flush=True)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, ctype: str, filename: str, code: int = 200):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', len(data))
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _authorized(token: str) -> bool:
        if not token:
            return False
        if SKILLS_API_KEY and secrets.compare_digest(token, SKILLS_API_KEY):
            return True
        with _sessions_lock:
            return token in _sessions

    def _token_from_request(self, qs: dict) -> str:
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        return (qs.get('token', [''])[0]) if qs else ''

    def _check_auth(self) -> bool:
        return self._authorized(self._token_from_request({}))

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)

        static = {
            '/':            ('frontend/index.html', 'text/html; charset=utf-8'),
            '/index.html':  ('frontend/index.html', 'text/html; charset=utf-8'),
            '/style.css':   ('frontend/style.css',  'text/css; charset=utf-8'),
            '/app.js':      ('frontend/app.js',     'application/javascript; charset=utf-8'),
            '/favicon.ico': ('frontend/favicon.svg', 'image/svg+xml'),
        }
        if path in static:
            rel_path, ctype = static[path]
            file_path = REPO_PATH / rel_path
            if file_path.exists():
                body = file_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', len(body))
                self._cors()
                self.end_headers()
                self.wfile.write(body)
            else:
                self._send_json({'error': f'File not found: {rel_path}'}, 404)
            return

        # Download — auth via header bearer ODER ?token=
        if path.startswith('/api/download/'):
            if not self._authorized(self._token_from_request(qs)):
                self._send_json({'error': 'Unauthorized'}, 401); return
            rel = unquote(path[len('/api/download/'):]).strip('/')
            fmt = qs.get('format', ['md'])[0]
            version = qs.get('version', [''])[0]
            skill_dir = REPO_PATH / rel
            if not (skill_dir / 'SKILL.md').exists() and not version:
                self._send_json({'error': 'Skill nöd gfunde'}, 404); return
            try:
                if fmt == 'zip':
                    treeish = f'{rel}@{version}:{rel}' if version else f'HEAD:{rel}'
                    self._send_bytes(_archive_zip(treeish), 'application/zip',
                                     f"{rel.split('/')[-1]}.zip")
                else:
                    if version:
                        r = _git(['show', f'{rel}@{version}:{rel}/SKILL.md'])
                        if r.returncode != 0:
                            self._send_json({'error': 'Version nöd gfunde'}, 404); return
                        data = r.stdout.encode('utf-8')
                    else:
                        data = (skill_dir / 'SKILL.md').read_bytes()
                    self._send_bytes(data, 'text/markdown; charset=utf-8', 'SKILL.md')
            except Exception as e:
                self._send_json({'error': str(e)}, 500)
            return

        # Versions list — convenience GET
        if path.startswith('/api/versions/'):
            if not self._authorized(self._token_from_request(qs)):
                self._send_json({'error': 'Unauthorized'}, 401); return
            rel = unquote(path[len('/api/versions/'):]).strip('/')
            name = (REPO_PATH / rel).name
            self._send_json(handle_list_versions({'name': name}))
            return

        if path.startswith('/api/'):
            info = {
                'service':      'goetschi-labs/skills-mcp',
                'version':      SERVER_VERSION,
                'status':       'ok',
                'skills_count': len(find_all_skills()),
                'github_token': bool(GITHUB_TOKEN),
                'api_key':      bool(SKILLS_API_KEY),
                'autopush':     AUTO_PUSH,
            }
            # Den echten Key nur an authentifizierte Clients (Frontend-Login/Agent) ausliefern
            if self._check_auth() and SKILLS_API_KEY:
                info['api_key_value'] = SKILLS_API_KEY
            self._send_json(info)
            return

        self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        path   = urlparse(self.path).path

        if path == '/api/login':
            try:
                data = json.loads(body)
                u, p = data.get('username', ''), data.get('password', '')
                if u == SKILLS_USER and p == SKILLS_PASS:
                    token = secrets.token_urlsafe(32)
                    with _sessions_lock:
                        _sessions[token] = u
                    self._send_json({'ok': True, 'token': token, 'username': u})
                else:
                    self._send_json({'ok': False, 'error': 'Falschi Credentials'}, 401)
            except Exception as e:
                self._send_json({'ok': False, 'error': str(e)}, 400)
            return

        if not self._check_auth():
            self._send_json({'error': 'Unauthorized'}, 401)
            return

        try:
            if path == '/api/upload':
                self._send_json(handle_upload_skill(json.loads(body)))
            elif path in ('/', '/api/rpc'):
                self._send_json(handle_mcp_request(json.loads(body)))
            else:
                self._send_json({'error': f'Unknown endpoint: {path}'}, 404)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)


# ── Main ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'http':
        port = int(os.environ.get('PORT', 8010))
        server = HTTPServer(('0.0.0.0', port), MCPHandler)
        gh = 'on' if GITHUB_TOKEN else 'off'
        key = 'on' if SKILLS_API_KEY else 'off'
        print(f'OK Skills Hub v{SERVER_VERSION} - port {port} - user={SKILLS_USER} - '
              f'GitHub:{gh} - APIKey:{key} - autopush:{AUTO_PUSH}', flush=True)
        server.serve_forever()
    else:
        print('OK Skills-MCP Server STDIO mode', flush=True)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                print(json.dumps(handle_mcp_request(json.loads(line))), flush=True)
            except Exception as e:
                print(json.dumps({'error': str(e)}), file=sys.stderr)


if __name__ == '__main__':
    main()

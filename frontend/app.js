/* ════════════════════════════════════════════════
   Skills Hub v3 — Goetschi Labs
   ════════════════════════════════════════════════ */

const STORAGE_KEY_TOK = 'sh_tok';
const STORAGE_KEY_USR = 'sh_usr';

let sessionToken  = null;
let allSkills     = [];
let allCats       = [];
let activeCategory = '';
let currentSkillContent = '';
let currentSkill = null;
let uploadMode = 'single';
let pendingZipB64 = '';
let searchDebounce = null;

// ── CATEGORY COLOR MAP ────────────────────────
const CAT_COLORS = {
  'devops':               '#3b82f6',
  'creative':             '#a855f7',
  'mlops':                '#06b6d4',
  'telephony':            '#f97316',
  'productivity':         '#22c55e',
  'research':             '#ec4899',
  'software-development': '#eab308',
  'knowledge-management': '#14b8a6',
  'finance':              '#10b981',
  'data':                 '#0ea5e9',
  'security':             '#f43f5e',
  'networking':           '#8b5cf6',
  'monitoring':           '#f59e0b',
  'automation':           '#34d399',
  'ai':                   '#818cf8',
  'writing':              '#fb7185',
  'communication':        '#38bdf8',
};

function catColor(cat) {
  return CAT_COLORS[cat] || '#6b7280';
}

// ── API LAYER ─────────────────────────────────

async function apiFetch(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: {
      'Authorization': `Bearer ${sessionToken}`,
      ...(opts.headers || {}),
    },
  });
  if (res.status === 401) { logout(); throw new Error('Session abgelaufen'); }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiPost(path, data) {
  return apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

async function mcpCall(toolName, args = {}) {
  const data = await apiPost('/', {
    jsonrpc: '2.0', id: 1,
    method: 'tools/call',
    params: { name: toolName, arguments: args },
  });
  if (data.error) throw new Error(data.error.message || 'MCP error');
  const text = data.content?.[0]?.text;
  return text ? JSON.parse(text) : null;
}

// ── AUTH ──────────────────────────────────────

function checkAuth() {
  const tok = sessionStorage.getItem(STORAGE_KEY_TOK);
  const usr = sessionStorage.getItem(STORAGE_KEY_USR);
  if (tok) {
    sessionToken = tok;
    document.getElementById('sidebar-username').textContent = usr || 'User';
    showApp();
    initApp();
    return true;
  }
  showLogin();
  return false;
}

async function login(username, password) {
  const errEl = document.getElementById('login-error');
  const btn   = document.getElementById('login-btn');
  errEl.classList.add('hidden');
  btn.textContent = 'Anmelden…';
  btn.disabled = true;
  try {
    const data = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(r => r.json());

    if (data.ok && data.token) {
      sessionToken = data.token;
      sessionStorage.setItem(STORAGE_KEY_TOK, data.token);
      sessionStorage.setItem(STORAGE_KEY_USR, username);
      document.getElementById('sidebar-username').textContent = username;
      showApp();
      initApp();
    } else {
      errEl.textContent = data.error || 'Falscher Benutzername oder Passwort.';
      errEl.classList.remove('hidden');
    }
  } catch (e) {
    errEl.textContent = 'Server nicht erreichbar: ' + e.message;
    errEl.classList.remove('hidden');
  } finally {
    btn.textContent = 'Anmelden';
    btn.disabled = false;
  }
}

function logout() {
  sessionStorage.removeItem(STORAGE_KEY_TOK);
  sessionStorage.removeItem(STORAGE_KEY_USR);
  sessionToken  = null;
  allSkills     = [];
  allCats       = [];
  activeCategory = '';
  showLogin();
  toast('Abgemeldet', 'info');
}

function showLogin() {
  document.getElementById('login-screen').classList.add('active');
  document.getElementById('app-shell').classList.remove('active');
  document.getElementById('app-shell').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
}

function showApp() {
  document.getElementById('login-screen').classList.remove('active');
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-shell').classList.add('active');
  document.getElementById('app-shell').style.display = 'flex';
}

// ── APP INIT ──────────────────────────────────

async function initApp() {
  try {
    const status = await apiFetch('/api/');
    document.getElementById('stat-total').textContent   = status.skills_count ?? '—';
    document.getElementById('stat-version').textContent = status.version || '—';
    document.getElementById('stat-github').textContent  = status.github_token ? '✓ OK' : '✗ Fehlt';
    document.getElementById('stat-github').style.color  = status.github_token ? 'var(--green)' : 'var(--red)';
    document.getElementById('brand-count').textContent  = `${status.skills_count || 0} Skills`;
    renderAgentCard(status);
  } catch (e) {
    console.error('Status load error:', e);
  }

  try {
    allCats = await mcpCall('get_categories');
    document.getElementById('stat-cats').textContent = allCats.length;
    renderSidebarCats(allCats);
    renderCatGrid(allCats);
    populateCatFilter(allCats);
  } catch (e) {
    console.error('Categories error:', e);
  }

  try {
    allSkills = await mcpCall('list_skills');
    renderRecentGrid(allSkills.slice(0, 8));
  } catch (e) {
    console.error('Skills error:', e);
  }
}

// ── VIEWS ─────────────────────────────────────

function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.getElementById('view-' + name)?.classList.add('active');
  document.querySelector(`.nav-item[data-view="${name}"]`)?.classList.add('active');
  if (name === 'browse') renderBrowse();
}

// ── SIDEBAR CATS ──────────────────────────────

function renderSidebarCats(cats) {
  const el = document.getElementById('sidebar-cats');
  el.innerHTML = cats.map(c => {
    const name = c.category || c;
    const cnt  = c.count || '';
    const col  = catColor(name);
    return `<div class="cat-item" data-cat="${esc(name)}" onclick="filterByCategory('${esc(name)}')" title="${esc(name)}">
      <span class="cat-dot" style="background:${col}"></span>
      <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(name)}</span>
      <span class="cat-count">${cnt}</span>
    </div>`;
  }).join('');
}

function filterByCategory(cat) {
  activeCategory = cat;
  document.querySelectorAll('.cat-item').forEach(el => {
    el.classList.toggle('active', el.dataset.cat === cat);
  });
  document.getElementById('cat-filter').value = cat;
  switchView('browse');
}

// ── DASHBOARD ─────────────────────────────────

function renderCatGrid(cats) {
  document.getElementById('cat-grid').innerHTML = cats.map(c => {
    const name = c.category || c;
    const cnt  = c.count || '';
    const col  = catColor(name);
    return `<div class="cat-tile" data-cat="${esc(name)}" onclick="filterByCategory('${esc(name)}')" title="${esc(name)}">
      <div class="cat-tile-name">${esc(name)}</div>
      <div class="cat-tile-count" style="color:${col}">${cnt}</div>
    </div>`;
  }).join('');
}

function renderRecentGrid(skills) {
  document.getElementById('recent-grid').innerHTML = skills.map(s => skillCard(s)).join('');
}

// ── BROWSE ────────────────────────────────────

function renderBrowse() {
  const q   = document.getElementById('browse-search').value.trim().toLowerCase();
  const cat = document.getElementById('cat-filter').value;
  const srt = document.getElementById('sort-select').value;

  if (!allSkills.length) {
    document.getElementById('browse-grid').innerHTML = [1,2,3,4,5,6].map(() => '<div class="skeleton-card"></div>').join('');
    mcpCall('list_skills').then(skills => {
      allSkills = skills;
      renderBrowse();
    }).catch(e => toast('Fehler: ' + e.message, 'error'));
    return;
  }

  let filtered = allSkills;
  if (cat) filtered = filtered.filter(s => s.category === cat);
  if (q)   filtered = filtered.filter(s =>
    (s.name || '').toLowerCase().includes(q) ||
    (s.description || '').toLowerCase().includes(q) ||
    (s.tags || []).some(t => t.toLowerCase().includes(q))
  );

  if (srt === 'cat') {
    filtered = [...filtered].sort((a,b) => (a.category||'').localeCompare(b.category||'') || (a.name||'').localeCompare(b.name||''));
  } else {
    filtered = [...filtered].sort((a,b) => (a.name||'').localeCompare(b.name||''));
  }

  const grid  = document.getElementById('browse-grid');
  const empty = document.getElementById('browse-empty');
  const badge = document.getElementById('browse-count');
  const desc  = document.getElementById('browse-filter-desc');

  badge.textContent = filtered.length;
  desc.textContent  = cat ? `Kategorie: ${cat}` : 'Alle Kategorien';
  if (q) desc.textContent += ` · Suche: "${q}"`;

  if (!filtered.length) {
    grid.innerHTML = '';
    empty.classList.remove('hidden');
  } else {
    empty.classList.add('hidden');
    grid.innerHTML = filtered.map(s => skillCard(s)).join('');
  }
}

function populateCatFilter(cats) {
  const sel = document.getElementById('cat-filter');
  const datalist = document.getElementById('cat-datalist');
  const opts = cats.map(c => {
    const name = c.category || c;
    return `<option value="${esc(name)}">${esc(name)}</option>`;
  }).join('');
  sel.innerHTML = '<option value="">Alle Kategorien</option>' + opts;
  if (datalist) datalist.innerHTML = opts;
}

// ── SKILL CARD ────────────────────────────────

function skillCard(s) {
  const col  = catColor(s.category || '');
  const tags = (s.tags || []).slice(0, 4).map(t =>
    `<span class="tag-pill" onclick="filterByTag('${esc(t)}', event)">${esc(t)}</span>`
  ).join('');
  return `<div class="skill-card" data-cat="${esc(s.category||'')}" onclick="showDetail('${esc(s.name||'')}')">
    <div class="skill-card-name">${esc(s.name || 'Unnamed')}</div>
    <div class="skill-card-desc">${esc(s.description || 'Keine Beschreibung.')}</div>
    ${tags ? `<div class="skill-tags">${tags}</div>` : ''}
    <div class="skill-card-footer">
      <span class="skill-cat-badge" style="color:${col};border-color:${col}30;background:${col}12">${esc(s.category||'—')}</span>
      <span class="skill-ver">v${esc(s.version||'?')}</span>
    </div>
  </div>`;
}

function filterByTag(tag, event) {
  event.stopPropagation();
  document.getElementById('browse-search').value = tag;
  document.getElementById('global-search').value = tag;
  activeCategory = '';
  document.getElementById('cat-filter').value = '';
  switchView('browse');
}

// ── DETAIL PANEL ──────────────────────────────

async function showDetail(skillName) {
  const overlay = document.getElementById('detail-overlay');
  const panel   = document.getElementById('detail-panel');

  document.getElementById('panel-title').textContent = skillName;
  document.getElementById('panel-category-badge').textContent = '…';
  document.getElementById('panel-version').textContent = '';
  document.getElementById('panel-tags').innerHTML = '';
  document.getElementById('panel-body').innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-3)">Wird geladen…</div>';
  currentSkillContent = '';
  currentSkill = null;
  document.getElementById('panel-version-select').classList.add('hidden');
  document.getElementById('panel-history').classList.add('hidden');

  overlay.classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  try {
    const skill = await mcpCall('get_skill', { name: skillName });
    currentSkillContent = skill.content || '';
    currentSkill = skill;

    const col = catColor(skill.category || '');
    const badge = document.getElementById('panel-category-badge');
    badge.textContent = skill.category || '—';
    badge.style.background = col + '15';
    badge.style.color       = col;
    badge.style.borderColor = col + '40';

    document.getElementById('panel-title').textContent   = skill.name || skillName;
    document.getElementById('panel-version').textContent = `v${skill.version || '?'}`;

    const tags = (skill.tags || []);
    document.getElementById('panel-tags').innerHTML = tags.map(t =>
      `<span class="tag-pill" onclick="filterByTag('${esc(t)}', event)">${esc(t)}</span>`
    ).join('');

    document.getElementById('panel-body').innerHTML = renderMarkdown(skill.content || '');
    addCopyCodeButtons();
    loadVersions(skill.name);

  } catch (e) {
    document.getElementById('panel-body').innerHTML = `<p style="color:var(--red);padding:20px">Fehler: ${esc(e.message)}</p>`;
    toast('Skill konnte nicht geladen werden', 'error');
  }
}

function closeDetail() {
  const overlay = document.getElementById('detail-overlay');
  overlay.classList.add('hidden');
  document.body.style.overflow = '';
  currentSkillContent = '';
}

function handleOverlayClick(event) {
  if (event.target === document.getElementById('detail-overlay')) {
    closeDetail();
  }
}

function copySkillContent() {
  if (!currentSkillContent) return;
  navigator.clipboard.writeText(currentSkillContent)
    .then(() => toast('SKILL.md kopiert!', 'success'))
    .catch(() => toast('Kopieren fehlgeschlagen', 'error'));
}

function addCopyCodeButtons() {
  document.querySelectorAll('.panel-body pre').forEach(pre => {
    if (pre.querySelector('.copy-code-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-code-btn';
    btn.textContent = 'Kopieren';
    btn.onclick = () => {
      const code = pre.querySelector('code')?.textContent || pre.textContent;
      navigator.clipboard.writeText(code).then(() => {
        btn.textContent = 'Kopiert!';
        setTimeout(() => { btn.textContent = 'Kopieren'; }, 2000);
      });
    };
    pre.appendChild(btn);
  });
}

// ── VERSIONS & DOWNLOAD ───────────────────────

async function loadVersions(skillName) {
  const sel  = document.getElementById('panel-version-select');
  const hist = document.getElementById('panel-history');
  try {
    const v = await mcpCall('list_versions', { name: skillName });
    const versions = (v.versions || []);
    if (versions.length > 1) {
      const cur = currentSkill && currentSkill.version;
      sel.innerHTML = versions.slice().reverse().map(ver =>
        `<option value="${esc(ver)}" ${ver === cur ? 'selected' : ''}>v${esc(ver)}</option>`).join('');
      sel.classList.remove('hidden');
    } else {
      sel.classList.add('hidden');
    }
    const h = (v.history || []).slice(0, 6);
    if (h.length) {
      hist.innerHTML = '<span class="ph-label">Verlauf:</span> ' + h.map(c =>
        `<span class="ph-item" title="${esc(c.hash)}">${esc(c.date)} · ${esc(c.subject)}</span>`).join('');
      hist.classList.remove('hidden');
    }
  } catch (e) { /* Versionierung optional */ }
}

async function loadSkillVersion() {
  const sel = document.getElementById('panel-version-select');
  const ver = sel.value;
  if (!currentSkill) return;
  try {
    const skill = await mcpCall('get_skill', { name: currentSkill.name, version: ver });
    currentSkillContent = skill.content || '';
    document.getElementById('panel-version').textContent = `v${ver}`;
    document.getElementById('panel-body').innerHTML = renderMarkdown(skill.content || '');
    addCopyCodeButtons();
  } catch (e) { toast('Version konnte nicht geladen werden', 'error'); }
}

function downloadCurrent(format) {
  if (!currentSkill) return;
  const verSel  = document.getElementById('panel-version-select');
  const version = (verSel && !verSel.classList.contains('hidden')) ? verSel.value : '';
  const base = currentSkill.download_url || ('/api/download/' + currentSkill.path);
  const url  = base + '?format=' + format + (version ? '&version=' + encodeURIComponent(version) : '');
  const leaf = currentSkill.path.split('/').pop();
  downloadViaBlob(url, format === 'zip' ? leaf + '.zip' : leaf + '-SKILL.md');
}

async function downloadViaBlob(url, filename) {
  try {
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${sessionToken}` } });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast('Download gestartet', 'success');
  } catch (e) { toast('Download fehlgeschlagen: ' + e.message, 'error'); }
}

// ── AGENT CARD ────────────────────────────────

function renderAgentCard(status) {
  const el = document.getElementById('agent-card');
  if (!el) return;
  const base = window.location.origin;
  const key  = status.api_key_value || '<API_KEY aus /etc/skills-hub.env>';
  const curlList = `curl -s -H "Authorization: Bearer ${key}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_skills","arguments":{}}}' \\\n  ${base}/`;
  const curlDl = `curl -s -H "Authorization: Bearer ${key}" \\\n  "${base}/api/download/<kategorie>/<skill>?format=zip" -o skill.zip`;
  el.innerHTML = `
    <div class="agent-head">
      <span class="agent-ico">🤖</span>
      <div><div class="agent-title">Für Agenten</div>
      <div class="agent-sub">Basis-URL & API-Key für automatischen Zugriff (kein Login nötig)</div></div>
    </div>
    <div class="agent-row">
      <span class="agent-k">Basis-URL</span>
      <code class="agent-v" id="ag-base">${esc(base)}</code>
      <button class="mini-copy" onclick="copyText(document.getElementById('ag-base').textContent)">⎘</button>
    </div>
    <div class="agent-row">
      <span class="agent-k">API-Key</span>
      <code class="agent-v" id="ag-key">${esc(key)}</code>
      <button class="mini-copy" onclick="copyText(document.getElementById('ag-key').textContent)">⎘</button>
    </div>
    <div class="agent-snip-head">Skills auflisten (MCP JSON-RPC)</div>
    <pre class="agent-snip"><code>${escHtml(curlList)}</code><button class="copy-code-btn" onclick="copyText(this.parentElement.querySelector('code').textContent)">Kopieren</button></pre>
    <div class="agent-snip-head">Skill als ZIP laden</div>
    <pre class="agent-snip"><code>${escHtml(curlDl)}</code><button class="copy-code-btn" onclick="copyText(this.parentElement.querySelector('code').textContent)">Kopieren</button></pre>
    <div class="agent-tools">Tools: <code>list_skills</code> <code>get_skill</code> <code>list_versions</code> <code>download_skill</code> <code>upload_skill</code> <code>get_categories</code></div>`;
  el.classList.remove('hidden');
}

function copyText(txt) {
  navigator.clipboard.writeText(txt)
    .then(() => toast('Kopiert!', 'success'))
    .catch(() => toast('Kopieren fehlgeschlagen', 'error'));
}

// ── UPLOAD MODE (single / zip) ────────────────

function setUploadMode(mode) {
  uploadMode = mode;
  document.querySelectorAll('.umode').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  document.getElementById('single-content-field').classList.toggle('hidden', mode !== 'single');
  document.getElementById('zip-content-field').classList.toggle('hidden', mode !== 'zip');
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload  = () => resolve(String(r.result).split(',', 2)[1] || '');
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

async function handleZipFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.zip')) { toast('Bitte eine .zip-Datei wählen', 'error'); return; }
  pendingZipB64 = await readFileAsBase64(file);
  document.getElementById('zip-name').textContent = `${file.name} · ${(file.size / 1024).toFixed(0)} KB bereit`;
  document.getElementById('zip-dropzone').classList.add('has-file');
}

// ── GITHUB SYNC ───────────────────────────────

async function syncGitHub() {
  const btn  = document.getElementById('sync-btn');
  const icon = document.getElementById('sync-icon');
  btn.disabled = true;
  btn.classList.add('loading');
  try {
    const result = await mcpCall('pull_from_github');
    if (result.success) {
      toast('GitHub Sync: ' + (result.output || 'OK').trim().slice(0, 100), 'success');
      allSkills = [];
      allCats   = [];
      await initApp();
    } else {
      toast('Sync fehlgeschlagen: ' + (result.error || result.output || '').slice(0, 120), 'error');
    }
  } catch (e) {
    toast('Sync fehlgeschlagen: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.classList.remove('loading');
  }
}

// ── MARKDOWN RENDERER ─────────────────────────

function renderMarkdown(md) {
  if (!md) return '';

  // Strip YAML frontmatter and show as meta badges
  let meta = {};
  let body = md;
  if (md.startsWith('---')) {
    const end = md.indexOf('---', 3);
    if (end > 0) {
      const fm = md.slice(3, end).trim();
      body = md.slice(end + 3).trim();
      fm.split('\n').forEach(line => {
        const m = line.match(/^(\w[\w-]*):\s*(.+)$/);
        if (m) meta[m[1].trim()] = m[2].trim();
      });
    }
  }

  // Meta badges HTML
  const metaFields = ['author','license','version','category','tags'].filter(k => meta[k]);
  let metaHtml = '';
  if (metaFields.length) {
    metaHtml = '<div class="meta-badges">' +
      metaFields.map(k => `<span class="meta-badge"><strong>${k}:</strong> ${esc(meta[k])}</span>`).join('') +
      '</div>';
  }

  // Tables: detect | col | col | rows
  body = body.replace(/(\|.+\|\n)+/g, match => {
    const rows = match.trim().split('\n');
    if (rows.length < 2) return match;
    const header = rows[0];
    const isDivider = rows[1] && /^[\s|:-]+$/.test(rows[1]);
    const dataRows  = isDivider ? rows.slice(2) : rows.slice(1);
    const parseCells = row => row.split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(c => c.trim());
    const thHtml = parseCells(header).map(c => `<th>${esc(c)}</th>`).join('');
    const tdHtml = dataRows.map(r => `<tr>${parseCells(r).map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('');
    return `<table><thead><tr>${thHtml}</tr></thead><tbody>${tdHtml}</tbody></table>`;
  });

  // Escape HTML (except already-produced table tags)
  const protect = [];
  body = body.replace(/<table[\s\S]*?<\/table>/g, match => {
    protect.push(match);
    return `\x00TABLE${protect.length - 1}\x00`;
  });

  // Code blocks (before escaping)
  const codeBlocks = [];
  body = body.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    codeBlocks.push(`<pre><code class="lang-${esc(lang)}">${escHtml(code)}</code></pre>`);
    return `\x00CODE${codeBlocks.length - 1}\x00`;
  });

  // Inline code
  const inlineCodes = [];
  body = body.replace(/`([^`\n]+)`/g, (_, code) => {
    inlineCodes.push(`<code>${escHtml(code)}</code>`);
    return `\x00INLINE${inlineCodes.length - 1}\x00`;
  });

  // HTML escape remaining text
  body = body
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Restore protected blocks (not double-escaped)
  body = body
    .replace(/\x00CODE(\d+)\x00/g, (_, i) => codeBlocks[+i])
    .replace(/\x00INLINE(\d+)\x00/g, (_, i) => inlineCodes[+i])
    .replace(/\x00TABLE(\d+)\x00/g, (_, i) => protect[+i]);

  // Block elements
  body = body
    .replace(/^#{6}\s+(.+)$/gm, '<h6>$1</h6>')
    .replace(/^#{5}\s+(.+)$/gm,  '<h5>$1</h5>')
    .replace(/^#{4}\s+(.+)$/gm,  '<h4>$1</h4>')
    .replace(/^#{3}\s+(.+)$/gm,  '<h3>$1</h3>')
    .replace(/^#{2}\s+(.+)$/gm,  '<h2>$1</h2>')
    .replace(/^#{1}\s+(.+)$/gm,  '<h1>$1</h1>')
    .replace(/^&gt;\s*(.+)$/gm,  '<blockquote>$1</blockquote>')
    .replace(/^---+$/gm,          '<hr>')
    .replace(/^[-*+]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>\n?)+/g, match => `<ul>${match}</ul>`);

  // Inline formatting
  body = body
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>')
    .replace(/\*([^*\n]+?)\*/g,    '<em>$1</em>')
    .replace(/_([^_\n]+?)_/g,      '<em>$1</em>')
    .replace(/~~(.+?)~~/g,         '<del>$1</del>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Paragraphs: blank lines become paragraph breaks
  body = body.replace(/\n{2,}/g, '\n\n');
  const lines = body.split('\n\n');
  body = lines.map(block => {
    const trimmed = block.trim();
    if (!trimmed) return '';
    if (/^<(h[1-6]|ul|ol|li|pre|blockquote|table|hr|div)/.test(trimmed)) return trimmed;
    return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

  return metaHtml + body;
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── TOAST SYSTEM ──────────────────────────────

function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add('fade-out');
    el.addEventListener('animationend', () => el.remove());
  }, 3500);
}

// ── HELPERS ───────────────────────────────────

function esc(str) {
  return String(str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── INIT ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  checkAuth();

  // Login form
  document.getElementById('login-form').addEventListener('submit', e => {
    e.preventDefault();
    login(
      document.getElementById('user-input').value.trim(),
      document.getElementById('pass-input').value,
    );
  });

  // Sidebar nav
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  // Search: global search → browse view
  document.getElementById('global-search').addEventListener('input', e => {
    const q = e.target.value;
    document.getElementById('browse-search').value = q;
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => switchView('browse'), 250);
  });

  // Browse filters
  document.getElementById('browse-search').addEventListener('input', () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(renderBrowse, 200);
  });

  document.getElementById('cat-filter').addEventListener('change', () => {
    activeCategory = document.getElementById('cat-filter').value;
    renderBrowse();
  });

  document.getElementById('sort-select').addEventListener('change', renderBrowse);

  // Sync button
  document.getElementById('sync-btn').addEventListener('click', syncGitHub);

  // Upload form
  document.getElementById('upload-form').addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('upload-btn');
    const res = document.getElementById('upload-result');
    btn.disabled = true;
    btn.innerHTML = '<span>Uploading…</span>';
    res.classList.add('hidden');

    const finishBtn = () => { btn.disabled = false; btn.innerHTML = '<span>⬆ Skill hochladen</span>'; };

    const tagsRaw = document.getElementById('upload-tags').value;
    const tags    = tagsRaw ? tagsRaw.split(',').map(t => t.trim()).filter(Boolean) : [];
    const verRaw  = document.getElementById('upload-version').value.trim();

    const data = {
      name:        document.getElementById('upload-name').value.trim(),
      category:    document.getElementById('upload-category').value.trim(),
      description: document.getElementById('upload-description').value.trim(),
      tags,
    };
    if (verRaw) data.version = verRaw;

    if (uploadMode === 'zip') {
      if (!data.name || !data.category || !pendingZipB64) {
        showUploadResult('Name, Kategorie und eine ZIP-Datei sind Pflicht.', false);
        finishBtn(); return;
      }
      data.zip_b64 = pendingZipB64;
    } else {
      data.content = document.getElementById('upload-content').value;
      if (!data.name || !data.category || !data.description || !data.content) {
        showUploadResult('Bitte alle Pflichtfelder ausfüllen.', false);
        finishBtn(); return;
      }
    }

    try {
      const result = await apiPost('/api/upload', data);
      if (result.success === false) throw new Error(result.error || 'Upload fehlgeschlagen');
      const pushed = result.git_push === true;
      const pushTxt = result.git_push === null ? '' : (pushed ? ' · GitHub Push ✓' : ' · GitHub Push fehlgeschlagen (kein Token?)');
      showUploadResult(`✓ "${result.name}" v${result.version} in "${result.category}" gespeichert!` + pushTxt, true);
      e.target.reset();
      document.getElementById('upload-version').value = '1.0.0';
      pendingZipB64 = '';
      document.getElementById('zip-name').textContent = 'Ganzer Skill-Ordner als .zip — inkl. scripts/, references/ …';
      document.getElementById('zip-dropzone').classList.remove('has-file');
      setUploadMode('single');
      allSkills = [];
      toast(`Skill "${result.name}" v${result.version} hochgeladen`, 'success');
    } catch (err) {
      showUploadResult(`Fehler: ${err.message}`, false);
      toast('Upload fehlgeschlagen', 'error');
    } finally {
      finishBtn();
    }
  });

  document.getElementById('upload-clear')?.addEventListener('click', () => {
    document.getElementById('upload-form').reset();
    document.getElementById('upload-version').value = '1.0.0';
    document.getElementById('upload-result').classList.add('hidden');
    pendingZipB64 = '';
    document.getElementById('zip-dropzone')?.classList.remove('has-file');
  });

  // ZIP drag & drop
  const dz = document.getElementById('zip-dropzone');
  const zf = document.getElementById('zip-file');
  if (dz && zf) {
    dz.addEventListener('click', () => zf.click());
    zf.addEventListener('change', () => handleZipFile(zf.files[0]));
    ['dragover', 'dragenter'].forEach(ev => dz.addEventListener(ev, e => {
      e.preventDefault(); dz.classList.add('dragging');
    }));
    ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => {
      e.preventDefault(); dz.classList.remove('dragging');
    }));
    dz.addEventListener('drop', e => {
      const f = e.dataTransfer?.files?.[0];
      if (f) handleZipFile(f);
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      if (!document.getElementById('detail-overlay').classList.contains('hidden')) {
        closeDetail();
      }
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      document.getElementById('global-search').focus();
      document.getElementById('global-search').select();
    }
  });
});

function showUploadResult(msg, success) {
  const el = document.getElementById('upload-result');
  el.textContent = msg;
  el.className = 'upload-result ' + (success ? 'success' : 'error');
  el.classList.remove('hidden');
}

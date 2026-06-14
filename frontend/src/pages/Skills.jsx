import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'

export default function Skills() {
  const [skills, setSkills] = useState([])
  const [cats, setCats] = useState([])
  const [searchParams, setSearchParams] = useSearchParams()
  const activeCat = searchParams.get('cat') || ''
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/rpc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/call', params: { name: 'list_skills', arguments: {} }, id: 1 })
    }).then(r => r.json()).then(res => {
      const text = res?.result?.content?.[0]?.text
      if (text) setSkills(JSON.parse(text))
    })
    fetch('/api/rpc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/call', params: { name: 'get_categories', arguments: {} }, id: 2 })
    }).then(r => r.json()).then(res => {
      const text = res?.result?.content?.[0]?.text
      if (text) setCats(JSON.parse(text))
    })
  }, [])

  const filtered = activeCat
    ? skills.filter(s => (s.category || '').startsWith(activeCat))
    : skills

  return (
    <div>
      <div className="page-header">
        <h1>Skills</h1>
        <p>{filtered.length} von {skills.length} Skills</p>
      </div>

      <div className="category-filters">
        <button className={!activeCat ? 'active' : ''} onClick={() => setSearchParams({})}>
          Alle
        </button>
        {cats.map(c => (
          <button key={c} className={activeCat === c ? 'active' : ''}
            onClick={() => setSearchParams({ cat: c })}>
            {c}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <div className="icon">🔍</div>
          <p>Kei Skills in dere Kategorie gfunde</p>
        </div>
      ) : (
        <div className="skills-grid">
          {filtered.map(s => (
            <Link key={s.name} to={`/skills/${encodeURIComponent(s.name)}`}
              style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="skill-card">
                <h3>{s.name}</h3>
                <div className="category">{s.category || '—'}</div>
                <div className="desc">{s.description || ''}</div>
                <div className="meta">
                  {s.version && <span className="version">v{s.version}</span>}
                  <span>{s.author || ''}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

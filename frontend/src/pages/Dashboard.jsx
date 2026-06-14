import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [cats, setCats] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/call', params: { name: 'list_skills', arguments: {} }, id: 1 })
      }).then(r => r.json()),
      fetch('/api/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'tools/call', params: { name: 'get_categories', arguments: {} }, id: 2 })
      }).then(r => r.json()),
    ]).then(([skillsRes, catsRes]) => {
      const skills = skillsRes?.result?.content?.[0]?.text
      setStats(skills ? JSON.parse(skills) : [])
      const categories = catsRes?.result?.content?.[0]?.text
      setCats(categories ? JSON.parse(categories) : [])
    })
  }, [])

  if (!stats) return <div className="loading">Lade Skills Hub...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Übersicht über den Goetschi Skills Marketplace</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="label">Skills Gesamt</div>
          <div className="value">{stats.length || '—'}</div>
        </div>
        <div className="stat-card">
          <div className="label">Kategorien</div>
          <div className="value">{cats?.length || '—'}</div>
        </div>
        <div className="stat-card">
          <div className="label">Letztes Update</div>
          <div className="value" style={{ fontSize: 18 }}>{new Date().toLocaleDateString('de-CH')}</div>
        </div>
        <div className="stat-card">
          <div className="label">Repository</div>
          <div className="value" style={{ fontSize: 18 }}>
            <a href="https://github.com/GoetschiM/skills" target="_blank">GitHub →</a>
          </div>
        </div>
      </div>

      {cats && (
        <>
          <div className="page-header">
            <h2>Kategorien</h2>
          </div>
          <div className="skills-grid">
            {cats.map(cat => (
              <div className="skill-card" key={cat}>
                <h3>{cat}</h3>
                <div className="category">Kategorie</div>
                <div className="meta">
                  <a href={`/skills?cat=${encodeURIComponent(cat)}`}>Skills anzeigen →</a>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

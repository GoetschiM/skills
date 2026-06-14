import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

export default function SkillDetail() {
  const { name } = useParams()
  const [skill, setSkill] = useState(null)

  useEffect(() => {
    fetch('/api/rpc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: { name: 'get_skill', arguments: { name } },
        id: 1
      })
    }).then(r => r.json()).then(res => {
      const text = res?.result?.content?.[0]?.text
      if (text) setSkill(JSON.parse(text))
    })
  }, [name])

  if (!skill) return <div className="loading">Lade Skill...</div>

  return (
    <div className="skill-detail">
      <Link to="/skills" className="back">← Zurück zu Skills</Link>
      <h1>{skill.name}</h1>
      <div className="detail-meta">
        <span>📁 {skill.category || '—'}</span>
        {skill.version && <span>🏷️ v{skill.version}</span>}
        {skill.author && <span>✏️ {skill.author}</span>}
        {skill.created && <span>📅 {skill.created}</span>}
      </div>

      {skill.description && (
        <div className="detail-meta" style={{ color: 'var(--text2)', fontSize: 14 }}>
          {skill.description}
        </div>
      )}

      {skill.changelog && skill.changelog.length > 0 && (
        <>
          <h2>Version History</h2>
          <div className="version-list">
            {skill.changelog.map((v, i) => (
              <div className="version-item" key={i}>
                <div className="ver">{v.version}</div>
                <div className="date">{v.date || ''}</div>
                <div className="notes">{v.changes || v.description || ''}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {skill.content && (
        <>
          <h2>Skill-Details</h2>
          <div className="detail-body">
            <ReactMarkdown>{skill.content}</ReactMarkdown>
          </div>
        </>
      )}
    </div>
  )
}

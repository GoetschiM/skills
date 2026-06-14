import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [name, setName] = useState('')
  const [category, setCategory] = useState('')
  const [author, setAuthor] = useState('')
  const [version, setVersion] = useState('1.0.0')
  const [content, setContent] = useState('')
  const [message, setMessage] = useState('')
  const [dragging, setDragging] = useState(false)
  const [success, setSuccess] = useState(false)
  const navigate = useNavigate()
  const fileRef = useRef()

  const handleFile = (f) => {
    setFile(f)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target.result
      setContent(text)
      // Try to extract name from frontmatter
      const match = text.match(/^---\n([\s\S]*?)\n---/)
      if (match) {
        const fm = match[1]
        const n = fm.match(/name:\s*(.+)/)
        const c = fm.match(/category:\s*(.+)/)
        const a = fm.match(/author:\s*(.+)/)
        const v = fm.match(/version:\s*(.+)/)
        if (n) setName(n[1].trim())
        if (c) setCategory(c[1].trim())
        if (a) setAuthor(a[1].trim())
        if (v) setVersion(v[1].trim())
      }
    }
    reader.readAsText(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0])
  }

  const handleUpload = async () => {
    if (!name || !category) {
      setMessage('Name und Kategorie sind Pflichtfelder')
      return
    }

    const skillData = {
      name,
      category,
      author: author || 'anonymous',
      version,
      content
    }

    try {
      // Call the MCP server's upload endpoint
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(skillData)
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setSuccess(true)
        setMessage(`✅ Skill "${name}" erfolgreich hochgeladen!`)
        setTimeout(() => navigate(`/skills/${encodeURIComponent(name)}`), 1500)
      } else {
        setMessage(`❌ Fehler: ${data.error || 'Unknown error'}`)
      }
    } catch (err) {
      setMessage(`❌ Fehler: ${err.message}`)
    }
  }

  if (success) {
    return (
      <div className="empty-state">
        <div className="icon">✅</div>
        <h2>Skill hochgeladen!</h2>
        <p>"{name}" wird jetz aufm Skills Hub azeigt.</p>
      </div>
    )
  }

  return (
    <div className="upload-form">
      <div className="page-header">
        <h1>Skill Upload</h1>
        <p>Lad en neue Skill als SKILL.md ufe</p>
      </div>

      <div className="upload-area"
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={`upload-area ${dragging ? 'dragging' : ''}`}>
        <div className="icon">📤</div>
        <p>{file ? file.name : 'SKILL.md hier rein ziehe oder klicke zum Auswähle'}</p>
        <input type="file" ref={fileRef} accept=".md,.txt" style={{ display: 'none' }}
          onChange={e => e.target.files[0] && handleFile(e.target.files[0])} />
      </div>

      <label>Name *</label>
      <input value={name} onChange={e => setName(e.target.value)} placeholder="z.B. my-awesome-skill" />

      <label>Kategorie *</label>
      <input value={category} onChange={e => setCategory(e.target.value)} placeholder="z.B. devops, mlops" />

      <label>Author</label>
      <input value={author} onChange={e => setAuthor(e.target.value)} placeholder="z.B. Michel G" />

      <label>Version</label>
      <input value={version} onChange={e => setVersion(e.target.value)} placeholder="1.0.0" />

      <label>SKILL.md Content</label>
      <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="---&#10;name: my-skill&#10;category: example&#10;---&#10;&#10;# My Skill&#10;..." />

      <button onClick={handleUpload}>🚀 Skill uploaden</button>

      {message && <div className={message.includes('✅') ? 'upload-success' : 'login-error'}>{message}</div>}
    </div>
  )
}

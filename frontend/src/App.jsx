import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Skills from './pages/Skills'
import SkillDetail from './pages/SkillDetail'
import Upload from './pages/Upload'
import Login from './pages/Login'

const API = '/api'

function requireAuth() {
  const stored = sessionStorage.getItem('skills_auth')
  if (!stored) return null
  try { return JSON.parse(stored) } catch { return null }
}

export default function App() {
  const [auth, setAuth] = useState(requireAuth)
  const loc = useLocation()

  if (!auth) return <Login onLogin={a => { setAuth(a); sessionStorage.setItem('skills_auth', JSON.stringify(a)) }} />

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: '📊' },
    { to: '/skills', label: 'Skills', icon: '🧩' },
    { to: '/upload', label: 'Upload', icon: '📤' },
  ]

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h2>🧩 Skills Hub</h2>
        <p className="subtitle">Goetschi Labs</p>
        <nav>
          {navLinks.map(l => (
            <Link key={l.to} to={l.to}
              className={loc.pathname === l.to ? 'active' : ''}>
              <span className="icon">{l.icon}</span>
              {l.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/skills/:name" element={<SkillDetail />} />
          <Route path="/upload" element={<Upload />} />
        </Routes>
      </main>
    </div>
  )
}

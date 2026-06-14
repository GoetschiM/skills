import { useState } from 'react'

export default function Login({ onLogin }) {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')
  const [err, setErr] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setErr('')
    if (user === 'michel' && pass === 'Louis_one_13') {
      onLogin({ user, role: 'admin' })
    } else {
      setErr('Falscher Benutzername oder Passwort')
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>🧩 Skills Hub</h1>
        <p>Goetschi Labs Skill Marketplace</p>
        <input
          type="text"
          placeholder="Benutzername"
          value={user}
          onChange={e => setUser(e.target.value)}
          autoFocus
        />
        <input
          type="password"
          placeholder="Passwort"
          value={pass}
          onChange={e => setPass(e.target.value)}
        />
        <button type="submit">Anmelden</button>
        {err && <div className="login-error">{err}</div>}
      </form>
    </div>
  )
}

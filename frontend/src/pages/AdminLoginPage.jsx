import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/client'
import './AdminLoginPage.css'

export default function AdminLoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    login(username, password)
      .then(() => navigate('/admin'))
      .catch(() => {
        setError('Invalid username or password')
        setLoading(false)
      })
  }

  return (
    <main className="admin-login">
      <div className="admin-login__card fade-in">
        <h1 className="admin-login__title">Sign in</h1>
        <p className="admin-login__subtitle">RobProject Admin</p>

        {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

        <form onSubmit={handleSubmit} className="admin-login__form">
          <div className="form-group">
            <label className="form-label" htmlFor="username">Username</label>
            <input
              id="username"
              className="form-input"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              className="form-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <button type="submit" className="btn btn-primary admin-login__btn" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </main>
  )
}

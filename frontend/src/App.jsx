import { useState, useEffect } from 'react'
import { runFullReport } from './api'
import LandingForm from './components/LandingForm'
import Dashboard from './components/Dashboard'
import AuthPage from './components/AuthPage'
import AdminPanel from './components/AdminPanel'
import './App.css'

const savedTheme = localStorage.getItem('theme') || 'light'
if (savedTheme === 'dark') {
  document.documentElement.setAttribute('data-theme', 'dark')
} else if (savedTheme === 'light') {
  document.documentElement.setAttribute('data-theme', 'light')
} else {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
}

export default function App() {
  const [state, setState] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [showAdmin, setShowAdmin] = useState(false)
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('sem_user')) || null } catch { return null }
  })
  const [token, setToken] = useState(() => {
    try { return localStorage.getItem('sem_token') || null } catch { return null }
  })
  const [sessionId, setSessionId] = useState(() => {
    try { return sessionStorage.getItem('sem_session_id') || null } catch { return null }
  })
  const [googleEmail, setGoogleEmail] = useState(() => {
    try { return sessionStorage.getItem('sem_google_email') || null } catch { return null }
  })

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')
    const email = params.get('email')
    if (sid) {
      setSessionId(sid)
      setGoogleEmail(email)
      try {
        sessionStorage.setItem('sem_session_id', sid)
        if (email) sessionStorage.setItem('sem_google_email', email)
      } catch {}
      // Auto-login via Google session
      if (email) {
        const API = import.meta.env.VITE_API_URL || ''
        fetch(`${API}/api/auth/google-login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sid, email }),
        }).then(r => r.json()).then(data => {
          if (data.token) {
            localStorage.setItem('sem_token', data.token)
            localStorage.setItem('sem_user', JSON.stringify(data.user))
            setUser(data.user)
            setToken(data.token)
          }
        }).catch(() => {})
      }
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  function handleAuth(userData, userToken) {
    setUser(userData)
    setToken(userToken)
  }

  function handleLogout() {
    localStorage.removeItem('sem_token')
    localStorage.removeItem('sem_user')
    setUser(null)
    setToken(null)
    setState('idle')
    setResult(null)
  }

  async function handleSubmit(data) {
    setState('loading')
    setError(null)
    try {
      const report = await runFullReport(data)
      setResult(report)
      setState('done')
    } catch (e) {
      setError(e.message)
      setState('error')
    }
  }

  function handleReset() {
    setState('idle')
    setResult(null)
    setError(null)
  }

  // Show auth page if not logged in
  if (!user) {
    return <AuthPage onAuth={handleAuth} />
  }

  // Show admin panel
  if (showAdmin && user.email === 'jsvking@gmail.com') {
    return <AdminPanel user={user} token={token} onBack={() => setShowAdmin(false)} />
  }

  if (state === 'done' && result) {
    return (
      <Dashboard
        data={result}
        onReset={handleReset}
        sessionId={sessionId}
        googleEmail={googleEmail}
        user={user}
        onLogout={handleLogout}
        onAdmin={user && user.email === 'jsvking@gmail.com' ? () => setShowAdmin(true) : null}
      />
    )
  }

  return (
    <LandingForm
      onSubmit={handleSubmit}
      loading={state === 'loading'}
      error={error}
      sessionId={sessionId}
      googleEmail={googleEmail}
      user={user}
      onLogout={handleLogout}
      onAdmin={user.email === 'jsvking@gmail.com' ? () => setShowAdmin(true) : null}
    />
  )
}
import { useState, useEffect } from 'react'
import { runFullReport } from './api'
import LandingForm from './components/LandingForm'
import Dashboard from './components/Dashboard'
import './App.css'

// Apply saved theme on load
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
  const [state, setState] = useState(() => {
    // Restore state from sessionStorage
    try {
      const saved = sessionStorage.getItem('sem_state')
      return saved ? 'done' : 'idle'
    } catch { return 'idle' }
  })
  const [result, setResult] = useState(() => {
    try {
      const saved = sessionStorage.getItem('sem_result')
      return saved ? JSON.parse(saved) : null
    } catch { return null }
  })
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(() => {
    try { return sessionStorage.getItem('sem_session_id') || null } catch { return null }
  })
  const [googleEmail, setGoogleEmail] = useState(() => {
    try { return sessionStorage.getItem('sem_google_email') || null } catch { return null }
  })

  // Check for OAuth callback params in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')
    const email = params.get('email')
    if (sid) {
      setSessionId(sid)
      setGoogleEmail(email)
      // Persist to sessionStorage
      try {
        sessionStorage.setItem('sem_session_id', sid)
        if (email) sessionStorage.setItem('sem_google_email', email)
      } catch {}
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  async function handleSubmit(data) {
    setState('loading')
    setError(null)
    try {
      const report = await runFullReport(data)
      setResult(report)
      setState('done')
      // Persist result
      try { sessionStorage.setItem('sem_result', JSON.stringify(report)) } catch {}
      try { sessionStorage.setItem('sem_state', 'done') } catch {}
    } catch (e) {
      setError(e.message)
      setState('error')
    }
  }

  function handleReset() {
    setState('idle')
    setResult(null)
    setError(null)
    try {
      sessionStorage.removeItem('sem_result')
      sessionStorage.removeItem('sem_state')
    } catch {}
  }

  if (state === 'done' && result) {
    return (
      <Dashboard
        data={result}
        onReset={handleReset}
        sessionId={sessionId}
        googleEmail={googleEmail}
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
    />
  )
}

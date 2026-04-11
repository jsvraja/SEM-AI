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
  const [state, setState] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [googleEmail, setGoogleEmail] = useState(null)

  // Check for OAuth callback params in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')
    const email = params.get('email')
    if (sid) {
      setSessionId(sid)
      setGoogleEmail(email)
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

import { useState, useEffect } from 'react'
import { runFullReport } from './api'
import PricingModal from './components/PricingModal'
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
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [showAdmin, setShowAdmin] = useState(false)
  const [featureFlags, setFeatureFlags] = useState({})

  useEffect(() => {
    const API = import.meta.env.VITE_API_URL || 'https://sem-ai-production.up.railway.app'
    fetch(`${API}/api/feature-flags`, { method: 'POST' })
      .then(r => r.json())
      .then(d => setFeatureFlags(d.flags || {}))
      .catch(() => {})
  }, [])
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('sem_user')) || null } catch { return null }
  })
  const [token, setToken] = useState(() => {
    try { return localStorage.getItem('sem_token') || null } catch { return null }
  })
  const [sessionId, setSessionId] = useState(() => {
    try { return localStorage.getItem('sem_session_id') || sessionStorage.getItem('sem_session_id') || null } catch { return null }
  })
  const [googleEmail, setGoogleEmail] = useState(() => {
    try { return sessionStorage.getItem('sem_google_email') || null } catch { return null }
  })

  // Check for invite token in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const inviteToken = params.get('invite')
    if (inviteToken) {
      sessionStorage.setItem('pending_invite', inviteToken)
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')
    const email = params.get('email')
    if (sid) {
      setSessionId(sid)
      setGoogleEmail(email)
      try {
        localStorage.setItem('sem_session_id', sid); sessionStorage.setItem('sem_session_id', sid)
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

  async function handleAuth(userData, userToken) {
    setUser(userData)
    setToken(userToken)
    // Accept pending invite
    const pendingInvite = sessionStorage.getItem('pending_invite')
    if (pendingInvite) {
      sessionStorage.removeItem('pending_invite')
      try {
        const API = import.meta.env.VITE_API_URL || 'https://sem-ai-production.up.railway.app'
        await fetch(`${API}/api/workspaces/accept-invite/${pendingInvite}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${userToken}` },
        })
      } catch(e) { console.error(e) }
    }
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
      // Normalize field names
      const normalizedData = {
        ...data,
        businessDescription: data.businessDescription || data.description || '',
      }
      const report = await runFullReport(normalizedData)
      // Normalize seo_report -> seo
      if (report && report.seo_report && !report.seo) {
        report.seo = report.seo_report
      }
      // Validate report has required fields
      if (!report || report.error || !report.seo) {
        throw new Error(report?.error || report?.message || 'Could not analyse this website. Please check the URL and try again.')
      }
      setResult(report)
      setState('done')
    } catch (e) {
      if (e.message.startsWith('USAGE_LIMIT:')) {
        setShowUpgradeModal(true)
      } else {
        setError(e.message)
      }
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
  if (showUpgradeModal) {
    return <PricingModal onClose={() => setShowUpgradeModal(false)} user={user} token={token} limitReached={true} onPlanUpgraded={(plan) => { setShowUpgradeModal(false); window.location.reload() }} />
  }

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
        featureFlags={featureFlags}
      />
    )
  }

  return (
    <LandingForm
      onSubmit={handleSubmit}
      loading={state === 'loading'}
      error={error}
      onClearError={() => setError(null)}
      sessionId={sessionId}
      googleEmail={googleEmail}
      user={user}
      onLogout={handleLogout}
      onAdmin={user.email === 'jsvking@gmail.com' ? () => setShowAdmin(true) : null}
      featureFlags={featureFlags}
    />
  )
}// Sun May  3 00:47:40 IST 2026

import { useState, useRef } from 'react'
import { Globe, Zap, BarChart3, Target, Search, TrendingUp, Share2, ChevronRight, Loader2, AlertCircle, Bot, Shield } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

export default function LandingForm({ onSubmit, loading, error, onClearError, user, onLogout, onAdmin }) {
  const lockedSite = user?.plan === 'startup' ? (localStorage.getItem('sem_locked_site') || '') : null
  const [url, setUrl] = useState(lockedSite || '')
  const [url, setUrl] = useState(lockedSite || '')
  const [desc, setDesc] = useState('')
  const [keywords, setKeywords] = useState('')
  const [aiDetecting, setAiDetecting] = useState(false)
  const [aiDetected, setAiDetected] = useState(false)
  const [urlError, setUrlError] = useState('')
  const [aiError, setAiError] = useState('')
  const debounceRef = useRef(null)

  function detectUrlType(u) {
    if (!u) return null
    const singlePageExts = ['.html', '.htm', '.php', '.aspx']
    const cleanUrl = u.replace(/https?:\/\//, '').replace(/\/$/, '')
    const path = cleanUrl.split('?')[0]
    if (singlePageExts.some(ext => path.endsWith(ext))) return 'single_page'
    const segments = path.split('/').filter(s => s && s !== '')
    if (segments.length <= 2) return 'whole_site'
    return 'whole_site'
  }

  function isValidUrl(u) {
    if (!u || typeof u !== 'string') return false
    try {
      const parsed = new URL(u.startsWith('http') ? u : 'https://' + u)
      return parsed.hostname.includes('.')
    } catch { return false }
  }

  async function handleUrlBlur() {
    if (!url.trim()) return
    if (!isValidUrl(url.trim())) {
      setUrlError('Please enter a valid website URL (e.g. example.com)')
      return
    }
    setUrlError('')
    if (aiDetected) return
    setAiDetecting(true)
    setAiError('')
    try {
      const fullUrl = url.trim().startsWith('http') ? url.trim() : 'https://' + url.trim()
      const res = await fetch('https://sem-ai-production.up.railway.app/api/detect-business', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: fullUrl })
      })
      const d = await res.json()
      if (d.error) { setAiError('AI could not detect business info. Please fill manually.') }
      else {
        const descVal = d.business_description || d.description || ''
        const kwVal = d.target_keywords || d.keywords || []
        if (descVal && !desc) setDesc(descVal)
        if (kwVal.length && !keywords) setKeywords(Array.isArray(kwVal) ? kwVal.join(', ') : kwVal)
        setAiDetected(true)
      }
    } catch(e) {
      setAiError('AI detection failed. Please fill manually.')
    }
    setAiDetecting(false)
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!isValidUrl(url.trim())) {
      setUrlError('Please enter a valid website URL (e.g. example.com)')
      return
    }
    setUrlError('')
    const fullUrl = url.trim().startsWith('http') ? url.trim() : 'https://' + url.trim()
    const urlType = detectUrlType(fullUrl)
    onSubmit({ url: fullUrl, description: desc.trim(), targetKeywords: keywords.split(',').map(k => k.trim()).filter(Boolean), urlType })
  }

  const leftFeatures = [
    { icon: Search, label: 'SEO Analysis', desc: 'Full site audit with AI recommendations' },
    { icon: Shield, label: 'Site Audit', desc: 'Technical SEO, speed & performance checks' },
    { icon: Zap, label: 'Google Ads', desc: 'Publish & optimise campaigns automatically' },
    { icon: TrendingUp, label: 'AI Traffic', desc: 'Track visitors from ChatGPT, Perplexity & more' },
  ]

  const rightFeatures = [
    { icon: Share2, label: 'Social Media', desc: 'Generate platform-optimised posts with AI' },
    { icon: Target, label: 'Competitors', desc: 'AI-powered competitive intelligence' },
    { icon: Bot, label: 'Auto-Pilot', desc: 'Autonomous AI SEM agent monitoring 24/7' },
  ]

  return (
    <div style={{ height: '100vh', background: 'var(--bg)', color: 'var(--text)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 32px', borderBottom: '1px solid var(--border)', background: 'var(--bg2)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={14} color="white" />
          </div>
          <span style={{ fontSize: '15px', fontWeight: 600, letterSpacing: '-0.01em' }}>SEM AI</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Powered by Sakthivelraja.AI</span>
          <ThemeToggle />
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 600, color: 'white' }}>
                {user.name ? user.name[0].toUpperCase() : user.email[0].toUpperCase()}
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text2)' }}>{user.name || user.email}</span>
              {onAdmin && <button onClick={onAdmin} style={{ fontSize: '11px', color: 'var(--accent)', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: '4px', padding: '3px 8px', cursor: 'pointer' }}>Admin</button>}
              <button onClick={onLogout} style={{ fontSize: '11px', color: 'var(--text3)', background: 'none', border: '1px solid var(--border)', borderRadius: '4px', padding: '3px 8px', cursor: 'pointer' }}>Logout</button>
            </div>
          )}
        </div>
      </header>

      {/* Main */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', padding: '10px 24px', paddingTop: '80px', overflow: 'auto' }}>
        <div style={{ width: '100%', maxWidth: '1100px' }}>

          {/* Heading */}
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', color: 'var(--accent)', fontSize: '12px', fontWeight: 500, marginBottom: '12px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)' }} />
              AI-Powered Marketing Platform
            </div>
            <h1 style={{ fontSize: '30px', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text)', marginBottom: '8px', lineHeight: 1.3 }}>
              Analyse your website. Launch better campaigns.
            </h1>
            <p style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: 1.6 }}>
              AI handles SEO, ads, content and monitoring — all in one platform.
            </p>
          </div>

          {/* 3 Columns */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 440px 1fr', gap: '28px', alignItems: 'start' }}>

            {/* Left */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {leftFeatures.map((f, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px' }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <f.icon size={15} color="var(--accent)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '2px' }}>{f.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', lineHeight: 1.4 }}>{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Center Form */}
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px' }}>
              <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>Website URL</label>
                  <div style={{ position: 'relative' }}>
                    <Globe size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }} />
                    <input type="text" value={url} readOnly={!!lockedSite} style={{ ...(lockedSite ? {background: "var(--bg3)", cursor: "not-allowed", opacity: 0.8} : {}) }} onChange={e => { if(lockedSite) return; setUrl(e.target.value); setAiDetected(false); setDesc(''); setKeywords(''); setAiError(''); setUrlError(''); if (onClearError) onClearError() }}
                      placeholder="https://yourwebsite.com" required
                      style={{ width: '100%', padding: '10px 12px 10px 32px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }}
                      onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                      onBlur={e => { e.target.style.borderColor = urlError ? '#f87171' : 'var(--border)'; handleUrlBlur() }} />
                  </div>
                  {urlError && <div style={{ marginTop: '6px', fontSize: '12px', color: '#f87171', display: 'flex', alignItems: 'center', gap: '4px' }}><AlertCircle size={12} /> {urlError}</div>}
                  {aiError && <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text3)', display: 'flex', alignItems: 'center', gap: '4px' }}><AlertCircle size={12} /> {aiError}</div>}
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>
                    Business Description
                    {aiDetecting && <span style={{ marginLeft: '8px', color: 'var(--accent)', fontSize: '11px' }}>⚡ AI detecting...</span>}
                    {aiDetected && desc && <span style={{ marginLeft: '8px', color: 'var(--green)', fontSize: '11px' }}>✓ AI filled</span>}
                  </label>
                  <input type="text" value={desc} onChange={e => setDesc(e.target.value)}
                    placeholder="e.g. AI automation services for Indian SMEs"
                    style={{ width: '100%', padding: '10px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }}
                    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border)'} />
                </div>

                <div style={{ marginBottom: '48px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>Target Keywords <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(comma separated)</span></label>
                  <input type="text" value={keywords} onChange={e => setKeywords(e.target.value)}
                    placeholder="AI automation, machine learning, data science"
                    style={{ width: '100%', padding: '10px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text)', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }}
                    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border)'} />
                </div>

                {error && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderRadius: '8px', background: 'var(--red-bg)', border: '1px solid rgba(162,45,45,0.2)', color: 'var(--red)', fontSize: '12px', marginBottom: '14px' }}>
                    <AlertCircle size={13} /> {error}
                  </div>
                )}

                <button type="submit" disabled={loading || !url.trim() || aiDetecting}
                  style={{ width: '100%', padding: '11px 16px', background: loading || !url.trim() || aiDetecting ? 'var(--bg3)' : 'var(--accent)', border: 'none', borderRadius: '8px', color: loading || !url.trim() || aiDetecting ? 'var(--text3)' : 'white', fontSize: '14px', fontWeight: 500, cursor: loading || !url.trim() || aiDetecting ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  {loading ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Analysing website...</>
                    : aiDetecting ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> AI detecting business...</>
                    : <>Analyse with AI <ChevronRight size={15} /></>}
                </button>
              </form>
            </div>

            {/* Right */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {rightFeatures.map((f, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px' }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <f.icon size={15} color="var(--accent)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '2px' }}>{f.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', lineHeight: 1.4 }}>{f.desc}</div>
                  </div>
                </div>
              ))}
              <div style={{ padding: '12px', background: 'linear-gradient(135deg, var(--accent-bg), var(--bg2))', border: '1px solid var(--accent-border)', borderRadius: '10px', textAlign: 'center' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', marginBottom: '4px' }}>9 users already onboard</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Join the AI marketing revolution</div>
              </div>
            </div>

          </div>
        </div>
      </main>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

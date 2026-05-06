import { useState, useRef } from 'react'
import { Globe, Zap, BarChart3, Target, Search, TrendingUp, Share2, ChevronRight, Loader2, AlertCircle, Sparkles } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

export default function LandingForm({ onSubmit, loading, error, user, onLogout, onAdmin }) {
  const [url, setUrl] = useState('')
  const [desc, setDesc] = useState('')
  const [keywords, setKeywords] = useState('')
  const [aiDetecting, setAiDetecting] = useState(false)
  const [aiDetected, setAiDetected] = useState(false)

  function detectUrlType(u) {
    if (!u) return null
    const singlePageExts = ['.html', '.htm', '.php', '.aspx', '.asp', '.jsp', '.cfm', '.shtml']
    const cleanUrl = u.replace(/https?:\/\//, '').replace(/\/$/, '')
    const path = cleanUrl.split('?')[0]
    if (singlePageExts.some(ext => path.endsWith(ext))) return 'single_page'
    const segments = path.split('/').filter(s => s && s !== '')
    if (segments.length <= 2) return 'whole_site'
    if (u.trim().endsWith('/')) return 'whole_site'
    if (segments.length >= 4) return 'single_page'
    return 'whole_site'
  }

  const urlType = detectUrlType(url)

  async function handleUrlBlur() {
    const trimmed = url.trim()
    if (!trimmed || aiDetected) return
    if (desc.trim() || keywords.trim()) return
    setAiDetecting(true)
    try {
      const backendUrl = import.meta.env.VITE_API_URL || ''
      const res = await fetch(`${backendUrl}/api/detect-business`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: trimmed }),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.business_description) setDesc(data.business_description)
        if (data.target_keywords && data.target_keywords.length > 0) {
          setKeywords(data.target_keywords.join(', '))
        }
        setAiDetected(true)
      }
    } catch (err) {
      console.error('AI detect failed:', err)
    } finally {
      setAiDetecting(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim()) return
    onSubmit({
      url: url.trim(),
      businessDescription: desc.trim(),
      targetKeywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
      urlType,
    })
  }

  const features = [
    { icon: Search, label: 'SEO Analysis', desc: 'Full site audit with AI recommendations' },
    { icon: Zap, label: 'Google Ads', desc: 'Publish & optimise campaigns automatically' },
    { icon: TrendingUp, label: 'AI Traffic', desc: 'Track visitors from ChatGPT, Perplexity & more' },
    { icon: Share2, label: 'Social Media', desc: 'Generate platform-optimised posts with AI' },
    { icon: Target, label: 'Competitors', desc: 'AI-powered competitive intelligence' },
    { icon: BarChart3, label: 'SEMA Agent', desc: 'Autonomous AI SEM agent monitoring 24/7' },
  ]

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 32px', borderBottom: '1px solid var(--border)', background: 'var(--bg2)' }}>
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
              {onAdmin && (
                <button onClick={onAdmin} style={{ fontSize: '11px', color: 'var(--accent)', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: '4px', padding: '3px 8px', cursor: 'pointer' }}>Admin</button>
              )}
              <button onClick={onLogout} style={{ fontSize: '11px', color: 'var(--text3)', background: 'none', border: '1px solid var(--border)', borderRadius: '4px', padding: '3px 8px', cursor: 'pointer' }}>Logout</button>
            </div>
          )}
        </div>
      </header>

      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
        <div style={{ width: '100%', maxWidth: '1100px', display: 'grid', gridTemplateColumns: '1fr 480px 1fr', gap: '40px', alignItems: 'center' }}>

          {/* Left Features */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: '20px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', color: 'var(--accent)', fontSize: '12px', fontWeight: 500, marginBottom: '12px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)' }} />
                AI-Powered Marketing Platform
              </div>
              <h1 style={{ fontSize: '26px', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text)', lineHeight: 1.3, marginBottom: '8px' }}>
                Analyse your website.<br />Launch better campaigns.
              </h1>
              <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.6 }}>
                AI handles SEO, ads, content and monitoring — all in one platform.
              </p>
            </div>
            {features.slice(0, 3).map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <f.icon size={15} color='var(--accent)' />
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '2px' }}>{f.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', lineHeight: 1.4 }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Center Form */}
          <div style={{ width: '100%' }}>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px' }}>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px' }}>
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>Website URL</label>
                <div style={{ position: 'relative' }}>
                  <Globe size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }} />
                  <input
                    type="text" value={url}
                    onChange={e => { setUrl(e.target.value); setAiDetected(false) }}

                    placeholder="https://yourwebsite.com"
                    required
                    style={{ width: '100%', padding: '10px 12px 10px 32px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
                    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                    onBlur={e => { e.target.style.borderColor = 'var(--border)'; handleUrlBlur() }}
                  />
                </div>
                {url && urlType && (
                  <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                    {urlType === 'single_page' ? (
                      <><span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--purple-bg)', color: 'var(--purple)', fontWeight: 500 }}>📄 Single Page</span><span style={{ color: 'var(--text3)' }}>Deep analysis of this specific page</span></>
                    ) : (
                      <><span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)', fontWeight: 500 }}>🌐 Whole Site</span><span style={{ color: 'var(--text3)' }}>Site-wide analysis + auto site audit</span></>
                    )}
                  </div>
                )}
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>
                  Business Description
                  {aiDetecting && <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent)', fontSize: '11px' }}><Loader2 size={10} style={{ animation: 'spin 1s linear infinite' }} /> AI detecting...</span>}
                  {aiDetected && !aiDetecting && <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--green)', fontSize: '11px' }}><Sparkles size={10} /> AI filled</span>}
                </label>
                <input
                  type="text" value={desc}
                  onChange={e => setDesc(e.target.value)}
                  placeholder={aiDetecting ? 'AI is detecting your business...' : 'e.g. AI automation services for Indian SMEs'}
                  style={{ width: '100%', padding: '10px 12px', background: aiDetected && desc ? 'var(--accent-bg)' : 'var(--bg)', border: `1px solid ${aiDetected && desc ? 'var(--accent-border)' : 'var(--border)'}`, borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: '13px', outline: 'none', transition: 'all 0.2s' }}
                  onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>
                  Target Keywords <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(comma separated)</span>
                  {aiDetected && !aiDetecting && keywords && <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--green)', fontSize: '11px' }}><Sparkles size={10} /> AI filled</span>}
                </label>
                <input
                  type="text" value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                  placeholder={aiDetecting ? 'AI is detecting keywords...' : 'AI automation, machine learning, data science'}
                  style={{ width: '100%', padding: '10px 12px', background: aiDetected && keywords ? 'var(--accent-bg)' : 'var(--bg)', border: `1px solid ${aiDetected && keywords ? 'var(--accent-border)' : 'var(--border)'}`, borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: '13px', outline: 'none', transition: 'all 0.2s' }}
                  onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
                {aiDetected && <p style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '5px' }}>✏️ AI detected these — you can edit before analysing</p>}
              </div>

              {error && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderRadius: 'var(--radius)', background: 'var(--red-bg)', border: '1px solid rgba(162,45,45,0.2)', color: 'var(--red)', fontSize: '12px', marginBottom: '14px' }}>
                  <AlertCircle size={13} /> {error}
                </div>
              )}

              <button type="submit" disabled={loading || !url.trim() || aiDetecting} style={{ width: '100%', padding: '11px 16px', background: loading || !url.trim() || aiDetecting ? 'var(--bg3)' : 'var(--accent)', border: 'none', borderRadius: 'var(--radius)', color: loading || !url.trim() || aiDetecting ? 'var(--text3)' : 'white', fontSize: '14px', fontWeight: 500, cursor: loading || !url.trim() || aiDetecting ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', transition: 'all 0.15s' }}>
                {loading ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Analysing website...</>
                  : aiDetecting ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> AI detecting business...</>
                  : <>Analyse with AI <ChevronRight size={15} /></>}
              </button>
            </form>
          </div>

          </div>
          </div>

          {/* Right Features */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ marginBottom: '8px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>Everything you need</div>
              <div style={{ fontSize: '12px', color: 'var(--text3)' }}>One platform to rule your marketing</div>
            </div>
            {features.slice(3).map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <f.icon size={15} color='var(--accent)' />
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
      </main>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

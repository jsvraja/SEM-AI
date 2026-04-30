import { useState } from 'react'
import { Globe, Zap, BarChart3, Target, Search, TrendingUp, Share2, ChevronRight, Loader2, AlertCircle } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

export default function LandingForm({ onSubmit, loading, error }) {
  const [url, setUrl] = useState('')
  const [desc, setDesc] = useState('')
  const [keywords, setKeywords] = useState('')

  function detectUrlType(u) {
    if (!u) return null
    const singlePageExts = ['.html', '.htm', '.php', '.aspx', '.asp', '.jsp', '.cfm', '.shtml']
    const cleanUrl = u.replace(/https?:\/\//, '').replace(/\/$/, '')
    const path = cleanUrl.split('?')[0]
    // Single page if has file extension
    if (singlePageExts.some(ext => path.endsWith(ext))) return 'single_page'
    // Whole site if it's just a domain or domain/section
    const segments = path.split('/').filter(s => s && s !== '')
    // domain only or domain/section = whole site
    // domain/section/page.html = single page (already caught above)
    // domain/products/ad-manager/ = whole site (it's a section, ends with /)
    if (segments.length <= 2) return 'whole_site'
    // 3+ segments but ends with / = it's a section/whole site
    if (u.trim().endsWith('/')) return 'whole_site'
    // 3+ segments without trailing slash and no extension = could be single page
    if (segments.length >= 4) return 'single_page'
    return 'whole_site'
  }

  const urlType = detectUrlType(url)

  function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim()) return
    if (!desc.trim()) { alert('Please enter a Business Description — this helps AI generate accurate analysis.'); return }
    if (!keywords.trim()) { alert('Please enter at least one Target Keyword — this improves SEO and ad targeting.'); return }
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
    <div style={{
      minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Top bar */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 32px', borderBottom: '1px solid var(--border)',
        background: 'var(--bg2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: '7px',
            background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Zap size={14} color="white" />
          </div>
          <span style={{ fontSize: '15px', fontWeight: 600, letterSpacing: '-0.01em' }}>SEM AI</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Powered by Sakthivelraja.AI</span>
          <ThemeToggle />
        </div>
      </header>

      {/* Hero */}
      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
        <div style={{ width: '100%', maxWidth: '520px' }}>

          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              padding: '4px 12px', borderRadius: '20px',
              background: 'var(--accent-bg)', border: '1px solid var(--accent-border)',
              color: 'var(--accent)', fontSize: '12px', fontWeight: 500, marginBottom: '16px',
            }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)' }} />
              AI-Powered Marketing Platform
            </div>
            <h1 style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text)', marginBottom: '10px', lineHeight: 1.3 }}>
              Analyse your website.<br />Launch better campaigns.
            </h1>
            <p style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: 1.6 }}>
              Enter your URL and let AI handle SEO analysis, ad copy, campaign publishing, and performance monitoring.
            </p>
          </div>

          {/* Form */}
          <div style={{
            background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: '14px', padding: '24px',
          }}>
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>
                  Website URL
                </label>
                <div style={{ position: 'relative' }}>
                  <Globe size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }} />
                  <input
                    type="text" value={url}
                    onChange={e => setUrl(e.target.value)}
                    placeholder="https://yourwebsite.com"
                    required
                    style={{
                      width: '100%', paddingLeft: '32px', padding: '10px 12px 10px 32px',
                      background: 'var(--bg)', border: '1px solid var(--border)',
                      borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: '13px',
                      outline: 'none',
                    }}
                    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border)'}
                  />
                </div>
                {url && urlType && (
                  <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                    {urlType === 'single_page' ? (
                      <>
                        <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--purple-bg)', color: 'var(--purple)', fontWeight: 500 }}>📄 Single Page</span>
                        <span style={{ color: 'var(--text3)' }}>Deep analysis of this specific page</span>
                      </>
                    ) : (
                      <>
                        <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)', fontWeight: 500 }}>🌐 Whole Site</span>
                        <span style={{ color: 'var(--text3)' }}>Site-wide analysis + auto site audit</span>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>
                  Business Description <span style={{ color: '#f87171', fontWeight: 600 }}>*</span>
                </label>
                <input
                  type="text" value={desc}
                  onChange={e => setDesc(e.target.value)}
                  placeholder="e.g. AI automation services for Indian SMEs"
                  style={{
                    width: '100%', padding: '10px 12px',
                    background: 'var(--bg)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: '13px',
                    outline: 'none',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px' }}>
                  Target Keywords <span style={{ color: '#f87171', fontWeight: 600 }}>*</span> <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(comma separated)</span>
                </label>
                <input
                  type="text" value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                  placeholder="AI automation, machine learning, data science"
                  style={{
                    width: '100%', padding: '10px 12px',
                    background: 'var(--bg)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: '13px',
                    outline: 'none',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              {error && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '10px 12px', borderRadius: 'var(--radius)',
                  background: 'var(--red-bg)', border: '1px solid rgba(162,45,45,0.2)',
                  color: 'var(--red)', fontSize: '12px', marginBottom: '14px',
                }}>
                  <AlertCircle size={13} /> {error}
                </div>
              )}

              <button type="submit" disabled={loading || !url.trim()} style={{
                width: '100%', padding: '11px 16px',
                background: loading || !url.trim() ? 'var(--bg3)' : 'var(--accent)',
                border: 'none', borderRadius: 'var(--radius)',
                color: loading || !url.trim() ? 'var(--text3)' : 'white',
                fontSize: '14px', fontWeight: 500, cursor: loading || !url.trim() ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.15s',
              }}>
                {loading ? (
                  <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Analysing website...</>
                ) : (
                  <>Analyse with AI <ChevronRight size={15} /></>
                )}
              </button>
            </form>
          </div>

          {/* Features grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '20px' }}>
            {features.map((f, i) => {
              const Icon = f.icon
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '9px',
                  padding: '10px 12px', borderRadius: 'var(--radius)',
                  background: 'var(--bg2)', border: '1px solid var(--border)',
                }}>
                  <div style={{
                    width: '26px', height: '26px', borderRadius: '6px', flexShrink: 0,
                    background: 'var(--accent-bg)', border: '1px solid var(--accent-border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Icon size={13} color="var(--accent)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text)', marginBottom: '1px' }}>{f.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', lineHeight: 1.4 }}>{f.desc}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </main>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

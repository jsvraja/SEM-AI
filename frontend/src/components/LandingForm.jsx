import { useState } from 'react'
import { Globe, Zap, BarChart3, Target, ChevronRight, Loader2, AlertCircle } from 'lucide-react'

export default function LandingForm({ onSubmit, loading, error }) {
  const [url, setUrl] = useState('')
  const [desc, setDesc] = useState('')
  const [keywords, setKeywords] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim()) return
    onSubmit({
      url: url.trim(),
      businessDescription: desc.trim(),
      targetKeywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
    })
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Nav */}
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 2rem', height: '60px',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(11,12,15,0.8)', backdropFilter: 'blur(12px)',
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: '6px',
            background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Zap size={14} color="white" />
          </div>
          <span style={{ fontWeight: 600, fontSize: '15px', letterSpacing: '-0.02em' }}>SEM<span style={{ color: 'var(--accent)' }}>AI</span></span>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text3)', fontFamily: 'var(--mono)' }}>MVP v1.0</span>
      </nav>

      {/* Hero */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }}>
        <div style={{ maxWidth: '680px', width: '100%', textAlign: 'center' }}>

          {/* Eyebrow */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            background: 'rgba(79,125,255,0.08)', border: '1px solid rgba(79,125,255,0.2)',
            borderRadius: '99px', padding: '4px 14px', marginBottom: '2rem',
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)', display: 'block' }}></span>
            <span style={{ fontSize: '12px', color: 'var(--accent)', fontWeight: 500 }}>Powered by Sakthivelraja.AI</span>
          </div>

          <h1 style={{
            fontSize: 'clamp(2rem, 5vw, 3.2rem)', fontWeight: 600,
            lineHeight: 1.1, letterSpacing: '-0.04em',
            marginBottom: '1rem',
          }}>
            AI-powered SEO &amp; SEM<br/>
            <span style={{ color: 'var(--text2)', fontWeight: 300, fontStyle: 'italic' }}>analysis in seconds</span>
          </h1>

          <p style={{ fontSize: '16px', color: 'var(--text2)', lineHeight: 1.65, marginBottom: '2.5rem', maxWidth: '480px', margin: '0 auto 2.5rem' }}>
            Enter any URL. Get a full SEO audit, SEM budget recommendations, keyword strategy, and ready-to-publish Google Ads copy.
          </p>

          {/* Feature chips */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '2.5rem' }}>
            {[
              { icon: Globe, label: 'Site Crawl' },
              { icon: BarChart3, label: 'SEO Score' },
              { icon: Target, label: 'Ad Copy' },
              { icon: Zap, label: 'SEM Plan' },
            ].map(({ icon: Icon, label }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: 'var(--bg3)', border: '1px solid var(--border)',
                borderRadius: '99px', padding: '6px 14px',
                fontSize: '13px', color: 'var(--text2)',
              }}>
                <Icon size={13} color="var(--accent)" />
                {label}
              </div>
            ))}
          </div>

          {/* Form card */}
          <div style={{
            background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: '16px', padding: '2rem',
            textAlign: 'left',
          }}>
            <form onSubmit={handleSubmit}>
              {/* URL */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                  Website URL *
                </label>
                <div style={{ position: 'relative' }}>
                  <Globe size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)' }} />
                  <input
                    type="text"
                    value={url}
                    onChange={e => setUrl(e.target.value)}
                    placeholder="https://example.com"
                    required
                    style={{
                      width: '100%', padding: '10px 12px 10px 36px',
                      background: 'var(--bg3)', border: '1px solid var(--border)',
                      borderRadius: '8px', color: 'var(--text)', fontSize: '14px',
                      outline: 'none', transition: 'border-color 0.15s',
                    }}
                    onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border)'}
                  />
                </div>
              </div>

              {/* Description */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                  Business Description <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(optional)</span>
                </label>
                <textarea
                  value={desc}
                  onChange={e => setDesc(e.target.value)}
                  placeholder="e.g. We sell project management software for remote teams..."
                  rows={2}
                  style={{
                    width: '100%', padding: '10px 12px',
                    background: 'var(--bg3)', border: '1px solid var(--border)',
                    borderRadius: '8px', color: 'var(--text)', fontSize: '14px',
                    outline: 'none', resize: 'vertical', lineHeight: 1.5,
                    transition: 'border-color 0.15s',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              {/* Keywords */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text2)', marginBottom: '6px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                  Target Keywords <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(comma-separated, optional)</span>
                </label>
                <input
                  type="text"
                  value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                  placeholder="project management, team software, kanban tool"
                  style={{
                    width: '100%', padding: '10px 12px',
                    background: 'var(--bg3)', border: '1px solid var(--border)',
                    borderRadius: '8px', color: 'var(--text)', fontSize: '14px',
                    outline: 'none', transition: 'border-color 0.15s',
                  }}
                  onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border)'}
                />
              </div>

              {/* Error */}
              {error && (
                <div style={{
                  display: 'flex', alignItems: 'flex-start', gap: '8px',
                  background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                  borderRadius: '8px', padding: '10px 12px', marginBottom: '1rem',
                  fontSize: '13px', color: '#f87171', lineHeight: 1.5,
                }}>
                  <AlertCircle size={15} style={{ flexShrink: 0, marginTop: '1px' }} />
                  {error}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || !url.trim()}
                style={{
                  width: '100%', padding: '12px',
                  background: loading ? 'var(--bg4)' : 'var(--accent)',
                  border: 'none', borderRadius: '8px',
                  color: 'white', fontSize: '14px', fontWeight: 500,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  transition: 'opacity 0.15s, background 0.15s',
                  opacity: !url.trim() ? 0.5 : 1,
                  cursor: !url.trim() || loading ? 'not-allowed' : 'pointer',
                }}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    Analyzing website — this takes ~30 seconds...
                  </>
                ) : (
                  <>
                    Run Full AI Analysis
                    <ChevronRight size={16} />
                  </>
                )}
              </button>
            </form>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '1rem' }}>
            Analysis includes SEO audit · SEM plan · keyword research · Google Ads copy
          </p>
        </div>
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        input::placeholder, textarea::placeholder { color: var(--text3); }
      `}</style>
    </div>
  )
}

import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Globe, CheckCircle, AlertTriangle, XCircle, Search, Zap, TrendingUp, Target } from 'lucide-react'
import { BASE } from '../api_config'

function IssueIcon({ severity }) {
  if (severity === 'critical') return <XCircle size={14} color="var(--red)" />
  if (severity === 'warning') return <AlertTriangle size={14} color="var(--yellow)" />
  return <CheckCircle size={14} color="var(--green)" />
}

function ScoreCircle({ score, size = 60 }) {
  const color = score >= 70 ? 'var(--green)' : score >= 40 ? 'var(--yellow)' : 'var(--red)'
  return (
    <div style={{ width: size, height: size, borderRadius: '50%', border: `3px solid ${color}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <span style={{ fontSize: size * 0.28, fontWeight: 700, color }}>{score}</span>
    </div>
  )
}

function SEMOpportunityCard({ page, onLaunchAd }) {
  const eligible = page.sem_eligible
  const color = eligible ? 'var(--green)' : 'var(--yellow)'
  const bg = eligible ? 'var(--green-bg)' : 'var(--yellow-bg)'
  return (
    <div style={{ padding: '14px', background: 'var(--bg2)', borderRadius: '12px', border: `1px solid ${eligible ? 'var(--green)' : 'var(--border)'}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{page.title || page.url}</div>
          <a href={page.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{page.url}</a>
        </div>
        <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: bg, color, fontWeight: 600, flexShrink: 0, marginLeft: '8px' }}>
          {eligible ? '✅ SEM Ready' : '⚠️ Needs Work'}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '6px', marginBottom: '10px' }}>
        {[
          { label: 'SEO Score', value: page.score || 0, color: page.score >= 70 ? 'var(--green)' : 'var(--yellow)' },
          { label: 'Est. CPC', value: `₹${page.estimated_cpc || 35}`, color: 'var(--accent)' },
          { label: 'Potential', value: page.sem_potential || 'Medium', color: 'var(--cyan)' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ textAlign: 'center', padding: '6px', background: 'var(--bg3)', borderRadius: '6px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</div>
          </div>
        ))}
      </div>
      {!eligible && page.sem_blockers && (
        <div style={{ marginBottom: '8px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--yellow)', marginBottom: '4px' }}>⚠️ Fix before running ads:</div>
          {(page.sem_blockers || []).map((b, i) => (
            <div key={i} style={{ fontSize: '11px', color: 'var(--text3)', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>• {b}</div>
          ))}
        </div>
      )}
      {eligible && (
        <button onClick={() => onLaunchAd(page)} style={{
          width: '100%', padding: '8px', borderRadius: '8px', border: 'none',
          background: 'linear-gradient(135deg, #4285f4, #34a853)', color: 'white',
          fontSize: '12px', fontWeight: 600, cursor: 'pointer'
        }}>🚀 Launch Ad for this page</button>
      )}
    </div>
  )
}

function SinglePageAudit({ url }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function runAudit() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/site-audit/single-page`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setResult(data)
    } catch(e) { setError(e.message) }
    setLoading(false)
  }

  useEffect(() => { if (url) runAudit() }, [url])

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text3)' }}>
      <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
      <div>Deep auditing this page...</div>
    </div>
  )
  if (error) return <div style={{ padding: '10px', background: 'var(--red-bg)', borderRadius: '8px', color: 'var(--red)', fontSize: '13px' }}>⚠ {error}</div>
  if (!result) return null

  const sem = result.sem_analysis || {}
  const eligible = sem.eligible

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Score Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px' }}>
        {[
          { label: 'Overall', value: result.overall_score || 0, icon: '🎯' },
          { label: 'SEO', value: result.seo_score || 0, icon: '🔍' },
          { label: 'Content', value: result.content_score || 0, icon: '📝' },
          { label: 'Technical', value: result.technical_score || 0, icon: '⚙️' },
        ].map(({ label, value, icon }) => (
          <div key={label} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '20px', marginBottom: '6px' }}>{icon}</div>
            <ScoreCircle score={value} size={50} />
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '6px', textTransform: 'uppercase' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* SEM Eligibility */}
      <div style={{ background: eligible ? 'var(--green-bg)' : 'var(--yellow-bg)', border: `1px solid ${eligible ? 'var(--green)' : 'var(--yellow)'}`, borderRadius: '12px', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, color: eligible ? 'var(--green)' : 'var(--yellow)' }}>
            {eligible ? '✅ This page is SEM Ready!' : '⚠️ This page needs improvements before running ads'}
          </div>
          <span style={{ fontSize: '18px', fontWeight: 700, color: eligible ? 'var(--green)' : 'var(--yellow)' }}>
            {sem.readiness_score || 0}/100
          </span>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6, marginBottom: '10px' }}>{sem.reason}</div>
        {eligible ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px', marginBottom: '10px' }}>
            {[
              { label: 'Est. CPC', value: `₹${sem.estimated_cpc || 35}` },
              { label: 'Est. CTR', value: `${sem.estimated_ctr || 2}%` },
              { label: 'Competition', value: sem.competition || 'Medium' },
            ].map(({ label, value }) => (
              <div key={label} style={{ textAlign: 'center', padding: '8px', background: 'white', borderRadius: '8px', opacity: 0.9 }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--green)' }}>{value}</div>
                <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--yellow)' }}>Fix these to run ads:</div>
            {(sem.blockers || []).map((b, i) => (
              <div key={i} style={{ fontSize: '12px', padding: '6px 10px', background: 'var(--yellow-bg)', borderRadius: '6px', border: '1px solid var(--yellow)', display: 'flex', gap: '6px' }}>
                <span>⚠️</span><span>{b}</span>
              </div>
            ))}
          </div>
        )}
        {(sem.suggestions || []).length > 0 && (
          <div>
            <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>💡 AI Suggestions:</div>
            {sem.suggestions.map((s, i) => (
              <div key={i} style={{ fontSize: '12px', padding: '6px 10px', background: 'rgba(255,255,255,0.5)', borderRadius: '6px', marginBottom: '4px' }}>→ {s}</div>
            ))}
          </div>
        )}
      </div>

      {/* Technical Issues */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
        <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>🔧 Technical Audit</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: '8px' }}>
          {(result.technical_checks || []).map((check, i) => (
            <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'center', padding: '8px', background: 'var(--bg3)', borderRadius: '8px' }}>
              <span style={{ fontSize: '16px' }}>{check.status === 'pass' ? '✅' : check.status === 'fail' ? '❌' : '⚠️'}</span>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{check.label}</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{check.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Content Analysis */}
      {result.content_analysis && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>📝 Content Analysis</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px', marginBottom: '12px' }}>
            {[
              { label: 'Word Count', value: result.content_analysis.word_count || 0 },
              { label: 'Readability', value: result.content_analysis.readability || 'N/A' },
              { label: 'Keyword Density', value: result.content_analysis.keyword_density || 'N/A' },
            ].map(({ label, value }) => (
              <div key={label} style={{ textAlign: 'center', padding: '8px', background: 'var(--bg3)', borderRadius: '8px' }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--accent)' }}>{value}</div>
                <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</div>
              </div>
            ))}
          </div>
          {(result.content_analysis.improvements || []).map((imp, i) => (
            <div key={i} style={{ fontSize: '12px', padding: '6px 10px', background: 'var(--bg3)', borderRadius: '6px', marginBottom: '4px', borderLeft: '3px solid var(--accent)' }}>
              💡 {imp}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SiteAudit({ autoUrl = null, urlType = 'single', savedResults = null, onResults = null }) {
  const [url, setUrl] = useState('')
  const [maxPages, setMaxPages] = useState(100)
  const [auditing, setAuditing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [mode, setMode] = useState('whole') // whole | single
  const pollRef = useRef(null)

  useEffect(() => {
    if (autoUrl) {
      setUrl(autoUrl)
      if (urlType === 'single') setMode('single')
      else setMode('whole')
    }
  }, [autoUrl, urlType])

  useEffect(() => {
    if (savedResults && !results) setResults(savedResults)
  }, [savedResults])

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  async function startAudit() {
    const auditUrl = url.trim()
    if (!auditUrl) { setError('Please enter a URL'); return }
    const finalUrl = auditUrl.startsWith('http') ? auditUrl : 'https://' + auditUrl

    if (pollRef.current) clearInterval(pollRef.current)
    setAuditing(true)
    setError(null)
    setResults(null)
    setJobId(null)
    if (onResults) onResults(null)
    setProgress({ status: 'starting', progress: 0, pages_found: 0, pages_crawled: 0, current_url: 'Starting...' })

    try {
      const res = await fetch(`${BASE}/api/site-audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: finalUrl, max_pages: maxPages }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)

      const id = data.job_id
      setJobId(id)

      pollRef.current = setInterval(async () => {
        try {
          const sr = await fetch(`${BASE}/api/site-audit/status/${id}`)
          const status = await sr.json()
          setProgress(status)
          if (status.status === 'complete') {
            clearInterval(pollRef.current)
            setResults(status.result)
            if (onResults) onResults(status.result)
            setAuditing(false)
            setActiveTab('overview')
          } else if (status.status === 'error') {
            clearInterval(pollRef.current)
            setError(status.error || 'Audit failed')
            setAuditing(false)
          }
        } catch (e) { console.error('Poll error:', e) }
      }, 2000)

      setTimeout(() => {
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
        setAuditing(false)
      }, 600000)

    } catch (e) {
      setError(e.message)
      setAuditing(false)
    }
  }

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'sem', label: `🎯 SEM Opportunities` },
    { id: 'top', label: `🏆 Top Pages` },
    { id: 'bottom', label: `📉 Low Scoring` },
    { id: 'issues', label: `🔧 Issues` },
    { id: 'action', label: '✅ Action Plan' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '8px', background: 'var(--bg2)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border)', width: 'fit-content' }}>
        {[
          { id: 'whole', label: '🌐 Full Site Audit' },
          { id: 'single', label: '📄 Single Page Audit' },
        ].map(m => (
          <button key={m.id} onClick={() => setMode(m.id)} style={{
            padding: '7px 16px', borderRadius: '8px', border: 'none', fontSize: '13px', fontWeight: 600,
            background: mode === m.id ? 'var(--accent)' : 'transparent',
            color: mode === m.id ? 'white' : 'var(--text3)', cursor: 'pointer'
          }}>{m.label}</button>
        ))}
      </div>

      {/* Single Page Mode */}
      {mode === 'single' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>Page URL to Audit</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input value={url} onChange={e => setUrl(e.target.value)}
                placeholder={autoUrl || 'https://example.com/page'}
                style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px', outline: 'none' }} />
              <button onClick={() => setUrl(url)} style={{ padding: '10px 20px', borderRadius: '8px', background: 'var(--accent)', border: 'none', color: 'white', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}>
                <Search size={14} />
              </button>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '6px' }}>
              Using: <strong>{url || autoUrl || 'No URL set'}</strong>
            </div>
          </div>
          <SinglePageAudit url={url || autoUrl} />
        </div>
      )}

      {/* Whole Site Mode */}
      {mode === 'whole' && (
        <>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>Website to Audit</div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input value={url} onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !auditing && startAudit()}
                placeholder="https://yourcompany.com" disabled={auditing}
                style={{ flex: 1, background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 12px', color: 'var(--text)', fontSize: '13px', outline: 'none' }} />
              <button onClick={startAudit} disabled={auditing} style={{
                padding: '10px 20px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                background: auditing ? 'var(--bg3)' : 'var(--accent)', border: 'none',
                color: auditing ? 'var(--text3)' : 'white', cursor: auditing ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0,
              }}>
                {auditing ? <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Search size={14} />}
                {auditing ? 'Auditing...' : 'Start Audit'}
              </button>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Max pages:</span>
              {[50, 100, 500, 1000, 5000].map(n => (
                <button key={n} onClick={() => !auditing && setMaxPages(n)} style={{
                  padding: '4px 10px', borderRadius: '5px', fontSize: '12px',
                  background: maxPages === n ? 'var(--accent-bg)' : 'var(--bg3)',
                  border: `1px solid ${maxPages === n ? 'var(--accent-border)' : 'var(--border)'}`,
                  color: maxPages === n ? 'var(--accent)' : 'var(--text3)',
                  cursor: auditing ? 'not-allowed' : 'pointer', fontWeight: maxPages === n ? 600 : 400,
                }}>{n >= 1000 ? `${n/1000}K` : n}</button>
              ))}
            </div>
          </div>

          {auditing && progress && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500 }}>
                  {progress.status === 'discovering' ? '🔍 Discovering pages...' : progress.status === 'crawling' ? '🕷️ Crawling pages...' : progress.status === 'analyzing' ? '🤖 Analysing...' : '⏳ Starting...'}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--accent)', fontWeight: 600 }}>{progress.progress || 0}%</span>
              </div>
              <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden', marginBottom: '12px' }}>
                <div style={{ height: '100%', borderRadius: '4px', background: 'linear-gradient(90deg, var(--accent), #7c3aed)', width: `${Math.max(2, progress.progress || 0)}%`, transition: 'width 0.5s' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                {[
                  { label: 'Found', val: progress.pages_found || 0 },
                  { label: 'Crawled', val: progress.pages_crawled || 0 },
                  { label: 'Target', val: maxPages >= 1000 ? `${maxPages/1000}K` : maxPages },
                ].map(({ label, val }) => (
                  <div key={label} style={{ padding: '8px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '16px', fontWeight: 700 }}>{val}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase' }}>{label}</div>
                  </div>
                ))}
              </div>
              {progress.current_url && (
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '10px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  🔍 {progress.current_url}
                </div>
              )}
            </div>
          )}

          {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

          {results && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Score cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
                {[
                  { label: 'Site Score', val: results.site_score || 0, color: results.site_score >= 70 ? 'var(--green)' : results.site_score >= 40 ? 'var(--yellow)' : 'var(--red)', icon: '🎯' },
                  { label: 'Pages Audited', val: (results.pages_crawled || 0).toLocaleString(), color: 'var(--accent)', icon: '📄' },
                  { label: 'Critical Issues', val: results.critical_issues || 0, color: 'var(--red)', icon: '❌' },
                  { label: 'SEM Ready Pages', val: (results.sem_opportunities || []).filter(p => p.sem_eligible).length, color: 'var(--green)', icon: '🚀' },
                ].map(({ label, val, color, icon }) => (
                  <div key={label} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '14px' }}>
                    <div style={{ fontSize: '20px', marginBottom: '6px' }}>{icon}</div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color }}>{val}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
                  </div>
                ))}
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
                {tabs.map(t => (
                  <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                    padding: '8px 14px', border: 'none', background: 'none', whiteSpace: 'nowrap',
                    borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
                    color: activeTab === t.id ? 'var(--accent)' : 'var(--text3)',
                    fontSize: '12px', fontWeight: activeTab === t.id ? 600 : 400, cursor: 'pointer', marginBottom: '-1px',
                  }}>{t.label}</button>
                ))}
              </div>

              {/* Overview */}
              {activeTab === 'overview' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>📋 Summary</div>
                    <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.7 }}>{results.summary}</p>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--green)', marginBottom: '8px', textTransform: 'uppercase' }}>✓ Strengths</div>
                      {(results.strengths || []).map((s, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '5px', paddingLeft: '8px', borderLeft: '2px solid var(--green)' }}>{s}</div>)}
                    </div>
                    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--red)', marginBottom: '8px', textTransform: 'uppercase' }}>✗ Weaknesses</div>
                      {(results.weaknesses || []).map((w, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '5px', paddingLeft: '8px', borderLeft: '2px solid var(--red)' }}>{w}</div>)}
                    </div>
                  </div>
                </div>
              )}

              {/* SEM Opportunities */}
              {activeTab === 'sem' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ padding: '12px 16px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: '10px', fontSize: '13px', color: 'var(--accent)', fontWeight: 500 }}>
                    🎯 {(results.sem_opportunities || []).filter(p => p.sem_eligible).length} pages ready for Google Ads — {(results.sem_opportunities || []).filter(p => !p.sem_eligible).length} pages need improvement first
                  </div>
                  {(results.sem_opportunities || []).map((page, i) => (
                    <SEMOpportunityCard key={i} page={page} onLaunchAd={(p) => alert(`Launch ad for: ${p.url}`)} />
                  ))}
                </div>
              )}

              {/* Top Pages */}
              {activeTab === 'top' && (
                <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--green)', marginBottom: '12px' }}>🏆 Top Performing Pages</div>
                  {(results.top_pages || []).map((p, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                      <span style={{ fontWeight: 700, color: 'var(--accent)', width: '24px', fontSize: '12px' }}>#{i+1}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                        <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none' }}>{p.url}</a>
                      </div>
                      <ScoreCircle score={p.score} size={44} />
                    </div>
                  ))}
                </div>
              )}

              {/* Low Scoring */}
              {activeTab === 'bottom' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid var(--red)', borderRadius: '10px', fontSize: '12px', color: 'var(--red)' }}>
                    ⚠️ These pages need improvement before running SEM ads
                  </div>
                  {(results.bottom_pages || []).map((p, i) => (
                    <div key={i} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '14px', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                      <ScoreCircle score={p.score} size={44} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                        <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', display: 'block', marginBottom: '6px' }}>{p.url}</a>
                        {p.main_issue && <div style={{ fontSize: '12px', color: 'var(--red)', marginBottom: '4px' }}>⚠️ {p.main_issue}</div>}
                        {(p.improvements || []).map((imp, j) => (
                          <div key={j} style={{ fontSize: '11px', color: 'var(--text3)', padding: '3px 8px', background: 'var(--bg3)', borderRadius: '4px', marginBottom: '3px' }}>→ {imp}</div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Issues */}
              {activeTab === 'issues' && (
                <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', marginBottom: '12px' }}>All Issues</div>
                  {(results.issues || []).map((issue, i) => (
                    <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                      <IssueIcon severity={issue.severity} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '2px' }}>{issue.title}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text3)' }}>{issue.description}</div>
                        {issue.affected_pages > 0 && <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '4px', background: 'var(--bg4)', color: 'var(--text3)' }}>{issue.affected_pages} pages</span>}
                      </div>
                      <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '4px', background: issue.severity === 'critical' ? 'var(--red-bg)' : 'var(--yellow-bg)', color: issue.severity === 'critical' ? 'var(--red)' : 'var(--yellow)', fontWeight: 500 }}>{issue.severity}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Action Plan */}
              {activeTab === 'action' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {(results.action_plan || []).map((action, i) => (
                    <div key={i} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem', display: 'flex', gap: '12px' }}>
                      <div style={{ width: '32px', height: '32px', borderRadius: '50%', flexShrink: 0, background: action.priority === 'high' ? 'var(--red-bg)' : action.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 700, color: action.priority === 'high' ? 'var(--red)' : action.priority === 'medium' ? 'var(--yellow)' : 'var(--green)' }}>{i+1}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <div style={{ fontSize: '13px', fontWeight: 600 }}>{action.title}</div>
                          <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: action.priority === 'high' ? 'var(--red-bg)' : action.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)', color: action.priority === 'high' ? 'var(--red)' : action.priority === 'medium' ? 'var(--yellow)' : 'var(--green)', fontWeight: 600 }}>{action.priority}</span>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{action.description}</div>
                        {action.estimated_impact && <div style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '4px' }}>📈 {action.estimated_impact}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

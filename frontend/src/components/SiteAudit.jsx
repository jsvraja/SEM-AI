import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Globe, CheckCircle, AlertTriangle, XCircle, Search } from 'lucide-react'
import { BASE } from '../api_config'

function IssueIcon({ severity }) {
  if (severity === 'critical') return <XCircle size={14} color="var(--red)" />
  if (severity === 'warning') return <AlertTriangle size={14} color="var(--yellow)" />
  return <CheckCircle size={14} color="var(--green)" />
}

export default function SiteAudit({ autoUrl = null, savedResults = null, onResults = null }) {
  const [url, setUrl] = useState('')
  const [maxPages, setMaxPages] = useState(100)
  const [auditing, setAuditing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const pollRef = useRef(null)

  // Set URL from autoUrl prop
  useEffect(() => {
    if (autoUrl) setUrl(autoUrl)
  }, [autoUrl])

  // Restore saved results
  useEffect(() => {
    if (savedResults && !results) setResults(savedResults)
  }, [savedResults])

  // Cleanup polling on unmount
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
          } else if (status.status === 'error') {
            clearInterval(pollRef.current)
            setError(status.error || 'Audit failed')
            setAuditing(false)
          }
        } catch (e) { console.error('Poll error:', e) }
      }, 2000)

      // Safety timeout 10 min
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
    { id: 'overview', label: 'Overview' },
    { id: 'top', label: `Top Pages${results ? ` (${results.top_pages?.length || 0})` : ''}` },
    { id: 'bottom', label: `Low Scoring${results ? ` (${results.bottom_pages?.length || 0})` : ''}` },
    { id: 'issues', label: `Issues${results ? ` (${(results.critical_issues || 0) + (results.warnings || 0)})` : ''}` },
    { id: 'action', label: 'Action Plan' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Globe size={18} color="var(--accent)" />
        </div>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>Full Site Audit</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>AI crawls and analyses every page — up to 20,000 pages</p>
        </div>
      </div>

      {/* Input */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>Website to Audit</div>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !auditing && startAudit()}
            placeholder="https://yourcompany.com"
            disabled={auditing}
            style={{ flex: 1, background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 12px', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
          />
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
          {[50, 100, 500, 1000, 5000, 10000, 20000].map(n => (
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

      {/* Progress */}
      {auditing && progress && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '13px', fontWeight: 500 }}>
              {progress.status === 'discovering' ? 'Discovering pages...' : progress.status === 'crawling' ? 'Crawling pages...' : progress.status === 'analyzing' ? 'Analysing...' : 'Starting...'}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--accent)', fontWeight: 600 }}>{progress.progress || 0}%</span>
          </div>
          <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden', marginBottom: '12px' }}>
            <div style={{ height: '100%', borderRadius: '4px', background: 'linear-gradient(90deg, var(--accent), #7c3aed)', width: `${Math.max(2, progress.progress || 0)}%`, transition: 'width 0.5s' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '10px' }}>
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
            <div style={{ fontSize: '11px', color: 'var(--text3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              🔍 {progress.current_url}
            </div>
          )}
        </div>
      )}

      {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

      {/* Results */}
      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            {[
              { label: 'Site Score', val: results.site_score || 0, color: results.site_score >= 70 ? 'var(--green)' : results.site_score >= 40 ? 'var(--yellow)' : 'var(--red)' },
              { label: 'Pages Audited', val: (results.pages_crawled || 0).toLocaleString(), color: 'var(--text)' },
              { label: 'Critical Issues', val: results.critical_issues || 0, color: 'var(--red)' },
              { label: 'Warnings', val: results.warnings || 0, color: 'var(--yellow)' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '14px' }}>
                <div style={{ fontSize: '24px', fontWeight: 700, color }}>{val}</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
              </div>
            ))}
          </div>

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

          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>Summary</div>
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

          {activeTab === 'top' && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--green)', marginBottom: '12px' }}>🏆 Top Performing Pages</div>
              {(results.top_pages || []).map((p, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent)', width: '24px', fontSize: '12px' }}>#{i+1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.url}</a>
                  </div>
                  <div style={{ fontWeight: 700, color: p.score >= 70 ? 'var(--green)' : p.score >= 40 ? 'var(--yellow)' : 'var(--red)', fontSize: '16px', flexShrink: 0 }}>{p.score}</div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'bottom' && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--red)', marginBottom: '12px' }}>⚠ Lowest Performing Pages</div>
              {(results.bottom_pages || []).map((p, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', display: 'block' }}>{p.url}</a>
                    {p.main_issue && <span style={{ fontSize: '11px', color: 'var(--red)' }}>⚠ {p.main_issue}</span>}
                  </div>
                  <div style={{ fontWeight: 700, color: p.score >= 70 ? 'var(--green)' : p.score >= 40 ? 'var(--yellow)' : 'var(--red)', fontSize: '16px', flexShrink: 0 }}>{p.score}</div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'issues' && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', marginBottom: '12px' }}>All Issues</div>
              {(results.issues || []).map((issue, i) => (
                <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                  <IssueIcon severity={issue.severity} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '2px' }}>{issue.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)' }}>{issue.description}</div>
                    {issue.affected_pages > 0 && <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '4px', background: 'var(--bg4)', color: 'var(--text3)' }}>{issue.affected_pages.toLocaleString()} pages</span>}
                  </div>
                  <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '4px', background: issue.severity === 'critical' ? 'var(--red-bg)' : 'var(--yellow-bg)', color: issue.severity === 'critical' ? 'var(--red)' : 'var(--yellow)', fontWeight: 500 }}>{issue.severity}</span>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'action' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(results.action_plan || []).map((action, i) => (
                <div key={i} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem', display: 'flex', gap: '12px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0, background: action.priority === 'high' ? 'var(--red-bg)' : action.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700, color: action.priority === 'high' ? 'var(--red)' : action.priority === 'medium' ? 'var(--yellow)' : 'var(--green)' }}>{i+1}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>{action.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{action.description}</div>
                    {action.estimated_impact && <div style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '4px' }}>📈 {action.estimated_impact}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

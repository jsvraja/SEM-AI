import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Globe, CheckCircle, AlertTriangle, XCircle, Search } from 'lucide-react'
import { BASE } from '../api_config'

function Card({ children, style }) {
  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem', ...style }}>
      {children}
    </div>
  )
}

function ScoreRing({ score, size = 64 }) {
  const color = score >= 70 ? 'var(--green)' : score >= 40 ? 'var(--yellow)' : 'var(--red)'
  const r = (size / 2) - 6
  const circ = 2 * Math.PI * r
  const dash = (score / 100) * circ
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)', flexShrink: 0 }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--bg4)" strokeWidth="5" />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="5"
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
      <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="middle"
        style={{ transform: `rotate(90deg) translate(0px, 0px)`, transformOrigin: `${size/2}px ${size/2}px`, fontSize: size > 50 ? '14px' : '11px', fontWeight: 700, fill: color }}>
        {score}
      </text>
    </svg>
  )
}

function IssueIcon({ severity }) {
  if (severity === 'critical') return <XCircle size={14} color="var(--red)" />
  if (severity === 'warning') return <AlertTriangle size={14} color="var(--yellow)" />
  return <CheckCircle size={14} color="var(--green)" />
}

export default function SiteAudit({ autoUrl = null }) {
  const [url, setUrl] = useState(autoUrl || '')
  const [maxPages, setMaxPages] = useState(100)
  const [autoStarted, setAutoStarted] = useState(false)

  useEffect(() => {
    if (autoUrl && !autoStarted) {
      setAutoStarted(true)
      // Small delay to let component render
      setTimeout(() => startAudit(autoUrl), 500)
    }
  }, [autoUrl])
  const [auditing, setAuditing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const pollRef = useRef(null)

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  async function startAudit(overrideUrl = null) {
    const rawUrl = overrideUrl || url
    if (!rawUrl.trim()) { setError('Please enter a URL'); return }
    let auditUrl = rawUrl.trim()
    if (!auditUrl.startsWith('http')) auditUrl = 'https://' + auditUrl

    setAuditing(true)
    setError(null)
    setResults(null)
    setProgress({ status: 'starting', progress: 0, pages_found: 0, pages_crawled: 0, current_url: 'Initialising...' })

    try {
      const res = await fetch(`${BASE}/api/site-audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: auditUrl, max_pages: maxPages }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)

      const id = data.job_id
      setJobId(id)

      // Poll for progress every 2 seconds
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${BASE}/api/site-audit/status/${id}`)
          const status = await statusRes.json()
          setProgress(status)

          if (status.status === 'complete') {
            clearInterval(pollRef.current)
            setResults(status.result)
            setAuditing(false)
          } else if (status.status === 'error') {
            clearInterval(pollRef.current)
            setError(status.error || 'Audit failed')
            setAuditing(false)
          }
        } catch (e) {
          console.error('Poll error:', e)
        }
      }, 2000)

    } catch (e) {
      setError(e.message)
      setAuditing(false)
    }
  }

  const statusLabels = {
    starting: 'Starting...',
    discovering: 'Discovering pages...',
    crawling: 'Crawling pages...',
    analyzing: 'Analysing results...',
    complete: 'Complete!',
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
      <style>{`@keyframes spin { to { transform: rotate(360deg); } } @keyframes shimmer { 0%{background-position:-200px 0} 100%{background-position:200px 0} }`}</style>

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
      <Card>
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
            background: auditing ? 'var(--bg3)' : 'var(--accent)',
            border: 'none', color: auditing ? 'var(--text3)' : 'white',
            cursor: auditing ? 'not-allowed' : 'pointer',
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
            }}>
              {n >= 1000 ? `${n/1000}K` : n}
            </button>
          ))}
          {maxPages >= 1000 && <span style={{ fontSize: '11px', color: 'var(--yellow)' }}>⚠ Large audit may take 10-20 minutes</span>}
        </div>
      </Card>

      {/* Progress */}
      {auditing && progress && (
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text)' }}>
              {statusLabels[progress.status] || progress.status}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--accent)', fontWeight: 600 }}>{progress.progress}%</span>
          </div>

          {/* Progress bar */}
          <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden', marginBottom: '12px' }}>
            <div style={{
              height: '100%', borderRadius: '4px',
              background: 'linear-gradient(90deg, var(--accent), #7c3aed)',
              width: `${Math.max(2, progress.progress)}%`,
              transition: 'width 0.5s ease',
            }} />
          </div>

          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '10px' }}>
            <div style={{ padding: '8px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text)' }}>{progress.pages_found || 0}</div>
              <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase' }}>Found</div>
            </div>
            <div style={{ padding: '8px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent)' }}>{progress.pages_crawled || 0}</div>
              <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase' }}>Crawled</div>
            </div>
            <div style={{ padding: '8px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text)' }}>{maxPages >= 1000 ? `${maxPages/1000}K` : maxPages}</div>
              <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase' }}>Target</div>
            </div>
          </div>

          {progress.current_url && (
            <div style={{ fontSize: '11px', color: 'var(--text3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              🔍 {progress.current_url}
            </div>
          )}
        </Card>
      )}

      {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid rgba(163,45,45,0.2)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

      {/* Results */}
      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <Card style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px' }}>
              <ScoreRing score={results.site_score || 0} size={52} />
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Site Score</div>
                <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text)' }}>
                  {results.site_score >= 70 ? 'Good' : results.site_score >= 40 ? 'Needs work' : 'Poor'}
                </div>
              </div>
            </Card>
            <Card style={{ padding: '14px' }}>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>{results.pages_crawled?.toLocaleString() || 0}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Pages Audited</div>
            </Card>
            <Card style={{ padding: '14px' }}>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--red)' }}>{results.critical_issues || 0}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Critical Issues</div>
            </Card>
            <Card style={{ padding: '14px' }}>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--yellow)' }}>{results.warnings || 0}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Warnings</div>
            </Card>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                padding: '8px 14px', border: 'none', background: 'none', whiteSpace: 'nowrap',
                borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
                color: activeTab === t.id ? 'var(--accent)' : 'var(--text3)',
                fontSize: '12px', fontWeight: activeTab === t.id ? 600 : 400,
                cursor: 'pointer', marginBottom: '-1px',
              }}>{t.label}</button>
            ))}
          </div>

          {/* Overview */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '8px' }}>Summary</div>
                <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.7 }}>{results.summary}</p>
              </Card>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <Card>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--green)', marginBottom: '8px', textTransform: 'uppercase' }}>✓ Strengths</div>
                  {(results.strengths || []).map((s, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '5px', paddingLeft: '8px', borderLeft: '2px solid var(--green)' }}>{s}</div>)}
                </Card>
                <Card>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--red)', marginBottom: '8px', textTransform: 'uppercase' }}>✗ Weaknesses</div>
                  {(results.weaknesses || []).map((w, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '5px', paddingLeft: '8px', borderLeft: '2px solid var(--red)' }}>{w}</div>)}
                </Card>
              </div>
              {results.score_breakdown && (
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>Score Breakdown</div>
                  {Object.entries(results.score_breakdown).map(([key, val], i) => (
                    <div key={i} style={{ marginBottom: '10px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                        <span style={{ color: 'var(--text2)', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                        <span style={{ fontWeight: 600, color: val >= 70 ? 'var(--green)' : val >= 40 ? 'var(--yellow)' : 'var(--red)' }}>{val}%</span>
                      </div>
                      <div style={{ height: '5px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', borderRadius: '3px', width: `${val}%`, background: val >= 70 ? 'var(--green)' : val >= 40 ? 'var(--yellow)' : 'var(--red)', transition: 'width 0.5s' }} />
                      </div>
                    </div>
                  ))}
                </Card>
              )}
            </div>
          )}

          {/* Top Pages */}
          {activeTab === 'top' && (
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px', color: 'var(--green)' }}>🏆 Top Performing Pages</div>
              {(results.top_pages || []).map((p, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ fontWeight: 700, color: 'var(--accent)', width: '24px', fontSize: '12px', flexShrink: 0 }}>#{i+1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{p.url}</a>
                    <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{p.word_count} words</span>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontWeight: 700, color: p.score >= 70 ? 'var(--green)' : p.score >= 40 ? 'var(--yellow)' : 'var(--red)', fontSize: '16px' }}>{p.score}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text3)' }}>/ 100</div>
                  </div>
                </div>
              ))}
            </Card>
          )}

          {/* Bottom Pages */}
          {activeTab === 'bottom' && (
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px', color: 'var(--red)' }}>⚠ Lowest Performing Pages</div>
              {(results.bottom_pages || []).map((p, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                    <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '11px', color: 'var(--accent)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block' }}>{p.url}</a>
                    {p.main_issue && <span style={{ fontSize: '11px', color: 'var(--red)', marginTop: '2px', display: 'block' }}>⚠ {p.main_issue}</span>}
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontWeight: 700, color: p.score >= 70 ? 'var(--green)' : p.score >= 40 ? 'var(--yellow)' : 'var(--red)', fontSize: '16px' }}>{p.score}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text3)' }}>/ 100</div>
                  </div>
                </div>
              ))}
            </Card>
          )}

          {/* Issues */}
          {activeTab === 'issues' && (
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>All Issues Found</div>
              {(results.issues || []).map((issue, i) => (
                <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                  <IssueIcon severity={issue.severity} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '2px' }}>{issue.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '4px' }}>{issue.description}</div>
                    {issue.affected_pages > 0 && (
                      <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '4px', background: 'var(--bg4)', color: 'var(--text3)' }}>
                        {issue.affected_pages.toLocaleString()} pages affected
                      </span>
                    )}
                  </div>
                  <span style={{
                    fontSize: '10px', padding: '2px 7px', borderRadius: '4px', flexShrink: 0,
                    background: issue.severity === 'critical' ? 'var(--red-bg)' : issue.severity === 'warning' ? 'var(--yellow-bg)' : 'var(--green-bg)',
                    color: issue.severity === 'critical' ? 'var(--red)' : issue.severity === 'warning' ? 'var(--yellow)' : 'var(--green)',
                    fontWeight: 500, textTransform: 'capitalize',
                  }}>{issue.severity}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Action Plan */}
          {activeTab === 'action' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(results.action_plan || []).map((action, i) => (
                <Card key={i} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                    background: action.priority === 'high' ? 'var(--red-bg)' : action.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '13px', fontWeight: 700,
                    color: action.priority === 'high' ? 'var(--red)' : action.priority === 'medium' ? 'var(--yellow)' : 'var(--green)',
                  }}>{i+1}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600 }}>{action.title}</span>
                      <span style={{
                        fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
                        background: action.priority === 'high' ? 'var(--red-bg)' : action.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)',
                        color: action.priority === 'high' ? 'var(--red)' : action.priority === 'medium' ? 'var(--yellow)' : 'var(--green)',
                        fontWeight: 500, textTransform: 'capitalize',
                      }}>{action.priority} priority</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{action.description}</div>
                    {action.estimated_impact && (
                      <div style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '4px' }}>📈 {action.estimated_impact}</div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

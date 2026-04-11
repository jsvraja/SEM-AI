import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Globe, CheckCircle, AlertTriangle, XCircle, TrendingUp, TrendingDown, Search, BarChart3 } from 'lucide-react'
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
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--bg4)" strokeWidth="5" />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="5"
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
      <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="middle"
        style={{ transform: 'rotate(90deg)', transformOrigin: `${size/2}px ${size/2}px`, fontSize: '14px', fontWeight: 700, fill: color }}>
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

export default function SiteAudit() {
  const [url, setUrl] = useState('')
  const [maxPages, setMaxPages] = useState(50)
  const [auditing, setAuditing] = useState(false)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const eventSourceRef = useRef(null)

  async function startAudit() {
    if (!url.trim()) { setError('Please enter a URL'); return }
    let auditUrl = url.trim()
    if (!auditUrl.startsWith('http')) auditUrl = 'https://' + auditUrl
    
    setAuditing(true)
    setError(null)
    setResults(null)
    setProgress({ crawled: 0, total: maxPages, pages: [], status: 'Initialising...' })

    try {
      const res = await fetch(`${BASE}/api/site-audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: auditUrl, max_pages: maxPages }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setResults(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setAuditing(false)
      setProgress(null)
    }
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'top', label: 'Top Pages' },
    { id: 'issues', label: 'Issues' },
    { id: 'action', label: 'Action Plan' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } } @keyframes progress-bar { from { width: 0% } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--accent-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Globe size={18} color="var(--accent)" />
        </div>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>Full Site Audit</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>AI crawls and analyses every page of your website</p>
        </div>
      </div>

      {/* Input */}
      <Card>
        <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>Website to Audit</div>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && startAudit()}
            placeholder="https://yourcompany.com"
            style={{ flex: 1, background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '10px 12px', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
          />
          <button onClick={startAudit} disabled={auditing} style={{
            padding: '10px 20px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
            background: auditing ? 'var(--bg3)' : 'var(--accent)',
            border: 'none', color: auditing ? 'var(--text3)' : 'white', cursor: auditing ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0,
          }}>
            {auditing ? <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Search size={14} />}
            {auditing ? 'Auditing...' : 'Start Audit'}
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Max pages:</span>
          {[25, 50, 100, 200, 500].map(n => (
            <button key={n} onClick={() => setMaxPages(n)} style={{
              padding: '4px 10px', borderRadius: '5px', fontSize: '12px',
              background: maxPages === n ? 'var(--accent-bg)' : 'var(--bg3)',
              border: `1px solid ${maxPages === n ? 'var(--accent-border)' : 'var(--border)'}`,
              color: maxPages === n ? 'var(--accent)' : 'var(--text3)',
              cursor: 'pointer', fontWeight: maxPages === n ? 600 : 400,
            }}>{n}</button>
          ))}
        </div>
      </Card>

      {/* Progress */}
      {auditing && progress && (
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
            <span style={{ fontWeight: 500 }}>{progress.status}</span>
            <span style={{ color: 'var(--text3)' }}>{progress.crawled}/{progress.total} pages</span>
          </div>
          <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{
              height: '100%', background: 'var(--accent)', borderRadius: '3px',
              width: `${(progress.crawled / progress.total) * 100}%`,
              transition: 'width 0.3s',
            }} />
          </div>
          <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text3)' }}>
            AI is crawling and analysing each page... This may take 1-3 minutes.
          </div>
        </Card>
      )}

      {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid rgba(163,45,45,0.2)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

      {/* Results */}
      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Summary cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <Card style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
                <ScoreRing score={results.site_score || 0} />
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Site Score</div>
            </Card>
            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text)', marginBottom: '4px' }}>{results.pages_crawled || 0}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Pages Crawled</div>
            </Card>
            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--red)', marginBottom: '4px' }}>{results.critical_issues || 0}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Critical Issues</div>
            </Card>
            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--yellow)', marginBottom: '4px' }}>{results.warnings || 0}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Warnings</div>
            </Card>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '2px', borderBottom: '1px solid var(--border)' }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                padding: '8px 16px', border: 'none', background: 'none',
                borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
                color: activeTab === t.id ? 'var(--accent)' : 'var(--text3)',
                fontSize: '13px', fontWeight: activeTab === t.id ? 500 : 400,
                cursor: 'pointer', marginBottom: '-1px',
              }}>{t.label}</button>
            ))}
          </div>

          {/* Overview tab */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>Executive Summary</div>
                <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.7 }}>{results.summary}</p>
              </Card>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--green)' }}>✓ What's Working</div>
                  {(results.strengths || []).map((s, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '5px', paddingLeft: '8px', borderLeft: '2px solid var(--green)' }}>{s}</div>)}
                </Card>
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--red)' }}>✗ Needs Attention</div>
                  {(results.weaknesses || []).map((w, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '5px', paddingLeft: '8px', borderLeft: '2px solid var(--red)' }}>{w}</div>)}
                </Card>
              </div>
              {/* Score breakdown */}
              {results.score_breakdown && (
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>Score Breakdown</div>
                  {Object.entries(results.score_breakdown).map(([key, val], i) => (
                    <div key={i} style={{ marginBottom: '10px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                        <span style={{ color: 'var(--text2)', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                        <span style={{ fontWeight: 600, color: val >= 70 ? 'var(--green)' : val >= 40 ? 'var(--yellow)' : 'var(--red)' }}>{val}/100</span>
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

          {/* Top Pages tab */}
          {activeTab === 'top' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--green)' }}>
                  🏆 Top Performing Pages
                </div>
                {(results.top_pages || []).map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: '12px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent)', width: '20px', flexShrink: 0 }}>#{i+1}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                      <div style={{ color: 'var(--text3)', fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.url}</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontWeight: 700, color: 'var(--green)', fontSize: '14px' }}>{p.score}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text3)' }}>score</div>
                    </div>
                  </div>
                ))}
              </Card>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--red)' }}>
                  ⚠ Lowest Performing Pages
                </div>
                {(results.bottom_pages || []).map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: '12px' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title || p.url}</div>
                      <div style={{ color: 'var(--text3)', fontSize: '11px' }}>{p.url}</div>
                      {p.main_issue && <div style={{ color: 'var(--red)', fontSize: '11px', marginTop: '2px' }}>Issue: {p.main_issue}</div>}
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontWeight: 700, color: 'var(--red)', fontSize: '14px' }}>{p.score}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text3)' }}>score</div>
                    </div>
                  </div>
                ))}
              </Card>
            </div>
          )}

          {/* Issues tab */}
          {activeTab === 'issues' && (
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>All Issues Found</div>
              {(results.issues || []).map((issue, i) => (
                <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px 0', borderBottom: '1px solid var(--border)', alignItems: 'flex-start' }}>
                  <IssueIcon severity={issue.severity} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text)', marginBottom: '2px' }}>{issue.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '4px' }}>{issue.description}</div>
                    {issue.affected_pages > 0 && (
                      <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '4px', background: 'var(--bg4)', color: 'var(--text3)' }}>
                        {issue.affected_pages} pages affected
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

          {/* Action Plan tab */}
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
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>{action.title}</span>
                      <span style={{
                        fontSize: '10px', padding: '1px 6px', borderRadius: '4px',
                        background: action.priority === 'high' ? 'var(--red-bg)' : action.priority === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)',
                        color: action.priority === 'high' ? 'var(--red)' : action.priority === 'medium' ? 'var(--yellow)' : 'var(--green)',
                        fontWeight: 500, textTransform: 'capitalize',
                      }}>{action.priority} priority</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{action.description}</div>
                    {action.estimated_impact && (
                      <div style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '4px' }}>📈 Expected impact: {action.estimated_impact}</div>
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

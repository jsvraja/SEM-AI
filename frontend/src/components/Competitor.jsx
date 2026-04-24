import { BASE } from '../api_config'
import { useState } from 'react'
import { RefreshCw, Search, Target, Zap, Plus, X, TrendingUp, Shield, Award } from 'lucide-react'

function Card({ children, style }) {
  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.25rem', ...style }}>
      {children}
    </div>
  )
}

function ScoreBadge({ score }) {
  const color = score >= 70 ? 'var(--green)' : score >= 40 ? 'var(--yellow)' : 'var(--red)'
  return (
    <div style={{ width: '44px', height: '44px', borderRadius: '50%', border: `2px solid ${color}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700, color, flexShrink: 0 }}>
      {score}
    </div>
  )
}

export default function Competitor({ url, seoReport }) {
  const [mode, setMode] = useState('ai')
  const [discovering, setDiscovering] = useState(false)
  const [discoveredCompetitors, setDiscoveredCompetitors] = useState([])
  const [selectedCompetitors, setSelectedCompetitors] = useState([])
  const [manualUrls, setManualUrls] = useState(['', '', ''])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  const domain = (() => { try { return new URL(url).hostname } catch { return url } })()

  async function discoverCompetitors() {
    setDiscovering(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/competitor/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          keywords: (seoReport?.keyword_suggestions || []).slice(0, 5).map(k => k.keyword),
          industry: seoReport?.content_analysis?.main_topics?.join(', ') || 'technology',
        }),
      })
      const data = await res.json()
      setDiscoveredCompetitors(data.competitors || [])
    } catch (e) {
      setError('Discovery failed: ' + e.message)
    } finally {
      setDiscovering(false)
    }
  }

  function toggleSelect(comp) {
    setSelectedCompetitors(prev =>
      prev.find(c => c.url === comp.url)
        ? prev.filter(c => c.url !== comp.url)
        : [...prev, comp]
    )
  }

  async function analyze() {
    const urls = mode === 'ai'
      ? selectedCompetitors.map(c => c.url)
      : manualUrls.filter(u => u.trim())
    if (urls.length === 0) { setError('Select or enter at least one competitor'); return }
    setAnalyzing(true)
    setError(null)
    setResults(null)
    try {
      const res = await fetch(`${BASE}/api/competitor/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          competitors: urls,
          seo_score: seoReport?.overall_seo_score || 50,
          keywords: (seoReport?.keyword_suggestions || []).map(k => k.keyword),
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setResults(data)
      setActiveTab('overview')
    } catch (e) {
      setError('Analysis failed: ' + e.message)
    } finally {
      setAnalyzing(false)
    }
  }

  const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: 'keywords', label: 'Keywords' },
    { id: 'content', label: 'Content Gaps' },
    { id: 'ads', label: 'Ad Intelligence' },
    { id: 'social', label: 'Social Compare' },
    { id: 'strategy', label: 'Winning Strategy' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <Card style={{ padding: '1rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(79,125,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Target size={16} color="var(--accent)" />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600 }}>Competitor Analysis</div>
            <div style={{ fontSize: '11px', color: 'var(--text3)' }}>AI-powered competitive intelligence for {domain}</div>
          </div>
        </div>
      </Card>

      {/* Mode selector */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {[['ai', '🤖 AI Discovery'], ['manual', '✏️ Manual Entry']].map(([id, label]) => (
          <button key={id} onClick={() => setMode(id)} style={{
            flex: 1, padding: '8px', borderRadius: '8px', border: `1px solid ${mode === id ? 'var(--accent)' : 'var(--border)'}`,
            background: mode === id ? 'rgba(79,125,255,0.1)' : 'var(--bg2)', color: mode === id ? 'var(--accent)' : 'var(--text2)',
            cursor: 'pointer', fontSize: '13px', fontWeight: mode === id ? 600 : 400,
          }}>{label}</button>
        ))}
      </div>

      {/* AI Discovery */}
      {mode === 'ai' && (
        <Card>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Competitor Discovery</div>
          <p style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '12px' }}>SEM AI analyzes your website, keywords, and industry to automatically identify your top competitors.</p>
          {discoveredCompetitors.length === 0 ? (
            <button onClick={discoverCompetitors} disabled={discovering} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'var(--accent)', border: 'none', color: 'white', cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}>
              {discovering ? <><RefreshCw size={14} style={{ animation: 'spin 1s linear infinite', display: 'inline', marginRight: '6px' }} />Discovering...</> : <><Search size={14} style={{ display: 'inline', marginRight: '6px' }} />Discover Competitors</>}
            </button>
          ) : (
            <>
              <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '8px' }}>Select competitors to analyse ({selectedCompetitors.length} selected)</div>
              {discoveredCompetitors.map((comp, i) => (
                <div key={i} onClick={() => toggleSelect(comp)} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px', borderRadius: '8px', marginBottom: '6px',
                  border: `1px solid ${selectedCompetitors.find(c => c.url === comp.url) ? 'var(--accent)' : 'var(--border)'}`,
                  background: selectedCompetitors.find(c => c.url === comp.url) ? 'rgba(79,125,255,0.06)' : 'var(--bg3)', cursor: 'pointer',
                }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '4px', border: `2px solid ${selectedCompetitors.find(c => c.url === comp.url) ? 'var(--accent)' : 'var(--border)'}`, background: selectedCompetitors.find(c => c.url === comp.url) ? 'var(--accent)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
                    {selectedCompetitors.find(c => c.url === comp.url) && <span style={{ color: 'white', fontSize: '12px' }}>✓</span>}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent)' }}>{comp.domain}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px', lineHeight: 1.5 }}>{comp.reason?.slice(0, 120)}...</div>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                      <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '3px', background: 'var(--bg2)', color: 'var(--text3)' }}>🚦 {comp.threat_level}</span>
                      <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '3px', background: 'var(--bg2)', color: 'var(--text3)' }}>📊 {comp.estimated_traffic}</span>
                    </div>
                  </div>
                </div>
              ))}
              <button onClick={discoverCompetitors} style={{ fontSize: '11px', padding: '5px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text2)', cursor: 'pointer', marginTop: '4px' }}>
                <RefreshCw size={11} style={{ display: 'inline', marginRight: '4px' }} />Rediscover
              </button>
            </>
          )}
        </Card>
      )}

      {/* Manual Entry */}
      {mode === 'manual' && (
        <Card>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Enter Competitor URLs</div>
          {manualUrls.map((u, i) => (
            <div key={i} style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
              <input value={u} onChange={e => { const arr = [...manualUrls]; arr[i] = e.target.value; setManualUrls(arr) }}
                placeholder={`https://competitor${i + 1}.com`}
                style={{ flex: 1, padding: '8px 10px', borderRadius: '7px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px', outline: 'none' }} />
              {manualUrls.length > 1 && <button onClick={() => setManualUrls(prev => prev.filter((_, j) => j !== i))} style={{ padding: '8px', borderRadius: '7px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--red)', cursor: 'pointer' }}><X size={14} /></button>}
            </div>
          ))}
          {manualUrls.length < 5 && (
            <button onClick={() => setManualUrls(prev => [...prev, ''])} style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text2)', cursor: 'pointer' }}>
              <Plus size={12} style={{ display: 'inline', marginRight: '4px' }} />Add another
            </button>
          )}
        </Card>
      )}

      {error && <div style={{ padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--red)', borderRadius: '8px', fontSize: '12px', color: 'var(--red)' }}>{error}</div>}

      {/* Analyze button */}
      <button onClick={analyze} disabled={analyzing} style={{ width: '100%', padding: '12px', borderRadius: '10px', background: analyzing ? 'var(--bg3)' : 'var(--accent)', border: 'none', color: analyzing ? 'var(--text3)' : 'white', cursor: analyzing ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: 600 }}>
        {analyzing ? <><RefreshCw size={14} style={{ animation: 'spin 1s linear infinite', display: 'inline', marginRight: '8px' }} />Analysing competitors...</> : <><Search size={14} style={{ display: 'inline', marginRight: '8px' }} />Analyse Competitors</>}
      </button>

      {/* Results */}
      {results && (
        <>
          {/* Score Card */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>🏆 Competitor Score Card</div>
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${1 + (results.competitors || []).length}, 1fr)`, gap: '8px', overflowX: 'auto' }}>
              {/* My site */}
              <div style={{ padding: '12px', background: 'rgba(79,125,255,0.08)', border: '2px solid var(--accent)', borderRadius: '10px', textAlign: 'center' }}>
                <ScoreBadge score={results.my_site?.score || 0} />
                <div style={{ fontSize: '12px', fontWeight: 600, marginTop: '8px', color: 'var(--accent)' }}>YOUR SITE</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{results.my_site?.domain}</div>
              </div>
              {/* Competitors */}
              {(results.competitors || []).map((comp, i) => {
                const diff = (comp.estimated_score || 0) - (results.my_site?.score || 0)
                return (
                  <div key={i} style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '10px', textAlign: 'center' }}>
                    <ScoreBadge score={comp.estimated_score || 0} />
                    <div style={{ fontSize: '11px', fontWeight: 600, marginTop: '8px' }}>COMPETITOR {i + 1}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{comp.domain}</div>
                    <div style={{ fontSize: '11px', marginTop: '4px', color: diff > 0 ? 'var(--red)' : 'var(--green)', fontWeight: 600 }}>
                      {diff > 0 ? `▲ ${diff} vs you` : diff < 0 ? `▼ ${Math.abs(diff)} behind you` : 'Equal'}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px' }}>{comp.estimated_traffic}</div>
                  </div>
                )
              })}
            </div>
            {/* Gap message */}
            {(() => {
              const maxScore = Math.max(...(results.competitors || []).map(c => c.estimated_score || 0))
              const gap = maxScore - (results.my_site?.score || 0)
              return gap > 0 ? (
                <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(251,174,75,0.1)', borderRadius: '8px', fontSize: '12px', color: '#d97706', textAlign: 'center' }}>
                  ⚡ {gap} points behind the leader — see action plan below to catch up
                </div>
              ) : (
                <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(34,197,94,0.1)', borderRadius: '8px', fontSize: '12px', color: 'var(--green)', textAlign: 'center' }}>
                  🏆 You are leading! Maintain your advantage.
                </div>
              )
            })()}
          </Card>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg3)', padding: '4px', borderRadius: '10px', overflowX: 'auto' }}>
            {TABS.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                flex: 1, padding: '6px 8px', borderRadius: '7px', border: 'none', cursor: 'pointer', fontSize: '11px', fontWeight: 500, whiteSpace: 'nowrap',
                background: activeTab === t.id ? 'var(--bg2)' : 'transparent',
                color: activeTab === t.id ? 'var(--text)' : 'var(--text3)',
              }}>{t.label}</button>
            ))}
          </div>

          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {(results.competitors || []).map((comp, i) => (
                <Card key={i}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                    <ScoreBadge score={comp.estimated_score || 0} />
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent)' }}>{comp.domain}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Est. Traffic: {comp.estimated_traffic} · Ad Spend: {comp.estimated_ad_spend || 'Unknown'}</div>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                    <div>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--green)', marginBottom: '6px' }}>✅ Strengths</div>
                      {(comp.strengths || []).map((s, j) => <div key={j} style={{ fontSize: '11px', color: 'var(--text2)', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>→ {s}</div>)}
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--red)', marginBottom: '6px' }}>❌ Weaknesses</div>
                      {(comp.weaknesses || []).map((w, j) => <div key={j} style={{ fontSize: '11px', color: 'var(--text2)', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>→ {w}</div>)}
                    </div>
                  </div>
                  <div style={{ fontSize: '11px', background: 'var(--bg3)', borderRadius: '8px', padding: '8px' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text2)' }}>📢 Social: </span>
                    <span style={{ color: 'var(--text3)' }}>{comp.social_presence}</span>
                  </div>
                </Card>
              ))}
              {/* Opportunities & Threats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--green)', marginBottom: '10px' }}>💡 Opportunities</div>
                  {(results.opportunities || []).map((o, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '6px 0', borderBottom: '1px solid var(--border)', lineHeight: 1.5 }}>→ {o}</div>)}
                </Card>
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--red)', marginBottom: '10px' }}>⚠️ Threats</div>
                  {(results.threats || []).map((t, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '6px 0', borderBottom: '1px solid var(--border)', lineHeight: 1.5 }}>→ {t}</div>)}
                </Card>
              </div>
            </div>
          )}

          {/* KEYWORDS TAB */}
          {activeTab === 'keywords' && results.keyword_overlap && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--yellow)', marginBottom: '10px' }}>🔄 Shared Keywords</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(results.keyword_overlap.shared_keywords || []).map((kw, i) => <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: 'rgba(251,174,75,0.1)', color: '#d97706', borderRadius: '4px', border: '1px solid rgba(251,174,75,0.2)' }}>{kw}</span>)}
                  </div>
                </Card>
                <Card>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--green)', marginBottom: '10px' }}>⭐ Your Unique Keywords</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(results.keyword_overlap.my_unique || []).map((kw, i) => <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: 'rgba(34,197,94,0.1)', color: 'var(--green)', borderRadius: '4px', border: '1px solid rgba(34,197,94,0.2)' }}>{kw}</span>)}
                  </div>
                </Card>
              </div>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', marginBottom: '10px' }}>🎯 Opportunity Keywords (Low Competition)</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {(results.keyword_overlap.opportunity_keywords || []).map((kw, i) => <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: 'rgba(79,125,255,0.1)', color: 'var(--accent)', borderRadius: '4px', border: '1px solid rgba(79,125,255,0.2)', cursor: 'pointer' }}>{kw}</span>)}
                </div>
              </Card>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--red)', marginBottom: '10px' }}>🏆 Competitor-Only Keywords</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {(results.keyword_overlap.competitor_only || []).map((kw, i) => <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: 'rgba(239,68,68,0.08)', color: 'var(--red)', borderRadius: '4px', border: '1px solid rgba(239,68,68,0.15)' }}>{kw}</span>)}
                </div>
              </Card>
            </div>
          )}

          {/* CONTENT GAPS TAB */}
          {activeTab === 'content' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text3)', padding: '4px 0' }}>Topics your competitors cover that you don't — ranked by priority</div>
              {(results.content_gaps || []).map((gap, i) => (
                <Card key={i}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: gap.priority === 'high' ? 'rgba(239,68,68,0.12)' : gap.priority === 'medium' ? 'rgba(251,174,75,0.12)' : 'rgba(34,197,94,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, color: gap.priority === 'high' ? 'var(--red)' : gap.priority === 'medium' ? '#d97706' : 'var(--green)', flexShrink: 0 }}>
                      {i + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <div style={{ fontSize: '13px', fontWeight: 600 }}>{gap.topic}</div>
                        <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '3px', background: gap.priority === 'high' ? 'rgba(239,68,68,0.1)' : 'rgba(251,174,75,0.1)', color: gap.priority === 'high' ? 'var(--red)' : '#d97706', fontWeight: 600 }}>{gap.priority} priority</span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '6px' }}>Covered by: {gap.competitor_covering}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text2)', background: 'var(--bg3)', borderRadius: '6px', padding: '6px 8px' }}>💡 {gap.opportunity}</div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* AD INTELLIGENCE TAB */}
          {activeTab === 'ads' && results.ad_intelligence && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>📢 Ad Intelligence</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                  <div style={{ background: 'var(--bg3)', borderRadius: '8px', padding: '10px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>COMPETITORS RUNNING ADS</div>
                    {(results.ad_intelligence.competitors_running_ads || []).map((c, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--red)', fontWeight: 500 }}>• {c}</div>)}
                  </div>
                  <div style={{ background: 'var(--bg3)', borderRadius: '8px', padding: '10px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>COMPETITION LEVEL</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: results.ad_intelligence.estimated_competition_level === 'high' ? 'var(--red)' : results.ad_intelligence.estimated_competition_level === 'medium' ? '#d97706' : 'var(--green)', textTransform: 'capitalize' }}>
                      {results.ad_intelligence.estimated_competition_level}
                    </div>
                  </div>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '6px', fontWeight: 600 }}>COMMON AD KEYWORDS</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(results.ad_intelligence.common_ad_keywords || []).map((kw, i) => <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: 'rgba(239,68,68,0.08)', color: 'var(--red)', borderRadius: '4px', border: '1px solid rgba(239,68,68,0.15)' }}>{kw}</span>)}
                  </div>
                </div>
                <div style={{ background: 'rgba(79,125,255,0.08)', borderRadius: '8px', padding: '10px', marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--accent)', fontWeight: 600, marginBottom: '4px' }}>YOUR AD OPPORTUNITY</div>
                  <div style={{ fontSize: '12px', color: 'var(--text2)' }}>{results.ad_intelligence.my_ad_opportunity}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '6px', fontWeight: 600 }}>RECOMMENDED KEYWORDS FOR YOUR ADS</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(results.ad_intelligence.recommended_ad_keywords || []).map((kw, i) => <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: 'rgba(34,197,94,0.1)', color: 'var(--green)', borderRadius: '4px', border: '1px solid rgba(34,197,94,0.2)' }}>{kw}</span>)}
                  </div>
                </div>
              </Card>
              {/* Per competitor ad keywords */}
              {(results.competitors || []).map((comp, i) => (
                <Card key={i}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent)', marginBottom: '8px' }}>{comp.domain} — Ad Strategy</div>
                  <div style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '8px' }}>{comp.ad_strategy}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                    {(comp.ad_keywords || []).map((kw, j) => <span key={j} style={{ fontSize: '11px', padding: '2px 7px', background: 'var(--bg3)', color: 'var(--text3)', borderRadius: '4px', border: '1px solid var(--border)' }}>{kw}</span>)}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* SOCIAL COMPARISON TAB */}
          {activeTab === 'social' && results.social_comparison && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>📱 Social Media Comparison</div>
                <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '12px' }}>Social leader: <strong style={{ color: 'var(--accent)' }}>{results.social_comparison.leader}</strong></div>
                {(results.social_comparison.platforms || []).map((p, i) => (
                  <div key={i} style={{ marginBottom: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 600 }}>{p.platform}</span>
                      <span style={{ color: 'var(--text3)' }}>You: <strong style={{ color: 'var(--accent)' }}>{p.my_score}</strong> vs Best: <strong style={{ color: 'var(--red)' }}>{p.best_competitor}</strong></span>
                    </div>
                    <div style={{ height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden', position: 'relative', marginBottom: '6px' }}>
                      <div style={{ position: 'absolute', height: '100%', width: `${p.best_competitor}%`, background: 'rgba(239,68,68,0.2)', borderRadius: '4px' }} />
                      <div style={{ position: 'absolute', height: '100%', width: `${p.my_score}%`, background: 'var(--accent)', borderRadius: '4px' }} />
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', background: 'var(--bg3)', borderRadius: '6px', padding: '5px 8px' }}>
                      Gap: <strong style={{ color: '#d97706' }}>{p.gap} points</strong> — {p.action}
                    </div>
                  </div>
                ))}
              </Card>
              {/* Per competitor social */}
              {(results.competitors || []).map((comp, i) => comp.social_platforms && (
                <Card key={i}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent)', marginBottom: '10px' }}>{comp.domain} — Social Presence</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                    {Object.entries(comp.social_platforms || {}).map(([platform, score]) => (
                      <div key={platform} style={{ textAlign: 'center', background: 'var(--bg3)', borderRadius: '8px', padding: '8px' }}>
                        <div style={{ fontSize: '18px', fontWeight: 700, color: score >= 70 ? 'var(--green)' : score >= 40 ? '#d97706' : 'var(--red)' }}>{score}</div>
                        <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'capitalize' }}>{platform}</div>
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* WINNING STRATEGY TAB */}
          {activeTab === 'strategy' && results.winning_strategy && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Card style={{ background: 'rgba(79,125,255,0.06)', border: '1px solid rgba(79,125,255,0.2)' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>🎯 Winning Strategy</div>
                <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.7, margin: 0 }}>{results.winning_strategy.summary}</p>
                <div style={{ marginTop: '10px', padding: '8px 10px', background: 'rgba(79,125,255,0.1)', borderRadius: '8px', fontSize: '12px', color: 'var(--accent)' }}>
                  ⭐ Your differentiator: <strong>{results.winning_strategy.differentiator}</strong>
                </div>
              </Card>

              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--green)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>⚡ Quick Wins</div>
                {(results.winning_strategy.quick_wins || []).map((w, i) => (
                  <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px', background: 'var(--bg3)', borderRadius: '8px', marginBottom: '8px' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'rgba(34,197,94,0.15)', color: 'var(--green)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, flexShrink: 0 }}>{i + 1}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '3px' }}>{w.action}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>Expected: {w.impact}</div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '3px', background: 'rgba(34,197,94,0.1)', color: 'var(--green)' }}>⏱ {w.timeline}</span>
                        <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '3px', background: 'var(--bg2)', color: 'var(--text3)' }}>{w.effort} effort</span>
                      </div>
                    </div>
                  </div>
                ))}
              </Card>

              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>🚀 Long-Term Strategy</div>
                {(results.winning_strategy.long_term || []).map((w, i) => (
                  <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px', background: 'var(--bg3)', borderRadius: '8px', marginBottom: '8px' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'rgba(79,125,255,0.15)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, flexShrink: 0 }}>{i + 1}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '3px' }}>{w.action}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>Expected: {w.impact}</div>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '3px', background: 'rgba(79,125,255,0.1)', color: 'var(--accent)' }}>⏱ {w.timeline}</span>
                        <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '3px', background: 'var(--bg2)', color: 'var(--text3)' }}>{w.effort} effort</span>
                      </div>
                    </div>
                  </div>
                ))}
              </Card>

              {/* Action Plan */}
              <Card>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>✅ Action Plan</div>
                {(results.action_plan || []).map((action, i) => (
                  <div key={i} style={{ display: 'flex', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'var(--accent)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0 }}>{i + 1}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{action}</div>
                  </div>
                ))}
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  )
}

import { BASE } from '../api_config'
import { useState } from 'react'
import { RefreshCw, Search, Target, Zap, Plus, X } from 'lucide-react'


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
  const [mode, setMode] = useState('ai') // 'ai' | 'manual'
  const [discovering, setDiscovering] = useState(false)
  const [discoveredCompetitors, setDiscoveredCompetitors] = useState([])
  const [selectedCompetitors, setSelectedCompetitors] = useState([])
  const [manualUrls, setManualUrls] = useState(['', '', ''])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

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
          keywords: (seoReport?.keyword_suggestions || []).slice(0, 5).map(k => k.keyword),
          strengths: [],
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setResults(data)
    } catch (e) {
      setError('Analysis failed: ' + e.message)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--yellow-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Target size={18} color="var(--yellow)" />
        </div>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>Competitor Analysis</h2>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>AI-powered competitive intelligence for {domain}</p>
        </div>
      </div>

      {/* Mode toggle */}
      <div style={{ display: 'flex', background: 'var(--bg3)', borderRadius: '8px', padding: '3px', gap: '2px' }}>
        <button onClick={() => setMode('ai')} style={{
          flex: 1, padding: '7px', borderRadius: '6px', border: 'none', fontSize: '13px', cursor: 'pointer',
          background: mode === 'ai' ? 'var(--bg)' : 'transparent',
          color: mode === 'ai' ? 'var(--accent)' : 'var(--text3)',
          fontWeight: mode === 'ai' ? 500 : 400,
          boxShadow: mode === 'ai' ? 'var(--shadow)' : 'none',
        }}>🤖 AI Discovery</button>
        <button onClick={() => setMode('manual')} style={{
          flex: 1, padding: '7px', borderRadius: '6px', border: 'none', fontSize: '13px', cursor: 'pointer',
          background: mode === 'manual' ? 'var(--bg)' : 'transparent',
          color: mode === 'manual' ? 'var(--accent)' : 'var(--text3)',
          fontWeight: mode === 'manual' ? 500 : 400,
          boxShadow: mode === 'manual' ? 'var(--shadow)' : 'none',
        }}>✏️ Manual Entry</button>
      </div>

      {/* AI Discovery mode */}
      {mode === 'ai' && (
        <Card>
          <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>
            AI Competitor Discovery
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '12px', lineHeight: 1.6 }}>
            SEMA analyses your website, keywords, and industry to automatically identify your top competitors.
          </div>

          {discoveredCompetitors.length === 0 ? (
            <button onClick={discoverCompetitors} disabled={discovering} style={{
              width: '100%', padding: '10px', borderRadius: '8px', border: 'none',
              background: discovering ? 'var(--bg3)' : 'linear-gradient(135deg, #7c3aed, #4f7dff)',
              color: discovering ? 'var(--text3)' : 'white',
              fontSize: '13px', fontWeight: 600, cursor: discovering ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}>
              {discovering
                ? <><RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} /> Discovering competitors...</>
                : <><Zap size={15} /> Discover Competitors with AI</>
              }
            </button>
          ) : (
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '10px' }}>
                Select competitors to analyse ({selectedCompetitors.length} selected):
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                {discoveredCompetitors.map((comp, i) => {
                  const isSelected = selectedCompetitors.find(c => c.url === comp.url)
                  return (
                    <div key={i} onClick={() => toggleSelect(comp)} style={{
                      display: 'flex', alignItems: 'center', gap: '10px',
                      padding: '10px 12px', borderRadius: '8px', cursor: 'pointer',
                      background: isSelected ? 'var(--accent-bg)' : 'var(--bg3)',
                      border: `1px solid ${isSelected ? 'var(--accent-border)' : 'var(--border)'}`,
                      transition: 'all 0.15s',
                    }}>
                      <div style={{
                        width: '18px', height: '18px', borderRadius: '4px', flexShrink: 0,
                        border: `2px solid ${isSelected ? 'var(--accent)' : 'var(--border2)'}`,
                        background: isSelected ? 'var(--accent)' : 'transparent',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        {isSelected && <span style={{ color: 'white', fontSize: '11px', fontWeight: 700 }}>✓</span>}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '13px', fontWeight: 500, color: isSelected ? 'var(--accent)' : 'var(--text)' }}>
                          {comp.domain}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                          {comp.reason}
                        </div>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', background: 'var(--bg4)', padding: '2px 8px', borderRadius: '10px' }}>
                        {comp.similarity}% match
                      </div>
                    </div>
                  )
                })}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={discoverCompetitors} disabled={discovering} style={{
                  padding: '7px 12px', borderRadius: '7px', border: '1px solid var(--border)',
                  background: 'transparent', color: 'var(--text2)', fontSize: '12px', cursor: 'pointer',
                }}>
                  <RefreshCw size={12} style={{ display: 'inline', marginRight: '4px' }} /> Rediscover
                </button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Manual mode */}
      {mode === 'manual' && (
        <Card>
          <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>
            Enter Competitor URLs
          </div>
          {manualUrls.map((u, i) => (
            <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--text3)', width: '20px' }}>{i + 1}.</span>
              <input
                value={u}
                onChange={e => { const n = [...manualUrls]; n[i] = e.target.value; setManualUrls(n) }}
                placeholder={`https://competitor${i + 1}.com`}
                style={{ flex: 1, background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
              />
              {manualUrls.length > 1 && (
                <button onClick={() => setManualUrls(manualUrls.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', padding: '4px' }}>
                  <X size={14} />
                </button>
              )}
            </div>
          ))}
          {manualUrls.length < 5 && (
            <button onClick={() => setManualUrls([...manualUrls, ''])} style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '6px 12px', borderRadius: '7px', border: '1px dashed var(--border)',
              background: 'transparent', color: 'var(--text3)', fontSize: '12px', cursor: 'pointer',
            }}>
              <Plus size={12} /> Add competitor
            </button>
          )}
        </Card>
      )}

      {/* Analyse button */}
      <button onClick={analyze} disabled={analyzing || (mode === 'ai' && selectedCompetitors.length === 0 && discoveredCompetitors.length === 0)} style={{
        padding: '12px', borderRadius: '10px',
        background: analyzing ? 'var(--bg3)' : 'linear-gradient(135deg, #f59e0b, #fbbf24)',
        border: 'none', color: analyzing ? 'var(--text3)' : '#1a1a1a',
        fontSize: '14px', fontWeight: 600, cursor: analyzing ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
      }}>
        {analyzing
          ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Analysing competitors...</>
          : <><Search size={16} /> Analyse Competitors</>
        }
      </button>

      {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid var(--red)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

      {/* Results */}
      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Score comparison */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>Score Comparison</div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: 'var(--accent-bg)', borderRadius: '10px', border: '1px solid var(--accent-border)', flex: 1, minWidth: '140px' }}>
                <ScoreBadge score={results.my_site?.score || 0} />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{results.my_site?.domain}</div>
                  <div style={{ fontSize: '11px', color: 'var(--accent)' }}>Your site</div>
                </div>
              </div>
              {(results.competitors || []).map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)', flex: 1, minWidth: '140px' }}>
                  <ScoreBadge score={c.estimated_score || 0} />
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.domain}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{c.estimated_traffic}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Competitor details */}
          {(results.competitors || []).map((c, i) => (
            <Card key={i}>
              <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px', color: 'var(--yellow)' }}>{c.domain}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 600, marginBottom: '6px' }}>STRENGTHS</div>
                  {c.strengths?.map((s, j) => <div key={j} style={{ fontSize: '12px', color: 'var(--green)', marginBottom: '3px' }}>✓ {s}</div>)}
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 600, marginBottom: '6px' }}>WEAKNESSES</div>
                  {c.weaknesses?.map((w, j) => <div key={j} style={{ fontSize: '12px', color: 'var(--red)', marginBottom: '3px' }}>✗ {w}</div>)}
                </div>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text2)', padding: '8px', background: 'var(--bg3)', borderRadius: '6px', marginBottom: '6px' }}>📢 {c.ad_strategy}</div>
              <div style={{ fontSize: '12px', color: 'var(--text2)', padding: '8px', background: 'var(--bg3)', borderRadius: '6px' }}>📱 {c.social_presence}</div>
              <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {c.top_keywords?.map((k, j) => (
                  <span key={j} style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'var(--yellow-bg)', color: 'var(--yellow)', border: '1px solid var(--yellow)' }}>{k}</span>
                ))}
              </div>
            </Card>
          ))}

          {/* Opportunities & Threats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--green)' }}>🎯 Opportunities</div>
              {(results.opportunities || []).map((o, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '6px', paddingLeft: '8px', borderLeft: '2px solid var(--green)' }}>{o}</div>)}
            </Card>
            <Card>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--red)' }}>⚠ Threats</div>
              {(results.threats || []).map((t, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '6px', paddingLeft: '8px', borderLeft: '2px solid var(--red)' }}>{t}</div>)}
            </Card>
          </div>

          {/* Action Plan */}
          <Card style={{ background: 'var(--purple-bg)', border: '1px solid var(--purple)' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px', color: 'var(--purple)' }}>🚀 Action Plan</div>
            {(results.action_plan || []).map((a, i) => (
              <div key={i} style={{ display: 'flex', gap: '10px', marginBottom: '8px', alignItems: 'flex-start' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--purple)', background: 'rgba(83,74,183,0.15)', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{i + 1}</span>
                <span style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.6 }}>{a}</span>
              </div>
            ))}
          </Card>
        </div>
      )}
    </div>
  )
}

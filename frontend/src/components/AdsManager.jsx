import { BASE } from '../api_config'
import { useState, useEffect, useRef , useCallback } from 'react'
import {
  Play, Pause, BarChart3, RefreshCw, Zap, Target,
  TrendingUp, Shield, ExternalLink, CheckCircle,
  DollarSign, Megaphone, Eye, MousePointer
} from 'lucide-react'


function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem', ...style
    }}>{children}</div>
  )
}

function StatusBadge({ status }) {
  const map = {
    ENABLED: { bg: 'rgba(34,197,94,0.12)',  color: '#4ade80', label: '● Running' },
    PAUSED:  { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', label: '⏸ Paused' },
    REMOVED: { bg: 'rgba(239,68,68,0.12)',  color: '#f87171', label: '✕ Removed' },
  }
  const s = map[status] || { bg: 'rgba(79,125,255,0.12)', color: '#818cf8', label: status }
  return (
    <span style={{ background: s.bg, color: s.color, fontSize: '11px', fontWeight: 500, padding: '3px 8px', borderRadius: '4px' }}>
      {s.label}
    </span>
  )
}

// ─── Connect Panel ────────────────────────────────────────────────────────────
function ConnectPanel() {
  return (
    <Card>
      <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
        <div style={{
          width: '56px', height: '56px', borderRadius: '12px',
          background: 'rgba(79,125,255,0.1)', border: '1px solid rgba(79,125,255,0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem',
        }}>
          <Target size={24} color="var(--accent)" />
        </div>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>Connect Google Ads</h2>
        <p style={{ fontSize: '14px', color: 'var(--text2)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
          Connect once — your session is saved permanently. AI will create and manage your campaigns automatically.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '1.5rem' }}>
          {[
            { icon: Zap,        text: 'AI creates campaigns instantly' },
            { icon: Shield,     text: 'Auto-pause at budget limit' },
            { icon: TrendingUp, text: 'Real-time spend tracking' },
            { icon: RefreshCw,  text: 'Auto-resume on budget reset' },
          ].map(({ icon: Icon, text }) => (
            <div key={text} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '10px', background: 'var(--bg3)',
              borderRadius: '8px', border: '1px solid var(--border)',
              fontSize: '12px', color: 'var(--text2)', textAlign: 'left',
            }}>
              <Icon size={13} color="var(--accent)" style={{ flexShrink: 0 }} />
              {text}
            </div>
          ))}
        </div>
        <a href={`${BASE}/auth/google`} style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          background: 'var(--accent)', color: 'white',
          padding: '12px 28px', borderRadius: '8px',
          fontSize: '14px', fontWeight: 500, textDecoration: 'none',
        }}>
          <ExternalLink size={15} />
          Connect Google Ads Account
        </a>
      </div>
    </Card>
  )
}

// ─── Live Campaigns ───────────────────────────────────────────────────────────
function CampaignMonitor({ sessionId }) {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState({})
  const [lastRefresh, setLastRefresh] = useState(null)
  const [error, setError] = useState(null)
  const [seenSEMAAlert, setSeenSEMAAlert] = useState(false)

  useEffect(() => { 
    if (sessionId) fetchCampaigns() 
  }, [sessionId])

  async function fetchCampaigns() {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/ads/campaigns/${sessionId}?customer_id=7836650842`)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to fetch campaigns')
      }
      const data = await res.json()
      setCampaigns(data.campaigns || [])
      setLastRefresh(new Date().toLocaleTimeString())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function deleteCampaign(campaign) {
    if (!window.confirm(`Delete campaign "${campaign.campaign_name}"? This cannot be undone.`)) return
    setActionLoading(a => ({ ...a, [campaign.resource_name + '_del']: true }))
    try {
      const res = await fetch(`${BASE}/api/ads/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          customer_id: '7836650842',
          campaign_resource_name: campaign.resource_name,
        }),
      })
      const data = await res.json()
      if (data.success) await fetchCampaigns()
      else throw new Error((data.errors || []).join(', '))
    } catch (e) {
      setError(e.message)
    } finally {
      setActionLoading(a => ({ ...a, [campaign.resource_name + '_del']: false }))
    }
  }

  async function toggleCampaign(campaign) {
    setActionLoading(a => ({ ...a, [campaign.resource_name]: true }))
    try {
      const endpoint = campaign.status === 'PAUSED' ? '/api/ads/resume' : '/api/ads/pause'
      const res = await fetch(`${BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          customer_id: '',
          campaign_resource_name: campaign.resource_name,
        }),
      })
      const data = await res.json()
      if (data.success) await fetchCampaigns()
      else throw new Error((data.errors || []).join(', '))
    } catch (e) {
      setError(e.message)
    } finally {
      setActionLoading(a => ({ ...a, [campaign.resource_name]: false }))
    }
  }

  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
        <BarChart3 size={14} color="var(--accent)" />
        <h2 style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', flex: 1 }}>
          Live Campaigns
        </h2>
        {lastRefresh && <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Updated {lastRefresh}</span>}
        <button onClick={fetchCampaigns} disabled={loading} style={{
          background: 'none', border: '1px solid var(--border)', borderRadius: '6px',
          padding: '4px 8px', color: 'var(--text2)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px',
        }}>
          <RefreshCw size={11} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '7px', padding: '10px 12px', marginBottom: '12px', fontSize: '13px', color: '#f87171' }}>
          ⚠ {error}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text3)', fontSize: '13px' }}>
          <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 8px', display: 'block' }} />
          Fetching campaigns...
        </div>
      )}

      {!loading && campaigns.length === 0 && !error && (
        <div style={{ textAlign: 'center', padding: '2.5rem 1rem' }}>
          <BarChart3 size={36} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.2 }} />
          <p style={{ fontSize: '14px', color: 'var(--text2)', marginBottom: '6px' }}>No campaigns running</p>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>Use the Publish tab to create your first campaign from AI-generated ad copy</p>
        </div>
      )}

      {/* SEMA Performance Alert */}
      {!seenSEMAAlert && campaigns.some(c => (c.clicks || 0) === 0 && (c.impressions || 0) === 0 && c.status === 'ENABLED') && (
        <SEMAPerformanceAlert 
          campaigns={campaigns.filter(c => (c.clicks || 0) === 0 && (c.impressions || 0) === 0 && c.status === 'ENABLED')}
          sessionId={sessionId}
          onDismiss={() => setSeenSEMAAlert(true)}
        />
      )}

      {campaigns.map(c => {
        const monitor = c.budget_monitoring
        const spendPct = monitor
          ? Math.min((monitor.monthly_spend_usd / monitor.monthly_budget_usd) * 100, 100)
          : 0
        const isActionLoading = actionLoading[c.resource_name]
        return (
          <div key={c.resource_name} style={{
            background: 'var(--bg3)', border: '1px solid var(--border)',
            borderRadius: '10px', padding: '14px', marginBottom: '8px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: '14px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.campaign_name}
                </span>
                <StatusBadge status={c.status} />
              </div>
              <div style={{ display: 'flex', gap: '6px', flexShrink: 0, marginLeft: '8px' }}>
                <button onClick={() => toggleCampaign(c)} disabled={isActionLoading} style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '6px 12px', borderRadius: '6px',
                  background: c.status === 'ENABLED' ? 'rgba(245,158,11,0.1)' : 'rgba(34,197,94,0.1)',
                  border: `1px solid ${c.status === 'ENABLED' ? 'rgba(245,158,11,0.3)' : 'rgba(34,197,94,0.3)'}`,
                  color: c.status === 'ENABLED' ? '#fbbf24' : '#4ade80',
                  fontSize: '12px', fontWeight: 500, cursor: isActionLoading ? 'not-allowed' : 'pointer',
                }}>
                  {isActionLoading
                    ? <RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} />
                    : c.status === 'ENABLED' ? <><Pause size={11} /> Pause</> : <><Play size={11} /> Resume</>
                  }
                </button>
                <button onClick={() => deleteCampaign(c)} disabled={actionLoading[c.resource_name + '_del']} style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '6px 12px', borderRadius: '6px',
                  background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                  color: '#f87171', fontSize: '12px', fontWeight: 500, cursor: 'pointer',
                }}>
                  {actionLoading[c.resource_name + '_del']
                    ? <RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} />
                    : '🗑 Delete'
                  }
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '6px', marginBottom: monitor ? '10px' : '0' }}>
              {[
                { label: 'Spend Today', value: `₹${(c.spend_today_usd||0).toFixed(2)}`, color: 'var(--cyan)' },
                { label: 'Clicks',      value: (c.clicks||0).toLocaleString(),           color: 'var(--text)' },
                { label: 'Impressions', value: (c.impressions||0).toLocaleString(),      color: 'var(--text)' },
                { label: 'CTR',         value: `${(c.ctr||0).toFixed(2)}%`,              color: 'var(--green)' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: 'var(--bg4)', borderRadius: '7px', padding: '8px', textAlign: 'center' }}>
                  <div style={{ fontSize: '15px', fontWeight: 600, color }}>{value}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px' }}>{label}</div>
                </div>
              ))}
            </div>

            {monitor && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>
                  <span>Monthly spend: ${(monitor.monthly_spend_usd||0).toFixed(2)} / ${monitor.monthly_budget_usd}</span>
                  <span style={{ color: spendPct >= 90 ? '#f87171' : spendPct >= 75 ? '#fbbf24' : 'var(--text3)' }}>{spendPct.toFixed(1)}%</span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg4)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: '3px', width: `${spendPct}%`,
                    background: spendPct >= 100 ? '#ef4444' : spendPct >= 90 ? '#f59e0b' : 'var(--accent)',
                    transition: 'width 0.5s',
                  }} />
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>
                  ${(monitor.budget_remaining_usd||0).toFixed(2)} remaining · Auto-pauses at 100%
                </div>
              </div>
            )}
          </div>
        )
      })}
    </Card>
  )
}

// ─── Publish Panel ────────────────────────────────────────────────────────────
function PublishPanel({ sessionId, adCopy, seoReport, url, recommendedPages }) {
  const [mode, setMode] = useState('ai') // 'ai' | 'custom'
  const [aiRec, setAiRec] = useState(null)
  const [loadingRec, setLoadingRec] = useState(false)
  const [selectedVariant, setSelectedVariant] = useState(0)
  const [selectedPage, setSelectedPage] = useState(null)
  const [dailyBudget, setDailyBudget] = useState('15')
  const [monthlyBudget, setMonthlyBudget] = useState('400')
  const [campaignName, setCampaignName] = useState(() => {
    try { return `SEM-AI — ${new URL(url).hostname}` } catch { return 'SEM-AI Campaign' }
  })
  const [publishing, setPublishing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Auto-generate AI recommendation on mount
  useEffect(() => {
    if (adCopy && seoReport && !aiRec) generateAIRecommendation()
  }, [adCopy, seoReport])

  async function generateAIRecommendation() {
    setLoadingRec(true)
    try {
      const res = await fetch(`${BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Based on this SEO analysis and ad copy, give me a specific Google Ads campaign recommendation in JSON format only:
SEO Score: ${seoReport?.overall_seo_score || 'N/A'}
Keywords: ${(seoReport?.keyword_suggestions || []).slice(0,5).map(k=>k.keyword).join(', ')}
Ad variants: ${(adCopy?.ad_variants || []).map(v=>v.variant_name).join(', ')}
URL: ${url}

Respond ONLY with this JSON (no other text):
{"recommended_variant": 0, "variant_reason": "why this variant", "daily_budget": 1500, "monthly_budget": 40000, "budget_reason": "why this budget", "top_keywords": ["kw1","kw2","kw3"], "strategy": "2 sentence campaign strategy"}`,
          session_id: sessionId,
          customer_id: '7836650842',
        }),
      })
      const data = await res.json()
      try {
        const text = data.response || ''
        const clean = text.replace(/```json|```/g, '').trim()
        const rec = JSON.parse(clean)
        setAiRec(rec)
        // Apply AI recommendation
        setSelectedVariant(rec.recommended_variant || 0)
        setDailyBudget(String(rec.daily_budget || 1500))
        setMonthlyBudget(String(rec.monthly_budget || 40000))
      } catch {
        // Fallback recommendation
        setAiRec({
          recommended_variant: 0,
          variant_reason: "This variant uses proven persuasion principles for your industry.",
          daily_budget: 15,
          monthly_budget: 400,
          budget_reason: "Optimal starting budget to gather data without overspending.",
          top_keywords: (seoReport?.keyword_suggestions || []).slice(0,3).map(k=>k.keyword),
          strategy: "Start with a focused search campaign targeting your top keywords. Monitor for 7 days before optimizing."
        })
      }
    } catch {
      setAiRec(null)
    } finally {
      setLoadingRec(false)
    }
  }

  const variants = adCopy?.ad_variants || []
  const keywords = seoReport?.keyword_suggestions?.map(k => k.keyword) || []
  const targetCountries = seoReport?.sem_recommendations?.target_countries || ['IN', 'US']
  const domain = (() => { try { return new URL(url).hostname } catch { return url } })()
  const pages = recommendedPages || []

  async function handlePublish() {
    const daily = parseFloat(dailyBudget)
    const monthly = parseFloat(monthlyBudget)

    if (isNaN(daily) || daily < 1) {
      setError(`Daily budget too low ($${daily || 0}). Google Ads requires minimum $1.00/day.`)
      return
    }
    if (isNaN(monthly) || monthly < daily) {
      setError(`Monthly budget ($${monthly || 0}) must be at least equal to daily budget ($${daily}).`)
      return
    }

    const variant = variants[selectedVariant]
    if (!variant) { setError('No ad variant available. Please re-run the analysis.'); return }

    setPublishing(true)
    setError(null)

    try {
      const res = await fetch(`${BASE}/api/ads/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          customer_id: '',   // backend resolves from session automatically
          campaign_name: campaignName,
          daily_budget_usd: daily,
          monthly_budget_usd: monthly,
          target_countries: targetCountries,
          keywords: keywords.slice(0, 15),
          headlines: selectedPage?.ad_copy 
            ? [selectedPage.ad_copy.headline_1, selectedPage.ad_copy.headline_2, selectedPage.ad_copy.headline_3].filter(Boolean)
            : variant.headlines.map(h => h.text),
          descriptions: selectedPage?.ad_copy
            ? [selectedPage.ad_copy.description_1, selectedPage.ad_copy.description_2].filter(Boolean)
            : variant.descriptions.map(d => d.text),
          final_url: selectedPage?.url || url,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Publish failed')
      if (data.success === false) throw new Error((data.errors || []).join(', ') || 'Publish failed')
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setPublishing(false)
    }
  }

  if (result?.success) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '1.5rem' }}>
          <CheckCircle size={44} color="var(--green)" style={{ margin: '0 auto 12px', display: 'block' }} />
          <h3 style={{ fontSize: '17px', fontWeight: 600, marginBottom: '8px' }}>Campaign Published!</h3>
          <p style={{ fontSize: '13px', color: 'var(--text2)', marginBottom: '1rem' }}>{result.message}</p>
          <div style={{ background: 'var(--bg3)', borderRadius: '8px', padding: '12px', fontSize: '12px', fontFamily: 'var(--mono)', color: 'var(--text2)', textAlign: 'left', marginBottom: '1rem' }}>
            <div>✓ Campaign created</div>
            <div>✓ {result.keywords_added} keywords added</div>
            <div>✓ Budget monitor active — auto-pauses at ${monthlyBudget}/month</div>
          </div>
          <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: '8px', padding: '10px 14px', fontSize: '12px', color: '#fbbf24', textAlign: 'left' }}>
            ⚠ Campaign starts PAUSED for review. Enable it in the Live Campaigns tab or in Google Ads dashboard.
          </div>
          <button onClick={() => setResult(null)} style={{
            marginTop: '1rem', padding: '8px 20px', background: 'var(--bg3)',
            border: '1px solid var(--border)', borderRadius: '7px',
            color: 'var(--text2)', fontSize: '13px', cursor: 'pointer',
          }}>Publish Another</button>
        </div>
      </Card>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

      {/* Step 1: Select variant */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
          <Megaphone size={14} color="var(--accent)" />
          <h2 style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Step 1 — Choose Ad Variant
          </h2>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '12px' }}>
          Select which AI-generated copy to publish. All 3 options come from your Ad Copy analysis.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {variants.map((v, i) => {
            const isSelected = selectedVariant === i
            return (
              <div key={i} onClick={() => setSelectedVariant(i)} style={{
                border: `2px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: '10px', padding: '12px 14px', cursor: 'pointer',
                background: isSelected ? 'rgba(79,125,255,0.05)' : 'var(--bg3)',
                transition: 'border-color 0.15s',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <div style={{
                    width: '18px', height: '18px', borderRadius: '50%', flexShrink: 0,
                    border: `2px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
                    background: isSelected ? 'var(--accent)' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {isSelected && <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'white' }} />}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '13px', color: isSelected ? 'var(--accent)' : 'var(--text)' }}>
                    Option {i + 1}: {v.variant_name}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text3)' }}>{v.angle}</span>
                  {isSelected && (
                    <span style={{ marginLeft: 'auto', fontSize: '11px', background: 'rgba(79,125,255,0.15)', color: 'var(--accent)', padding: '2px 8px', borderRadius: '4px', fontWeight: 500 }}>
                      Selected
                    </span>
                  )}
                </div>

                {/* Ad preview */}
                <div style={{ background: 'var(--bg4)', borderRadius: '7px', padding: '10px 12px', marginBottom: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#4ade80', marginBottom: '2px' }}>Ad · {domain}{v.display_url_path}</div>
                  <div style={{ fontSize: '14px', color: 'var(--accent)', marginBottom: '4px', lineHeight: 1.3 }}>
                    {v.headlines.slice(0, 3).map(h => h.text).join(' | ')}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{v.descriptions[0]?.text}</div>
                </div>

                {/* Headlines chips */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {v.headlines.map((h, j) => (
                    <span key={j} style={{
                      fontSize: '11px', padding: '2px 7px',
                      background: 'var(--bg4)', borderRadius: '4px',
                      color: h.char_count > 30 ? '#f87171' : 'var(--text3)',
                      border: '1px solid var(--border)',
                    }}>
                      {h.text} <span style={{ opacity: 0.5 }}>{h.char_count}/30</span>
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Step 2: Budget */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
          <DollarSign size={14} color="var(--accent)" />
          <h2 style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Step 2 — Set Budget
          </h2>
        </div>

        {pages.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: 'var(--text2)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Landing Page (from Ad Copy)
              </label>
              <select value={selectedPage ? pages.indexOf(selectedPage) : -1}
                onChange={e => { const i = parseInt(e.target.value); setSelectedPage(i >= 0 ? pages[i] : null); if (i >= 0 && pages[i]) setCampaignName(pages[i].title?.slice(0,40) || campaignName) }}
                style={{ width: '100%', padding: '8px 10px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '7px', color: 'var(--text)', fontSize: '13px' }}>
                <option value={-1}>Use analysed URL: {url}</option>
                {pages.map((p, i) => <option key={i} value={i}>#{i+1} {p.title?.slice(0,50)} — {p.url?.replace('https://','').slice(0,40)}</option>)}
              </select>
              {selectedPage && <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--accent)', padding: '4px 8px', background: 'var(--accent-bg)', borderRadius: '4px' }}>✓ Using ad copy from: {selectedPage.url}</div>}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: 'var(--text2)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Campaign Name
            </label>
            <input value={campaignName} onChange={e => setCampaignName(e.target.value)}
              style={{ width: '100%', padding: '8px 10px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '7px', color: 'var(--text)', fontSize: '13px', outline: 'none', gridColumn: '1 / -1' }}
              onFocus={e => e.target.style.borderColor = 'var(--accent)'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
          <div style={{ gridColumn: '1 / -1', height: '1px', background: 'var(--border)' }} />
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: 'var(--text2)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Daily Budget (USD)</label>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', fontSize: '13px' }}>$</span>
              <input value={dailyBudget} onChange={e => setDailyBudget(e.target.value)} type="number" min="1"
                style={{ width: '100%', padding: '8px 10px 8px 22px', background: 'var(--bg3)', border: `1px solid ${parseFloat(dailyBudget) < 1 ? 'rgba(239,68,68,0.5)' : 'var(--border)'}`, borderRadius: '7px', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
                onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                onBlur={e => e.target.style.borderColor = parseFloat(dailyBudget) < 1 ? 'rgba(239,68,68,0.5)' : 'var(--border)'}
              />
            </div>
            {parseFloat(dailyBudget) < 1 && (
              <p style={{ fontSize: '11px', color: '#f87171', marginTop: '3px' }}>Minimum $1.00/day required</p>
            )}
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: 'var(--text2)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Monthly Budget (USD)</label>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', fontSize: '13px' }}>$</span>
              <input value={monthlyBudget} onChange={e => setMonthlyBudget(e.target.value)} type="number" min="1"
                style={{ width: '100%', padding: '8px 10px 8px 22px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '7px', color: 'var(--text)', fontSize: '13px', outline: 'none' }}
                onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                onBlur={e => e.target.style.borderColor = 'var(--border)'}
              />
            </div>
          </div>
        </div>

        {/* Summary */}
        <div style={{ background: 'var(--bg3)', borderRadius: '7px', padding: '10px 12px', marginBottom: '12px', fontSize: '12px', color: 'var(--text3)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <span style={{ color: parseFloat(dailyBudget) >= 1 ? '#4ade80' : '#f87171' }}>
            {parseFloat(dailyBudget) >= 1 ? '✓' : '✗'} Daily budget: ₹{dailyBudget}/day
          </span>
          <span>✓ {Math.min(keywords.length, 15)} keywords from SEO analysis</span>
          <span>✓ Target countries: {targetCountries.join(', ')}</span>
          <span>✓ Auto-pause enabled at ${monthlyBudget}/month</span>
          <span>✓ Customer ID loaded from your connected account</span>
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '7px', padding: '10px 12px', marginBottom: '12px', fontSize: '13px', color: '#f87171', lineHeight: 1.5 }}>
            ⚠ {error}
          </div>
        )}

        <button onClick={handlePublish} disabled={publishing || parseFloat(dailyBudget) < 1} style={{
          width: '100%', padding: '12px', background: publishing ? 'var(--bg4)' : 'var(--accent)',
          border: 'none', borderRadius: '8px', color: 'white', fontSize: '14px', fontWeight: 500,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
          cursor: publishing || parseFloat(dailyBudget) < 1 ? 'not-allowed' : 'pointer',
          opacity: parseFloat(dailyBudget) < 1 ? 0.5 : 1,
        }}>
          {publishing
            ? <><RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} /> Publishing...</>
            : <><Zap size={15} /> Publish Option {selectedVariant + 1}: {variants[selectedVariant]?.variant_name}</>
          }
        </button>
      </Card>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────


// ─── SEMA Performance Alert Component ────────────────────────────────────────
function SEMAPerformanceAlert({ campaigns, sessionId, onDismiss }) {
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [step, setStep] = useState('alert')
  const [pendingChanges, setPendingChanges] = useState([])
  const [applying, setApplying] = useState(false)

  function dismiss() { onDismiss && onDismiss() }

  async function handleAnalyze() {
    setStep('analyzing')
    setAnalyzing(true)
    try {
      const res = await fetch(`${BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: `My campaign "${campaigns[0]?.campaign_name}" has been running for several days but shows 0 clicks and 0 impressions. Please analyze why and give me specific fixes. Return analysis as JSON with: {"diagnosis": "reason", "issues": ["issue1","issue2"], "fixes": [{"change": "what to change", "reason": "why", "type": "bid|keyword|budget|targeting"}]}`,
        })
      })
      const data = await res.json()
      // Parse AI response
      let parsed = null
      try {
        const raw = data.response || data.message || ''
        const jsonMatch = raw.match(/\{[\s\S]*\}/)
        if (jsonMatch) parsed = JSON.parse(jsonMatch[0])
      } catch(e) {}
      
      if (parsed) {
        setAnalysis(parsed)
        setPendingChanges(parsed.fixes || [])
        setStep('results')
      } else {
        setAnalysis({ diagnosis: data.response || 'Analysis complete', issues: [], fixes: [] })
        setStep('results')
      }
    } catch(e) {
      setAnalysis({ diagnosis: 'Failed to analyze. Please try again.', issues: [], fixes: [] })
      setStep('results')
    }
    setAnalyzing(false)
  }

  async function applyChanges() {
    setApplying(true)
    try {
      const res = await fetch(`${BASE}/api/ads/apply-sema-fixes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          campaign_resource: campaigns[0]?.resource_name,
          fixes: pendingChanges,
        })
      })
      const data = await res.json()
      setApplied(true)
      setStep('done')
    } catch(e) {
      console.error(e)
    }
    setApplying(false)
  }

  return (
    <div style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.08), rgba(79,125,255,0.08))', border: '1px solid rgba(124,58,237,0.25)', borderRadius: '14px', padding: '1.25rem', marginBottom: '12px', position: 'relative' }}>
      <button onClick={dismiss} style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: '16px' }}>×</button>
      
      {step === 'alert' && (
        <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
          {/* SEMA Avatar */}
          <div style={{ width: '52px', height: '52px', borderRadius: '50%', background: 'linear-gradient(135deg, #7c3aed, #4f7dff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', flexShrink: 0, boxShadow: '0 0 20px rgba(124,58,237,0.3)' }}>
            🤖
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#a78bfa' }}>SEMA</span>
              <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '10px', background: 'rgba(124,58,237,0.15)', color: '#a78bfa' }}>AI Agent</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.6, margin: '0 0 12px' }}>
              👋 Hey! I noticed your campaign <strong style={{ color: 'var(--text)' }}>"{campaigns[0]?.campaign_name}"</strong> has been running for a few days but has <strong style={{ color: '#f87171' }}>0 clicks and 0 impressions</strong>. 
              Something might be blocking it. Want me to analyze why and fix it?
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={handleAnalyze} style={{ padding: '8px 18px', borderRadius: '8px', background: 'linear-gradient(135deg, #7c3aed, #4f7dff)', border: 'none', color: 'white', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>
                Yes, analyze it! 🔍
              </button>
              <button onClick={() => setShow(false)} style={{ padding: '8px 14px', borderRadius: '8px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', fontSize: '13px', cursor: 'pointer' }}>
                Not now
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'analyzing' && (
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
          <div style={{ width: '52px', height: '52px', borderRadius: '50%', background: 'linear-gradient(135deg, #7c3aed, #4f7dff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', flexShrink: 0 }}>🤖</div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#a78bfa', marginBottom: '4px' }}>SEMA is analyzing your campaign...</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)' }}>Checking bid settings, keywords, targeting, and ad quality...</div>
            <div style={{ marginTop: '8px', height: '4px', background: 'var(--bg3)', borderRadius: '2px', overflow: 'hidden', width: '200px' }}>
              <div style={{ height: '100%', background: 'linear-gradient(90deg, #7c3aed, #4f7dff)', borderRadius: '2px', animation: 'pulse 1.5s ease-in-out infinite', width: '60%' }} />
            </div>
          </div>
        </div>
      )}

      {step === 'results' && analysis && (
        <div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', marginBottom: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'linear-gradient(135deg, #7c3aed, #4f7dff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px', flexShrink: 0 }}>🤖</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#a78bfa', marginBottom: '6px' }}>SEMA's Analysis</div>
              <div style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.6, background: 'var(--bg3)', borderRadius: '8px', padding: '10px 12px', marginBottom: '10px' }}>
                {analysis.diagnosis}
              </div>
              {(analysis.issues || []).length > 0 && (
                <div style={{ marginBottom: '10px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#f87171', marginBottom: '6px' }}>⚠️ Issues Found:</div>
                  {analysis.issues.map((issue, i) => (
                    <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>→ {issue}</div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {pendingChanges.length > 0 && (
            <div style={{ background: 'var(--bg3)', borderRadius: '10px', padding: '12px', marginBottom: '12px' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '8px' }}>🔧 Recommended Changes:</div>
              {pendingChanges.map((fix, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', padding: '8px', background: 'var(--bg2)', borderRadius: '8px', marginBottom: '6px' }}>
                  <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'rgba(124,58,237,0.2)', color: '#a78bfa', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, flexShrink: 0 }}>{i+1}</div>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '2px' }}>{fix.change}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{fix.reason}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px' }}>
            {pendingChanges.length > 0 && (
              <button onClick={applyChanges} disabled={applying} style={{ padding: '8px 18px', borderRadius: '8px', background: 'linear-gradient(135deg, #7c3aed, #4f7dff)', border: 'none', color: 'white', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>
                {applying ? 'Applying...' : '✅ Apply Changes to Google Ads'}
              </button>
            )}
            <button onClick={() => setShow(false)} style={{ padding: '8px 14px', borderRadius: '8px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', fontSize: '13px', cursor: 'pointer' }}>
              Dismiss
            </button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'linear-gradient(135deg, #7c3aed, #4f7dff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px', flexShrink: 0 }}>🤖</div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#4ade80', marginBottom: '4px' }}>✅ Changes Applied!</div>
            <div style={{ fontSize: '12px', color: 'var(--text2)' }}>I've updated your campaign in Google Ads. Check back in a few hours to see performance improvements.</div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── SEMA Consult Component ───────────────────────────────────────────────────

function SEMAConsult({ sessionId }) {
  const [message, setMessage] = useState('')
  const [chat, setChat] = useState([])
  const [sending, setSending] = useState(false)
  const [pulse, setPulse] = useState(true)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat])

  useEffect(() => {
    const t = setInterval(() => setPulse(p => !p), 1500)
    return () => clearInterval(t)
  }, [])

  const quickQ = [
    "How are my campaigns performing?",
    "Which campaign has the best CTR?",
    "How can I reduce my cost per click?",
    "Should I increase my budget?",
    "Why are my impressions low?",
    "What keywords should I add?",
  ]

  async function send() {
    if (!message.trim() || sending) return
    const msg = message.trim()
    setMessage('')
    setSending(true)
    setChat(c => [...c, { role: 'user', text: msg }])
    try {
      const res = await fetch(`${BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId, customer_id: '7836650842' }),
      })
      const data = await res.json()
      setChat(c => [...c, { role: 'sema', text: data.response }])
    } catch {
      setChat(c => [...c, { role: 'sema', text: 'I encountered an error. Please try again.' }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`
        @keyframes pulse-ring {
          0% { transform: scale(1); opacity: 0.8; }
          50% { transform: scale(1.08); opacity: 0.4; }
          100% { transform: scale(1); opacity: 0.8; }
        }
        @keyframes float {
          0%,100% { transform: translateY(0px); }
          50% { transform: translateY(-4px); }
        }
        @keyframes typing {
          0%,60%,100% { opacity: 0.2; }
          30% { opacity: 1; }
        }
      `}</style>

      {/* Hero header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(124,58,237,0.08) 0%, rgba(79,125,255,0.08) 100%)',
        border: '1px solid rgba(124,58,237,0.2)',
        borderRadius: '16px', padding: '1.5rem',
        display: 'flex', alignItems: 'center', gap: '1.25rem',
      }}>
        {/* Animated avatar */}
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <div style={{
            position: 'absolute', inset: '-6px', borderRadius: '50%',
            border: '2px solid rgba(124,58,237,0.3)',
            animation: 'pulse-ring 2s ease-in-out infinite',
          }} />
          <div style={{
            width: '56px', height: '56px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #7c3aed, #4f7dff)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'float 3s ease-in-out infinite',
            fontSize: '24px',
          }}>🤖</div>
          <div style={{
            position: 'absolute', bottom: '2px', right: '2px',
            width: '12px', height: '12px', borderRadius: '50%',
            background: '#4ade80', border: '2px solid var(--bg2)',
          }} />
        </div>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>
            SEMA — Your AI SEM Expert
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>
            Get expert advice on your Google Ads campaigns. SEMA analyses your real campaign data 
            and provides precise, actionable recommendations to maximise your ROI.
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
            {['Campaign Analysis', 'Budget Optimisation', 'Keyword Strategy', 'Performance Insights'].map((tag, i) => (
              <span key={i} style={{
                fontSize: '10px', padding: '2px 8px', borderRadius: '10px',
                background: 'rgba(124,58,237,0.12)', color: '#a78bfa',
                border: '1px solid rgba(124,58,237,0.2)', fontWeight: 500,
              }}>{tag}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Quick questions */}
      <div>
        <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px', fontWeight: 600, letterSpacing: '0.05em' }}>
          SUGGESTED QUESTIONS
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {quickQ.map((q, i) => (
            <button key={i} onClick={() => setMessage(q)} style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              borderRadius: '20px', padding: '5px 12px', fontSize: '12px',
              color: 'var(--text2)', cursor: 'pointer', transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.target.style.borderColor = '#a78bfa'; e.target.style.color = '#a78bfa' }}
            onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text2)' }}
            >{q}</button>
          ))}
        </div>
      </div>

      {/* Chat */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{
          height: '320px', overflowY: 'auto', padding: '1rem',
          display: 'flex', flexDirection: 'column', gap: '10px',
        }}>
          {chat.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text3)' }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>💬</div>
              <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '6px' }}>Ask SEMA anything about your campaigns</div>
              <div style={{ fontSize: '12px' }}>Your personal AI SEM consultant is ready to help</div>
            </div>
          )}
          {chat.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
              {m.role === 'sema' && (
                <div style={{
                  width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                  background: 'linear-gradient(135deg, #7c3aed, #4f7dff)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '14px', marginRight: '8px', marginTop: '2px',
                }}>🤖</div>
              )}
              <div style={{
                maxWidth: '80%', padding: '10px 14px', fontSize: '13px', lineHeight: 1.6,
                borderRadius: m.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                background: m.role === 'user' ? '#7c3aed' : 'var(--bg3)',
                border: m.role === 'user' ? 'none' : '1px solid var(--border)',
                color: m.role === 'user' ? 'white' : 'var(--text)',
                whiteSpace: 'pre-wrap',
              }}>
                {m.role === 'sema' && (
                  <div style={{ fontSize: '9px', color: '#a78bfa', fontWeight: 700, marginBottom: '4px', letterSpacing: '0.08em' }}>SEMA</div>
                )}
                {m.text}
              </div>
            </div>
          ))}
          {sending && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%',
                background: 'linear-gradient(135deg, #7c3aed, #4f7dff)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px',
              }}>🤖</div>
              <div style={{
                padding: '10px 14px', borderRadius: '14px 14px 14px 4px',
                background: 'var(--bg3)', border: '1px solid var(--border)',
                display: 'flex', gap: '4px', alignItems: 'center',
              }}>
                {[0, 0.2, 0.4].map((d, i) => (
                  <div key={i} style={{
                    width: '6px', height: '6px', borderRadius: '50%', background: '#a78bfa',
                    animation: `typing 1s ${d}s ease-in-out infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '12px', borderTop: '1px solid var(--border)',
          display: 'flex', gap: '8px', alignItems: 'center',
          background: 'var(--bg2)',
        }}>
          <input
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask SEMA about your campaigns..."
            style={{
              flex: 1, background: 'var(--bg3)', border: '1px solid var(--border)',
              borderRadius: '10px', padding: '10px 14px', color: 'var(--text)',
              fontSize: '13px', outline: 'none',
            }}
          />
          <button onClick={send} disabled={sending || !message.trim()} style={{
            width: '40px', height: '40px', borderRadius: '10px',
            background: message.trim() ? '#7c3aed' : 'var(--bg3)',
            border: '1px solid var(--border)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.15s',
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={message.trim() ? 'white' : 'var(--text3)'} strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </Card>
    </div>
  )
}

// ─── Optimize Panel ───────────────────────────────────────────────────────────
function BidAdjuster({ rec, sessionId }) {
  const [pct, setPct] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [applying, setApplying] = useState(false)

  const isIncrease = rec.action === 'increase_bid'
  const min = rec.min_pct || (isIncrease ? 10 : 5)
  const max = rec.max_pct || (isIncrease ? 50 : 40)
  const ideal_min = rec.ideal_min_pct || (isIncrease ? 30 : 15)
  const ideal_max = rec.ideal_max_pct || (isIncrease ? 50 : 30)

  function getFeedback(val) {
    const v = parseFloat(val)
    if (isNaN(v) || v <= 0) return null
    if (isIncrease) {
      if (v < ideal_min) return {
        type: 'warning',
        color: '#f87171',
        icon: '⚠️',
        title: `Too low — below SEMA's recommended minimum of ${ideal_min}%`,
        reason: `A ${v}% increase may not be enough to meaningfully improve your ad rank and visibility. Your current CTR of ${((rec.current_ctr||0)*100).toFixed(2)}% suggests you need a stronger bid signal to compete. Consider at least ${ideal_min}% to see measurable results.`
      }
      if (v <= ideal_max) return {
        type: 'perfect',
        color: '#4ade80',
        icon: '✅',
        title: `Perfect — within SEMA's recommended range (${ideal_min}%–${ideal_max}%)`,
        reason: `A ${v}% bid increase is optimal for your campaign. This should improve your ad position without overspending. Expected outcome: ${Math.round(v * 0.6)}–${Math.round(v * 0.9)}% improvement in impressions within 3–5 days.`
      }
      return {
        type: 'aggressive',
        color: '#fbbf24',
        icon: '📈',
        title: `Aggressive — above SEMA's recommended max of ${ideal_max}%`,
        reason: `A ${v}% increase is higher than recommended. While this may boost visibility faster, it could significantly increase your cost-per-click. Monitor spend closely. If your conversion rate is above 3%, this may still be worthwhile. Reduce to ${ideal_max}% if spend exceeds budget within 48 hours.`
      }
    } else {
      if (v < ideal_min) return {
        type: 'warning',
        color: '#f87171',
        icon: '⚠️',
        title: `Too small — below SEMA's recommended minimum reduction of ${ideal_min}%`,
        reason: `A ${v}% decrease may not be enough to reduce wasted spend. Your campaign is currently overspending relative to results. Consider at least ${ideal_min}% reduction to meaningfully improve efficiency.`
      }
      if (v <= ideal_max) return {
        type: 'perfect',
        color: '#4ade80',
        icon: '✅',
        title: `Perfect — within SEMA's recommended range (${ideal_min}%–${ideal_max}%)`,
        reason: `A ${v}% bid reduction is well-calibrated. This should reduce wasted spend while maintaining ad visibility for your best-performing keywords. Review performance after 7 days.`
      }
      return {
        type: 'aggressive',
        color: '#fbbf24',
        icon: '📉',
        title: `Aggressive — above SEMA's recommended max reduction of ${ideal_max}%`,
        reason: `A ${v}% decrease is quite large and risks dropping your ads out of the auction entirely. Your impressions may fall sharply. If your goal is purely cost reduction, this may work — but you could lose significant traffic. Consider ${ideal_max}% first and evaluate after a week.`
      }
    }
  }

  const fb = getFeedback(pct)

  async function applyBidChange() {
    if (!pct || !fb) return
    setApplying(true)
    try {
      const res = await fetch(`${BASE}/api/ads/adjust-bid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          campaign_resource_name: rec.campaign_resource,
          adjustment_pct: isIncrease ? parseFloat(pct) : -parseFloat(pct),
          current_cpc_micros: rec.current_cpc_micros || 1000000,
        }),
      })
      const data = await res.json()
      if (data.success) {
        setFeedback({ 
          type: 'perfect', color: '#4ade80', icon: '✅', applied: true,
          title: `Bid ${isIncrease ? 'increased' : 'decreased'} by ${pct}% successfully!`,
          reason: `${data.message}. New CPC: ₹${data.new_cpc_inr}. Changes are now live in Google Ads and will take effect within minutes.`
        })
      } else {
        setFeedback({ type: 'error', color: '#f87171', icon: '❌', title: 'Failed to apply', reason: data.error || 'Unknown error' })
      }
    } catch (e) {
      setFeedback({ type: 'error', color: '#f87171', icon: '❌', title: 'Error', reason: e.message })
    } finally {
      setApplying(false)
    }
  }

  return (
    <div style={{ marginTop: '12px', padding: '12px', background: 'var(--bg4)', borderRadius: '8px', border: '1px solid var(--border)' }}>
      <div style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 600, marginBottom: '8px', letterSpacing: '0.05em' }}>
        {isIncrease ? '📈 INCREASE BID' : '📉 DECREASE BID'} — SEMA recommends {ideal_min}%–{ideal_max}%
      </div>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            type="number" min="1" max="100"
            value={pct}
            onChange={e => { setPct(e.target.value); setFeedback(null) }}
            placeholder={`Enter % (e.g. ${ideal_min}–${ideal_max})`}
            style={{
              width: '100%', background: 'var(--bg3)', border: `1px solid ${fb ? fb.color : 'var(--border)'}`,
              borderRadius: '8px', padding: '9px 40px 9px 12px', color: 'var(--text)',
              fontSize: '13px', outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
            }}
          />
          <span style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '12px', color: 'var(--text3)' }}>%</span>
        </div>
        <button onClick={applyBidChange} disabled={!pct || !fb || applying || fb?.applied} style={{
          padding: '9px 16px', borderRadius: '8px', fontSize: '12px', fontWeight: 600,
          background: fb?.applied ? 'rgba(34,197,94,0.15)' : fb?.type === 'perfect' ? '#4ade80' : fb ? 'var(--bg3)' : 'var(--bg3)',
          border: `1px solid ${fb?.type === 'perfect' ? '#4ade80' : 'var(--border)'}`,
          color: fb?.type === 'perfect' && !fb?.applied ? '#0a0a0a' : 'var(--text2)',
          cursor: applying || !pct || fb?.applied ? 'not-allowed' : 'pointer', flexShrink: 0,
        }}>
          {applying ? '...' : fb?.applied ? '✅ Applied' : `Apply ${isIncrease ? '↑' : '↓'}`}
        </button>
      </div>

      {/* Range indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
        <span style={{ fontSize: '10px', color: '#f87171' }}>Too low</span>
        <div style={{ flex: 1, height: '4px', borderRadius: '2px', background: `linear-gradient(to right, #f87171 0%, #f87171 ${ideal_min}%, #4ade80 ${ideal_min}%, #4ade80 ${ideal_max}%, #fbbf24 ${ideal_max}%, #fbbf24 100%)`, position: 'relative' }}>
          {pct && parseFloat(pct) > 0 && parseFloat(pct) <= 100 && (
            <div style={{
              position: 'absolute', top: '-4px', left: `${Math.min(parseFloat(pct), 100)}%`,
              transform: 'translateX(-50%)', width: '12px', height: '12px',
              borderRadius: '50%', background: fb?.color || 'white', border: '2px solid var(--bg4)',
              transition: 'left 0.2s',
            }} />
          )}
        </div>
        <span style={{ fontSize: '10px', color: '#fbbf24' }}>Too high</span>
      </div>

      {fb && (
        <div style={{
          padding: '10px 12px', borderRadius: '8px', marginTop: '4px',
          background: `${fb.color}12`, border: `1px solid ${fb.color}40`,
        }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: fb.color, marginBottom: '4px' }}>
            {fb.icon} {fb.title}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>{fb.reason}</div>
        </div>
      )}
    </div>
  )
}

function OptimizePanel({ sessionId }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [applying, setApplying] = useState({})

  async function runOptimization() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/ads/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function applyNegativeKeywords(rec) {
    if (!rec.negative_keywords?.length) return
    setApplying(a => ({ ...a, [rec.campaign_resource]: true }))
    try {
      const res = await fetch(`${BASE}/api/ads/negative-keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          campaign_resource_name: rec.campaign_resource,
          keywords: rec.negative_keywords,
        }),
      })
      const data = await res.json()
      if (data.success) alert(`✅ Added ${data.added} negative keywords!`)
      else throw new Error(data.error)
    } catch (e) {
      alert('Error: ' + e.message)
    } finally {
      setApplying(a => ({ ...a, [rec.campaign_resource]: false }))
    }
  }

  const healthColor = result?.overall_health === 'good' ? '#4ade80' : result?.overall_health === 'warning' ? '#fbbf24' : '#f87171'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ padding: '14px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }}>
        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>⚡ AI Campaign Optimiser</div>
        <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>
          SEMA analyses your campaign performance and recommends bid adjustments. Enter your desired percentage change — SEMA will validate it and explain the impact before applying.
        </div>
      </div>

      <button onClick={runOptimization} disabled={loading} style={{
        padding: '12px', borderRadius: '10px',
        background: loading ? 'var(--bg3)' : 'linear-gradient(135deg, #6366f1, #818cf8)',
        border: 'none', color: loading ? 'var(--text3)' : 'white',
        fontSize: '14px', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
      }}>
        {loading
          ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Analysing campaigns...</>
          : '⚡ Run AI Optimisation'
        }
      </button>

      {error && <div style={{ padding: '10px 14px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px', fontSize: '13px', color: '#f87171' }}>⚠ {error}</div>}

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ padding: '12px 14px', background: 'var(--bg3)', borderRadius: '10px', border: `1px solid ${healthColor}40` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: healthColor }} />
              <span style={{ fontSize: '13px', fontWeight: 600, color: healthColor, textTransform: 'capitalize' }}>
                {result.overall_health || 'Analysed'} — Campaign Health
              </span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text2)', lineHeight: 1.6 }}>{result.summary}</div>
          </div>

          {(result.recommendations || []).length === 0 ? (
            <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text3)', fontSize: '13px' }}>
              No optimisations needed — campaigns are performing well!
            </div>
          ) : (result.recommendations || []).map((rec, i) => (
            <div key={i} style={{ padding: '14px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{rec.campaign_name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                    CTR: {((rec.current_ctr || 0) * 100).toFixed(2)}% · Avg CPC: ₹{rec.avg_cpc || 0}
                  </div>
                </div>
                <span style={{
                  fontSize: '11px', padding: '3px 8px', borderRadius: '6px', fontWeight: 500,
                  background: rec.action === 'increase_bid' ? 'rgba(34,197,94,0.1)' : 'rgba(245,158,11,0.1)',
                  color: rec.action === 'increase_bid' ? '#4ade80' : '#fbbf24',
                  border: `1px solid ${rec.action === 'increase_bid' ? 'rgba(34,197,94,0.3)' : 'rgba(245,158,11,0.3)'}`,
                }}>
                  {rec.action === 'increase_bid' ? '📈 Increase Bid' : '📉 Decrease Bid'}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '4px', lineHeight: 1.6 }}>{rec.reason}</div>
              {rec.suggested_change && (
                <div style={{ fontSize: '12px', color: '#818cf8', marginBottom: '4px' }}>💡 SEMA suggests: {rec.suggested_change}</div>
              )}

              {(rec.action === 'increase_bid' || rec.action === 'decrease_bid') && (
                <BidAdjuster rec={rec} sessionId={sessionId} />
              )}

              {rec.negative_keywords?.length > 0 && (
                <div style={{ marginTop: '10px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '6px' }}>Suggested negative keywords:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '8px' }}>
                    {rec.negative_keywords.map((kw, j) => (
                      <span key={j} style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>−{kw}</span>
                    ))}
                  </div>
                  <button onClick={() => applyNegativeKeywords(rec)} disabled={applying[rec.campaign_resource]} style={{
                    padding: '6px 12px', borderRadius: '7px', fontSize: '12px',
                    background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                    color: '#f87171', cursor: 'pointer', fontWeight: 500,
                  }}>
                    {applying[rec.campaign_resource] ? 'Adding...' : '+ Add Negative Keywords'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Report Panel ─────────────────────────────────────────────────────────────
function ReportPanel({ sessionId }) {
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  async function generateReport() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/ads/report/${sessionId}`)
      const data = await res.json()
      if (data.success) setReport(data.report)
      else throw new Error(data.error || 'Failed to generate report')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function copyReport() {
    navigator.clipboard.writeText(report)
    alert('Report copied to clipboard!')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ padding: '14px', background: 'rgba(79,125,255,0.06)', border: '1px solid rgba(79,125,255,0.15)', borderRadius: '12px' }}>
        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>📊 Weekly Performance Report</div>
        <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.6 }}>
          AI-generated report summarising your campaign performance, highlights, and recommended actions for next week.
        </div>
      </div>

      <button onClick={generateReport} disabled={loading} style={{
        padding: '12px', borderRadius: '10px',
        background: loading ? 'var(--bg3)' : 'linear-gradient(135deg, #4f7dff, #818cf8)',
        border: 'none', color: loading ? 'var(--text3)' : 'white',
        fontSize: '14px', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
      }}>
        {loading
          ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Generating report...</>
          : '📊 Generate Weekly Report'
        }
      </button>

      {error && <div style={{ padding: '10px 14px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px', fontSize: '13px', color: '#f87171' }}>⚠ {error}</div>}

      {report && (
        <div style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '10px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>Weekly Report</div>
            <button onClick={copyReport} style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '5px 10px', borderRadius: '6px', fontSize: '11px',
              background: 'var(--bg4)', border: '1px solid var(--border)',
              color: 'var(--text2)', cursor: 'pointer',
            }}>
              📋 Copy Report
            </button>
          </div>
          <div style={{ fontSize: '13px', lineHeight: 1.8, color: 'var(--text)', whiteSpace: 'pre-wrap' }}>
            {report}
          </div>
        </div>
      )}
    </div>
  )
}


export default function AdsManager({ sessionId, adCopy, seoReport, url, recommendedPages, onRecommendedPages }) {
  const [seenSEMAAlert, setSeenSEMAAlert] = useState(false)
  const [tab, setTab] = useState(sessionId ? 'overview' : 'connect')

  useEffect(() => {
    setTab(sessionId ? 'overview' : 'connect')
  }, [sessionId])

  const tabs = sessionId
    ? [
        { id: 'overview', label: 'Live Campaigns' },
        { id: 'publish', label: 'Publish Campaign' },
        { id: 'sema', label: 'Consult SEMA' },
        { id: 'optimize', label: '⚡ Optimise' },
        { id: 'report', label: '📊 Report' },
      ]
    : [{ id: 'connect', label: 'Connect Account' }]

  return (
    <div>
      {sessionId && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem',
          padding: '8px 12px', background: 'rgba(34,197,94,0.06)',
          border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px',
          fontSize: '12px', color: '#4ade80',
        }}>
          <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#4ade80' }} />
          Google Ads connected · Budget monitor active · Auto-pauses at limit
        </div>
      )}

      <div style={{ display: 'flex', gap: '2px', marginBottom: '1rem', borderBottom: '1px solid var(--border)' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: '9px 14px', background: 'none', border: 'none',
            borderBottom: tab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
            color: tab === t.id ? 'var(--text)' : 'var(--text3)',
            fontSize: '13px', fontWeight: tab === t.id ? 500 : 400,
            cursor: 'pointer', marginBottom: '-1px',
          }}>{t.label}</button>
        ))}
      </div>

      {tab === 'connect' && <ConnectPanel />}
      {tab === 'overview' && sessionId && <CampaignMonitor sessionId={sessionId} />}
      {tab === 'publish' && sessionId && (
        <PublishPanel sessionId={sessionId} adCopy={adCopy} seoReport={seoReport} url={url} recommendedPages={recommendedPages || []} />
      )}
      {tab === 'sema' && sessionId && <SEMAConsult sessionId={sessionId} />}
      {tab === 'optimize' && sessionId && <OptimizePanel sessionId={sessionId} />}
      {tab === 'report' && sessionId && <ReportPanel sessionId={sessionId} />}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { BASE } from '../api_config'
import { Zap, RefreshCw, Copy, Check, ChevronDown, ChevronUp, ArrowRight, ExternalLink, MessageSquare, BarChart3, Plus } from 'lucide-react'

function CopyBtn({ text }) {
  const [ok, setOk] = useState(false)
  return (
    <button onClick={() => { navigator.clipboard.writeText(text); setOk(true); setTimeout(() => setOk(false), 2000) }}
      style={{ padding: '3px 8px', borderRadius: '5px', border: '1px solid var(--border)', background: 'var(--bg3)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text3)' }}>
      {ok ? <Check size={10} color="var(--green)" /> : <Copy size={10} />}
      {ok ? 'Copied' : 'Copy'}
    </button>
  )
}

function ScoreBadge({ score }) {
  const color = score >= 80 ? 'var(--green)' : score >= 60 ? 'var(--yellow)' : 'var(--red)'
  const bg = score >= 80 ? 'var(--green-bg)' : score >= 60 ? 'var(--yellow-bg)' : 'var(--red-bg)'
  const label = score >= 80 ? 'High' : score >= 60 ? 'Medium' : 'Low'
  return <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: bg, color, fontWeight: 600 }}>{label} {score}/100</span>
}

function AdCard({ ad, url, selected, onSelect }) {
  const [open, setOpen] = useState(false)
  const domain = url?.replace(/https?:\/\//, '').split('/')[0] || ''
  return (
    <div style={{ border: `2px solid ${selected ? 'var(--accent)' : 'var(--border)'}`, borderRadius: '12px', overflow: 'hidden', background: selected ? 'var(--accent-bg)' : 'var(--bg2)', transition: 'all 0.2s' }}>
      <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
        <input type="checkbox" checked={selected} onChange={onSelect} style={{ marginTop: '3px', width: '16px', height: '16px', cursor: 'pointer', accentColor: 'var(--accent)' }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-bg)', padding: '2px 8px', borderRadius: '4px' }}>{ad.angle}</span>
            <ScoreBadge score={ad.predicted_score || 75} />
          </div>
          <div style={{ padding: '10px 12px', background: 'white', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
            <div style={{ fontSize: '11px', color: '#666', marginBottom: '2px' }}>
              <span style={{ background: '#e8f0fe', color: '#1a73e8', padding: '1px 4px', borderRadius: '2px', fontSize: '10px', fontWeight: 600, marginRight: '4px' }}>Ad</span>
              {domain}
            </div>
            <div style={{ fontSize: '14px', color: '#1a0dab', fontWeight: 400, marginBottom: '3px', lineHeight: 1.3 }}>
              {ad.headlines?.slice(0, 3).join(' | ')}
            </div>
            <div style={{ fontSize: '12px', color: '#4d5156', lineHeight: 1.5 }}>{ad.descriptions?.[0]}</div>
          </div>
          {ad.why && <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '6px' }}>💡 {ad.why}</div>}
        </div>
        <button onClick={() => setOpen(!open)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', padding: '4px', flexShrink: 0 }}>
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>
      {open && (
        <div style={{ padding: '0 14px 14px', borderTop: '1px solid var(--border)' }}>
          <div style={{ marginTop: '12px', marginBottom: '10px' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Headlines</div>
            {(ad.headlines || []).map((h, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', background: 'var(--bg3)', borderRadius: '6px', marginBottom: '3px' }}>
                <span style={{ fontSize: '12px' }}>{h}</span>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0 }}>
                  <span style={{ fontSize: '10px', color: h.length > 30 ? 'var(--red)' : 'var(--text3)' }}>{h.length}/30</span>
                  <CopyBtn text={h} />
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Descriptions</div>
            {(ad.descriptions || []).map((d, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', padding: '6px 10px', background: 'var(--bg3)', borderRadius: '6px', marginBottom: '3px' }}>
                <span style={{ fontSize: '12px', lineHeight: 1.5 }}>{d}</span>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0 }}>
                  <span style={{ fontSize: '10px', color: d.length > 90 ? 'var(--red)' : 'var(--text3)' }}>{d.length}/90</span>
                  <CopyBtn text={d} />
                </div>
              </div>
            ))}
          </div>
          {ad.keywords?.length > 0 && (
            <div>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)', marginBottom: '6px', textTransform: 'uppercase' }}>Keywords</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {ad.keywords.map((k, i) => (
                  <span key={i} style={{ fontSize: '11px', padding: '3px 9px', borderRadius: '10px', background: 'var(--accent-bg)', color: 'var(--accent)', border: '1px solid var(--accent-border)' }}>{k}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function CampaignMonitor({ sessionId: propSessionId }) {
  const sessionId = propSessionId || sessionStorage.getItem('sem_session_id')
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState({})

  useEffect(() => {
    if (!sessionId) return
    fetchCampaigns()
  }, [sessionId])

  async function fetchCampaigns() {
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/api/ads/campaigns/${sessionId}?customer_id=7836650842`)
      const d = await res.json()
      setCampaigns((Array.isArray(d) ? d : d.campaigns || []).filter(c => c.status !== 'REMOVED').map(c => ({...c, id: c.campaign_id || c.id, name: c.campaign_name || c.name, resource_name: c.resource_name, budget: c.budget_usd ? Math.round(c.budget_usd * 83) : 0, status: c.status, clicks: c.clicks || 0, impressions: c.impressions || 0, ctr: c.ctr || 0, spend: c.spend_today_usd ? Math.round(c.spend_today_usd * 83) : 0})))
    } catch(e) {}
    setLoading(false)
  }

  async function toggleCampaign(id, status, resourceName) {
    setActionLoading(p => ({ ...p, [id]: true }))
    try {
      await fetch(`${BASE}/api/ads/${status === 'ENABLED' ? 'pause' : 'resume'}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, campaign_resource_name: resourceName })
      })
      fetchCampaigns()
    } catch(e) { console.error(e) }
    setActionLoading(p => ({ ...p, [id]: false }))
  }

  if (!sessionId) return (
    <div style={{ textAlign: 'center', padding: '24px', background: 'var(--bg3)', borderRadius: '10px' }}>
      <div style={{ fontSize: '32px', marginBottom: '8px' }}>🔗</div>
      <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Connect Google Ads to view campaigns</div>
      <a href={BASE + '/auth/google'} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 18px', borderRadius: '8px', background: 'linear-gradient(135deg, #4285f4, #34a853)', color: 'white', textDecoration: 'none', fontSize: '13px', fontWeight: 600 }}>
        Connect Google Ads
      </a>
    </div>
  )
  if (loading) return <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)' }}>⏳ Loading campaigns...</div>
  if (!campaigns.length) return (
    <div style={{ textAlign: 'center', padding: '24px', background: 'var(--bg3)', borderRadius: '10px', color: 'var(--text3)' }}>
      <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
      <div>No campaigns yet. Launch your first campaign above!</div>
    </div>
  )
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {campaigns.map(c => (
        <div key={c.id} style={{ padding: '14px', background: 'var(--bg2)', borderRadius: '10px', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name && c.name !== 'undefined' ? c.name : 'Campaign #' + (c.id?.toString().slice(-4) || '?')}</div>
              <div style={{ fontSize: '11px', color: 'var(--text3)' }}>₹{c.budget || 0}/day</div>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
              <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: c.status === 'ENABLED' ? 'var(--green-bg)' : 'var(--yellow-bg)', color: c.status === 'ENABLED' ? 'var(--green)' : 'var(--yellow)' }}>
                {c.status === 'ENABLED' ? '● Running' : '⏸ Paused'}
              </span>
              <button onClick={() => toggleCampaign(c.id, c.status, c.resource_name)} disabled={actionLoading[c.id]} style={{ padding: '4px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg3)', cursor: 'pointer', fontSize: '11px' }}>
                {actionLoading[c.id] ? '⏳' : c.status === 'ENABLED' ? '⏸ Pause' : '▶ Resume'}
              </button>
              <button onClick={async () => {
                if (!window.confirm('Remove this campaign?')) return
                try {
                  const removeRes = await fetch(`${BASE}/api/ads/campaigns/${c.id}/remove`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId, campaign_resource_name: c.resource_name })
                  })
                  const removeData = await removeRes.json()
                  console.log('Remove result:', removeData)
                  await fetchCampaigns()
                } catch(e) {}
              }} style={{ padding: '4px 10px', borderRadius: '6px', border: '1px solid var(--red)', background: 'var(--red-bg)', cursor: 'pointer', fontSize: '11px', color: 'var(--red)' }}>
                ✕ Remove
              </button>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '8px' }}>
            {[{ label: 'Clicks', value: c.clicks || 0 }, { label: 'Impressions', value: c.impressions || 0 }, { label: 'CTR', value: (c.ctr || 0) + '%' }, { label: 'Spend', value: '₹' + (c.spend || 0) }].map(({ label, value }) => (
              <div key={label} style={{ textAlign: 'center', padding: '8px', background: 'var(--bg3)', borderRadius: '8px' }}>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent)' }}>{value}</div>
                <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}


// ─── SEMA Agent ──────────────────────────────────────────────────────────────
function SEMAAgent({ sessionId }) {
  const [chat, setChat] = useState([
    { role: 'sema', text: 'Hi! I am SEMA, your AI SEM expert. I can help you optimize your campaigns, analyze performance, and suggest improvements. What would you like to know?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function sendMessage() {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setChat(c => [...c, { role: 'user', text: userMsg }])
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, session_id: sessionId })
      })
      const data = await res.json()
      setChat(c => [...c, { role: 'sema', text: data.response || 'No response received.' }])
    } catch(e) {
      setChat(c => [...c, { role: 'sema', text: 'Error connecting to SEMA. Please try again.' }])
    }
    setLoading(false)
  }

  const suggestions = [
    'Which campaign is performing best?',
    'Pause low performing ads',
    'Suggest budget optimization',
    'Generate weekly report',
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
        <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '4px' }}>🤖 SEMA — AI SEM Expert</div>
        <div style={{ fontSize: '12px', color: 'var(--text3)' }}>Ask anything about your campaigns, performance, and optimization</div>
      </div>
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ height: '350px', overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {chat.map((m, i) => (
            <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', flexDirection: m.role === 'user' ? 'row-reverse' : 'row' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', background: m.role === 'sema' ? 'var(--accent-bg)' : 'var(--bg3)', border: '1px solid var(--border)' }}>
                {m.role === 'sema' ? '🤖' : '👤'}
              </div>
              <div style={{ maxWidth: '75%', padding: '10px 12px', borderRadius: '10px', fontSize: '13px', lineHeight: 1.6, background: m.role === 'sema' ? 'var(--bg3)' : 'var(--accent-bg)', color: m.role === 'sema' ? 'var(--text)' : 'var(--accent)', border: `1px solid ${m.role === 'sema' ? 'var(--border)' : 'var(--accent-border)'}` }}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', background: 'var(--accent-bg)' }}>🤖</div>
              <div style={{ padding: '10px 12px', borderRadius: '10px', background: 'var(--bg3)', border: '1px solid var(--border)', fontSize: '13px', color: 'var(--text3)' }}>⏳ Thinking...</div>
            </div>
          )}
        </div>
        <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', display: 'flex', gap: '8px' }}>
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Ask SEMA anything..." style={{ flex: 1, padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px', outline: 'none' }} />
          <button onClick={sendMessage} disabled={loading || !input.trim()} style={{ padding: '8px 16px', borderRadius: '8px', background: input.trim() ? 'var(--accent)' : 'var(--bg3)', border: 'none', color: input.trim() ? 'white' : 'var(--text3)', cursor: input.trim() ? 'pointer' : 'not-allowed', fontWeight: 600, fontSize: '13px' }}>Send</button>
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {suggestions.map((s, i) => (
          <button key={i} onClick={() => { setInput(s); }} style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '20px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text2)', cursor: 'pointer' }}>{s}</button>
        ))}
      </div>
    </div>
  )
}

export default function SmartAdStudio({ url, seoReport, sessionId, googleEmail }) {
  const [mainTab, setMainTab] = useState('create') // create | campaigns | sema
  const [step, setStep] = useState('generate')
  const [generating, setGenerating] = useState(false)
  const [adVariants, setAdVariants] = useState([])
  const [selectedAds, setSelectedAds] = useState([])
  const [error, setError] = useState(null)
  const [launching, setLaunching] = useState(false)
  const [launched, setLaunched] = useState(false)
  const [budget, setBudget] = useState(500)
  const [targetCountry, setTargetCountry] = useState('IN')

  const isConnected = !!sessionId && !!googleEmail

  async function generateAds() {
    setGenerating(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/ads/generate-variants`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, seo_report: seoReport }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setAdVariants(data.variants || [])
      setStep('select')
    } catch(e) { setError(e.message) }
    setGenerating(false)
  }

  async function launchCampaign() {
    if (!selectedAds.length) { alert('Select at least one ad!'); return }
    setLaunching(true)
    try {
      const selected = adVariants.filter((_, i) => selectedAds.includes(i))
      const res = await fetch(`${BASE}/api/ads/publish`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          campaign_name: `SEMA - ${new URL(url).hostname} - ${new Date().toLocaleDateString()}`,
          daily_budget_usd: budget / 83,
          monthly_budget_usd: (budget * 30) / 83,
          target_countries: [targetCountry],
          keywords: selected.flatMap(a => a.keywords || []).slice(0, 20),
          headlines: selected.flatMap(a => a.headlines || []).slice(0, 15),
          descriptions: selected.flatMap(a => a.descriptions || []).slice(0, 4),
          final_url: url,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setLaunched(true)
      setMainTab('campaigns')
      setStep('generate')
    } catch(e) { setError(e.message) }
    setLaunching(false)
  }

  const steps = [
    { id: 'generate', label: '1. Generate', icon: '⚡' },
    { id: 'select', label: '2. Select', icon: '✅' },
    { id: 'launch', label: '3. Launch', icon: '🚀' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>

      {/* Main Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--border)', paddingBottom: '0' }}>
        {[
          { id: 'create', label: '⚡ Create Campaign', icon: Plus },
          { id: 'campaigns', label: '📊 My Campaigns', icon: BarChart3 },
          { id: 'sema', label: '🤖 SEMA Agent', icon: MessageSquare },
        ].map(t => (
          <button key={t.id} onClick={() => setMainTab(t.id)} style={{
            padding: '10px 18px', border: 'none', borderBottom: mainTab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
            background: 'transparent', color: mainTab === t.id ? 'var(--accent)' : 'var(--text3)',
            fontWeight: mainTab === t.id ? 700 : 500, fontSize: '13px', cursor: 'pointer',
          }}>{t.label}</button>
        ))}
      </div>

      {error && <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid var(--red)', borderRadius: '8px', fontSize: '13px', color: 'var(--red)' }}>⚠ {error}</div>}

      {/* My Campaigns Tab */}
      {mainTab === 'campaigns' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {launched && (
            <div style={{ padding: '12px 16px', background: 'var(--green-bg)', border: '1px solid var(--green)', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '20px' }}>🎉</span>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--green)' }}>Campaign Launched!</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Ads will appear in 1-2 hours</div>
              </div>
            </div>
          )}
          <CampaignMonitor sessionId={sessionId} />
        </div>
      )}

      {/* SEMA Tab */}
      {mainTab === 'sema' && <SEMAAgent sessionId={sessionId} />}

      {/* Create Campaign Tab */}
      {mainTab === 'create' && (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Progress Steps */}
      <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg2)', borderRadius: '12px', padding: '10px 16px', border: '1px solid var(--border)' }}>
        {steps.map((s, i) => (
          <div key={s.id} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
            <div onClick={() => adVariants.length > 0 && setStep(s.id)} style={{
              display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '8px', cursor: adVariants.length > 0 ? 'pointer' : 'default',
              background: step === s.id ? 'var(--accent-bg)' : 'transparent',
              color: step === s.id ? 'var(--accent)' : 'var(--text3)',
              fontWeight: step === s.id ? 700 : 400, fontSize: '12px',
              border: step === s.id ? '1px solid var(--accent-border)' : '1px solid transparent',
            }}>
              <span>{s.icon}</span><span>{s.label}</span>
            </div>
            {i < 2 && <ArrowRight size={14} color="var(--text3)" style={{ flexShrink: 0 }} />}
          </div>
        ))}
      </div>

      {/* Step 1: Generate */}
      {step === 'generate' && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px' }}>
          <div style={{ fontSize: '15px', fontWeight: 700, marginBottom: '8px' }}>⚡ AI Ad Variation Generator</div>
          <div style={{ fontSize: '13px', color: 'var(--text3)', lineHeight: 1.6, marginBottom: '16px' }}>
            AI will generate <strong>5-8 ad variations</strong> with different angles — each with a predicted CTR score so you pick the best ones.
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', marginBottom: '16px' }}>
            {[
              { icon: '🎯', label: 'Pain Point', desc: 'Address problems' },
              { icon: '💪', label: 'Benefit', desc: 'Key benefits' },
              { icon: '🏆', label: 'Social Proof', desc: 'Trust & credibility' },
              { icon: '🔥', label: 'Urgency', desc: 'Time-sensitive' },
              { icon: '❓', label: 'Question', desc: 'Engage curiosity' },
            ].map(({ icon, label, desc }) => (
              <div key={label} style={{ padding: '10px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center' }}>
                <div style={{ fontSize: '20px', marginBottom: '4px' }}>{icon}</div>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{label}</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{desc}</div>
              </div>
            ))}
          </div>
          <button onClick={generateAds} disabled={generating} style={{
            width: '100%', padding: '14px', borderRadius: '10px', fontSize: '14px', fontWeight: 600,
            background: generating ? 'var(--bg3)' : 'linear-gradient(135deg, var(--accent), #818cf8)',
            border: 'none', color: generating ? 'var(--text3)' : 'white', cursor: generating ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
          }}>
            {generating ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Generating...</> : <><Zap size={16} /> Generate Ad Variations</>}
          </button>
        </div>
      )}

      {/* Step 2: Select */}
      {step === 'select' && adVariants.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700 }}>✅ Select Your Best Ads</div>
              <div style={{ fontSize: '12px', color: 'var(--text3)' }}>{selectedAds.length} selected</div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={() => setSelectedAds(adVariants.map((_, i) => i))} style={{ fontSize: '11px', padding: '5px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg3)', cursor: 'pointer' }}>Select All</button>
              <button onClick={() => setSelectedAds([])} style={{ fontSize: '11px', padding: '5px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg3)', cursor: 'pointer' }}>Clear</button>
              <button onClick={() => setStep('launch')} disabled={!selectedAds.length} style={{
                fontSize: '12px', padding: '6px 14px', borderRadius: '8px',
                background: selectedAds.length ? 'var(--accent)' : 'var(--bg3)',
                border: 'none', color: selectedAds.length ? 'white' : 'var(--text3)',
                cursor: selectedAds.length ? 'pointer' : 'not-allowed', fontWeight: 600
              }}>Launch Selected →</button>
            </div>
          </div>
          {adVariants.map((ad, i) => (
            <AdCard key={i} ad={ad} url={url} selected={selectedAds.includes(i)}
              onSelect={() => setSelectedAds(p => p.includes(i) ? p.filter(x => x !== i) : [...p, i])} />
          ))}
        </div>
      )}

      {/* Step 3: Launch */}
      {step === 'launch' && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ fontSize: '15px', fontWeight: 700 }}>🚀 Campaign Settings</div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: '6px' }}>Daily Budget (₹)</label>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {[200, 500, 1000, 2000, 5000].map(b => (
                <button key={b} onClick={() => setBudget(b)} style={{
                  padding: '6px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: 600,
                  background: budget === b ? 'var(--accent-bg)' : 'var(--bg3)',
                  border: `1px solid ${budget === b ? 'var(--accent-border)' : 'var(--border)'}`,
                  color: budget === b ? 'var(--accent)' : 'var(--text2)', cursor: 'pointer',
                }}>₹{b}</button>
              ))}
              <input type="number" value={budget} onChange={e => setBudget(Number(e.target.value))}
                style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '12px' }} />
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>Monthly: ₹{(budget*30).toLocaleString()} | Est. clicks: {Math.round(budget/35)}-{Math.round(budget/25)}/day</div>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: '6px' }}>Target Country</label>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {[{code:'IN',flag:'🇮🇳',name:'India'},{code:'US',flag:'🇺🇸',name:'USA'},{code:'GB',flag:'🇬🇧',name:'UK'},{code:'AU',flag:'🇦🇺',name:'Australia'},{code:'SG',flag:'🇸🇬',name:'Singapore'}].map(({ code, flag, name }) => (
                <button key={code} onClick={() => setTargetCountry(code)} style={{
                  padding: '6px 12px', borderRadius: '8px', fontSize: '12px',
                  background: targetCountry === code ? 'var(--accent-bg)' : 'var(--bg3)',
                  border: `1px solid ${targetCountry === code ? 'var(--accent-border)' : 'var(--border)'}`,
                  color: targetCountry === code ? 'var(--accent)' : 'var(--text2)', cursor: 'pointer',
                }}>{flag} {name}</button>
              ))}
            </div>
          </div>

          <div style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>📋 Summary</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.8 }}>
              <div>✅ {selectedAds.length} ad variations</div>
              <div>🎯 {url}</div>
              <div>💰 ₹{budget}/day</div>
              <div>🌍 {targetCountry}</div>
            </div>
          </div>

          {!isConnected ? (
            <a href={`${BASE}/auth/google`} target="_blank" rel="noreferrer" style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              padding: '14px', borderRadius: '10px', fontSize: '14px', fontWeight: 600,
              background: 'linear-gradient(135deg, #4285f4, #34a853)', color: 'white', textDecoration: 'none',
            }}><ExternalLink size={16} /> Connect Google Ads to Launch</a>
          ) : (
            <button onClick={launchCampaign} disabled={launching} style={{
              width: '100%', padding: '14px', borderRadius: '10px', fontSize: '14px', fontWeight: 600,
              background: launching ? 'var(--bg3)' : 'linear-gradient(135deg, #4285f4, #34a853)',
              border: 'none', color: launching ? 'var(--text3)' : 'white', cursor: launching ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}>
              {launching ? <><RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> Launching...</> : <>🚀 Launch on Google Ads</>}
            </button>
          )}
          <div style={{ fontSize: '11px', color: 'var(--text3)', textAlign: 'center', marginTop: '8px' }}>
            Connected as: {googleEmail || 'Not connected'}
          </div>
        </div>
      )}
      </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}

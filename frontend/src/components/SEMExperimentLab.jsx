import { useState, useEffect } from 'react'
import { BASE } from '../api_config'
import { Zap, RefreshCw, Plus, TrendingUp, Target, BarChart3, Play, CheckCircle } from 'lucide-react'

export default function SEMExperimentLab({ url, seoReport, sessionId }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [experiments, setExperiments] = useState([])
  const [newExp, setNewExp] = useState({ hypothesis: '', type: 'budget', variant_a: '', variant_b: '' })

  const sem = seoReport?.sem_recommendations || {}
  const budget = sem.monthly_budget_inr || 0
  const cpc = sem.estimated_cpc_inr || 35
  const clicks = sem.monthly_clicks_estimate || '0'

  async function generateAnalysis() {
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/api/sem/experiment-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, seo_report: seoReport, session_id: sessionId })
      })
      const data = await res.json()
      setAnalysis(data)
    } catch(e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => {
    if (url && seoReport) generateAnalysis()
  }, [])

  function addExperiment() {
    if (!newExp.hypothesis) return
    setExperiments(prev => [...prev, {
      id: Date.now(),
      ...newExp,
      status: 'running',
      created: new Date().toLocaleDateString(),
      result: null
    }])
    setNewExp({ hypothesis: '', type: 'budget', variant_a: '', variant_b: '' })
  }

  const tabs = [
    { id: 'overview', label: '📊 SEM Overview' },
    { id: 'simulator', label: '🔮 What-If Simulator' },
    { id: 'experiments', label: '🧪 Experiments' },
    { id: 'roadmap', label: '🗺️ Roadmap' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--border)', paddingBottom: '0' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: '8px 16px', border: 'none',
            borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
            background: 'transparent', color: activeTab === t.id ? 'var(--accent)' : 'var(--text3)',
            fontWeight: activeTab === t.id ? 700 : 500, fontSize: '13px', cursor: 'pointer',
          }}>{t.label}</button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Key Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '12px' }}>
            {[
              { label: 'Monthly Budget', value: `₹${budget.toLocaleString()}`, sub: 'Recommended', color: 'var(--green)', icon: '💰' },
              { label: 'Est. Clicks/mo', value: clicks, sub: `@₹${cpc} avg CPC`, color: 'var(--cyan)', icon: '👆' },
              { label: 'Competition', value: sem.competition_level || 'Medium', sub: 'In your niche', color: 'var(--yellow)', icon: '⚔️' },
            ].map(({ label, value, sub, color, icon }) => (
              <div key={label} style={{ padding: '16px', background: 'var(--bg2)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>{icon}</div>
                <div style={{ fontSize: '22px', fontWeight: 700, color }}>{value}</div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)' }}>{label}</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{sub}</div>
              </div>
            ))}
          </div>

          {/* AI Analysis */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700 }}>🤖 AI SEM Analysis</div>
              <button onClick={generateAnalysis} disabled={loading} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg3)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <RefreshCw size={11} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
                {loading ? 'Analysing...' : 'Refresh'}
              </button>
            </div>
            {loading && <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)' }}>⏳ AI analysing your SEM potential...</div>}
            {analysis && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {(analysis.insights || []).map((insight, i) => (
                  <div key={i} style={{ padding: '12px', background: 'var(--bg3)', borderRadius: '8px', border: '1px solid var(--border)', display: 'flex', gap: '10px' }}>
                    <span style={{ fontSize: '18px', flexShrink: 0 }}>{insight.icon || '💡'}</span>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '3px' }}>{insight.title}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.5 }}>{insight.description}</div>
                      {insight.action && <div style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '4px', fontWeight: 600 }}>→ {insight.action}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Country budgets */}
          {(sem.country_budgets || []).length > 0 && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>🌍 Market Budget Split</div>
              {sem.country_budgets.map((cb, i) => {
                const flag = {IN:'🇮🇳',US:'🇺🇸',GB:'🇬🇧',UK:'🇬🇧',AU:'🇦🇺',CA:'🇨🇦',SG:'🇸🇬',AE:'🇦🇪'}[cb.code] || '🌍'
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '16px' }}>{flag}</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, width: '80px' }}>{cb.country}</span>
                    <div style={{ flex: 1, height: '8px', background: 'var(--bg4)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: cb.budget_pct + '%', background: 'var(--accent)', borderRadius: '4px' }} />
                    </div>
                    <span style={{ fontSize: '12px', color: 'var(--text3)', width: '40px', textAlign: 'right' }}>{cb.budget_pct}%</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--green)', width: '70px', textAlign: 'right' }}>₹{(cb.budget_inr||0).toLocaleString()}</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* What-If Simulator */}
      {activeTab === 'simulator' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '4px' }}>🔮 What-If Simulator</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '16px' }}>Simulate different scenarios and see projected impact</div>
            
            {[
              { label: 'Double my budget', icon: '💰', current: `₹${budget.toLocaleString()}/mo`, projected: `₹${(budget*2).toLocaleString()}/mo`, impact: `+${Math.round(parseInt(clicks.toString().split('-')[0] || '0') * 1.8).toLocaleString()} clicks`, positive: true },
              { label: 'Reduce budget by 30%', icon: '📉', current: `₹${budget.toLocaleString()}/mo`, projected: `₹${Math.round(budget*0.7).toLocaleString()}/mo`, impact: `-${Math.round(parseInt(clicks.toString().split('-')[0] || '0') * 0.35).toLocaleString()} clicks`, positive: false },
              { label: 'Target India only', icon: '🇮🇳', current: 'Multiple countries', projected: 'India focus', impact: 'Lower CPC, Higher volume', positive: true },
              { label: 'Increase bids by 20%', icon: '⬆️', current: `₹${cpc} avg CPC`, projected: `₹${Math.round(cpc*1.2)} avg CPC`, impact: 'Better ad position, +15% CTR', positive: true },
              { label: 'Switch to broad match', icon: '🎯', current: 'Exact match', projected: 'Broad match', impact: '+40% reach, +25% CPC', positive: null },
              { label: 'Add 10 negative keywords', icon: '🚫', current: 'Current targeting', projected: 'Refined targeting', impact: '-15% wasted spend', positive: true },
            ].map(({ label, icon, current, projected, impact, positive }) => (
              <div key={label} style={{ padding: '14px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '24px', flexShrink: 0 }}>{icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>{label}</div>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: 'var(--text3)' }}>
                    <span>Now: {current}</span>
                    <span>→</span>
                    <span>After: {projected}</span>
                  </div>
                </div>
                <div style={{ padding: '4px 10px', borderRadius: '8px', fontSize: '12px', fontWeight: 600,
                  background: positive === true ? 'var(--green-bg)' : positive === false ? 'var(--red-bg)' : 'var(--yellow-bg)',
                  color: positive === true ? 'var(--green)' : positive === false ? 'var(--red)' : 'var(--yellow)',
                  flexShrink: 0
                }}>{impact}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Experiments Tab */}
      {activeTab === 'experiments' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Create experiment */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>➕ New Experiment</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <input value={newExp.hypothesis} onChange={e => setNewExp(p => ({...p, hypothesis: e.target.value}))}
                placeholder="Hypothesis: e.g. Increasing budget by 20% will improve CTR by 15%"
                style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                <select value={newExp.type} onChange={e => setNewExp(p => ({...p, type: e.target.value}))}
                  style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px' }}>
                  <option value="budget">Budget Test</option>
                  <option value="bidding">Bid Strategy</option>
                  <option value="ad_copy">Ad Copy</option>
                  <option value="targeting">Targeting</option>
                  <option value="keywords">Keywords</option>
                </select>
                <input value={newExp.variant_a} onChange={e => setNewExp(p => ({...p, variant_a: e.target.value}))}
                  placeholder="Variant A (Control)"
                  style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px' }} />
                <input value={newExp.variant_b} onChange={e => setNewExp(p => ({...p, variant_b: e.target.value}))}
                  placeholder="Variant B (Test)"
                  style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg3)', color: 'var(--text)', fontSize: '13px' }} />
              </div>
              <button onClick={addExperiment} disabled={!newExp.hypothesis} style={{
                padding: '10px', borderRadius: '8px', border: 'none',
                background: newExp.hypothesis ? 'var(--accent)' : 'var(--bg3)',
                color: newExp.hypothesis ? 'white' : 'var(--text3)',
                cursor: newExp.hypothesis ? 'pointer' : 'not-allowed', fontWeight: 600, fontSize: '13px'
              }}>🧪 Start Experiment</button>
            </div>
          </div>

          {/* Experiment list */}
          {experiments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', background: 'var(--bg3)', borderRadius: '10px', color: 'var(--text3)' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🧪</div>
              <div style={{ fontSize: '13px' }}>No experiments yet. Create your first experiment above!</div>
            </div>
          ) : (
            experiments.map(exp => (
              <div key={exp.id} style={{ padding: '14px', background: 'var(--bg2)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600 }}>{exp.hypothesis}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>Started: {exp.created} | Type: {exp.type}</div>
                  </div>
                  <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'var(--green-bg)', color: 'var(--green)', fontWeight: 600 }}>
                    ● Running
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div style={{ padding: '8px', background: 'var(--bg3)', borderRadius: '6px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text3)', marginBottom: '2px' }}>VARIANT A (Control)</div>
                    <div style={{ fontSize: '12px' }}>{exp.variant_a || 'Current setup'}</div>
                  </div>
                  <div style={{ padding: '8px', background: 'var(--accent-bg)', borderRadius: '6px', border: '1px solid var(--accent-border)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--accent)', marginBottom: '2px' }}>VARIANT B (Test)</div>
                    <div style={{ fontSize: '12px' }}>{exp.variant_b || 'New variant'}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Roadmap Tab */}
      {activeTab === 'roadmap' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px' }}>🗺️ Your SEM Roadmap</div>
            {[
              { week: 'Week 1', title: 'Launch & Setup', color: 'var(--accent)', tasks: ['Create first campaign with AI-generated ads', 'Set up conversion tracking', 'Configure budget and targeting', 'Launch and monitor for 48 hours'] },
              { week: 'Week 2-3', title: 'Optimize & Test', color: 'var(--cyan)', tasks: ['Analyse CTR — pause ads below 0.5%', 'A/B test headlines', 'Add negative keywords from search terms', 'Adjust bids based on performance'] },
              { week: 'Month 2', title: 'Scale Winners', color: 'var(--green)', tasks: ['Increase budget for top campaigns', 'Expand to new keyword variations', 'Test new markets/countries', 'Create remarketing campaign'] },
              { week: 'Month 3+', title: 'Advanced Strategy', color: 'var(--purple)', tasks: ['Target CPA/ROAS bidding', 'Dynamic search ads', 'Competitor keyword targeting', 'Seasonal campaign planning'] },
            ].map(({ week, title, color, tasks }, i) => (
              <div key={i} style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '13px', fontWeight: 700 }}>{i+1}</div>
                  {i < 3 && <div style={{ width: '2px', flex: 1, background: 'var(--border)', marginTop: '4px', minHeight: '40px' }} />}
                </div>
                <div style={{ flex: 1, paddingBottom: '16px' }}>
                  <div style={{ fontSize: '11px', color, fontWeight: 600, marginBottom: '2px' }}>{week}</div>
                  <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '8px' }}>{title}</div>
                  {tasks.map((task, j) => (
                    <div key={j} style={{ display: 'flex', gap: '6px', marginBottom: '4px', alignItems: 'center' }}>
                      <CheckCircle size={12} color="var(--text3)" />
                      <span style={{ fontSize: '12px', color: 'var(--text2)' }}>{task}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

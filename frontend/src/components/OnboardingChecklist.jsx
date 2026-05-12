import { useState, useEffect } from 'react'
import { CheckCircle, Circle } from 'lucide-react'

const ITEMS = [
  { id: 'analyse', label: 'Analyse your first website', tab: null },
  { id: 'seo', label: 'Review SEO report', tab: 'seo' },
  { id: 'adcopy', label: 'Generate ad copy', tab: 'ad-copy' },
  { id: 'ads', label: 'Connect Google Ads', tab: 'ads' },
  { id: 'autopilot', label: 'Enable Auto-Pilot', tab: 'ads' },
  { id: 'aitraffic', label: 'Set up AI Traffic tracker', tab: 'ai-traffic' },
]

export default function OnboardingChecklist({ currentTab, hasAnalysed, googleConnected }) {
  const [checked, setChecked] = useState(() => {
    try { return JSON.parse(localStorage.getItem('sem_checklist') || '{}') } catch { return {} }
  })
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const next = { ...checked }
    if (hasAnalysed) next['analyse'] = true
    if (currentTab === 'seo' && hasAnalysed) next['seo'] = true
    if (currentTab === 'ad-copy' && hasAnalysed) next['adcopy'] = true
    if (googleConnected) next['ads'] = true
    if (googleConnected && localStorage.getItem('sem_autopilot_enabled') === 'true') next['autopilot'] = true
    if (currentTab === 'ai-traffic') next['aitraffic'] = true
    localStorage.setItem('sem_checklist', JSON.stringify(next))
    setChecked(next)
  }, [currentTab, hasAnalysed])

  const total = ITEMS.length
  const done = ITEMS.filter(i => checked[i.id]).length
  const pct = Math.round((done / total) * 100)

  if (done === total) return null // Hide when complete

  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', overflow: 'hidden', marginBottom: '12px',
    }}>
      {/* Header */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        style={{
          padding: '10px 14px', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
            🚀 Getting started
          </span>
          <span style={{
            fontSize: '11px', color: '#a5b4fc',
            background: 'rgba(99,102,241,0.15)',
            padding: '2px 8px', borderRadius: '10px', fontWeight: 600,
          }}>{done}/{total}</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{collapsed ? '▼' : '▲'}</span>
      </div>

      {/* Progress bar */}
      <div style={{ height: '3px', background: 'var(--bg3)', margin: '0 14px' }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
          borderRadius: '2px', transition: 'width 0.5s',
        }} />
      </div>

      {/* Items */}
      {!collapsed && (
        <div style={{ padding: '10px 14px 12px' }}>
          {ITEMS.map(item => (
            <div key={item.id} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '5px 0',
            }}>
              {checked[item.id]
                ? <CheckCircle size={14} color="#22c55e" />
                : <Circle size={14} color="var(--text3)" />
              }
              <span style={{
                fontSize: '12px',
                color: checked[item.id] ? 'var(--text3)' : 'var(--text2)',
                textDecoration: checked[item.id] ? 'line-through' : 'none',
              }}>{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

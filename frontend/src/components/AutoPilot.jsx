import { useState, useEffect } from 'react'
import { BASE } from '../api_config'
import { Bot, Play, Pause, Zap, AlertTriangle, CheckCircle, Info } from 'lucide-react'

export default function AutoPilot({ sessionId, customerId = '7836650842' }) {
  const [enabled, setEnabled] = useState(false)
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [actions, setActions] = useState([])
  const [lastRun, setLastRun] = useState(null)

  useEffect(() => {
    fetchStatus()
  }, [])

  async function fetchStatus() {
    try {
      const res = await fetch(BASE + '/api/ads/autopilot/status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
      const d = await res.json()
      setEnabled(d.enabled)
      setLastRun(d.last_run)
      setActions(d.actions || [])
    } catch(e) {}
  }

  async function toggleAutoPilot() {
    setLoading(true)
    try {
      const res = await fetch(BASE + '/api/ads/autopilot/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, enabled: !enabled })
      })
      const d = await res.json()
      if (d.success) setEnabled(!enabled)
    } catch(e) {}
    setLoading(false)
  }

  async function runNow() {
    setRunning(true)
    try {
      const res = await fetch(BASE + '/api/ads/autopilot/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, customer_id: customerId })
      })
      const d = await res.json()
      if (d.success) {
        setActions(d.actions || [])
        setLastRun(new Date().toISOString())
      }
    } catch(e) {}
    setRunning(false)
  }

  const severityColor = { high: '#f87171', medium: '#fbbf24', low: '#4ade80', info: '#60a5fa' }
  const typeIcon = { warning: AlertTriangle, ai_recommendation: Zap, info: CheckCircle }

  return (
    <div style={{ padding: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bot size={22} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text)', margin: 0 }}>Auto-Pilot Mode</h2>
            <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0 }}>AI monitors and optimizes your campaigns 24/7</p>
          </div>
        </div>
        {/* Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '13px', color: enabled ? '#4ade80' : 'var(--text2)', fontWeight: 600 }}>
            {enabled ? '● ACTIVE' : '○ INACTIVE'}
          </span>
          <div onClick={!loading ? toggleAutoPilot : undefined}
            style={{ width: '52px', height: '28px', borderRadius: '14px', background: enabled ? '#6366f1' : 'var(--bg3)', cursor: loading ? 'not-allowed' : 'pointer', position: 'relative', transition: 'all 0.3s' }}>
            <div style={{ position: 'absolute', top: '3px', left: enabled ? '26px' : '3px', width: '22px', height: '22px', borderRadius: '50%', background: 'white', transition: 'all 0.3s' }} />
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '1.5rem' }}>
        {[
          { label: 'Status', value: enabled ? 'Running' : 'Paused', color: enabled ? '#4ade80' : '#f87171' },
          { label: 'Last Run', value: lastRun ? new Date(lastRun).toLocaleTimeString() : 'Never' },
          { label: 'Actions Found', value: actions.length }
        ].map((card, i) => (
          <div key={i} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '4px' }}>{card.label}</div>
            <div style={{ fontSize: '20px', fontWeight: 700, color: card.color || 'var(--text)' }}>{card.value}</div>
          </div>
        ))}
      </div>

      {/* Run Now Button */}
      <button onClick={runNow} disabled={running}
        style={{ width: '100%', padding: '12px', borderRadius: '10px', background: running ? 'var(--bg3)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: 'white', fontSize: '14px', fontWeight: 600, cursor: running ? 'not-allowed' : 'pointer', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
        <Play size={16} />
        {running ? 'Analyzing Campaigns...' : 'Run Auto-Pilot Now'}
      </button>

      {/* Actions Log */}
      {actions.length > 0 && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
            📋 Auto-Pilot Report
          </div>
          {actions.map((a, i) => {
            const Icon = typeIcon[a.type] || Info
            const color = severityColor[a.severity] || '#60a5fa'
            return (
              <div key={i} style={{ padding: '12px 16px', borderBottom: i < actions.length-1 ? '1px solid var(--border)' : 'none', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <Icon size={16} color={color} style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  {a.campaign && <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '2px' }}>{a.campaign}</div>}
                  <div style={{ fontSize: '13px', color: 'var(--text)', fontWeight: a.type === 'ai_recommendation' ? 600 : 400 }}>{a.action}</div>
                  {a.reason && <div style={{ fontSize: '12px', color: 'var(--text2)', marginTop: '2px' }}>{a.reason}</div>}
                </div>
                <div style={{ marginLeft: 'auto', fontSize: '11px', color, background: color + '20', padding: '2px 8px', borderRadius: '12px', flexShrink: 0 }}>{a.severity}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

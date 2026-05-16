import { useState, useEffect } from 'react'
import { BASE } from '../api_config'
import { Bot, Play, Pause, Zap, AlertTriangle, CheckCircle, Info } from 'lucide-react'

export default function AutoPilot({ sessionId, customerId = '7836650842' }) {
  const [enabled, setEnabled] = useState(false)
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [actions, setActions] = useState([])
  const [lastRun, setLastRun] = useState(null)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [autonomousRunning, setAutonomousRunning] = useState(false)
  const [autonomousResult, setAutonomousResult] = useState(null)
  const [checkDetails, setCheckDetails] = useState(null)
  const [showCheckModal, setShowCheckModal] = useState(false)
  const [approving, setApproving] = useState({})

  useEffect(() => {
    fetchStatus()
    fetchPending()
  }, [])

  async function fetchPending() {
    try {
      const res = await fetch(BASE + '/api/ads/autonomous/pending', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: sessionId})
      })
      const d = await res.json()
      setPendingApprovals(d.pending || [])
    } catch(e) {}
  }

  async function runAutonomous() {
    setAutonomousRunning(true)
    setCheckDetails(null)
    try {
      const res = await fetch(BASE + '/api/ads/autonomous/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, customer_id: '' })
      })
      const d = await res.json()
      setAutonomousResult(d)
      if (d.success) {
        setCheckDetails(d)
        setShowCheckModal(true)
        fetchPending()
      }
    } catch(e) {}
    setAutonomousRunning(false)
  }

  async function handleApprove(runId, actionIndex, action) {
    setApproving(prev => ({ ...prev, [actionIndex]: 'approving' }))
    try {
      const res = await fetch(BASE + '/api/ads/autonomous/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runId, action_index: actionIndex, session_id: sessionId })
      })
      const d = await res.json()
      if (d.success) {
        setApproving(prev => ({ ...prev, [actionIndex]: 'approved' }))
        fetchPending()
      }
    } catch(e) {}
  }

  function handleReject(actionIndex) {
    setApproving(prev => ({ ...prev, [actionIndex]: 'rejected' }))
  }

  async function fetchHistory() {
    setHistoryLoading(true)
    try {
      const res = await fetch(BASE + '/api/ads/autopilot/history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, limit: 10 })
      })
      const d = await res.json()
      setHistory(d.history || [])
      setShowHistory(true)
    } catch(e) {}
    setHistoryLoading(false)
  }

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
      if (d.success) {
        setEnabled(!enabled)
        localStorage.setItem('sem_autopilot_enabled', (!enabled).toString())
      }
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


  const typeIcon = { warning: AlertTriangle, ai_recommendation: Zap, info: CheckCircle }

  const severityColor = (s) => s === 'critical' ? '#f87171' : s === 'high' ? '#fbbf24' : s === 'medium' ? '#60a5fa' : '#4ade80'
  const severityBg = (s) => s === 'critical' ? 'rgba(239,68,68,0.1)' : s === 'high' ? 'rgba(251,191,36,0.1)' : s === 'medium' ? 'rgba(96,165,250,0.1)' : 'rgba(34,197,94,0.1)'

  return (
    <div style={{ padding: '1.5rem', maxWidth: '900px', margin: '0 auto' }}>

      {/* Check Details Modal */}
      {showCheckModal && checkDetails && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '20px', maxWidth: '600px', width: '100%', maxHeight: '85vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            
            {/* Modal Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>🔍 Campaign Health Check</h2>
                <p style={{ fontSize: '13px', color: 'var(--text3)', margin: '4px 0 0' }}>
                  {checkDetails.summary?.total || 0} issues found · {checkDetails.summary?.auto_applied || 0} auto-fixed
                </p>
              </div>
              <button onClick={() => setShowCheckModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text3)', cursor: 'pointer', fontSize: '20px' }}>×</button>
            </div>

            {/* Modal Body */}
            <div style={{ overflowY: 'auto', padding: '16px 24px', flex: 1 }}>
              
              {/* Auto-applied summary */}
              {checkDetails.auto_actions?.length > 0 && (
                <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '10px', padding: '12px 14px', marginBottom: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#4ade80', marginBottom: '6px' }}>✅ Auto-applied fixes</div>
                  {checkDetails.auto_actions.map((a, i) => (
                    <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '4px 0' }}>• {a.action || a.type?.replace(/_/g,' ')}</div>
                  ))}
                </div>
              )}

              {/* Needs approval */}
              {checkDetails.approve_actions?.length > 0 ? (
                <>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px' }}>📧 Actions needing your review:</div>
                  {checkDetails.approve_actions.map((a, i) => {
                    const status = approving[i]
                    return (
                      <div key={i} style={{ background: 'var(--bg3)', border: `1px solid ${severityColor(a.severity)}30`, borderRadius: '12px', padding: '16px', marginBottom: '12px' }}>
                        
                        {/* Action header */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                          <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text)' }}>
                            {a.type?.replace(/_/g,' ').replace(/\w/g, c => c.toUpperCase())}
                          </div>
                          <span style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '10px', background: severityBg(a.severity), color: severityColor(a.severity), fontWeight: 600 }}>
                            {a.severity?.toUpperCase()}
                          </span>
                        </div>

                        {/* Campaign */}
                        <div style={{ marginBottom: '10px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '2px' }}>CAMPAIGN</div>
                          <div style={{ fontSize: '13px', color: 'var(--text2)' }}>{a.campaign}</div>
                        </div>

                        {/* Problem */}
                        <div style={{ marginBottom: '10px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '2px' }}>⚠️ PROBLEM DETECTED</div>
                          <div style={{ fontSize: '13px', color: '#fbbf24' }}>{a.reason}</div>
                        </div>

                        {/* Recommendation */}
                        <div style={{ background: 'rgba(99,102,241,0.08)', borderRadius: '8px', padding: '10px 12px', marginBottom: '10px' }}>
                          <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>💡 RECOMMENDED FIX</div>
                          <div style={{ fontSize: '13px', color: '#a5b4fc' }}>{a.recommendation || 'Review campaign settings and take appropriate action'}</div>
                        </div>

                        {/* Budget comparison */}
                        {a.current_budget && a.recommended_budget && (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                            <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px', padding: '10px', textAlign: 'center' }}>
                              <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>CURRENT BUDGET</div>
                              <div style={{ fontSize: '18px', fontWeight: 700, color: '#f87171' }}>₹{a.current_budget}/day</div>
                            </div>
                            <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '10px', textAlign: 'center' }}>
                              <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '4px' }}>RECOMMENDED</div>
                              <div style={{ fontSize: '18px', fontWeight: 700, color: '#4ade80' }}>₹{a.recommended_budget}/day</div>
                            </div>
                          </div>
                        )}

                        {/* After approve */}
                        {a.after_approve && (
                          <div style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', padding: '8px 12px', marginBottom: '10px' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '2px' }}>✅ AFTER APPROVAL</div>
                            <div style={{ fontSize: '13px', color: '#86efac' }}>{a.after_approve}</div>
                          </div>
                        )}

                        {/* Approve / Reject */}
                        {!status && (
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button onClick={() => handleApprove(checkDetails.run_id, i, a)} style={{
                              flex: 1, padding: '10px', background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)',
                              borderRadius: '8px', color: '#4ade80', fontSize: '13px', fontWeight: 600, cursor: 'pointer'
                            }}>✅ Approve & Apply</button>
                            <button onClick={() => handleReject(i)} style={{
                              flex: 1, padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                              borderRadius: '8px', color: '#f87171', fontSize: '13px', fontWeight: 600, cursor: 'pointer'
                            }}>❌ Reject</button>
                          </div>
                        )}
                        {status === 'approving' && <div style={{ textAlign: 'center', color: 'var(--text3)', fontSize: '13px', padding: '8px' }}>⏳ Processing...</div>}
                        {status === 'approved' && <div style={{ textAlign: 'center', color: '#4ade80', fontSize: '13px', padding: '8px', background: 'rgba(34,197,94,0.08)', borderRadius: '8px' }}>✅ Approved & Applied</div>}
                        {status === 'rejected' && <div style={{ textAlign: 'center', color: '#f87171', fontSize: '13px', padding: '8px', background: 'rgba(239,68,68,0.08)', borderRadius: '8px' }}>❌ Rejected — keeping current settings</div>}
                      </div>
                    )
                  })}
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text3)' }}>
                  <div style={{ fontSize: '40px', marginBottom: '12px' }}>✅</div>
                  <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', marginBottom: '8px' }}>All campaigns healthy!</div>
                  <div style={{ fontSize: '13px' }}>No issues requiring your approval were found.</div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)' }}>
              <button onClick={() => setShowCheckModal(false)} style={{
                width: '100%', padding: '11px', background: 'var(--bg3)',
                border: '1px solid var(--border)', borderRadius: '10px',
                color: 'var(--text2)', fontSize: '14px', cursor: 'pointer'
              }}>Close</button>
            </div>
          </div>
        </div>
      )}
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '1.5rem' }}>
        {[
          { label: 'Status', value: enabled ? 'Running' : 'Paused', color: enabled ? '#4ade80' : '#f87171' },
          { label: 'Last Run', value: lastRun ? new Date(lastRun).toLocaleTimeString() : 'Never' },
          { label: 'Actions Found', value: actions.length },
          { label: 'Next Scheduled', value: enabled ? (() => { const next = new Date(); next.setHours(next.getHours() + 6); return next.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) })() : '—', color: '#6366f1' }
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

      {/* Autonomous Engine Section */}
      <div style={{ background: 'var(--bg2)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>🤖 Autonomous Engine</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>AI analyses campaigns and auto-fixes small issues</div>
          </div>
          <button onClick={runAutonomous} disabled={autonomousRunning} style={{
            padding: '8px 16px', background: autonomousRunning ? 'var(--bg3)' : 'linear-gradient(135deg,#6366f1,#8b5cf6)',
            border: 'none', borderRadius: '8px', color: 'white', fontSize: '12px',
            fontWeight: 600, cursor: autonomousRunning ? 'not-allowed' : 'pointer',
          }}>
            {autonomousRunning ? '⏳ Analysing...' : '▶ Run Now'}
          </button>
        </div>

        {/* Trust levels */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
          <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '8px 12px' }}>
            <div style={{ fontSize: '11px', color: '#4ade80', fontWeight: 600, marginBottom: '4px' }}>✅ AUTO-APPLY</div>
            <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Bid ±10%, Pause low CTR, Ad copy test</div>
          </div>
          <div style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.2)', borderRadius: '8px', padding: '8px 12px' }}>
            <div style={{ fontSize: '11px', color: '#fbbf24', fontWeight: 600, marginBottom: '4px' }}>📧 NEEDS APPROVAL</div>
            <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Budget increase, New campaign, Big bid changes</div>
          </div>
        </div>

        {/* Result */}
        {autonomousResult && autonomousResult.success && (
          <div style={{ background: 'rgba(99,102,241,0.08)', borderRadius: '8px', padding: '10px 12px', fontSize: '12px' }}>
            <div style={{ color: '#4ade80', marginBottom: '4px' }}>✅ Auto-applied: {autonomousResult.summary?.auto_applied || 0} fixes</div>
            <div style={{ color: '#fbbf24' }}>📧 Pending approval: {autonomousResult.summary?.pending_approval || 0} actions</div>
          </div>
        )}
      </div>

      {/* Pending Approvals */}
      {pendingApprovals.length > 0 && (
        <div style={{ background: 'var(--bg2)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: '12px', overflow: 'hidden', marginBottom: '16px' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#fbbf24' }}>📧 Pending Approvals</span>
            <span style={{ fontSize: '11px', background: 'rgba(251,191,36,0.15)', color: '#fbbf24', padding: '2px 8px', borderRadius: '10px' }}>{pendingApprovals.reduce((s,r) => s + r.approve_actions.length, 0)}</span>
          </div>
          {pendingApprovals.map((run, ri) => (
            <div key={ri} style={{ padding: '12px 16px', borderBottom: ri < pendingApprovals.length-1 ? '1px solid var(--border)' : 'none' }}>
              <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px' }}>🕐 {run.run_at}</div>
              {run.approve_actions.filter(a => !a.approved).map((a, ai) => (
                <div key={ai} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '8px', background: 'var(--bg3)', borderRadius: '8px', marginBottom: '6px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)', marginBottom: '2px' }}>{a.type?.replace(/_/g,' ').replace(/\w/g, c => c.toUpperCase())}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '2px' }}>{a.campaign}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text2)' }}>{a.reason}</div>
                  </div>
                  <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: a.severity === 'critical' ? 'rgba(239,68,68,0.15)' : a.severity === 'high' ? 'rgba(251,191,36,0.15)' : 'rgba(96,165,250,0.15)', color: a.severity === 'critical' ? '#f87171' : a.severity === 'high' ? '#fbbf24' : '#60a5fa', flexShrink: 0 }}>{a.severity}</span>
                </div>
              ))}
              <a href="https://believable-rebirth-production-7e19.up.railway.app" style={{ display: 'block', textAlign: 'center', padding: '8px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: 'white', borderRadius: '8px', textDecoration: 'none', fontSize: '12px', fontWeight: 600, marginTop: '8px' }}>
                Review & Approve in Dashboard →
              </a>
            </div>
          ))}
        </div>
      )}

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
      {/* Activity History */}
      <div style={{ marginTop: '1.5rem' }}>
        <button onClick={showHistory ? () => setShowHistory(false) : fetchHistory}
          style={{ width: '100%', padding: '10px', borderRadius: '10px', background: 'var(--bg2)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: '13px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          {historyLoading ? '⏳ Loading...' : showHistory ? '▲ Hide Activity Log' : '📜 View Activity Log'}
        </button>

        {showHistory && (
          <div style={{ marginTop: '12px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', fontSize: '13px', fontWeight: 600, color: 'var(--text)', display: 'flex', justifyContent: 'space-between' }}>
              <span>📜 Activity Log</span>
              <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Last {history.length} runs</span>
            </div>
            {history.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text3)', fontSize: '13px' }}>
                No history yet. Run Auto-Pilot to start tracking.
              </div>
            ) : history.map((run, i) => (
              <div key={i} style={{ padding: '12px 16px', borderBottom: i < history.length-1 ? '1px solid var(--border)' : 'none' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>🤖 Run #{history.length - i}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{run.run_at}</div>
                  <div style={{ fontSize: '11px', color: '#6366f1', background: '#6366f120', padding: '2px 8px', borderRadius: '12px' }}>{run.total_actions} actions</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {(run.actions || []).slice(0, 3).map((a, j) => {
                    const color = { high: '#f87171', medium: '#fbbf24', low: '#4ade80', info: '#60a5fa' }[a.severity] || '#60a5fa'
                    return (
                      <div key={j} style={{ fontSize: '12px', color: 'var(--text2)', display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
                        <span style={{ color, flexShrink: 0 }}>●</span>
                        <span>{a.action}</span>
                      </div>
                    )
                  })}
                  {(run.actions || []).length > 3 && (
                    <div style={{ fontSize: '11px', color: 'var(--text3)' }}>+{run.actions.length - 3} more actions</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

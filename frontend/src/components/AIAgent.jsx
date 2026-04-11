import { useState, useEffect, useRef } from 'react'
import { RefreshCw, Send, Zap, AlertTriangle, CheckCircle, Activity, FileText, Power, Trash2 } from 'lucide-react'

const BASE = 'https://sem-ai-production.up.railway.app'

function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '1.25rem', ...style
    }}>{children}</div>
  )
}

function AlertBadge({ level }) {
  const colors = {
    critical: { bg: 'rgba(239,68,68,0.12)', color: '#f87171', border: 'rgba(239,68,68,0.2)' },
    warning: { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: 'rgba(245,158,11,0.2)' },
    info: { bg: 'rgba(79,125,255,0.12)', color: '#7ba3ff', border: 'rgba(79,125,255,0.2)' },
  }
  const c = colors[level] || colors.info
  return (
    <span style={{
      background: c.bg, color: c.color, border: `1px solid ${c.border}`,
      padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 500,
      textTransform: 'uppercase', letterSpacing: '0.06em',
    }}>{level}</span>
  )
}

function StatusDot({ active }) {
  return (
    <span style={{
      display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%',
      background: active ? '#4ade80' : '#6b7280',
      boxShadow: active ? '0 0 6px #4ade80' : 'none',
      marginRight: '6px',
    }} />
  )
}

export default function AIAgent({ sessionId, customerId }) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [chatHistory, setChatHistory] = useState([])
  const [report, setReport] = useState(null)
  const [generatingReport, setGeneratingReport] = useState(false)
  const [activeTab, setActiveTab] = useState('chat')
  const chatEndRef = useRef(null)

  useEffect(() => { fetchStatus() }, [])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatHistory])

  async function fetchStatus() {
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/api/agent/status`)
      const data = await res.json()
      setStatus(data)
      setChatHistory(data.chat_history || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function runAnalysis() {
    setAnalyzing(true)
    try {
      const res = await fetch(`${BASE}/api/agent/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, customer_id: customerId }),
      })
      const data = await res.json()
      setAnalysis(data)
      await fetchStatus()
    } catch (e) {
      console.error(e)
    } finally {
      setAnalyzing(false)
    }
  }

  async function sendMessage() {
    if (!message.trim() || sending) return
    const userMsg = message.trim()
    setMessage('')
    setSending(true)
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg, timestamp: new Date().toISOString() }])
    try {
      const res = await fetch(`${BASE}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, session_id: sessionId, customer_id: customerId }),
      })
      const data = await res.json()
      setChatHistory(prev => [...prev, { role: 'agent', content: data.response, timestamp: data.timestamp }])
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'agent', content: 'Sorry, I encountered an error. Please try again.', timestamp: new Date().toISOString() }])
    } finally {
      setSending(false)
    }
  }

  async function generateReport() {
    setGeneratingReport(true)
    try {
      const res = await fetch(`${BASE}/api/agent/report?session_id=${sessionId}&customer_id=${customerId}`)
      const data = await res.json()
      setReport(data)
      setActiveTab('report')
    } catch (e) {
      console.error(e)
    } finally {
      setGeneratingReport(false)
    }
  }

  async function toggleAgent() {
    const newActive = !status?.active
    await fetch(`${BASE}/api/agent/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: newActive }),
    })
    await fetchStatus()
  }

  async function clearChat() {
    await fetch(`${BASE}/api/agent/clear-chat`, { method: 'POST' })
    setChatHistory([])
  }

  const statusColor = {
    healthy: 'var(--green)',
    warning: '#fbbf24',
    critical: '#f87171',
    no_campaigns: 'var(--text3)',
  }

  const quickQuestions = [
    "How are my campaigns performing today?",
    "Which campaign has the lowest CTR?",
    "Am I close to my budget limit?",
    "What should I optimize first?",
    "Why am I getting low impressions?",
    "Give me a performance summary",
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '10px',
            background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.25)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Zap size={18} color="#a78bfa" />
          </div>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>SEMA — AI SEM Agent</h2>
            <p style={{ fontSize: '12px', color: 'var(--text3)' }}>
              <StatusDot active={status?.active} />
              {status?.active ? 'Active — monitoring your campaigns' : 'Paused'}
              {status?.last_check && ` · Last check: ${new Date(status.last_check).toLocaleTimeString()}`}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={generateReport} disabled={generatingReport} style={{
            background: 'none', border: '1px solid var(--border)', borderRadius: '7px',
            padding: '6px 12px', color: 'var(--text2)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px',
          }}>
            {generatingReport ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <FileText size={12} />}
            Weekly report
          </button>
          <button onClick={runAnalysis} disabled={analyzing} style={{
            background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.25)',
            borderRadius: '7px', padding: '6px 12px', color: '#a78bfa',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px',
          }}>
            {analyzing ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Activity size={12} />}
            Analyze now
          </button>
          <button onClick={toggleAgent} style={{
            background: 'none', border: '1px solid var(--border)', borderRadius: '7px',
            padding: '6px 10px', color: status?.active ? '#4ade80' : 'var(--text3)',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px',
          }}>
            <Power size={12} />
            {status?.active ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Analysis result */}
      {analysis && (
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Activity size={14} color={statusColor[analysis.status] || 'var(--text2)'} />
            <span style={{ fontSize: '13px', fontWeight: 600, color: statusColor[analysis.status] }}>
              {analysis.status?.toUpperCase()} — {analysis.summary}
            </span>
          </div>
          {analysis.alerts?.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {analysis.alerts.map((a, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '8px 10px', background: 'var(--bg3)',
                  borderRadius: '7px', border: '1px solid var(--border)', fontSize: '12px',
                }}>
                  <AlertTriangle size={13} color="#fbbf24" />
                  <AlertBadge level={a.level} />
                  <span style={{ color: 'var(--text2)' }}>{a.campaign}: {a.message}</span>
                </div>
              ))}
            </div>
          )}
          {analysis.recommendations?.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '6px', fontWeight: 600, letterSpacing: '0.06em' }}>RECOMMENDATIONS</div>
              {analysis.recommendations.map((r, i) => (
                <div key={i} style={{
                  display: 'flex', gap: '8px', padding: '6px 0',
                  borderBottom: '1px solid var(--border)', fontSize: '12px',
                }}>
                  <CheckCircle size={13} color="var(--green)" style={{ flexShrink: 0, marginTop: '1px' }} />
                  <span><strong>{r.campaign}</strong>: {r.action} — <span style={{ color: 'var(--text3)' }}>{r.reason}</span></span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--border)', paddingBottom: '0' }}>
        {['chat', 'alerts', 'report'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: '8px 16px', background: 'none',
            border: 'none', borderBottom: activeTab === tab ? '2px solid var(--accent)' : '2px solid transparent',
            color: activeTab === tab ? 'var(--accent)' : 'var(--text2)',
            cursor: 'pointer', fontSize: '13px', fontWeight: 500, textTransform: 'capitalize',
            marginBottom: '-1px',
          }}>{tab}</button>
        ))}
      </div>

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Quick questions */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {quickQuestions.map((q, i) => (
              <button key={i} onClick={() => setMessage(q)} style={{
                background: 'var(--bg3)', border: '1px solid var(--border)',
                borderRadius: '20px', padding: '4px 12px', fontSize: '11px',
                color: 'var(--text2)', cursor: 'pointer',
              }}>{q}</button>
            ))}
          </div>

          {/* Chat messages */}
          <Card style={{ padding: '0', overflow: 'hidden' }}>
            <div style={{ height: '380px', overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {chatHistory.length === 0 && (
                <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text3)' }}>
                  <Zap size={32} color="var(--text3)" style={{ margin: '0 auto 12px', display: 'block' }} />
                  <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '6px' }}>Ask SEMA anything</div>
                  <div style={{ fontSize: '12px' }}>Your AI SEM agent knows your campaigns inside out</div>
                </div>
              )}
              {chatHistory.map((msg, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}>
                  <div style={{
                    maxWidth: '80%',
                    padding: '10px 14px',
                    borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                    background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg3)',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                    fontSize: '13px',
                    lineHeight: '1.6',
                    color: msg.role === 'user' ? 'white' : 'var(--text)',
                    whiteSpace: 'pre-wrap',
                  }}>
                    {msg.role === 'agent' && (
                      <div style={{ fontSize: '10px', color: 'var(--text3)', marginBottom: '4px', fontWeight: 600, letterSpacing: '0.06em' }}>
                        SEMA
                      </div>
                    )}
                    {msg.content}
                  </div>
                </div>
              ))}
              {sending && (
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <div style={{
                    padding: '10px 14px', borderRadius: '14px 14px 14px 4px',
                    background: 'var(--bg3)', border: '1px solid var(--border)',
                    fontSize: '12px', color: 'var(--text3)',
                    display: 'flex', alignItems: 'center', gap: '6px',
                  }}>
                    <RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} />
                    SEMA is thinking...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            {/* Input */}
            <div style={{
              padding: '12px', borderTop: '1px solid var(--border)',
              display: 'flex', gap: '8px', alignItems: 'center',
            }}>
              <input
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder="Ask SEMA about your campaigns..."
                style={{
                  flex: 1, background: 'var(--bg3)', border: '1px solid var(--border)',
                  borderRadius: '8px', padding: '8px 12px', color: 'var(--text)',
                  fontSize: '13px', outline: 'none',
                }}
              />
              <button onClick={sendMessage} disabled={sending || !message.trim()} style={{
                width: '36px', height: '36px', borderRadius: '8px',
                background: 'var(--accent)', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                opacity: sending || !message.trim() ? 0.5 : 1,
              }}>
                <Send size={15} color="white" />
              </button>
              <button onClick={clearChat} title="Clear chat" style={{
                width: '36px', height: '36px', borderRadius: '8px',
                background: 'none', border: '1px solid var(--border)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Trash2 size={13} color="var(--text3)" />
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <Card>
          <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px', color: 'var(--text)' }}>
            Recent Alerts ({status?.total_alerts || 0} total)
          </div>
          {(!status?.recent_alerts || status.recent_alerts.length === 0) ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text3)', fontSize: '13px' }}>
              <CheckCircle size={24} color="var(--green)" style={{ margin: '0 auto 8px', display: 'block' }} />
              No alerts — your campaigns are looking healthy!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {status.recent_alerts.map((a, i) => (
                <div key={i} style={{
                  padding: '10px 12px', background: 'var(--bg3)',
                  borderRadius: '8px', border: '1px solid var(--border)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <AlertBadge level={a.level} />
                    <span style={{ fontSize: '10px', color: 'var(--text3)' }}>{a.timestamp ? new Date(a.timestamp).toLocaleString() : ''}</span>
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '2px' }}>{a.campaign}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text2)' }}>{a.message}</div>
                </div>
              ))}
            </div>
          )}

          {/* Recent actions */}
          {status?.recent_actions?.length > 0 && (
            <>
              <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', margin: '16px 0 12px', color: 'var(--text)' }}>
                Recent Actions
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {status.recent_actions.map((a, i) => (
                  <div key={i} style={{
                    display: 'flex', gap: '8px', alignItems: 'center',
                    padding: '8px 10px', background: 'var(--bg3)',
                    borderRadius: '7px', border: '1px solid var(--border)', fontSize: '12px',
                  }}>
                    <Zap size={12} color="var(--accent)" />
                    <span style={{ fontWeight: 500, textTransform: 'uppercase', fontSize: '10px', color: 'var(--accent)' }}>{a.type}</span>
                    <span style={{ color: 'var(--text2)' }}>{a.reason}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      )}

      {/* Report Tab */}
      {activeTab === 'report' && (
        <Card>
          {!report ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text3)' }}>
              <FileText size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
              <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>No report generated yet</div>
              <button onClick={generateReport} disabled={generatingReport} style={{
                padding: '8px 20px', background: 'var(--accent)', border: 'none',
                borderRadius: '8px', color: 'white', fontSize: '13px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '6px', margin: '0 auto',
              }}>
                {generatingReport ? <RefreshCw size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <FileText size={13} />}
                Generate weekly report
              </button>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text3)' }}>Generated: {new Date(report.generated_at).toLocaleString()}</span>
                <button onClick={generateReport} disabled={generatingReport} style={{
                  background: 'none', border: '1px solid var(--border)', borderRadius: '6px',
                  padding: '4px 10px', fontSize: '12px', color: 'var(--text2)', cursor: 'pointer',
                }}>Regenerate</button>
              </div>
              <div style={{
                fontSize: '13px', lineHeight: '1.8', color: 'var(--text)',
                whiteSpace: 'pre-wrap',
              }}>{report.report}</div>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

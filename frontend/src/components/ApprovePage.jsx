import { useState, useEffect } from 'react'

const BASE = 'https://sem-ai-production.up.railway.app'

export default function ApprovePage({ runId, actionIndex, sessionId }) {
  const [status, setStatus] = useState('loading')
  const [message, setMessage] = useState('')
  const [action, setAction] = useState(null)

  useEffect(() => {
    fetch(BASE + '/api/ads/autonomous/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: parseInt(runId),
        action_index: parseInt(actionIndex),
        session_id: sessionId
      })
    })
    .then(r => r.json())
    .then(d => {
      if (d.success) {
        setStatus('success')
        setMessage(d.message || 'Action approved!')
        setAction(d.action)
      } else {
        setStatus('error')
        setMessage(d.error || 'Something went wrong')
      }
    })
    .catch(() => { setStatus('error'); setMessage('Network error.') })
  }, [])

  const s = { fontFamily: '-apple-system,sans-serif', background: '#0a0a0f', color: '#f0f0f8', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', margin: 0, padding: '20px' }
  const box = { textAlign: 'center', padding: '40px 32px', background: '#111118', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.08)', maxWidth: '480px', width: '100%' }
  const btn = { display: 'inline-block', padding: '12px 24px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: 'white', borderRadius: '10px', textDecoration: 'none', fontWeight: 600, fontSize: '14px' }

  return (
    <div style={s}>
      <div style={box}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '28px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>⚡</div>
          <span style={{ fontSize: '16px', fontWeight: 700 }}>SEM AI</span>
        </div>
        {status === 'loading' && <><div style={{ fontSize: '40px', marginBottom: '16px' }}>⏳</div><h2>Processing...</h2><p style={{ color: '#a0a0b8' }}>Approving your action</p></>}
        {status === 'success' && (
          <>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
            <h2 style={{ marginBottom: '8px' }}>Action Approved!</h2>
            {action && (
              <div style={{ background: '#1a1a24', borderRadius: '10px', padding: '14px', textAlign: 'left', margin: '16px 0', fontSize: '13px' }}>
                <div style={{ color: '#606070', marginBottom: '4px' }}>ACTION</div>
                <div style={{ color: '#f0f0f8', marginBottom: '8px' }}>{(action.type || '').replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
                <div style={{ color: '#606070', marginBottom: '4px' }}>CAMPAIGN</div>
                <div style={{ color: '#a0a0b8', marginBottom: '8px' }}>{action.campaign}</div>
                <div style={{ color: '#606070', marginBottom: '4px' }}>REASON</div>
                <div style={{ color: '#a0a0b8' }}>{action.reason}</div>
              </div>
            )}
            <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '10px', fontSize: '13px', color: '#4ade80', marginBottom: '20px' }}>✓ {message}</div>
            <p style={{ color: '#606070', fontSize: '13px', marginBottom: '12px' }}>You can close this tab or return to SEM AI.</p>
            <a href="https://believable-rebirth-production-7e19.up.railway.app" style={btn}>Open SEM AI →</a>
          </>
        )}
        {status === 'error' && (
          <>
            <div style={{ fontSize: '40px', marginBottom: '16px' }}>❌</div>
            <h2 style={{ marginBottom: '8px' }}>Something went wrong</h2>
            <p style={{ color: '#a0a0b8', marginBottom: '20px' }}>{message}</p>
            <a href="https://believable-rebirth-production-7e19.up.railway.app" style={btn}>Go to Dashboard →</a>
          </>
        )}
      </div>
    </div>
  )
}

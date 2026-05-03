import { useState } from 'react'
import { X, Crown, Zap, Building2, AlertTriangle, Check } from 'lucide-react'

const API = 'https://sem-ai-production.up.railway.app'

export default function SubscriptionModal({ onClose, user, token, onPlanChanged }) {
  const [loading, setLoading] = useState(false)
  const [confirm, setConfirm] = useState(null)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const plans = [
    { key: 'free', name: 'Free', price: 0, icon: Zap, color: '#6b7280', features: ['1 analysis/day', 'Basic SEO report'] },
    { key: 'pro', name: 'Pro', price: 2999, icon: Crown, color: '#6366f1', features: ['Unlimited analyses', 'Full SEO + Ads'] },
    { key: 'agency', name: 'Agency', price: 9999, icon: Building2, color: '#8b5cf6', features: ['Everything in Pro', 'White-label'] },
  ]

  async function handlePlanChange(newPlan) {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/api/subscription/change`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ plan: newPlan }),
      })
      const data = await res.json()
      if (data.error) { setError(data.error); return }
      setSuccess(`Plan changed to ${newPlan} successfully`)
      setConfirm(null)
      if (onPlanChanged) onPlanChanged(newPlan)
      setTimeout(() => { onClose(); window.location.reload() }, 1500)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const currentPlan = user?.plan || 'free'

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div style={{ background: 'var(--bg)', borderRadius: '16px', width: '100%', maxWidth: '500px', border: '1px solid var(--border)' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text)' }}>Manage Subscription</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}><X size={18} /></button>
        </div>

        <div style={{ padding: '20px 24px' }}>
          <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg2)', border: '1px solid var(--border)', marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '4px' }}>Current Plan</div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text)', textTransform: 'capitalize' }}>{currentPlan} Plan</div>
          </div>

          {success && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', borderRadius: '8px', background: 'rgba(34,197,94,0.1)', color: '#22c55e', fontSize: '13px', marginBottom: '16px' }}>
              <Check size={14} /> {success}
            </div>
          )}

          {error && (
            <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--red-bg)', color: 'var(--red)', fontSize: '13px', marginBottom: '16px' }}>
              {error}
            </div>
          )}

          {confirm && (
            <div style={{ padding: '16px', borderRadius: '10px', background: 'var(--yellow-bg)', border: '1px solid var(--yellow)', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <AlertTriangle size={16} color="var(--yellow)" />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                  {confirm === 'free' ? 'Cancel Subscription?' : `Change to ${confirm} plan?`}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '12px' }}>
                {confirm === 'free' ? 'You will lose access to all Pro/Agency features immediately.' : `Your plan will be changed to ${confirm}.`}
              </p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => handlePlanChange(confirm)} disabled={loading}
                  style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'var(--red)', border: 'none', color: 'white', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                  {loading ? 'Processing...' : 'Confirm'}
                </button>
                <button onClick={() => setConfirm(null)}
                  style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text)', fontSize: '12px', cursor: 'pointer' }}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {plans.map(plan => {
              const Icon = plan.icon
              const isCurrent = plan.key === currentPlan
              const planOrder = { free: 0, pro: 1, agency: 2 }
              const isDowngrade = planOrder[plan.key] < planOrder[currentPlan]
              return (
                <div key={plan.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', borderRadius: '10px', border: `1px solid ${isCurrent ? plan.color : 'var(--border)'}`, background: isCurrent ? plan.color + '10' : 'var(--bg2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: plan.color + '20', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon size={15} color={plan.color} />
                    </div>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>{plan.name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{plan.price === 0 ? 'Free' : `Rs.${plan.price.toLocaleString()}/mo`}</div>
                    </div>
                  </div>
                  {isCurrent ? (
                    <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', background: plan.color + '20', color: plan.color, fontWeight: 600 }}>Current</span>
                  ) : (
                    <button onClick={() => setConfirm(plan.key)}
                      style={{ padding: '6px 14px', borderRadius: '6px', border: `1px solid ${plan.color}`, background: isDowngrade ? 'var(--bg)' : plan.color, color: isDowngrade ? plan.color : 'white', fontSize: '12px', fontWeight: 500, cursor: 'pointer' }}>
                      {isDowngrade ? 'Downgrade' : 'Upgrade'}
                    </button>
                  )}
                </div>
              )
            })}
          </div>

          {currentPlan !== 'free' && (
            <button onClick={() => setConfirm('free')}
              style={{ width: '100%', marginTop: '16px', padding: '10px', borderRadius: '8px', background: 'none', border: '1px solid var(--red)', color: 'var(--red)', fontSize: '13px', cursor: 'pointer' }}>
              Cancel Subscription
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
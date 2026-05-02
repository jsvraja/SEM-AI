import { useState } from 'react'
import { X, Check, Zap, Crown, Building2, Loader2 } from 'lucide-react'

const API = 'https://sem-ai-production.up.railway.app'

export default function PricingModal({ onClose, user, token, onPlanUpgraded }) {
  const [loading, setLoading] = useState(null)
  const [error, setError] = useState('')

  async function handleUpgrade(planKey) {
    if (!user || !token) return
    setLoading(planKey)
    setError('')
    try {
      const res = await fetch(`${API}/api/payment/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ plan: planKey, user_id: user.id }),
      })
      const order = await res.json()
      if (order.error) { setError(order.error); return }

      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: 'SEM AI',
        description: order.name,
        order_id: order.order_id,
        handler: async function (response) {
          const verifyRes = await fetch(`${API}/api/payment/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              plan: planKey,
              user_id: user.id,
            }),
          })
          const result = await verifyRes.json()
          if (result.success) {
            // Update localStorage user data
            const userData = JSON.parse(localStorage.getItem('sem_user') || '{}')
            userData.plan = planKey
            localStorage.setItem('sem_user', JSON.stringify(userData))
            if (onPlanUpgraded) onPlanUpgraded(planKey)
            onClose()
            alert(`Successfully upgraded to ${planKey} plan!`)
          } else {
            setError(result.error || 'Payment verification failed')
          }
        },
        prefill: { email: user.email, name: user.name },
        theme: { color: '#6366f1' },
      }

      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (e) {
      setError('Payment failed: ' + e.message)
    } finally {
      setLoading(null)
    }
  }

  const plans = [
    {
      key: 'free',
      name: 'Free',
      price: 0,
      period: 'forever',
      icon: Zap,
      color: '#6b7280',
      current: user?.plan === 'free',
      features: ['1 website analysis/day', 'Basic SEO report', 'Ad copy generation', 'Google Ads (limited)', 'AI Traffic tracking'],
      disabled: ['Competitor analysis', 'Social media AI', 'SEMA Agent', 'Priority support'],
    },
    {
      key: 'pro',
      name: 'Pro',
      price: 2999,
      period: 'month',
      icon: Crown,
      color: '#6366f1',
      popular: true,
      current: user?.plan === 'pro',
      features: ['Unlimited analyses', 'Full SEO + Site audit', 'Google Ads full access', 'Competitor intelligence', 'Social media AI posts', 'SEMA Agent 24/7', 'Email reports', 'Priority support'],
      disabled: [],
    },
    {
      key: 'agency',
      name: 'Agency',
      price: 9999,
      period: 'month',
      icon: Building2,
      color: '#8b5cf6',
      current: user?.plan === 'agency',
      features: ['Everything in Pro', 'Unlimited websites', 'White-label reports', 'Team workspaces', 'Client portal', 'Custom branding', 'API access', 'Dedicated support'],
      disabled: [],
    },
  ]

  return (
    <>
      <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
        <div style={{ background: 'var(--bg)', borderRadius: '16px', width: '100%', maxWidth: '860px', maxHeight: '90vh', overflow: 'auto', border: '1px solid var(--border)' }}>
          <div style={{ padding: '24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text)' }}>Choose your plan</h2>
              <p style={{ fontSize: '13px', color: 'var(--text3)', marginTop: '4px' }}>Scale your marketing with AI — cancel anytime</p>
            </div>
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', padding: '4px' }}>
              <X size={20} />
            </button>
          </div>

          {error && (
            <div style={{ margin: '16px 24px', padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid rgba(162,45,45,0.2)', borderRadius: '8px', color: 'var(--red)', fontSize: '13px' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', padding: '24px' }}>
            {plans.map((plan) => {
              const Icon = plan.icon
              return (
                <div key={plan.key} style={{ border: `2px solid ${plan.popular ? plan.color : 'var(--border)'}`, borderRadius: '12px', padding: '20px', position: 'relative', background: plan.popular ? 'var(--bg2)' : 'var(--bg)' }}>
                  {plan.popular && (
                    <div style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: plan.color, color: 'white', fontSize: '11px', fontWeight: 600, padding: '3px 12px', borderRadius: '20px' }}>
                      Most Popular
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: `${plan.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon size={16} color={plan.color} />
                    </div>
                    <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}>{plan.name}</span>
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <span style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text)' }}>
                      {plan.price === 0 ? 'Free' : `₹${plan.price.toLocaleString()}`}
                    </span>
                    {plan.price > 0 && <span style={{ fontSize: '13px', color: 'var(--text3)' }}>/{plan.period}</span>}
                  </div>
                  <button
                    onClick={() => !plan.current && plan.key !== 'free' && handleUpgrade(plan.key)}
                    disabled={plan.current || plan.key === 'free' || loading === plan.key}
                    style={{
                      width: '100%', padding: '10px', borderRadius: '8px',
                      background: plan.current ? 'var(--bg3)' : plan.popular ? plan.color : 'var(--bg2)',
                      color: plan.current ? 'var(--text3)' : plan.popular ? 'white' : plan.color,
                      fontSize: '13px', fontWeight: 500,
                      cursor: plan.current || plan.key === 'free' ? 'default' : 'pointer',
                      border: plan.current ? '1px solid var(--border)' : `1px solid ${plan.color}`,
                      marginBottom: '16px',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                    }}>
                    {loading === plan.key ? <><Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> Processing...</> :
                     plan.current ? 'Current Plan' :
                     plan.key === 'free' ? 'Downgrade' :
                     `Upgrade to ${plan.name}`}
                  </button>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {plan.features.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text2)' }}>
                        <Check size={12} color="#22c55e" />{f}
                      </div>
                    ))}
                    {plan.disabled.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text3)', opacity: 0.5 }}>
                        <X size={12} color="var(--text3)" />{f}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
          <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', textAlign: 'center', fontSize: '12px', color: 'var(--text3)' }}>
            🔒 Secure payments via Razorpay · Cancel anytime · No hidden fees
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  )
}
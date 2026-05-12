import { useState } from 'react'

const steps = [
  {
    icon: '🚀',
    title: 'Welcome to SEM AI!',
    desc: "Your AI-powered SEO & Google Ads co-pilot. Let's get you started in 3 quick steps.",
    tip: null,
  },
  {
    icon: '🔍',
    title: 'Step 1 — Analyse your website',
    desc: 'Paste any website URL. AI will auto-detect your business, fill keywords, and generate a full SEO report + ad copy in ~60 seconds.',
    tip: '💡 Try your own website or a competitor URL!',
  },
  {
    icon: '🎯',
    title: 'Step 2 — Connect Google Ads',
    desc: 'Connect your Google Ads account to publish campaigns directly. Budget auto-pause protects you from overspending.',
    tip: '💡 You need a Manager (MCC) account to publish. We will guide you.',
  },
  {
    icon: '🤖',
    title: 'Step 3 — Enable Auto-Pilot',
    desc: 'Turn on Auto-Pilot mode and AI will monitor your campaigns every 6 hours — detecting issues and logging every action.',
    tip: '💡 Your first analysis is free. No credit card needed.',
  },
]

export default function OnboardingModal({ onClose }) {
  const [step, setStep] = useState(0)

  function handleNext() {
    if (step < steps.length - 1) {
      setStep(step + 1)
    } else {
      localStorage.setItem('sem_onboarded', 'true')
      onClose()
    }
  }

  function handleSkip() {
    localStorage.setItem('sem_onboarded', 'true')
    onClose()
  }

  const s = steps[step]

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px',
    }}>
      <div style={{
        background: 'var(--bg2)', border: '1px solid var(--border)',
        borderRadius: '20px', padding: '40px 36px',
        maxWidth: '480px', width: '100%',
        position: 'relative', textAlign: 'center',
      }}>
        <button onClick={handleSkip} style={{
          position: 'absolute', top: '16px', right: '16px',
          background: 'none', border: 'none', color: 'var(--text3)',
          fontSize: '13px', cursor: 'pointer',
        }}>Skip</button>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginBottom: '28px' }}>
          {steps.map((_, i) => (
            <div key={i} style={{
              width: i === step ? '20px' : '6px', height: '6px',
              borderRadius: '3px', transition: 'all 0.3s',
              background: i <= step ? 'var(--accent)' : 'var(--bg3)',
            }} />
          ))}
        </div>

        <div style={{ fontSize: '48px', marginBottom: '20px' }}>{s.icon}</div>

        <h2 style={{
          fontSize: '22px', fontWeight: 800, color: 'var(--text)',
          marginBottom: '12px', letterSpacing: '-0.02em',
        }}>{s.title}</h2>

        <p style={{
          fontSize: '15px', color: 'var(--text2)',
          lineHeight: 1.7, marginBottom: s.tip ? '16px' : '32px',
        }}>{s.desc}</p>

        {s.tip && (
          <div style={{
            background: 'rgba(99,102,241,0.08)',
            border: '1px solid rgba(99,102,241,0.2)',
            borderRadius: '10px', padding: '10px 14px',
            fontSize: '13px', color: '#a5b4fc',
            marginBottom: '32px', textAlign: 'left',
          }}>{s.tip}</div>
        )}

        <button onClick={handleNext} style={{
          width: '100%', padding: '13px',
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          border: 'none', borderRadius: '10px',
          color: 'white', fontSize: '15px', fontWeight: 600,
          cursor: 'pointer',
        }}>
          {step < steps.length - 1 ? 'Next →' : 'Get started! 🚀'}
        </button>
      </div>
    </div>
  )
}

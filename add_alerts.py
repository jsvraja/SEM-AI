# Add Alert System to Dashboard
path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# 1. Add alerts state
old_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [sendingReport, setSendingReport] = useState(false)"""

new_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [sendingReport, setSendingReport] = useState(false)
  const [alerts, setAlerts] = useState([])
  const [showAlerts, setShowAlerts] = useState(false)

  // Generate alerts based on analysis data
  useEffect(() => {
    if (!seo) return
    const newAlerts = []
    const score = seo?.overall_seo_score || 0
    const meta = seo?.page_metadata?.meta_description || ''
    const hasSchema = seo?.technical_issues?.some(i => i.type === 'schema') || !seo?.score_breakdown?.schema
    const budget = seo?.sem_recommendations?.monthly_budget_inr || 0
    const imgMissing = seo?.images_without_alt_count || 0

    if (score < 50) newAlerts.push({ type: 'critical', icon: '🚨', title: 'Critical SEO Score', msg: 'SEO score is ' + score + '/100 — urgent fixes needed to avoid ranking drop', time: 'Just now' })
    else if (score < 70) newAlerts.push({ type: 'warning', icon: '⚠️', title: 'Low SEO Score', msg: 'SEO score is ' + score + '/100 — several improvements needed', time: 'Just now' })
    if (!meta || meta.length < 50) newAlerts.push({ type: 'critical', icon: '📝', title: 'Meta Description Missing/Short', msg: 'Missing or too short meta description hurts CTR by up to 30%', time: 'Just now' })
    if (meta && meta.length > 160) newAlerts.push({ type: 'warning', icon: '✂️', title: 'Meta Description Too Long', msg: 'Meta is ' + meta.length + ' chars — Google will truncate at 160 chars', time: 'Just now' })
    if (imgMissing > 0) newAlerts.push({ type: 'warning', icon: '🖼️', title: 'Images Missing Alt Text', msg: imgMissing + ' images without alt text — affects accessibility & SEO', time: 'Just now' })
    if (budget > 100000) newAlerts.push({ type: 'warning', icon: '💰', title: 'High Budget Recommendation', msg: 'Recommended budget ₹' + budget.toLocaleString() + '/mo — verify this fits your goals', time: 'Just now' })
    if (!seo?.page_metadata?.title) newAlerts.push({ type: 'critical', icon: '🏷️', title: 'Page Title Missing', msg: 'No title tag found — critical for SEO rankings', time: 'Just now' })
    
    setAlerts(newAlerts)
  }, [seo?.overall_seo_score])"""

content = content.replace(old_state, new_state)

# 2. Add Bell icon to sidebar/header area - add after the tab navigation
old_tabs = """      <main style={{"""

new_tabs = """      {/* Alert Bell */}
      {alerts.length > 0 && (
        <div style={{ position: 'fixed', top: '16px', right: '16px', zIndex: 999 }}>
          <button onClick={() => setShowAlerts(!showAlerts)} style={{ position: 'relative', width: '40px', height: '40px', borderRadius: '50%', background: 'var(--bg2)', border: '1px solid var(--border)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            🔔
            <span style={{ position: 'absolute', top: '-4px', right: '-4px', background: alerts.some(a => a.type === 'critical') ? 'var(--red)' : 'var(--yellow)', color: 'white', fontSize: '10px', fontWeight: 700, width: '18px', height: '18px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {alerts.length}
            </span>
          </button>
          
          {showAlerts && (
            <div style={{ position: 'absolute', top: '48px', right: 0, width: '340px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.15)', overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 700 }}>🔔 Alerts ({alerts.length})</span>
                <button onClick={() => setShowAlerts(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', fontSize: '16px' }}>✕</button>
              </div>
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {alerts.map((alert, i) => (
                  <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '10px', background: alert.type === 'critical' ? 'var(--red-bg)' : 'var(--yellow-bg)' }}>
                    <span style={{ fontSize: '20px', flexShrink: 0 }}>{alert.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: alert.type === 'critical' ? 'var(--red)' : 'var(--yellow)', marginBottom: '2px' }}>{alert.title}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: 1.5 }}>{alert.msg}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '4px' }}>{alert.time}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ padding: '10px 16px', background: 'var(--bg3)', fontSize: '11px', color: 'var(--text3)', textAlign: 'center' }}>
                Alerts auto-generated based on your SEO analysis
              </div>
            </div>
          )}
        </div>
      )}

      <main style={{"""

content = content.replace(old_tabs, new_tabs, 1)

# 3. Add useEffect import if missing
if 'useEffect' not in content:
    content = content.replace(
        "import { useState } from 'react'",
        "import { useState, useEffect } from 'react'"
    )
elif 'useState, useEffect' not in content and 'useEffect, useState' not in content:
    content = content.replace(
        "import { useState } from 'react'",
        "import { useState, useEffect } from 'react'"
    )

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("Alert system added!")
print("Has alerts state:", "const [alerts" in content)
print("Has bell icon:", "Alert Bell" in content)

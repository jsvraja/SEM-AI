import os

# 1. Update PageSpeed API to also return screenshot and mobile issues
main_path = '/Users/sakthivel-1528/Personal/sem-app/backend/main_with_ads.py'
with open(main_path) as f:
    content = f.read()

old_pagespeed = """                cats = data.get("lighthouseResult", {}).get("categories", {})
                audits = data.get("lighthouseResult", {}).get("audits", {})

                results[strategy] = {
                    "performance": round((cats.get("performance", {}).get("score", 0) or 0) * 100),
                    "accessibility": round((cats.get("accessibility", {}).get("score", 0) or 0) * 100),
                    "best_practices": round((cats.get("best-practices", {}).get("score", 0) or 0) * 100),
                    "seo": round((cats.get("seo", {}).get("score", 0) or 0) * 100),
                    "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                    "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                    "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                    "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
                    "speed_index": audits.get("speed-index", {}).get("displayValue", "N/A"),
                }"""

new_pagespeed = """                cats = data.get("lighthouseResult", {}).get("categories", {})
                audits = data.get("lighthouseResult", {}).get("audits", {})
                lr = data.get("lighthouseResult", {})
                
                # Screenshot thumbnail
                screenshot = audits.get("final-screenshot", {}).get("details", {}).get("data", "")
                
                # Mobile specific issues
                mobile_issues = []
                if strategy == "mobile":
                    if audits.get("viewport", {}).get("score", 1) == 0:
                        mobile_issues.append("No viewport meta tag")
                    if audits.get("font-size", {}).get("score", 1) == 0:
                        mobile_issues.append("Text too small to read")
                    if audits.get("tap-targets", {}).get("score", 1) == 0:
                        mobile_issues.append("Tap targets too small")
                    if audits.get("content-width", {}).get("score", 1) == 0:
                        mobile_issues.append("Content wider than screen")

                results[strategy] = {
                    "performance": round((cats.get("performance", {}).get("score", 0) or 0) * 100),
                    "accessibility": round((cats.get("accessibility", {}).get("score", 0) or 0) * 100),
                    "best_practices": round((cats.get("best-practices", {}).get("score", 0) or 0) * 100),
                    "seo": round((cats.get("seo", {}).get("score", 0) or 0) * 100),
                    "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                    "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                    "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                    "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
                    "speed_index": audits.get("speed-index", {}).get("displayValue", "N/A"),
                    "screenshot": screenshot,
                    "mobile_issues": mobile_issues,
                    "interactive": audits.get("interactive", {}).get("displayValue", "N/A"),
                }"""

if old_pagespeed in content:
    content = content.replace(old_pagespeed, new_pagespeed)
    print("PageSpeed enhanced!")
else:
    print("ERROR: pagespeed not found")

with open(main_path, 'w') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(main_path, doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print("ERROR:", e)

# 2. Update Dashboard modal to show Mobile vs Desktop comparison
dash_path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(dash_path) as f:
    dcontent = f.read()

old_modal_scores = """                  {pageSpeed?.results && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {['mobile', 'desktop'].map(strategy => {
                        const r = pageSpeed.results[strategy]
                        if (!r || r.error) return null
                        return (
                          <div key={strategy}>
                            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
                              {strategy === 'mobile' ? '📱 Mobile' : '🖥 Desktop'}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px', marginBottom: '12px' }}>
                              {[
                                { label: 'Performance', score: r.performance, icon: '⚡' },
                                { label: 'SEO', score: r.seo, icon: '🔍' },
                                { label: 'Accessibility', score: r.accessibility, icon: '♿' },
                                { label: 'Best Practices', score: r.best_practices, icon: '✅' },
                              ].map(({ label, score, icon }) => {
                                const c = score >= 90 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                                const bg = score >= 90 ? 'var(--green-bg)' : score >= 50 ? 'var(--yellow-bg)' : 'var(--red-bg)'
                                return (
                                  <div key={label} style={{ textAlign: 'center', padding: '14px 6px', background: bg, borderRadius: '12px', border: `1px solid ${c}` }}>
                                    <div style={{ fontSize: '13px', marginBottom: '4px' }}>{icon}</div>
                                    <div style={{ fontSize: '28px', fontWeight: 800, color: c, letterSpacing: '-0.03em' }}>{score}</div>
                                    <div style={{ fontSize: '10px', color: c, textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '2px', fontWeight: 600 }}>{label}</div>
                                  </div>
                                )
                              })}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px' }}>
                              {[
                                { label: 'First Contentful Paint', val: r.fcp },
                                { label: 'Largest Contentful Paint', val: r.lcp },
                                { label: 'Cumulative Layout Shift', val: r.cls },
                              ].map(({ label, val }) => (
                                <div key={label} style={{ padding: '8px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
                                  <div style={{ fontSize: '16px', fontWeight: 700 }}>{val}</div>
                                  <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px' }}>{label}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                      <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px' }}>
                        🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor
                      </div>
                    </div>
                  )}"""

new_modal_scores = """                  {pageSpeed?.results && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {/* Side by side comparison */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                        {['mobile', 'desktop'].map(strategy => {
                          const r = pageSpeed.results[strategy]
                          if (!r || r.error) return null
                          return (
                            <div key={strategy} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
                              {/* Header */}
                              <div style={{ padding: '10px 14px', background: strategy === 'mobile' ? 'var(--accent-bg)' : 'var(--bg3)', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '18px' }}>{strategy === 'mobile' ? '📱' : '🖥'}</span>
                                <span style={{ fontSize: '13px', fontWeight: 700 }}>{strategy === 'mobile' ? 'Mobile' : 'Desktop'}</span>
                                <span style={{ marginLeft: 'auto', fontSize: '22px', fontWeight: 800, color: r.performance >= 90 ? 'var(--green)' : r.performance >= 50 ? 'var(--yellow)' : 'var(--red)' }}>{r.performance}</span>
                              </div>
                              {/* Screenshot */}
                              {r.screenshot && (
                                <div style={{ padding: '8px', background: 'var(--bg4)', borderBottom: '1px solid var(--border)', textAlign: 'center' }}>
                                  <img src={r.screenshot} alt={strategy + ' screenshot'} style={{ maxWidth: '100%', borderRadius: '4px', maxHeight: '120px', objectFit: 'cover' }} />
                                </div>
                              )}
                              {/* Scores */}
                              <div style={{ padding: '10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                                {[
                                  { label: 'Performance', score: r.performance },
                                  { label: 'SEO', score: r.seo },
                                  { label: 'Accessibility', score: r.accessibility },
                                  { label: 'Best Practices', score: r.best_practices },
                                ].map(({ label, score }) => {
                                  const c = score >= 90 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                                  return (
                                    <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'var(--bg3)', borderRadius: '6px' }}>
                                      <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{label}</span>
                                      <span style={{ fontSize: '11px', fontWeight: 700, color: c }}>{score}</span>
                                    </div>
                                  )
                                })}
                              </div>
                              {/* Core Web Vitals */}
                              <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border)' }}>
                                <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text3)', marginBottom: '5px', textTransform: 'uppercase' }}>Core Web Vitals</div>
                                {[
                                  { label: 'FCP', val: r.fcp },
                                  { label: 'LCP', val: r.lcp },
                                  { label: 'CLS', val: r.cls },
                                  { label: 'TBT', val: r.tbt },
                                  { label: 'TTI', val: r.interactive },
                                ].map(({ label, val }) => (
                                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                                    <span style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</span>
                                    <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text2)' }}>{val || 'N/A'}</span>
                                  </div>
                                ))}
                              </div>
                              {/* Mobile issues */}
                              {strategy === 'mobile' && r.mobile_issues?.length > 0 && (
                                <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border)', background: 'var(--red-bg)' }}>
                                  <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--red)', marginBottom: '4px' }}>⚠ Mobile Issues</div>
                                  {r.mobile_issues.map((issue, i) => (
                                    <div key={i} style={{ fontSize: '10px', color: 'var(--red)', marginBottom: '2px' }}>• {issue}</div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px' }}>
                        🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor
                      </div>
                    </div>
                  )}"""

if old_modal_scores in dcontent:
    dcontent = dcontent.replace(old_modal_scores, new_modal_scores)
    print("Modal updated!")
else:
    print("ERROR: modal not found")

with open(dash_path, 'w') as f:
    f.write(dcontent)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(dcontent)
print("Done!")

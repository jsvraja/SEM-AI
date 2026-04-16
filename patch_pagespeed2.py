path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Find the Summary card closing and add PageSpeed after it
old = """            {/* Summary */}
            <Card>
              <SectionTitle icon={Zap}>AI Summary</SectionTitle>
              <p style={{ color: 'var(--text2)', fontSize: '14px', lineHeight: 1.7 }}>{seo?.ai_summary || seo?.summary || 'AI analysis complete. Check the sections below for detailed insights.'}</p>"""

new = """            {/* Summary */}
            <Card>
              <SectionTitle icon={Zap}>AI Summary</SectionTitle>
              <p style={{ color: 'var(--text2)', fontSize: '14px', lineHeight: 1.7 }}>{seo?.ai_summary || seo?.summary || 'AI analysis complete. Check the sections below for detailed insights.'}</p>"""

print("Found Summary card:", old in content)

# Find end of summary card and insert PageSpeed after it
idx = content.find("            {/* Summary */}")
# Find the closing </Card> after this
card_end = content.find("            </Card>", idx)
next_section = content.find("\n\n            {", card_end)
print(f"Summary card at {idx}, ends at {card_end}, next section at {next_section}")

pagespeed_card = """

            {/* PageSpeed Insights */}
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={BarChart3}>PageSpeed Insights (Google)</SectionTitle>
                <button onClick={async () => {
                    if (loadingSpeed) return
                    setLoadingSpeed(true)
                    setPageSpeed(null)
                    try {
                      const res = await fetch(`${BASE}/api/pagespeed`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url }),
                      })
                      const data = await res.json()
                      setPageSpeed(data)
                    } catch(e) { console.error(e) }
                    setLoadingSpeed(false)
                  }} style={{ padding: '6px 14px', borderRadius: '7px', background: loadingSpeed ? 'var(--bg3)' : 'var(--accent)', border: 'none', color: loadingSpeed ? 'var(--text3)' : 'white', fontSize: '12px', fontWeight: 600, cursor: loadingSpeed ? 'not-allowed' : 'pointer' }}>
                  {loadingSpeed ? '⏳ Running...' : pageSpeed ? '↺ Re-run' : '🚀 Run PageSpeed Test'}
                </button>
              </div>
              {!pageSpeed && !loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)', fontSize: '13px', background: 'var(--bg3)', borderRadius: '8px' }}>
                  Click "Run PageSpeed Test" to get real Performance, SEO, Accessibility & Best Practices scores from Google
                </div>
              )}
              {loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)', fontSize: '13px' }}>
                  ⏳ Running PageSpeed analysis... this takes 20-30 seconds
                </div>
              )}
              {pageSpeed?.error && <div style={{ color: 'var(--red)', fontSize: '13px' }}>⚠ {pageSpeed.error}</div>}
              {pageSpeed?.results && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {['mobile', 'desktop'].map(strategy => {
                    const r = pageSpeed.results[strategy]
                    if (!r || r.error) return null
                    return (
                      <div key={strategy}>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                          {strategy === 'mobile' ? '📱 Mobile' : '🖥️ Desktop'}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '8px', marginBottom: '10px' }}>
                          {[
                            { label: 'Performance', score: r.performance },
                            { label: 'SEO', score: r.seo },
                            { label: 'Accessibility', score: r.accessibility },
                            { label: 'Best Practices', score: r.best_practices },
                          ].map(({ label, score }) => {
                            const c = score >= 90 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                            return (
                              <div key={label} style={{ textAlign: 'center', padding: '10px 6px', background: 'var(--bg3)', borderRadius: '10px', border: `2px solid ${c}` }}>
                                <div style={{ fontSize: '22px', fontWeight: 700, color: c }}>{score}</div>
                                <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase', marginTop: '2px' }}>{label}</div>
                              </div>
                            )
                          })}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '6px' }}>
                          {[
                            { label: 'FCP', val: r.fcp },
                            { label: 'LCP', val: r.lcp },
                            { label: 'CLS', val: r.cls },
                          ].map(({ label, val }) => (
                            <div key={label} style={{ padding: '6px', background: 'var(--bg3)', borderRadius: '6px', textAlign: 'center' }}>
                              <div style={{ fontSize: '13px', fontWeight: 600 }}>{val}</div>
                              <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{label}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '6px 8px', background: 'var(--bg3)', borderRadius: '6px' }}>
                    🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor &nbsp;&nbsp; Powered by Google PageSpeed Insights
                  </div>
                </div>
              )}
            </Card>"""

# Insert after the summary card closing tag
insert_pos = content.find("            </Card>", idx) + len("            </Card>")
content = content[:insert_pos] + pagespeed_card + content[insert_pos:]

# Add BASE import if not already there
if "from '../api_config'" not in content:
    content = content.replace(
        "import { useState",
        "import { BASE } from '../api_config'\nimport { useState"
    )

with open(path, 'w') as f:
    f.write(content)

# Also update local frontend
path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("PageSpeed card added!")
print("Has PageSpeed Insights:", "PageSpeed Insights" in content)

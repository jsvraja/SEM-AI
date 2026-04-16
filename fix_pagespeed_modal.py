path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Fix 1: Remove the PageSpeed card from overview flow entirely
# Replace {showGoogleScore && <Card>...} block with a modal
old_ps_card = """{showGoogleScore && <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text)' }}>⚡ Performance Analysis</div>
                <button onClick={() => { setShowGoogleScore(null) }} style={{ padding: '4px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', fontSize: '11px', cursor: 'pointer' }}>
                  {loadingSpeed ? '⏳ Running...' : pageSpeed ? '↺ Re-run' : '⚡ Analyse Performance'}
                </button>
              </div>"""

print("Found old PS card:", old_ps_card[:50] in content)

# Find the pagespeed card block
start = content.find('{showGoogleScore && <Card>')
end = content.find('</Card>}', start) + len('</Card>}')
ps_block = content[start:end]
print("PS block length:", len(ps_block))

# Replace with modal
modal_code = """{showGoogleScore && (
              <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}
                onClick={() => setShowGoogleScore(false)}>
                <div style={{ background: 'var(--bg2)', borderRadius: '16px', padding: '24px', maxWidth: '700px', width: '100%', maxHeight: '80vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}
                  onClick={e => e.stopPropagation()}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text)' }}>🔍 Performance Analysis</div>
                    <button onClick={() => setShowGoogleScore(false)} style={{ padding: '5px 12px', borderRadius: '7px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', fontSize: '12px', cursor: 'pointer' }}>✕ Close</button>
                  </div>
                  {loadingSpeed && <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text3)' }}>⏳ Running analysis... (20-30 seconds)</div>}
                  {pageSpeed?.error && <div style={{ color: 'var(--red)', fontSize: '13px' }}>⚠ {pageSpeed.error}</div>}
                  {pageSpeed?.results && (
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
                  )}
                </div>
              </div>
            )}"""

content = content[:start] + modal_code + content[end:]

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("Modal added!")
print("Has modal:", "position: 'fixed'" in content)

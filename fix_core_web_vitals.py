path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add Core Web Vitals card after AI Fix Suggestions in SEO tab
old_marker = """            {/* Content Analysis Deep Dive */}"""

new_cwv = """            {/* Core Web Vitals */}
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={Zap}>Core Web Vitals</SectionTitle>
                {!pageSpeed && !loadingSpeed && (
                  <button onClick={async () => {
                    setLoadingSpeed(true)
                    setPageSpeed(null)
                    try {
                      const res = await fetch('https://sem-ai-production.up.railway.app/api/pagespeed', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url }),
                      })
                      const data = await res.json()
                      setPageSpeed(data)
                    } catch(e) { setPageSpeed({ error: 'Network error — try again' }) }
                    setLoadingSpeed(false)
                  }} style={{ fontSize: '11px', padding: '5px 12px', borderRadius: '7px', background: 'var(--accent)', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 600 }}>
                    ⚡ Run Test
                  </button>
                )}
                {loadingSpeed && <span style={{ fontSize: '11px', color: 'var(--text3)' }}>⏳ Running... (20-30s)</span>}
                {pageSpeed && !loadingSpeed && (
                  <button onClick={() => { setPageSpeed(null); setShowGoogleScore(false) }} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', cursor: 'pointer' }}>↺ Re-run</button>
                )}
              </div>

              {!pageSpeed && !loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '20px', background: 'var(--bg3)', borderRadius: '10px', color: 'var(--text3)', fontSize: '13px' }}>
                  Click "⚡ Run Test" to get real Core Web Vitals from Google PageSpeed
                </div>
              )}

              {loadingSpeed && (
                <div style={{ textAlign: 'center', padding: '24px' }}>
                  <div style={{ fontSize: '28px', marginBottom: '8px' }}>⏳</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>Analysing Core Web Vitals...</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>This takes 20-30 seconds</div>
                </div>
              )}

              {pageSpeed?.error && (
                <div style={{ color: 'var(--red)', fontSize: '13px', padding: '10px', background: 'var(--red-bg)', borderRadius: '8px' }}>⚠ {pageSpeed.error}</div>
              )}

              {pageSpeed?.results && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {['mobile', 'desktop'].map(strategy => {
                    const r = pageSpeed.results[strategy]
                    if (!r || r.error) return null

                    const vitals = [
                      { 
                        label: 'First Contentful Paint', short: 'FCP', val: r.fcp, 
                        good: '< 1.8s', poor: '> 3s',
                        status: r.fcp && parseFloat(r.fcp) < 1.8 ? 'good' : parseFloat(r.fcp) < 3 ? 'warn' : 'bad',
                        desc: 'Time until first content appears on screen'
                      },
                      { 
                        label: 'Largest Contentful Paint', short: 'LCP', val: r.lcp,
                        good: '< 2.5s', poor: '> 4s',
                        status: r.lcp && parseFloat(r.lcp) < 2.5 ? 'good' : parseFloat(r.lcp) < 4 ? 'warn' : 'bad',
                        desc: 'Time until largest visible element loads'
                      },
                      { 
                        label: 'Cumulative Layout Shift', short: 'CLS', val: r.cls,
                        good: '< 0.1', poor: '> 0.25',
                        status: r.cls && parseFloat(r.cls) < 0.1 ? 'good' : parseFloat(r.cls) < 0.25 ? 'warn' : 'bad',
                        desc: 'Visual stability — how much elements shift during load'
                      },
                      { 
                        label: 'Total Blocking Time', short: 'TBT', val: r.tbt,
                        good: '< 200ms', poor: '> 600ms',
                        status: r.tbt && parseFloat(r.tbt) < 200 ? 'good' : parseFloat(r.tbt) < 600 ? 'warn' : 'bad',
                        desc: 'Time main thread is blocked from responding to user input'
                      },
                      { 
                        label: 'Time to Interactive', short: 'TTI', val: r.interactive,
                        good: '< 3.8s', poor: '> 7.3s',
                        status: r.interactive && parseFloat(r.interactive) < 3.8 ? 'good' : parseFloat(r.interactive) < 7.3 ? 'warn' : 'bad',
                        desc: 'Time until page is fully interactive'
                      },
                    ]

                    return (
                      <div key={strategy}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                          <span style={{ fontSize: '16px' }}>{strategy === 'mobile' ? '📱' : '🖥'}</span>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text)' }}>{strategy === 'mobile' ? 'Mobile' : 'Desktop'}</span>
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: r.performance >= 90 ? 'var(--green-bg)' : r.performance >= 50 ? 'var(--yellow-bg)' : 'var(--red-bg)', color: r.performance >= 90 ? 'var(--green)' : r.performance >= 50 ? 'var(--yellow)' : 'var(--red)', fontWeight: 700 }}>Performance: {r.performance}/100</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {vitals.map(({ label, short, val, good, poor, status, desc }) => {
                            const c = status === 'good' ? 'var(--green)' : status === 'warn' ? 'var(--yellow)' : 'var(--red)'
                            const bg = status === 'good' ? 'var(--green-bg)' : status === 'warn' ? 'var(--yellow-bg)' : 'var(--red-bg)'
                            const icon = status === 'good' ? '✅' : status === 'warn' ? '⚠️' : '❌'
                            return (
                              <div key={short} style={{ display: 'grid', gridTemplateColumns: '80px 1fr auto', gap: '10px', alignItems: 'center', padding: '8px 12px', background: bg, borderRadius: '8px', border: '1px solid ' + c }} title={desc}>
                                <div style={{ textAlign: 'center' }}>
                                  <div style={{ fontSize: '18px', fontWeight: 800, color: c }}>{val || 'N/A'}</div>
                                  <div style={{ fontSize: '10px', fontWeight: 700, color: c }}>{short}</div>
                                </div>
                                <div>
                                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>{label}</div>
                                  <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{desc}</div>
                                  <div style={{ fontSize: '10px', color: 'var(--text3)', marginTop: '2px' }}>Good: {good} | Poor: {poor}</div>
                                </div>
                                <span style={{ fontSize: '16px' }}>{icon}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                  <div style={{ fontSize: '11px', color: 'var(--text3)', padding: '8px 10px', background: 'var(--bg3)', borderRadius: '8px', textAlign: 'center' }}>
                    🟢 Good &nbsp;|&nbsp; 🟡 Needs Improvement &nbsp;|&nbsp; 🔴 Poor &nbsp;|&nbsp; Data from Google PageSpeed Insights
                  </div>
                </div>
              )}
            </Card>

            {/* Content Analysis Deep Dive */}"""

if old_marker in content:
    content = content.replace(old_marker, new_cwv)
    print("Core Web Vitals card added!")
else:
    print("ERROR: marker not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))

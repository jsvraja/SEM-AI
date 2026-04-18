path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add Search Console state
old_state = """  const [expandedFix, setExpandedFix] = useState(null)"""
new_state = """  const [expandedFix, setExpandedFix] = useState(null)
  const [scConnected, setScConnected] = useState(false)
  const [scData, setScData] = useState(null)
  const [scLoading, setScLoading] = useState(false)
  const scSessionId = 'default'"""

content = content.replace(old_state, new_state)

# Add Search Console card after Core Web Vitals in SEO tab
old_marker = """            {/* AI Fix Suggestions */}"""

new_sc_card = """            {/* Search Console Data */}
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <SectionTitle icon={Search}>Search Console Data</SectionTitle>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  {scConnected && <span style={{ fontSize: '11px', color: 'var(--green)', fontWeight: 600 }}>✅ Connected</span>}
                  {!scConnected ? (
                    <button onClick={async () => {
                      try {
                        const res = await fetch('https://sem-ai-production.up.railway.app/api/search-console/auth?session_id=' + scSessionId)
                        const data = await res.json()
                        if (data.auth_url) {
                          const popup = window.open(data.auth_url, 'SC Auth', 'width=500,height=600')
                          window.addEventListener('message', async (e) => {
                            if (e.data?.type === 'SC_AUTH_SUCCESS') {
                              popup?.close()
                              setScConnected(true)
                              // Auto fetch data
                              setScLoading(true)
                              const dr = await fetch('https://sem-ai-production.up.railway.app/api/search-console/data', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ url, session_id: scSessionId })
                              })
                              const dd = await dr.json()
                              setScData(dd)
                              setScLoading(false)
                            }
                          }, { once: true })
                        }
                      } catch(e) { console.error(e) }
                    }} style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '8px', background: '#4285f4', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>🔍</span> Connect Google Search Console
                    </button>
                  ) : (
                    <button onClick={async () => {
                      setScLoading(true)
                      const res = await fetch('https://sem-ai-production.up.railway.app/api/search-console/data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, session_id: scSessionId })
                      })
                      const data = await res.json()
                      setScData(data)
                      setScLoading(false)
                    }} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text3)', cursor: 'pointer' }}>↺ Refresh</button>
                  )}
                </div>
              </div>

              {!scConnected && !scData && (
                <div style={{ textAlign: 'center', padding: '24px', background: 'var(--bg3)', borderRadius: '10px' }}>
                  <div style={{ fontSize: '32px', marginBottom: '8px' }}>📊</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>Connect Google Search Console</div>
                  <div style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.6 }}>
                    Get real impressions, clicks, rankings and keyword data directly from Google.<br/>
                    <span style={{ color: 'var(--accent)' }}>Your data stays private — read-only access only.</span>
                  </div>
                </div>
              )}

              {scLoading && (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text3)', fontSize: '13px' }}>
                  ⏳ Fetching Search Console data...
                </div>
              )}

              {scData?.error && (
                <div style={{ color: 'var(--red)', fontSize: '13px', padding: '10px', background: 'var(--red-bg)', borderRadius: '8px' }}>
                  ⚠ {scData.error}
                </div>
              )}

              {scData?.connected && scData?.page_metrics && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Page metrics */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '8px' }}>
                    {[
                      { label: 'Total Clicks', value: scData.page_metrics.clicks.toLocaleString(), color: 'var(--accent)', icon: '👆' },
                      { label: 'Impressions', value: scData.page_metrics.impressions.toLocaleString(), color: 'var(--cyan)', icon: '👁' },
                      { label: 'Avg CTR', value: scData.page_metrics.ctr + '%', color: scData.page_metrics.ctr >= 3 ? 'var(--green)' : 'var(--yellow)', icon: '📈' },
                      { label: 'Avg Position', value: '#' + scData.page_metrics.position, color: scData.page_metrics.position <= 10 ? 'var(--green)' : scData.page_metrics.position <= 20 ? 'var(--yellow)' : 'var(--red)', icon: '🏆' },
                    ].map(({ label, value, color, icon }) => (
                      <div key={label} style={{ textAlign: 'center', padding: '12px 8px', background: 'var(--bg3)', borderRadius: '10px' }}>
                        <div style={{ fontSize: '18px', marginBottom: '4px' }}>{icon}</div>
                        <div style={{ fontSize: '20px', fontWeight: 800, color }}>{value}</div>
                        <div style={{ fontSize: '10px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '2px' }}>{label}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', textAlign: 'center' }}>{scData.period}</div>

                  {/* Top queries */}
                  {scData.top_queries?.length > 0 && (
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>🔑 Top Search Queries</div>
                      <div style={{ border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                          <thead style={{ background: 'var(--bg3)' }}>
                            <tr>
                              {['Keyword', 'Clicks', 'Impressions', 'CTR', 'Position'].map(h => (
                                <th key={h} style={{ padding: '7px 10px', textAlign: h === 'Keyword' ? 'left' : 'center', color: 'var(--text3)', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {scData.top_queries.map((q, i) => (
                              <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--bg)' : 'var(--bg3)' }}>
                                <td style={{ padding: '6px 10px', color: 'var(--accent)', fontWeight: 500 }}>{q.keyword}</td>
                                <td style={{ padding: '6px 10px', textAlign: 'center', color: 'var(--text2)', fontWeight: 600 }}>{q.clicks}</td>
                                <td style={{ padding: '6px 10px', textAlign: 'center', color: 'var(--text3)' }}>{q.impressions}</td>
                                <td style={{ padding: '6px 10px', textAlign: 'center', color: q.ctr >= 3 ? 'var(--green)' : 'var(--yellow)' }}>{q.ctr}%</td>
                                <td style={{ padding: '6px 10px', textAlign: 'center', color: q.position <= 10 ? 'var(--green)' : q.position <= 20 ? 'var(--yellow)' : 'var(--red)', fontWeight: 700 }}>#{Math.round(q.position)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* AI Fix Suggestions */}"""

if old_marker in content:
    content = content.replace(old_marker, new_sc_card)
    print("Search Console card added!")
else:
    print("ERROR: marker not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))

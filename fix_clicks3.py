path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

old = """                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      \u20b9{seo?.sem_recommendations?.estimated_cpc_inr || 0} avg CPC
                    </div>
                  </>
                )}
            """

new = """                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      \u20b9{seo?.sem_recommendations?.estimated_cpc_inr || 0} avg CPC
                    </div>
                    {(() => {
                      const sem = seo.sem_recommendations
                      const budget = sem?.monthly_budget_inr || 0
                      const cpc = sem?.estimated_cpc_inr || 30
                      const baseClicks = cpc > 0 ? Math.round(budget / cpc) : 0
                      const low = Math.round(baseClicks * 0.8)
                      const high = Math.round(baseClicks * 1.2)
                      const cbs = sem?.country_budgets || []
                      return (
                        <div style={{ marginTop: '8px', padding: '8px', background: 'var(--bg3)', borderRadius: '8px', fontSize: '11px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>How calculated:</div>
                          <div style={{ color: 'var(--text3)', lineHeight: 1.6 }}>
                            <div>📊 Budget: \u20b9{budget.toLocaleString()}/mo</div>
                            <div>💰 Avg CPC: \u20b9{cpc}</div>
                            <div>📐 \u20b9{budget.toLocaleString()} ÷ \u20b9{cpc} = {baseClicks.toLocaleString()} clicks</div>
                            <div>📈 Range: ±20% ({low.toLocaleString()} – {high.toLocaleString()})</div>
                          </div>
                          {cbs.length > 0 && (
                            <div style={{ marginTop: '6px', borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>By Market:</div>
                              {cbs.map((cb, i) => {
                                const flags = {IN:'🇮🇳',US:'🇺🇸',GB:'🇬🇧',UK:'🇬🇧',AU:'🇦🇺',CA:'🇨🇦',SG:'🇸🇬',AE:'🇦🇪'}
                                const flag = flags[cb.code] || '🌍'
                                return (
                                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text3)', marginBottom: '2px' }}>
                                    <span>{flag} {cb.country}</span>
                                    <span style={{ color: 'var(--cyan)', fontWeight: 600 }}>{cb.monthly_clicks}</span>
                                  </div>
                                )
                              })}
                            </div>
                          )}
                          <div style={{ marginTop: '4px', padding: '4px 6px', background: 'var(--accent-bg)', borderRadius: '5px', color: 'var(--accent)', fontSize: '10px' }}>
                            💡 Higher budget or lower CPC = more clicks
                          </div>
                        </div>
                      )
                    })()}
                  </>
                )}
            """

if old in content:
    content = content.replace(old, new)
    print("Fixed!")
else:
    print("ERROR: not found")
    # Debug
    idx = content.find('estimated_cpc_inr || 0} avg CPC')
    print("CPC line context:", repr(content[idx:idx+100]))

with open(path, 'w') as f:
    f.write(content)

# Also update frontend
path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Both files updated, size:", len(content))

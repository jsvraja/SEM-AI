path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

old = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Est. Monthly Clicks</div>
                {seo.sem_recommendations && (
                  <>
                    <div style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--cyan)' }}>
                      {seo?.sem_recommendations?.estimated_monthly_clicks ? `${(seo.sem_recommendations.estimated_monthly_clicks.min || 0).toLocaleString()}-${(seo.sem_recommendations.estimated_monthly_clicks.max || 0).toLocaleString()}` : (seo?.sem_recommendations?.monthly_clicks_estimate || "N/A")}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>
                      ₹{seo?.sem_recommendations?.estimated_cpc_inr || seo?.sem_recommendations?.estimated_cpc_usd?.min || 0} avg CPC"""

new = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '8px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Est. Monthly Clicks</div>
                {seo.sem_recommendations && (
                  <>
                    <div style={{ fontSize: '28px', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--cyan)' }}>
                      {seo?.sem_recommendations?.estimated_monthly_clicks ? `${(seo.sem_recommendations.estimated_monthly_clicks.min || 0).toLocaleString()}-${(seo.sem_recommendations.estimated_monthly_clicks.max || 0).toLocaleString()}` : (seo?.sem_recommendations?.monthly_clicks_estimate || "N/A")}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      ₹{seo?.sem_recommendations?.estimated_cpc_inr || 0} avg CPC"""

content = content.replace(old, new)

# Find closing of Est Monthly Clicks card and add breakdown before it
old2 = """                    <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>
                      ₹{seo?.sem_recommendations?.estimated_cpc_inr || seo?.sem_recommendations?.estimated_cpc_usd?.min || 0} avg CPC
                    </div>
                  </>
                )}
              </Card>

              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Page Stats</div>"""

new2 = """                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      ₹{seo?.sem_recommendations?.estimated_cpc_inr || 0} avg CPC
                    </div>
                    {(() => {
                      const sem = seo.sem_recommendations
                      const budget = sem?.monthly_budget_inr || 0
                      const cpc = sem?.estimated_cpc_inr || 30
                      const baseClicks = cpc > 0 ? Math.round(budget / cpc) : 0
                      const low = Math.round(baseClicks * 0.8)
                      const high = Math.round(baseClicks * 1.2)
                      const countryBudgets = sem?.country_budgets || []
                      return (
                        <div style={{ marginTop: '8px', padding: '8px', background: 'var(--bg3)', borderRadius: '8px', fontSize: '11px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>How calculated:</div>
                          <div style={{ color: 'var(--text3)', lineHeight: 1.6 }}>
                            <div>📊 Budget: ₹{budget.toLocaleString()}/mo</div>
                            <div>💰 Avg CPC: ₹{cpc}</div>
                            <div>📐 Formula: ₹{budget.toLocaleString()} ÷ ₹{cpc} = {baseClicks.toLocaleString()} clicks</div>
                            <div>📈 Range: ±20% ({low.toLocaleString()} – {high.toLocaleString()})</div>
                          </div>
                          {countryBudgets.length > 0 && (
                            <div style={{ marginTop: '6px', borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text2)', marginBottom: '4px' }}>By Market:</div>
                              {countryBudgets.map((cb, i) => {
                                const flag = {IN:'🇮🇳',US:'🇺🇸',GB:'🇬🇧',UK:'🇬🇧',AU:'🇦🇺',CA:'🇨🇦',SG:'🇸🇬',AE:'🇦🇪'}[cb.code] || '🌍'
                                return (
                                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text3)', marginBottom: '2px' }}>
                                    <span>{flag} {cb.country}</span>
                                    <span style={{ color: 'var(--cyan)', fontWeight: 600 }}>{cb.monthly_clicks} clicks</span>
                                  </div>
                                )
                              })}
                            </div>
                          )}
                          <div style={{ marginTop: '4px', padding: '4px 6px', background: 'var(--accent-bg)', borderRadius: '5px', color: 'var(--accent)', fontSize: '10px', lineHeight: 1.5 }}>
                            💡 Higher budget or lower CPC keywords = more clicks
                          </div>
                        </div>
                      )
                    })()}
                  </>
                )}
              </Card>

              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Page Stats</div>"""

content = content.replace(old2, new2)

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("Done!")
print("Has How calculated:", "How calculated:" in content)
print("Has By Market:", "By Market:" in content)

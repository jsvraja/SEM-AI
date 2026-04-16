import os

# Try both possible paths
paths = [
    '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx',
    '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx',
]

for path in paths:
    if not os.path.exists(path):
        print(f"Not found: {path}")
        continue
    
    with open(path) as f:
        content = f.read()
    
    if 'country_budgets' in content:
        print(f"Already has country_budgets: {path}")
        continue

    old = """                  <Card>
                    <SectionTitle icon={Globe}>Target Countries</SectionTitle>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {(seo.sem_recommendations.target_countries || []).map((c, i) => (
                        <span key={i} className="badge badge-blue">{c}</span>
                      ))}
                    </div>
                  </Card>"""

    new = """                  <Card>
                    <SectionTitle icon={Globe}>Country-Wise Budget</SectionTitle>
                    {(seo.sem_recommendations.country_budgets || []).length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {(seo.sem_recommendations.country_budgets || []).map((cb, i) => {
                          const cc = cb.competition === 'high' ? 'var(--red)' : cb.competition === 'medium' ? 'var(--yellow)' : 'var(--green)'
                          const cbg = cb.competition === 'high' ? 'var(--red-bg)' : cb.competition === 'medium' ? 'var(--yellow-bg)' : 'var(--green-bg)'
                          const flag = {IN:'🇮🇳',US:'🇺🇸',GB:'🇬🇧',UK:'🇬🇧',AU:'🇦🇺',CA:'🇨🇦',SG:'🇸🇬',AE:'🇦🇪'}[cb.code] || '🌍'
                          return (
                            <div key={i} style={{ padding: '10px 12px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <span style={{ fontSize: '16px' }}>{flag}</span>
                                  <div>
                                    <div style={{ fontSize: '12px', fontWeight: 600 }}>{cb.country}</div>
                                    <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{cb.notes}</div>
                                  </div>
                                </div>
                                <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: cbg, color: cc, fontWeight: 500 }}>{cb.competition}</span>
                              </div>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '4px' }}>
                                {[
                                  { label: 'Budget', val: '\\u20b9' + (cb.budget_inr||0).toLocaleString(), color: 'var(--green)' },
                                  { label: 'Share', val: cb.budget_pct + '%', color: 'var(--accent)' },
                                  { label: 'Avg CPC', val: '\\u20b9' + cb.avg_cpc_inr, color: 'var(--yellow)' },
                                  { label: 'Clicks', val: cb.monthly_clicks, color: 'var(--cyan)' },
                                ].map(({ label, val, color }) => (
                                  <div key={label} style={{ textAlign: 'center', padding: '5px', background: 'var(--bg4)', borderRadius: '5px' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 700, color }}>{val}</div>
                                    <div style={{ fontSize: '9px', color: 'var(--text3)', textTransform: 'uppercase' }}>{label}</div>
                                  </div>
                                ))}
                              </div>
                              <div style={{ marginTop: '6px', height: '4px', background: 'var(--bg4)', borderRadius: '2px' }}>
                                <div style={{ height: '100%', width: cb.budget_pct + '%', background: 'var(--accent)', borderRadius: '2px' }} />
                              </div>
                            </div>
                          )
                        })}
                        <div style={{ padding: '8px 10px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: '8px', fontSize: '11px', color: 'var(--accent-text)', lineHeight: 1.5 }}>
                          US/UK markets cost more per click but deliver higher-value leads. India offers volume at lower cost.
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {(seo.sem_recommendations.target_countries || []).map((c, i) => (
                          <span key={i} className="badge badge-blue">{c}</span>
                        ))}
                      </div>
                    )}
                  </Card>"""

    if old in content:
        content = content.replace(old, new)
        with open(path, 'w') as f:
            f.write(content)
        print(f"Patched: {path}")
    else:
        print(f"Target Countries section not found in: {path}")
        # Show what's near Globe in SEM tab
        idx = content.find("tab === 'sem'")
        sem_block = content[idx:idx+3000]
        globe_idx = sem_block.find('Globe')
        print("Globe context:", sem_block[globe_idx-50:globe_idx+200])

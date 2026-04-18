path = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Competitor.jsx'
with open(path) as f:
    content = f.read()

old = """          {/* Score comparison */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px' }}>Score Comparison</div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: 'var(--accent-bg)', borderRadius: '10px', border: '1px solid var(--accent-border)', flex: 1, minWidth: '140px' }}>
                <ScoreBadge score={results.my_site?.score || 0} />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{results.my_site?.domain}</div>
                  <div style={{ fontSize: '11px', color: 'var(--accent)' }}>Your site</div>
                </div>
              </div>
              {(results.competitors || []).map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)', flex: 1, minWidth: '140px' }}>
                  <ScoreBadge score={c.estimated_score || 0} />
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600 }}>{c.domain}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{c.estimated_traffic}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>"""

new = """          {/* Score Card */}
          <Card>
            <div style={{ fontSize: '12px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '16px' }}>📊 Competitor Score Card</div>
            {/* Header row */}
            <div style={{ display: 'grid', gridTemplateColumns: '140px repeat(' + (1 + (results.competitors?.length || 0)) + ', 1fr)', gap: '8px', marginBottom: '8px' }}>
              <div />
              <div style={{ textAlign: 'center', padding: '10px', background: 'var(--accent-bg)', borderRadius: '10px', border: '2px solid var(--accent)' }}>
                <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--accent)' }}>{results.my_site?.score || 0}</div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent)' }}>YOUR SITE</div>
                <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{results.my_site?.domain}</div>
              </div>
              {(results.competitors || []).map((c, i) => {
                const myScore = results.my_site?.score || 0
                const diff = (c.estimated_score || 0) - myScore
                return (
                  <div key={i} style={{ textAlign: 'center', padding: '10px', background: 'var(--bg3)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '24px', fontWeight: 800, color: c.estimated_score >= myScore ? 'var(--red)' : 'var(--green)' }}>{c.estimated_score || 0}</div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)' }}>COMPETITOR {i+1}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)' }}>{c.domain}</div>
                    <div style={{ fontSize: '11px', fontWeight: 700, marginTop: '2px', color: diff > 0 ? 'var(--red)' : 'var(--green)' }}>
                      {diff > 0 ? '▲ +' + diff : '▼ ' + diff} vs you
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Comparison rows */}
            {[
              { label: 'SEO Score', myVal: results.my_site?.score || 0, getVal: c => c.estimated_score || 0, unit: '/100', isScore: true },
              { label: 'Est. Traffic', myVal: 'Your site', getVal: c => c.estimated_traffic || 'N/A', unit: '', isScore: false },
              { label: 'Top Keywords', myVal: (results.my_site?.strengths?.[0] || 'See SEO Report'), getVal: c => c.top_keywords?.slice(0,2).join(', ') || 'N/A', unit: '', isScore: false },
              { label: 'Ad Strategy', myVal: 'Your campaigns', getVal: c => c.ad_strategy?.slice(0,40) + '...' || 'N/A', unit: '', isScore: false },
            ].map(({ label, myVal, getVal, unit, isScore }) => (
              <div key={label} style={{ display: 'grid', gridTemplateColumns: '140px repeat(' + (1 + (results.competitors?.length || 0)) + ', 1fr)', gap: '8px', marginBottom: '6px', alignItems: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                <div style={{ padding: '6px 10px', background: 'var(--accent-bg)', borderRadius: '6px', fontSize: '12px', fontWeight: isScore ? 700 : 400, color: 'var(--accent)', textAlign: 'center' }}>
                  {myVal}{unit}
                </div>
                {(results.competitors || []).map((c, i) => {
                  const val = getVal(c)
                  const myScore = results.my_site?.score || 0
                  const worse = isScore && typeof val === 'number' && val > myScore
                  return (
                    <div key={i} style={{ padding: '6px 10px', background: 'var(--bg3)', borderRadius: '6px', fontSize: '12px', fontWeight: isScore ? 700 : 400, color: worse ? 'var(--red)' : 'var(--text2)', textAlign: 'center' }}>
                      {val}{unit}
                    </div>
                  )
                })}
              </div>
            ))}

            {/* Winner badge */}
            {(() => {
              const myScore = results.my_site?.score || 0
              const allScores = (results.competitors || []).map(c => c.estimated_score || 0)
              const maxComp = Math.max(...allScores)
              const isWinning = myScore >= maxComp
              return (
                <div style={{ marginTop: '12px', padding: '10px 14px', borderRadius: '10px', background: isWinning ? 'var(--green-bg)' : 'var(--yellow-bg)', border: '1px solid ' + (isWinning ? 'var(--green)' : 'var(--yellow)'), fontSize: '13px', fontWeight: 600, color: isWinning ? 'var(--green)' : 'var(--yellow)', textAlign: 'center' }}>
                  {isWinning ? '🏆 Your site is leading the competition!' : '⚡ ' + (maxComp - myScore) + ' points behind the leader — see action plan below to catch up'}
                </div>
              )
            })()}
          </Card>"""

if old in content:
    content = content.replace(old, new)
    print("Score Card enhanced!")
else:
    print("ERROR: not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Competitor.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))

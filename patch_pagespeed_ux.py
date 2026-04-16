path = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Fix 1 & 4: Hide PageSpeed card by default, show when button clicked
# Add showGoogleScore state
old_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)"""

new_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)
  const [showGoogleScore, setShowGoogleScore] = useState(false)"""

content = content.replace(old_state, new_state)

# Fix 2 & 3: Update SEO Health card to add disclaimer and Google Score button
old_seo_card = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEO Health</div>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginBottom: '12px' }}>
                  <ScoreRing score={seo.overall_seo_score} label="Overall SEO" />
                  <ScoreRing score={seo.content_analysis?.quality_score || seo.content_analysis?.readability_score || (seo.overall_seo_score ? Math.round(seo.overall_seo_score * 0.8) : 0)} label="Content" />
                </div>"""

new_seo_card = """              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEO Health <span style={{ color: 'var(--text3)', fontSize: '10px', fontWeight: 400 }}>(Our Score)</span></div>
                  <button onClick={() => { setShowGoogleScore(true); if (!pageSpeed && !loadingSpeed) { setLoadingSpeed(true); fetch('https://sem-ai-production.up.railway.app/api/pagespeed', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({url}) }).then(r=>r.json()).then(d=>{setPageSpeed(d);setLoadingSpeed(false)}).catch(()=>setLoadingSpeed(false)) } }} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '6px', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {loadingSpeed ? '⏳' : '🔍'} {loadingSpeed ? 'Loading...' : 'Google Score'}
                  </button>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginBottom: '12px' }}>
                  <ScoreRing score={seo.overall_seo_score} label="Overall SEO" />
                  <ScoreRing score={seo.content_analysis?.quality_score || seo.content_analysis?.readability_score || (seo.overall_seo_score ? Math.round(seo.overall_seo_score * 0.8) : 0)} label="Content" />
                </div>"""

content = content.replace(old_seo_card, new_seo_card)

# Add disclaimer at end of SEO Health card (after score breakdown)
old_disclaimer = """                      <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text3)', padding: '6px 8px', background: 'var(--bg3)', borderRadius: '6px', lineHeight: 1.5 }}>
                        💡 <strong>How scores work:</strong> Each factor is evaluated based on your page content. Hover each bar for details.
                      </div>"""

new_disclaimer = """                      <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text3)', padding: '6px 8px', background: 'var(--bg3)', borderRadius: '6px', lineHeight: 1.5 }}>
                        💡 <strong>How scores work:</strong> Each factor is evaluated based on your page content. Hover each bar for details.
                      </div>
                      <div style={{ marginTop: '6px', fontSize: '10px', color: 'var(--text3)', padding: '5px 8px', background: 'var(--yellow-bg)', borderRadius: '6px', lineHeight: 1.5, border: '1px solid var(--yellow)' }}>
                        ⚠ Scores based on raw HTML. JS-rendered sites may show different values. Click "Google Score" for full accuracy.
                      </div>"""

content = content.replace(old_disclaimer, new_disclaimer)

# Fix 4: Hide PageSpeed card by default, show only when showGoogleScore is true
# Also replace the top 4 cards row when Google Score is shown
old_top_row = """            {/* Score row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>"""

new_top_row = """            {/* Score row */}
            <div style={{ display: 'grid', gridTemplateColumns: showGoogleScore && pageSpeed ? '1fr' : 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>"""

content = content.replace(old_top_row, new_top_row)

# Hide PageSpeed card unless showGoogleScore
old_ps_card = "            {/* PageSpeed Insights */}\n            <Card>"
new_ps_card = "            {/* PageSpeed Insights */}\n            {showGoogleScore && <Card>"

content = content.replace(old_ps_card, new_ps_card)

# Close the conditional Card
# Find the closing of PageSpeed card
old_ps_end = """              )}
            </Card>

            {/* Summary */}"""
new_ps_end = """              )}
            </Card>}

            {/* Summary */}"""

content = content.replace(old_ps_end, new_ps_end)

# When showGoogleScore, show Google scores instead of budget/clicks/pagestats
old_budget_card = """              <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>"""

new_budget_card = """              {!showGoogleScore && <Card>
                <div style={{ fontSize: '11px', color: 'var(--text3)', marginBottom: '12px', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Budget Range</div>"""

content = content.replace(old_budget_card, new_budget_card)

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("Done!")
print("showGoogleScore state:", "showGoogleScore" in content)
print("Google Score button:", "Google Score" in content)
print("Disclaimer:", "JS-rendered sites" in content)

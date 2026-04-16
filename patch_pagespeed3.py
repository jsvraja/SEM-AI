path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Fix 1: Remove Google branding
content = content.replace('PageSpeed Insights (Google)', 'Page Performance Analysis')
content = content.replace('🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor &nbsp;&nbsp; Powered by Google PageSpeed Insights', '🟢 90-100 Good &nbsp;|&nbsp; 🟡 50-89 Needs Improvement &nbsp;|&nbsp; 🔴 0-49 Poor')
content = content.replace('Click "Run PageSpeed Test" to get real Performance, SEO, Accessibility & Best Practices scores from Google', 'Click "Analyse Performance" to get real Performance, SEO, Accessibility & Best Practices scores')
content = content.replace("'🚀 Run PageSpeed Test'", "'⚡ Analyse Performance'")
content = content.replace('PAGESPEED INSIGHTS (GOOGLE)', 'PAGE PERFORMANCE ANALYSIS')

# Fix 2: Auto-load when URL is analysed - add useEffect
old_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)"""

new_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)

  // Auto-load PageSpeed when analysis is done
  useEffect(() => {
    if (url && !pageSpeed && !loadingSpeed) {
      const fetchSpeed = async () => {
        setLoadingSpeed(true)
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
      }
      // Small delay to not block initial render
      setTimeout(fetchSpeed, 2000)
    }
  }, [url])"""

content = content.replace(old_state, new_state)

# Fix 3: Update design to match our theme - score cards with circle style like ScoreRing
old_scores = """                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '8px', marginBottom: '10px' }}>
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
                        </div>"""

new_scores = """                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px', marginBottom: '12px' }}>
                          {[
                            { label: 'Performance', score: r.performance, icon: '⚡' },
                            { label: 'SEO', score: r.seo, icon: '🔍' },
                            { label: 'Accessibility', score: r.accessibility, icon: '♿' },
                            { label: 'Best Practices', score: r.best_practices, icon: '✅' },
                          ].map(({ label, score, icon }) => {
                            const c = score >= 90 ? 'var(--green)' : score >= 50 ? 'var(--yellow)' : 'var(--red)'
                            const bg = score >= 90 ? 'var(--green-bg)' : score >= 50 ? 'var(--yellow-bg)' : 'var(--red-bg)'
                            return (
                              <div key={label} style={{ textAlign: 'center', padding: '12px 6px', background: bg, borderRadius: '12px', border: `1px solid ${c}` }}>
                                <div style={{ fontSize: '11px', marginBottom: '4px' }}>{icon}</div>
                                <div style={{ fontSize: '26px', fontWeight: 800, color: c, letterSpacing: '-0.03em' }}>{score}</div>
                                <div style={{ fontSize: '10px', color: c, textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '2px', fontWeight: 600 }}>{label}</div>
                              </div>
                            )
                          })}
                        </div>"""

content = content.replace(old_scores, new_scores)

# Fix mobile/desktop headers style
content = content.replace(
    "strategy === 'mobile' ? '📱 Mobile' : '🖥️ Desktop'",
    "strategy === 'mobile' ? '📱 Mobile' : '🖥 Desktop'"
)

# Fix section title
content = content.replace(
    '<SectionTitle icon={BarChart3}>Page Performance Analysis</SectionTitle>',
    '<div style={{ fontSize: \'13px\', fontWeight: 700, color: \'var(--text)\' }}>⚡ Performance Analysis</div>'
)

with open(path, 'w') as f:
    f.write(content)

# Also update local frontend
path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)

print("All 3 fixes applied!")
print("Auto-load useEffect:", "Auto-load PageSpeed" in content)
print("Google removed:", "Google" not in content[content.find("Page Performance"):content.find("Page Performance")+200])

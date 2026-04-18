path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add trend tracking - save score on each analysis
# Add useEffect to save trend data when seo data loads
old_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)
  const [showGoogleScore, setShowGoogleScore] = useState(false)"""

new_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)
  const [showGoogleScore, setShowGoogleScore] = useState(false)
  const [trendData, setTrendData] = useState([])

  // Save SEO score trend to sessionStorage on each analysis
  useEffect(() => {
    if (!seo?.overall_seo_score || !url) return
    try {
      const key = 'seo_trend_' + url.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 50)
      const existing = JSON.parse(localStorage.getItem(key) || '[]')
      const today = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
      const last = existing[existing.length - 1]
      // Only add if date changed or first entry
      if (!last || last.date !== today) {
        const newEntry = { date: today, score: seo.overall_seo_score, content: seo.content_analysis?.quality_score || 0 }
        const updated = [...existing, newEntry].slice(-10) // Keep last 10
        localStorage.setItem(key, JSON.stringify(updated))
        setTrendData(updated)
      } else {
        setTrendData(existing)
      }
    } catch(e) {}
  }, [seo?.overall_seo_score, url])"""

content = content.replace(old_state, new_state)

# Add SEO Trend card after Quick Wins section
old_trend = """            {/* SERP Preview */}"""

new_trend = """            {/* SEO Health Trend */}
            {trendData.length >= 2 && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <SectionTitle icon={TrendingUp}>SEO Health Trend</SectionTitle>
                  <div style={{ fontSize: '11px', color: 'var(--text3)' }}>Last {trendData.length} analyses</div>
                </div>
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text3)' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text3)' }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                      formatter={(val, name) => [val + '/100', name === 'score' ? 'SEO Score' : 'Content Score']}
                    />
                    <Line type="monotone" dataKey="score" stroke="var(--accent)" strokeWidth={2} dot={{ fill: 'var(--accent)', r: 4 }} name="score" />
                    <Line type="monotone" dataKey="content" stroke="var(--cyan)" strokeWidth={2} dot={{ fill: 'var(--cyan)', r: 4 }} name="content" strokeDasharray="4 4" />
                  </LineChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginTop: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: 'var(--text3)' }}>
                    <div style={{ width: '16px', height: '2px', background: 'var(--accent)' }} /> SEO Score
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: 'var(--text3)' }}>
                    <div style={{ width: '16px', height: '2px', background: 'var(--cyan)', borderTop: '2px dashed var(--cyan)' }} /> Content Score
                  </div>
                </div>
                {(() => {
                  const first = trendData[0]?.score || 0
                  const last = trendData[trendData.length - 1]?.score || 0
                  const diff = last - first
                  if (diff === 0) return null
                  return (
                    <div style={{ marginTop: '8px', padding: '6px 10px', borderRadius: '6px', background: diff > 0 ? 'var(--green-bg)' : 'var(--red-bg)', border: '1px solid ' + (diff > 0 ? 'var(--green)' : 'var(--red)'), fontSize: '12px', color: diff > 0 ? 'var(--green)' : 'var(--red)', fontWeight: 600, textAlign: 'center' }}>
                      {diff > 0 ? '📈 Improved by +' + diff + ' points since first analysis!' : '📉 Dropped by ' + Math.abs(diff) + ' points — check what changed'}
                    </div>
                  )
                })()}
              </Card>
            )}
            {trendData.length === 1 && (
              <Card>
                <SectionTitle icon={TrendingUp}>SEO Health Trend</SectionTitle>
                <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text3)', fontSize: '12px' }}>
                  📊 Re-analyse this URL tomorrow to start tracking your SEO score trend over time
                </div>
              </Card>
            )}

            {/* SERP Preview */}"""

if old_trend in content:
    content = content.replace(old_trend, new_trend)
    print("Trend tracker added!")
else:
    print("ERROR: SERP Preview marker not found")

# Also need LineChart import - check recharts imports
if 'LineChart' not in content:
    content = content.replace(
        'BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,',
        'BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,'
    )
    print("Added LineChart import!")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done! Size:", len(content))

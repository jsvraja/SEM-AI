path = '/Users/sakthivel-1528/Personal/sem-app/backend/frontend/src/components/Dashboard.jsx'
with open(path) as f:
    content = f.read()

# Add trendData state
old_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)
  const [showGoogleScore, setShowGoogleScore] = useState(false)"""

new_state = """  const [pageSpeed, setPageSpeed] = useState(null)
  const [loadingSpeed, setLoadingSpeed] = useState(false)
  const [showGoogleScore, setShowGoogleScore] = useState(false)
  const [trendData, setTrendData] = useState(null)

  // Fetch trend data after analysis
  useEffect(() => {
    if (!url || !seo?.overall_seo_score) return
    fetch('https://sem-ai-production.up.railway.app/api/seo-trend?url=' + encodeURIComponent(url))
      .then(r => r.json())
      .then(d => setTrendData(d.trend || []))
      .catch(() => {})
  }, [seo?.overall_seo_score])"""

content = content.replace(old_state, new_state)

# Add LineChart import if missing
if 'LineChart' not in content:
    content = content.replace(
        'BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,',
        'BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,'
    )

# Add trend card before SERP Preview
old_serp = """            {/* SERP Preview */}"""

new_serp = """            {/* SEO Health Trend */}
            {trendData && trendData.length >= 2 && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <SectionTitle icon={TrendingUp}>SEO Health Trend</SectionTitle>
                  <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Last {trendData.length} analyses</span>
                </div>
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text3)' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text3)' }} />
                    <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }} formatter={(v, n) => [v + '/100', n === 'score' ? 'SEO Score' : 'Content']} />
                    <Line type="monotone" dataKey="score" stroke="var(--accent)" strokeWidth={2} dot={{ fill: 'var(--accent)', r: 4 }} name="score" />
                    <Line type="monotone" dataKey="content" stroke="var(--cyan)" strokeWidth={2} dot={{ fill: 'var(--cyan)', r: 3 }} strokeDasharray="4 4" name="content" />
                  </LineChart>
                </ResponsiveContainer>
                {(() => {
                  const diff = (trendData[trendData.length-1]?.score || 0) - (trendData[0]?.score || 0)
                  if (!diff) return null
                  return (
                    <div style={{ marginTop: '8px', padding: '6px 10px', borderRadius: '6px', background: diff > 0 ? 'var(--green-bg)' : 'var(--red-bg)', border: '1px solid ' + (diff > 0 ? 'var(--green)' : 'var(--red)'), fontSize: '12px', fontWeight: 600, color: diff > 0 ? 'var(--green)' : 'var(--red)', textAlign: 'center' }}>
                      {diff > 0 ? '📈 +' + diff + ' points improvement!' : '📉 ' + diff + ' points — check what changed'}
                    </div>
                  )
                })()}
              </Card>
            )}
            {trendData && trendData.length === 1 && (
              <Card>
                <SectionTitle icon={TrendingUp}>SEO Health Trend</SectionTitle>
                <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text3)', fontSize: '12px' }}>
                  📊 Re-analyse this URL to start tracking your SEO score trend over time
                </div>
              </Card>
            )}

            {/* SERP Preview */}"""

if old_serp in content:
    content = content.replace(old_serp, new_serp)
    print("Trend card added!")
else:
    print("ERROR: SERP Preview marker not found")

with open(path, 'w') as f:
    f.write(content)

path2 = '/Users/sakthivel-1528/Personal/sem-app/frontend/src/components/Dashboard.jsx'
with open(path2, 'w') as f:
    f.write(content)
print("Done!")
